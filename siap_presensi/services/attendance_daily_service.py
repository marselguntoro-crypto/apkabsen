"""
Modul Layanan Absensi Harian (AttendanceDailyService) untuk SIAP.
Mengorkestrasi pembentukan data absensi harian (attendance_daily) dengan memadukan:
1. Master Karyawan Aktif
2. Kalender Hari Kerja (work_calendars)
3. Data Transaksi Scan Mentah (attendance_raw)
"""
from datetime import date, datetime
import calendar as py_calendar
from typing import Dict, List, Optional, Tuple, Any, Set

from sqlalchemy import and_, or_, func, desc, extract
from sqlalchemy.orm import Session, joinedload

from database.connection import get_db_session
from database.models import (
    Employee,
    EmployeeStatus,
    WorkCalendar,
    CalendarStatus,
    AttendanceRaw,
    AttendanceDaily,
    AttendanceStatus,
    CheckScanStatus,
    AuditLog,
)
from utils.logger import get_logger
from utils.time_parser import parse_time_str

logger = get_logger("AttendanceDailyService")


class AttendanceDailyService:
    """Layanan pembentukan dan pengelolaan absensi harian."""

    @classmethod
    def generate_daily_attendance(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        employee_id: Optional[int] = None,
        mode: str = "GENERATE_NEW",  # GENERATE_NEW | REGENERATE | UPDATE_LATEST
        user_name: str = "ADMIN",
    ) -> Dict[str, Any]:
        """
        Membentuk catatan absensi harian untuk setiap Karyawan Aktif x Hari Kerja.
        Menghubungkan scan masuk (paling awal) dan scan pulang (paling akhir).
        Menandai karyawan yang tidak hadir sebagai TIDAK_ABSEN (tanpa menghitung potongan rupiah).
        """
        with get_db_session() as session:
            # 1. Validasi Keberadaan Kalender Kerja
            working_days = (
                session.query(WorkCalendar)
                .filter(
                    WorkCalendar.year == year,
                    WorkCalendar.month == month,
                    WorkCalendar.is_working_day == True,
                )
                .order_by(WorkCalendar.calendar_date.asc())
                .all()
            )

            if not working_days:
                # Periksa apakah kalender bulan tersebut sudah digenerate sama sekali
                all_calendar_days = (
                    session.query(WorkCalendar)
                    .filter(WorkCalendar.year == year, WorkCalendar.month == month)
                    .count()
                )
                if all_calendar_days == 0:
                    return {
                        "success": False,
                        "error_type": "CALENDAR_NOT_FOUND",
                        "message": f"Kalender kerja untuk periode {month:02d}/{year} belum dibuat. Silakan buka menu Kalender Kerja dan klik 'Generate Kalender' terlebih dahulu.",
                    }
                else:
                    return {
                        "success": False,
                        "error_type": "NO_WORKING_DAYS",
                        "message": f"Tidak ditemukan hari kerja aktif untuk periode {month:02d}/{year} (seluruh tanggal berstatus libur/akhir pekan).",
                    }

            # 2. Ambil Karyawan Aktif
            emp_query = session.query(Employee).filter(Employee.status == EmployeeStatus.AKTIF)
            if unit and unit != "ALL" and unit.strip():
                emp_query = emp_query.filter(Employee.unit == unit)
            if employee_id:
                emp_query = emp_query.filter(Employee.id == employee_id)

            employees: List[Employee] = emp_query.order_by(Employee.nama.asc()).all()

            if not employees:
                return {
                    "success": False,
                    "error_type": "NO_ACTIVE_EMPLOYEES",
                    "message": "Tidak ditemukan data karyawan aktif untuk diproses.",
                }

            start_date = date(year, month, 1)
            end_date = date(year, month, py_calendar.monthrange(year, month)[1])

            # 3. Ambil seluruh transaksi attendance_raw pada periode bulan & tahun ini
            raw_records: List[AttendanceRaw] = (
                session.query(AttendanceRaw)
                .filter(
                    AttendanceRaw.tanggal >= start_date,
                    AttendanceRaw.tanggal <= end_date,
                )
                .all()
            )

            # Mapping Data Mentah per Karyawan dan per Tanggal
            # Format: map[(emp_id, tanggal)] -> list of AttendanceRaw
            raw_map: Dict[Tuple[int, date], List[AttendanceRaw]] = {}
            unmatched_raw_ids: Set[int] = set()

            # Index helper karyawan
            emp_by_id = {e.id: e for e in employees}
            emp_by_num = {e.emp_num.strip(): e for e in employees if e.emp_num and e.emp_num.strip()}
            emp_by_no_id = {e.no_id.strip(): e for e in employees if e.no_id and e.no_id.strip()}
            emp_by_name = {e.nama.strip().upper(): e for e in employees if e.nama}

            for raw in raw_records:
                matched_emp: Optional[Employee] = None

                # 1) Direct FK jika sudah dipetakan
                if raw.employee_id and raw.employee_id in emp_by_id:
                    matched_emp = emp_by_id[raw.employee_id]
                # 2) Emp Num + No ID
                elif raw.emp_num and raw.no_id and raw.emp_num.strip() in emp_by_num and raw.no_id.strip() in emp_by_no_id:
                    if emp_by_num[raw.emp_num.strip()].id == emp_by_no_id[raw.no_id.strip()].id:
                        matched_emp = emp_by_num[raw.emp_num.strip()]
                # 3) Emp Num
                elif raw.emp_num and raw.emp_num.strip() in emp_by_num:
                    matched_emp = emp_by_num[raw.emp_num.strip()]
                # 4) No ID
                elif raw.no_id and raw.no_id.strip() in emp_by_no_id:
                    matched_emp = emp_by_no_id[raw.no_id.strip()]
                # 5) Nama Lengkap
                elif raw.nama and raw.nama.strip().upper() in emp_by_name:
                    matched_emp = emp_by_name[raw.nama.strip().upper()]

                if matched_emp:
                    key = (matched_emp.id, raw.tanggal)
                    if key not in raw_map:
                        raw_map[key] = []
                    raw_map[key].append(raw)
                else:
                    unmatched_raw_ids.add(raw.id)

            # 4. Pengambilan Record attendance_daily yang sudah ada untuk periode ini
            existing_daily = (
                session.query(AttendanceDaily)
                .filter(
                    AttendanceDaily.attendance_date >= start_date,
                    AttendanceDaily.attendance_date <= end_date,
                )
                .all()
            )
            daily_by_key = {(d.employee_id, d.attendance_date): d for d in existing_daily}

            created_count = 0
            updated_count = 0
            skipped_count = 0
            hadir_lengkap_count = 0
            hanya_masuk_count = 0
            hanya_pulang_count = 0
            tidak_absen_count = 0
            data_bermasalah_count = 0

            # 5. Iterasi Matriks: Karyawan Aktif x Tanggal Hari Kerja
            for emp in employees:
                for cal in working_days:
                    tgl = cal.calendar_date

                    # Evaluasi tanggal mulai kerja karyawan (jika belum mulai, lewati tanggal ini)
                    if emp.tanggal_mulai and emp.tanggal_mulai > tgl:
                        continue

                    pair_key = (emp.id, tgl)
                    existing_record = daily_by_key.get(pair_key)

                    if mode == "GENERATE_NEW" and existing_record:
                        skipped_count += 1
                        # Update counter statistik
                        if existing_record.attendance_status == AttendanceStatus.HADIR_LENGKAP:
                            hadir_lengkap_count += 1
                        elif existing_record.attendance_status == AttendanceStatus.HANYA_ABSEN_MASUK:
                            hanya_masuk_count += 1
                        elif existing_record.attendance_status == AttendanceStatus.HANYA_ABSEN_PULANG:
                            hanya_pulang_count += 1
                        elif existing_record.attendance_status == AttendanceStatus.TIDAK_ABSEN:
                            tidak_absen_count += 1
                        continue

                    # Jika mode REGENERATE dan record sebelumnya disesuaikan manual
                    if mode == "REGENERATE" and existing_record and existing_record.is_manually_adjusted:
                        # Pertahankan jika ada penyesuaian manual dan tidak dipaksa
                        skipped_count += 1
                        continue

                    # Ambil list transaksi mentah yang relevan
                    raw_list = raw_map.get(pair_key, [])

                    # Analisis Waktu Scan
                    scan_in_list = []
                    scan_out_list = []
                    raw_in_id = None
                    raw_out_id = None
                    has_conflict = False

                    for r in raw_list:
                        in_t = parse_time_str(r.scan_masuk)
                        out_t = parse_time_str(r.scan_pulang)

                        if in_t:
                            scan_in_list.append((in_t, r.id))
                        if out_t:
                            scan_out_list.append((out_t, r.id))

                    # 1. Tentukan Jam Masuk Paling Awal
                    actual_in = None
                    if scan_in_list:
                        scan_in_list.sort(key=lambda x: x[0])
                        actual_in = scan_in_list[0][0]
                        raw_in_id = scan_in_list[0][1]
                        if len(scan_in_list) > 1:
                            has_conflict = True  # Beberapa scan masuk terdeteksi

                    # 2. Tentukan Jam Pulang Paling Akhir
                    actual_out = None
                    if scan_out_list:
                        scan_out_list.sort(key=lambda x: x[0])
                        actual_out = scan_out_list[-1][0]
                        raw_out_id = scan_out_list[-1][1]
                        if len(scan_out_list) > 1:
                            has_conflict = True  # Beberapa scan pulang terdeteksi

                    # Format ke string HH:MM untuk database String(10)
                    actual_in_str = actual_in.strftime("%H:%M") if actual_in else None
                    actual_out_str = actual_out.strftime("%H:%M") if actual_out else None

                    # 3. Status Kehadiran
                    check_in_st = CheckScanStatus.ADA if actual_in else CheckScanStatus.TIDAK_ADA
                    check_out_st = CheckScanStatus.ADA if actual_out else CheckScanStatus.TIDAK_ADA
                    has_incomplete = False

                    if actual_in and actual_out:
                        att_status = AttendanceStatus.HADIR_LENGKAP
                        hadir_lengkap_count += 1
                    elif actual_in and not actual_out:
                        att_status = AttendanceStatus.HANYA_ABSEN_MASUK
                        has_incomplete = True
                        hanya_masuk_count += 1
                    elif not actual_in and actual_out:
                        att_status = AttendanceStatus.HANYA_ABSEN_PULANG
                        has_incomplete = True
                        hanya_pulang_count += 1
                    else:
                        att_status = AttendanceStatus.TIDAK_ABSEN
                        tidak_absen_count += 1

                    # Catatan
                    notes_list = []
                    if has_incomplete:
                        notes_list.append("Scan tidak lengkap (hanya satu scan)")
                    if has_conflict:
                        notes_list.append("Ditemukan beberapa catatan scan dalam 1 hari")

                    notes_str = "; ".join(notes_list) if notes_list else None

                    # Simpan ke Database (Insert or Update)
                    if existing_record:
                        existing_record.calendar_id = cal.id
                        existing_record.day_name = cal.day_name
                        existing_record.scheduled_check_in = cal.scheduled_check_in
                        existing_record.scheduled_check_out = cal.scheduled_check_out
                        existing_record.actual_check_in = actual_in_str
                        existing_record.actual_check_out = actual_out_str
                        existing_record.check_in_status = check_in_st.value
                        existing_record.check_out_status = check_out_st.value
                        existing_record.attendance_status = att_status.value
                        existing_record.source_raw_in_id = raw_in_id
                        existing_record.source_raw_out_id = raw_out_id
                        existing_record.has_incomplete_scan = has_incomplete
                        existing_record.has_conflict = has_conflict
                        existing_record.notes = notes_str
                        existing_record.updated_at = datetime.utcnow()
                        existing_record.updated_by = user_name
                        updated_count += 1
                    else:
                        new_daily = AttendanceDaily(
                            employee_id=emp.id,
                            attendance_date=tgl,
                            calendar_id=cal.id,
                            day_name=cal.day_name,
                            scheduled_check_in=cal.scheduled_check_in,
                            scheduled_check_out=cal.scheduled_check_out,
                            actual_check_in=actual_in_str,
                            actual_check_out=actual_out_str,
                            check_in_status=check_in_st.value,
                            check_out_status=check_out_st.value,
                            attendance_status=att_status.value,
                            source_raw_in_id=raw_in_id,
                            source_raw_out_id=raw_out_id,
                            has_incomplete_scan=has_incomplete,
                            has_conflict=has_conflict,
                            is_manually_adjusted=False,
                            notes=notes_str,
                            generated_at=datetime.utcnow(),
                            generated_by=user_name,
                            updated_at=datetime.utcnow(),
                            updated_by=user_name,
                        )
                        session.add(new_daily)
                        created_count += 1

            session.flush()

            # Catat Audit Log
            audit_action = "GENERATE_DAILY_ATTENDANCE" if mode == "GENERATE_NEW" else "REGENERATE_DAILY_ATTENDANCE"
            audit = AuditLog(
                action=audit_action,
                module="ATTENDANCE_DAILY",
                description=(
                    f"Generate absensi harian {month:02d}/{year} (Mode: {mode}). "
                    f"Karyawan: {len(employees)}, Hari Kerja: {len(working_days)}. "
                    f"Hasil: {created_count} baru, {updated_count} diperbarui, {skipped_count} dilewati. "
                    f"Hadir: {hadir_lengkap_count}, Masuk Saja: {hanya_masuk_count}, Pulang Saja: {hanya_pulang_count}, Tidak Absen: {tidak_absen_count}."
                ),
                created_at=datetime.utcnow(),
            )
            session.add(audit)

            logger.info(
                f"Absensi harian {month:02d}/{year} selesai: {created_count} baru, {updated_count} update. "
                f"TIDAK_ABSEN: {tidak_absen_count}, HADIR_LENGKAP: {hadir_lengkap_count}"
            )

            return {
                "success": True,
                "mode": mode,
                "year": year,
                "month": month,
                "total_employees": len(employees),
                "total_working_days": len(working_days),
                "created_count": created_count,
                "updated_count": updated_count,
                "skipped_count": skipped_count,
                "hadir_lengkap_count": hadir_lengkap_count,
                "hanya_masuk_count": hanya_masuk_count,
                "hanya_pulang_count": hanya_pulang_count,
                "tidak_absen_count": tidak_absen_count,
                "data_bermasalah_count": data_bermasalah_count,
                "unmatched_raw_count": len(unmatched_raw_ids),
                "message": (
                    f"Pembentukan absensi harian berhasil diproses! "
                    f"{created_count + updated_count} record terbentuk ({hadir_lengkap_count} Hadir Lengkap, "
                    f"{hanya_masuk_count} Hanya Masuk, {hanya_pulang_count} Hanya Pulang, {tidak_absen_count} Tidak Absen)."
                ),
            }

    @classmethod
    def get_daily_attendance_list(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        attendance_status: Optional[str] = None,
        keyword: Optional[str] = None,
        specific_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 25,
        sort_by: str = "attendance_date",
        sort_dir: str = "asc",
    ) -> Dict[str, Any]:
        """
        Mengambil daftar absensi harian dengan filter multi-kriteria, pencarian, dan pagination.
        """
        start_date = date(year, month, 1)
        end_date = date(year, month, py_calendar.monthrange(year, month)[1])

        with get_db_session() as session:
            query = (
                session.query(AttendanceDaily)
                .join(Employee, AttendanceDaily.employee_id == Employee.id)
                .filter(
                    AttendanceDaily.attendance_date >= start_date,
                    AttendanceDaily.attendance_date <= end_date,
                )
            )

            # Filter Unit
            if unit and unit != "ALL" and unit.strip():
                query = query.filter(Employee.unit == unit)

            # Filter Status
            if attendance_status and attendance_status != "ALL" and attendance_status.strip():
                query = query.filter(AttendanceDaily.attendance_status == attendance_status)

            # Filter Tanggal Spesifik
            if specific_date:
                query = query.filter(AttendanceDaily.attendance_date == specific_date)

            # Filter Pencarian Kata Kunci
            if keyword and keyword.strip():
                term = f"%{keyword.strip()}%"
                query = query.filter(
                    or_(
                        Employee.nama.ilike(term),
                        Employee.emp_num.ilike(term),
                        Employee.no_id.ilike(term),
                        Employee.nik.ilike(term),
                    )
                )

            # Total data sebelum paginasi
            total_records = query.count()

            # Sorting
            sort_column = getattr(AttendanceDaily, sort_by, AttendanceDaily.attendance_date)
            if sort_by == "nama":
                sort_column = Employee.nama
            elif sort_by == "unit":
                sort_column = Employee.unit
            elif sort_by == "emp_num":
                sort_column = Employee.emp_num

            if sort_dir.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column.asc())

            # Paginasi
            offset = (page - 1) * page_size
            items: List[AttendanceDaily] = (
                query.options(joinedload(AttendanceDaily.employee))
                .offset(offset)
                .limit(page_size)
                .all()
            )

            total_pages = max(1, (total_records + page_size - 1) // page_size)

            return {
                "total_records": total_records,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "records": [item.to_dict() for item in items],
            }

    @classmethod
    def get_attendance_statistics(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mengambil statistik ringkasan kehadiran untuk dashboard:
        - Total Karyawan
        - Total Hari Kerja Kalender
        - Total Record Absensi Harian
        - Hadir Lengkap
        - Hanya Absen Masuk
        - Hanya Absen Pulang
        - Tidak Absen
        - Data Bermasalah / Konflik
        """
        with get_db_session() as session:
            # 1. Hari kerja kalender
            working_days_count = (
                session.query(WorkCalendar)
                .filter(
                    WorkCalendar.year == year,
                    WorkCalendar.month == month,
                    WorkCalendar.is_working_day == True,
                )
                .count()
            )

            start_date = date(year, month, 1)
            end_date = date(year, month, py_calendar.monthrange(year, month)[1])

            # 2. Query absensi harian
            query = (
                session.query(AttendanceDaily)
                .join(Employee, AttendanceDaily.employee_id == Employee.id)
                .filter(
                    AttendanceDaily.attendance_date >= start_date,
                    AttendanceDaily.attendance_date <= end_date,
                )
            )

            if unit and unit != "ALL" and unit.strip():
                query = query.filter(Employee.unit == unit)

            all_daily = query.all()

            total_records = len(all_daily)
            unique_employees = len(set(d.employee_id for d in all_daily))

            hadir_lengkap = sum(1 for d in all_daily if d.attendance_status == AttendanceStatus.HADIR_LENGKAP.value)
            hanya_masuk = sum(1 for d in all_daily if d.attendance_status == AttendanceStatus.HANYA_ABSEN_MASUK.value)
            hanya_pulang = sum(1 for d in all_daily if d.attendance_status == AttendanceStatus.HANYA_ABSEN_PULANG.value)
            tidak_absen = sum(1 for d in all_daily if d.attendance_status == AttendanceStatus.TIDAK_ABSEN.value)
            data_bermasalah = sum(1 for d in all_daily if d.attendance_status == AttendanceStatus.DATA_BERMASALAH.value)
            has_conflict_count = sum(1 for d in all_daily if d.has_conflict)
            incomplete_scan_count = sum(1 for d in all_daily if d.has_incomplete_scan)

            return {
                "year": year,
                "month": month,
                "unit": unit or "ALL",
                "unique_employees": unique_employees,
                "working_days": working_days_count,
                "total_records": total_records,
                "hadir_lengkap": hadir_lengkap,
                "hanya_masuk": hanya_masuk,
                "hanya_pulang": hanya_pulang,
                "tidak_absen": tidak_absen,
                "data_bermasalah": data_bermasalah,
                "has_conflict_count": has_conflict_count,
                "incomplete_scan_count": incomplete_scan_count,
            }
