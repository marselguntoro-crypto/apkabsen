"""
Modul Layanan Kalender Kerja (CalendarService) untuk SIAP.
Mengelola pembentukan kalender bulanan, penentuan hari kerja & akhir pekan,
hari libur nasional/cuti bersama, jam operasional default, serta import dari Excel.
"""
import calendar as py_calendar
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy import and_, extract, desc
from sqlalchemy.orm import Session

from database.connection import get_db_session
from database.models import (
    WorkCalendar,
    CalendarStatus,
    AuditLog,
    Setting,
)
from utils.logger import get_logger
from utils.date_parser import parse_flexible_date, format_indonesian_date
from utils.time_parser import parse_time_str
from utils.excel_reader import extract_excel_sheets, get_sheet_names

logger = get_logger("CalendarService")

# Pemetaan nama hari Indonesia
INDONESIAN_DAY_NAMES = {
    0: "Senin",
    1: "Selasa",
    2: "Rabu",
    3: "Kamis",
    4: "Jumat",
    5: "Sabtu",
    6: "Minggu",
}


class CalendarService:
    """Layanan pengelolaan kalender hari kerja bulanan."""

    @staticmethod
    def get_operational_hours(session: Session) -> Dict[str, str]:
        """
        Mengambil konfigurasi jam operasional standar dari database.
        Default:
        Senin - Kamis: 08:15 - 16:30
        Jumat: 08:15 - 17:00
        """
        settings = session.query(Setting).all()
        config = {s.setting_key: s.setting_value for s in settings}

        return {
            "in_senin_kamis": config.get("jam_masuk_senin_kamis", "08:15"),
            "out_senin_kamis": config.get("jam_pulang_senin_kamis", "16:30"),
            "in_jumat": config.get("jam_masuk_jumat", "08:15"),
            "out_jumat": config.get("jam_pulang_jumat", "17:00"),
            "working_days_target": config.get("target_hari_kerja_bulanan", "18"),
            "working_days_policy": config.get("kebijakan_hari_kerja", "CALENDAR_ACTUAL"),
        }

    @classmethod
    def generate_monthly_calendar(
        cls,
        year: int,
        month: int,
        overwrite: bool = False,
        created_by: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """
        Membuat seluruh tanggal dalam bulan yang dipilih.
        Menentukan hari kerja, akhir pekan, jam masuk, dan jam pulang.
        Jika kalender sudah ada dan overwrite=False, mengembalikan status peringatan.
        """
        with get_db_session() as session:
            # 1. Cek data kalender yang sudah ada untuk periode ini
            existing_days = (
                session.query(WorkCalendar)
                .filter(WorkCalendar.year == year, WorkCalendar.month == month)
                .all()
            )

            if existing_days and not overwrite:
                # Periksa apakah ada yang diedit khusus
                special_days_count = sum(1 for d in existing_days if d.is_special_day)
                return {
                    "success": False,
                    "already_exists": True,
                    "total_existing": len(existing_days),
                    "special_days_count": special_days_count,
                    "message": f"Kalender untuk {py_calendar.month_name[month]} {year} sudah terbentuk ({len(existing_days)} hari). Gunakan opsi overwrite untuk memperbarui.",
                }

            # 2. Ambil aturan jam operasional
            op_hours = cls.get_operational_hours(session)

            # Hitung jumlah hari dalam bulan
            _, num_days = py_calendar.monthrange(year, month)

            created_count = 0
            updated_count = 0

            # 3. Bentuk record untuk setiap tanggal 1 s/d num_days
            for day in range(1, num_days + 1):
                cur_date = date(year, month, day)
                weekday = cur_date.weekday()  # 0: Senin ... 6: Minggu
                day_name = INDONESIAN_DAY_NAMES.get(weekday, "")

                # Default status & jam
                if weekday in [0, 1, 2, 3]:  # Senin - Kamis
                    cal_status = CalendarStatus.HARI_KERJA
                    is_work = True
                    check_in = op_hours["in_senin_kamis"]
                    check_out = op_hours["out_senin_kamis"]
                    desc = "Hari Kerja Normal (Senin - Kamis)"
                elif weekday == 4:  # Jumat
                    cal_status = CalendarStatus.HARI_KERJA
                    is_work = True
                    check_in = op_hours["in_jumat"]
                    check_out = op_hours["out_jumat"]
                    desc = "Hari Kerja Normal (Jumat)"
                else:  # Sabtu & Minggu
                    cal_status = CalendarStatus.AKHIR_PEKAN
                    is_work = False
                    check_in = None
                    check_out = None
                    desc = "Akhir Pekan"

                # Cari record existing jika mode overwrite
                existing = (
                    session.query(WorkCalendar)
                    .filter(WorkCalendar.calendar_date == cur_date)
                    .first()
                )

                if existing:
                    # Update data
                    existing.day_name = day_name
                    existing.calendar_status = cal_status
                    existing.is_working_day = is_work
                    existing.scheduled_check_in = check_in
                    existing.scheduled_check_out = check_out
                    existing.description = desc
                    existing.is_special_day = False
                    existing.updated_by = created_by
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    new_item = WorkCalendar(
                        calendar_date=cur_date,
                        year=year,
                        month=month,
                        day_name=day_name,
                        calendar_status=cal_status,
                        is_working_day=is_work,
                        scheduled_check_in=check_in,
                        scheduled_check_out=check_out,
                        description=desc,
                        is_special_day=False,
                        created_by=created_by,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    session.add(new_item)
                    created_count += 1

            session.flush()

            # Hitung hari kerja aktual
            working_days_actual = (
                session.query(WorkCalendar)
                .filter(
                    WorkCalendar.year == year,
                    WorkCalendar.month == month,
                    WorkCalendar.is_working_day == True,
                )
                .count()
            )

            # Catat audit log
            audit = AuditLog(
                action="GENERATE_CALENDAR",
                module="CALENDAR",
                description=f"Generate kalender periode {month:02d}/{year}: {created_count} baru, {updated_count} diperbarui. Total hari kerja: {working_days_actual} hari.",
                created_at=datetime.utcnow(),
            )
            session.add(audit)

            logger.info(f"Kalender {month:02d}/{year} berhasil di-generate. Hari kerja aktual: {working_days_actual}")

            return {
                "success": True,
                "created_count": created_count,
                "updated_count": updated_count,
                "total_days": num_days,
                "working_days_actual": working_days_actual,
                "working_days_target": int(op_hours["working_days_target"]),
                "policy": op_hours["working_days_policy"],
                "message": f"Kalender periode {month:02d}/{year} berhasil dibuat. Total hari kerja: {working_days_actual} hari.",
            }

    @classmethod
    def get_monthly_calendar(
        cls,
        year: int,
        month: int,
    ) -> List[Dict[str, Any]]:
        """Mengambil seluruh data kalender pada bulan dan tahun yang dipilih."""
        with get_db_session() as session:
            records = (
                session.query(WorkCalendar)
                .filter(WorkCalendar.year == year, WorkCalendar.month == month)
                .order_by(WorkCalendar.calendar_date.asc())
                .all()
            )
            return [r.to_dict() for r in records]

    @classmethod
    def get_calendar_summary(
        cls,
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """
        Menghasilkan ringkasan statistik kalender:
        - Total hari
        - Jumlah hari kerja aktual
        - Jumlah akhir pekan
        - Jumlah libur / cuti bersama
        - Target hari kerja setting (18 hari)
        - Selisih hari kerja
        """
        with get_db_session() as session:
            records = (
                session.query(WorkCalendar)
                .filter(WorkCalendar.year == year, WorkCalendar.month == month)
                .all()
            )

            op_hours = cls.get_operational_hours(session)
            target = int(op_hours["working_days_target"])

            total_days = len(records)
            working_days = sum(1 for r in records if r.is_working_day)
            weekend_days = sum(1 for r in records if r.calendar_status == CalendarStatus.AKHIR_PEKAN)
            holidays = sum(
                1 for r in records
                if r.calendar_status in [CalendarStatus.LIBUR, CalendarStatus.LIBUR_NASIONAL, CalendarStatus.CUTI_BERSAMA]
            )
            special_days = sum(1 for r in records if r.is_special_day)

            return {
                "total_days": total_days,
                "working_days": working_days,
                "weekend_days": weekend_days,
                "holidays": holidays,
                "special_days": special_days,
                "target_days": target,
                "policy": op_hours["working_days_policy"],
                "difference": working_days - target,
            }

    @classmethod
    def update_calendar_day(
        cls,
        calendar_id: int,
        status: CalendarStatus,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: str = "ADMIN",
    ) -> Dict[str, Any]:
        """
        Mengubah status tanggal tertentu pada kalender.
        Admin dapat mengubah menjadi:
        - LIBUR
        - CUTI_BERSAMA
        - LIBUR_NASIONAL
        - HARI_KERJA
        - HARI_KERJA_KHUSUS
        - AKHIR_PEKAN
        """
        with get_db_session() as session:
            item = session.query(WorkCalendar).filter(WorkCalendar.id == calendar_id).first()
            if not item:
                return {"success": False, "message": f"Data kalender dengan ID {calendar_id} tidak ditemukan."}

            old_status = item.calendar_status.value if hasattr(item.calendar_status, "value") else str(item.calendar_status)

            # Tentukan apakah ini hari kerja
            if status in [CalendarStatus.HARI_KERJA, CalendarStatus.HARI_KERJA_KHUSUS]:
                item.is_working_day = True
            else:
                item.is_working_day = False

            item.calendar_status = status
            item.description = description or item.description

            # Atur jam jika hari kerja
            if item.is_working_day:
                op = cls.get_operational_hours(session)
                weekday = item.calendar_date.weekday()
                default_in = op["in_jumat"] if weekday == 4 else op["in_senin_kamis"]
                default_out = op["out_jumat"] if weekday == 4 else op["out_senin_kamis"]

                item.scheduled_check_in = check_in.strip() if check_in and check_in.strip() else default_in
                item.scheduled_check_out = check_out.strip() if check_out and check_out.strip() else default_out
            else:
                item.scheduled_check_in = None
                item.scheduled_check_out = None

            item.is_special_day = True
            item.updated_by = updated_by
            item.updated_at = datetime.utcnow()

            session.flush()

            # Audit log
            audit = AuditLog(
                action="UPDATE_CALENDAR_DAY",
                module="CALENDAR",
                description=f"Ubah status tanggal {item.calendar_date} ({item.day_name}) dari {old_status} menjadi {status.value}. Keterangan: {description or '-'}.",
                created_at=datetime.utcnow(),
            )
            session.add(audit)

            return {
                "success": True,
                "message": f"Status tanggal {item.calendar_date} berhasil diubah menjadi {status.value}.",
                "data": item.to_dict(),
            }

    @classmethod
    def import_calendar_from_excel(
        cls,
        file_path: str,
        sheet_name: Optional[str] = None,
        update_existing: bool = True,
        user_name: str = "ADMIN",
    ) -> Dict[str, Any]:
        """
        Mengimpor konfigurasi kalender kerja dari file Excel.
        Mendukung kolom: Tanggal, Status Kalender, Jam Masuk, Jam Pulang, Keterangan.
        """
        sheets = extract_excel_sheets(file_path)
        if not sheets:
            return {"success": False, "message": "Gagal membaca lembar kerja dari berkas Excel."}

        target_sheet = sheet_name if sheet_name and sheet_name in sheets else list(sheets.keys())[0]
        raw_rows = sheets[target_sheet]

        if not raw_rows or len(raw_rows) < 2:
            return {"success": False, "message": "Lembar kerja Excel kosong atau tidak memiliki baris data."}

        # Header normalisasi
        headers = [str(col).strip().upper() for col in raw_rows[0]]

        # Temukan index kolom
        date_idx = -1
        status_idx = -1
        in_idx = -1
        out_idx = -1
        desc_idx = -1

        for idx, h in enumerate(headers):
            if "TANGGAL" in h or "DATE" in h:
                date_idx = idx
            elif "STATUS" in h:
                status_idx = idx
            elif "MASUK" in h or "CHECK IN" in h:
                in_idx = idx
            elif "PULANG" in h or "CHECK OUT" in h:
                out_idx = idx
            elif "KET" in h or "DESC" in h or "CATATAN" in h:
                desc_idx = idx

        if date_idx == -1:
            return {"success": False, "message": "Kolom 'Tanggal' tidak ditemukan pada berkas Excel."}

        with get_db_session() as session:
            op_hours = cls.get_operational_hours(session)
            total_rows = len(raw_rows) - 1
            valid_count = 0
            invalid_count = 0
            duplicate_count = 0
            errors = []

            for row_idx, row in enumerate(raw_rows[1:], start=2):
                if not row or all(v is None or str(v).strip() == "" for v in row):
                    continue

                raw_date_val = row[date_idx] if date_idx < len(row) else None
                parsed_date = parse_flexible_date(raw_date_val)

                if not parsed_date:
                    invalid_count += 1
                    errors.append(f"Baris {row_idx}: Format tanggal tidak valid ('{raw_date_val}')")
                    continue

                # Status parsing
                raw_status = str(row[status_idx]).strip().upper() if status_idx != -1 and status_idx < len(row) and row[status_idx] else "HARI_KERJA"
                # Normalisasi alias status
                if "KERJA KHUSUS" in raw_status or "HARI KERJA KHUSUS" in raw_status:
                    cal_status = CalendarStatus.HARI_KERJA_KHUSUS
                    is_work = True
                elif "CUTI" in raw_status:
                    cal_status = CalendarStatus.CUTI_BERSAMA
                    is_work = False
                elif "NASIONAL" in raw_status:
                    cal_status = CalendarStatus.LIBUR_NASIONAL
                    is_work = False
                elif "LIBUR" in raw_status:
                    cal_status = CalendarStatus.LIBUR
                    is_work = False
                elif "AKHIR PEKAN" in raw_status or "WEEKEND" in raw_status or "SABTU" in raw_status or "MINGGU" in raw_status:
                    cal_status = CalendarStatus.AKHIR_PEKAN
                    is_work = False
                else:
                    cal_status = CalendarStatus.HARI_KERJA
                    is_work = True

                # Jam masuk & pulang
                raw_in = str(row[in_idx]).strip() if in_idx != -1 and in_idx < len(row) and row[in_idx] else None
                raw_out = str(row[out_idx]).strip() if out_idx != -1 and out_idx < len(row) and row[out_idx] else None
                desc = str(row[desc_idx]).strip() if desc_idx != -1 and desc_idx < len(row) and row[desc_idx] else None

                weekday = parsed_date.weekday()
                day_name = INDONESIAN_DAY_NAMES.get(weekday, "")

                if is_work:
                    default_in = op_hours["in_jumat"] if weekday == 4 else op_hours["in_senin_kamis"]
                    default_out = op_hours["out_jumat"] if weekday == 4 else op_hours["out_senin_kamis"]
                    check_in = parse_time_str(raw_in) or default_in
                    check_out = parse_time_str(raw_out) or default_out
                else:
                    check_in = None
                    check_out = None

                # Cek existing
                existing = session.query(WorkCalendar).filter(WorkCalendar.calendar_date == parsed_date).first()

                if existing:
                    duplicate_count += 1
                    if update_existing:
                        existing.day_name = day_name
                        existing.calendar_status = cal_status
                        existing.is_working_day = is_work
                        existing.scheduled_check_in = check_in
                        existing.scheduled_check_out = check_out
                        existing.description = desc or existing.description
                        existing.is_special_day = True
                        existing.updated_by = user_name
                        existing.updated_at = datetime.utcnow()
                        valid_count += 1
                else:
                    new_item = WorkCalendar(
                        calendar_date=parsed_date,
                        year=parsed_date.year,
                        month=parsed_date.month,
                        day_name=day_name,
                        calendar_status=cal_status,
                        is_working_day=is_work,
                        scheduled_check_in=check_in,
                        scheduled_check_out=check_out,
                        description=desc or f"Import Excel ({target_sheet})",
                        is_special_day=True,
                        created_by=user_name,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    session.add(new_item)
                    valid_count += 1

            session.flush()

            # Audit
            audit = AuditLog(
                action="IMPORT_CALENDAR_EXCEL",
                module="CALENDAR",
                description=f"Import kalender dari Excel '{file_path}': {valid_count} berhasil, {invalid_count} gagal, {duplicate_count} tanggal telah ada.",
                created_at=datetime.utcnow(),
            )
            session.add(audit)

            return {
                "success": True,
                "total_rows": total_rows,
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "duplicate_count": duplicate_count,
                "errors": errors[:50],  # Maksimal 50 error sample
                "message": f"Import kalender selesai: {valid_count} tanggal berhasil diproses, {invalid_count} tidak valid.",
            }
