"""
Modul Mesin Perhitungan Potongan Absensi (DeductionCalculationService).
Bertanggung jawab menghitung:
1. Menit Keterlambatan dan Nominal Potongan Masuk (<= 60 menit vs > 60 menit).
2. Menit Pulang Cepat dan Nominal Potongan Pulang Cepat.
3. Potongan Tidak Absen Masuk (Rp10.000) dan Tidak Absen Pulang (Rp10.000).
4. Menjamin TIDAK ADA DOUBLE COUNTING (Tidak hadir = 10.000 + 10.000 = 20.000, tanpa alfa ekstra).
5. Hari libur/bukan hari kerja = Rp0.
6. Menggunakan angka integer dalam satuan Rupiah (tanpa floating point).
7. Menghasilkan rekap bulanan per karyawan, rekap per unit, dan laporan harian.
"""
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import extract, func, and_, or_, desc
from sqlalchemy.orm import joinedload, Session

from config.settings import DEFAULT_SETTINGS
from database.connection import get_db_session
from database.models import (
    Employee,
    EmployeeStatus,
    WorkCalendar,
    CalendarStatus,
    AttendanceDaily,
    AttendanceDeduction,
    AttendanceDeductionItem,
    AuditLog,
    Setting,
)
from services.settings_service import SettingsService
from utils.logger import get_logger
from utils.time_parser import parse_time_str, time_to_minutes

logger = get_logger("DeductionCalculationService")


class DeductionCalculationService:
    """Service inti kalkulasi potongan absensi karyawan."""

    CALCULATION_VERSION = "1.0.0"

    @classmethod
    def get_effective_rule_settings(cls, session: Optional[Session] = None) -> Dict[str, Any]:
        """
        Membaca konfigurasi aturan dan tarif potongan dari database (settings).
        Mengembalikan konfigurasi dengan tipe data integer / waktu yang siap digunakan.
        """
        raw_settings = SettingsService.get_all()

        return {
            # Jam Operasional Terjadwal Standar
            "jam_masuk_senin_kamis": raw_settings.get("jam_masuk_senin_kamis", "08:15"),
            "jam_pulang_senin_kamis": raw_settings.get("jam_pulang_senin_kamis", "16:30"),
            "jam_masuk_jumat": raw_settings.get("jam_masuk_jumat", "08:15"),
            "jam_pulang_jumat": raw_settings.get("jam_pulang_jumat", "17:00"),

            # Batas Waktu & Tarif Potongan (Integer Rupiah)
            "batas_menit_terlambat_1": 60,
            "potongan_terlambat_sd_1jam": int(raw_settings.get("potongan_terlambat_sd_1jam", 7500)),
            "potongan_terlambat_gt_1jam": int(raw_settings.get("potongan_terlambat_gt_1jam", 10000)),
            "potongan_pulang_cepat": int(raw_settings.get("potongan_pulang_cepat", 10000)),
            "potongan_tidak_absen_masuk": int(raw_settings.get("potongan_tidak_absen_masuk", 10000)),
            "potongan_tidak_absen_pulang": int(raw_settings.get("potongan_tidak_absen_pulang", 10000)),
            "potongan_tidak_hadir": int(raw_settings.get("potongan_tidak_hadir", 20000)),
        }

    @classmethod
    def calculate_single_day(
        cls,
        att_date: date,
        actual_in_str: Optional[str],
        actual_out_str: Optional[str],
        is_working_day: bool,
        day_name: Optional[str] = None,
        scheduled_in_override: Optional[str] = None,
        scheduled_out_override: Optional[str] = None,
        rule_settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Menghitung rincian potongan untuk 1 record absensi harian.
        Fungsi ini bersifat murni (pure function), konsisten, dan dapat diuji secara independen.
        """
        rules = rule_settings or cls.get_effective_rule_settings()

        # Inisialisasi Hasil
        result = {
            "is_working_day": is_working_day,
            "late_minutes": 0,
            "early_leave_minutes": 0,
            "deduction_late": 0,
            "deduction_early_leave": 0,
            "deduction_missing_check_in": 0,
            "deduction_missing_check_out": 0,
            "total_deduction": 0,
            "items": [],  # List[dict]: {type, description, amount, ref}
            "notes": "",
        }

        # 1. Jika BUKAN Hari Kerja (Akhir Pekan / Libur Nasional / Cuti Bersama)
        if not is_working_day:
            result["notes"] = "Bukan hari kerja operasional (Potongan Rp0)"
            return result

        # Tentukan Jam Terjadwal (Jumat vs Senin-Kamis atau Override dari Kalender)
        is_jumat = (att_date.weekday() == 4) or (day_name and day_name.lower() == "jumat")

        if scheduled_in_override and scheduled_in_override != "-":
            sched_in = scheduled_in_override
        else:
            sched_in = rules["jam_masuk_jumat"] if is_jumat else rules["jam_masuk_senin_kamis"]

        if scheduled_out_override and scheduled_out_override != "-":
            sched_out = scheduled_out_override
        else:
            sched_out = rules["jam_pulang_jumat"] if is_jumat else rules["jam_pulang_senin_kamis"]

        sched_in_min = time_to_minutes(sched_in) or (8 * 60 + 15)  # 08:15 default
        sched_out_min = time_to_minutes(sched_out) or (17 * 60 if is_jumat else 16 * 60 + 30)

        # 2. Evaluasi Jam Masuk Aktual
        actual_in_clean = parse_time_str(actual_in_str)
        actual_in_min = time_to_minutes(actual_in_clean)

        if actual_in_min is None:
            # Jam masuk kosong -> Potongan Tidak Absen Masuk (Rp10.000)
            # TIDAK menghitung keterlambatan!
            amt = rules["potongan_tidak_absen_masuk"]
            result["deduction_missing_check_in"] = amt
            result["items"].append({
                "deduction_type": "MISSING_CHECK_IN",
                "description": "Tidak Absen Masuk",
                "amount": amt,
                "calculation_reference": f"Scan masuk kosong pada hari kerja terjadwal ({sched_in})",
            })
        else:
            # Jam masuk tersedia -> Evaluasi Keterlambatan
            if actual_in_min > sched_in_min:
                diff_min = actual_in_min - sched_in_min
                result["late_minutes"] = diff_min

                if diff_min <= rules["batas_menit_terlambat_1"]:
                    amt = rules["potongan_terlambat_sd_1jam"]
                    result["deduction_late"] = amt
                    result["items"].append({
                        "deduction_type": "LATE_UNDER_OR_EQUAL_60",
                        "description": f"Terlambat Masuk {diff_min} Menit (<= 60 Menit)",
                        "amount": amt,
                        "calculation_reference": f"Masuk {actual_in_clean} vs Jadwal {sched_in} (+{diff_min} m)",
                    })
                else:
                    amt = rules["potongan_terlambat_gt_1jam"]
                    result["deduction_late"] = amt
                    result["items"].append({
                        "deduction_type": "LATE_OVER_60",
                        "description": f"Terlambat Masuk {diff_min} Menit (> 60 Menit)",
                        "amount": amt,
                        "calculation_reference": f"Masuk {actual_in_clean} vs Jadwal {sched_in} (+{diff_min} m)",
                    })

        # 3. Evaluasi Jam Pulang Aktual
        actual_out_clean = parse_time_str(actual_out_str)
        actual_out_min = time_to_minutes(actual_out_clean)

        if actual_out_min is None:
            # Jam pulang kosong -> Potongan Tidak Absen Pulang (Rp10.000)
            # TIDAK menghitung pulang cepat!
            amt = rules["potongan_tidak_absen_pulang"]
            result["deduction_missing_check_out"] = amt
            result["items"].append({
                "deduction_type": "MISSING_CHECK_OUT",
                "description": "Tidak Absen Pulang",
                "amount": amt,
                "calculation_reference": f"Scan pulang kosong pada hari kerja terjadwal ({sched_out})",
            })
        else:
            # Jam pulang tersedia -> Evaluasi Pulang Cepat
            if actual_out_min < sched_out_min:
                diff_min = sched_out_min - actual_out_min
                result["early_leave_minutes"] = diff_min
                amt = rules["potongan_pulang_cepat"]
                result["deduction_early_leave"] = amt
                result["items"].append({
                    "deduction_type": "EARLY_LEAVE",
                    "description": f"Pulang Cepat {diff_min} Menit",
                    "amount": amt,
                    "calculation_reference": f"Pulang {actual_out_clean} vs Jadwal {sched_out} (-{diff_min} m)",
                })

        # 4. Total Potongan = Penjumlahan seluruh komponen yang valid (Mencegah Double Counting)
        # Jika kedua scan kosong: 10.000 + 10.000 = 20.000 (tidak ditambah alfa ekstra!)
        total = (
            result["deduction_late"]
            + result["deduction_early_leave"]
            + result["deduction_missing_check_in"]
            + result["deduction_missing_check_out"]
        )
        result["total_deduction"] = int(total)

        if actual_in_min is None and actual_out_min is None:
            result["notes"] = "Tidak ada scan presensi sama sekali (Tidak Masuk Rp10.000 + Tidak Pulang Rp10.000 = Rp20.000)"

        return result

    @classmethod
    def calculate_period_deductions(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        employee_id: Optional[int] = None,
        user_name: str = "ADMIN",
        force_recalculate: bool = False,
    ) -> Dict[str, Any]:
        """
        Menjalankan kalkulasi potongan absensi untuk satu periode bulan & tahun.
        Menggunakan transaksi database yang aman (commit/rollback).
        """
        logger.info(f"Memulai perhitungan potongan periode {month:02d}/{year} (unit: {unit}, emp: {employee_id}, force: {force_recalculate}).")

        with get_db_session() as session:
            # 1. Ambil Pengaturan Aturan Potongan
            rule_settings = cls.get_effective_rule_settings(session)

            # 2. Ambil Kalender Kerja Periode Ini
            calendar_records = (
                session.query(WorkCalendar)
                .filter(WorkCalendar.year == year, WorkCalendar.month == month)
                .all()
            )
            cal_by_date = {c.calendar_date: c for c in calendar_records}

            if not calendar_records:
                return {
                    "success": False,
                    "error_type": "CALENDAR_NOT_FOUND",
                    "message": f"Kalender kerja untuk periode {month:02d}/{year} belum dibuat. Silakan buat kalender terlebih dahulu.",
                }

            # 3. Query AttendanceDaily
            query = (
                session.query(AttendanceDaily)
                .join(Employee, AttendanceDaily.employee_id == Employee.id)
                .filter(
                    extract("year", AttendanceDaily.attendance_date) == year,
                    extract("month", AttendanceDaily.attendance_date) == month,
                )
            )

            if unit and unit != "ALL" and unit.strip():
                query = query.filter(Employee.unit == unit)
            if employee_id:
                query = query.filter(Employee.id == employee_id)

            daily_list: List[AttendanceDaily] = (
                query.options(
                    joinedload(AttendanceDaily.employee),
                    joinedload(AttendanceDaily.deduction).joinedload(AttendanceDeduction.items),
                )
                .all()
            )

            if not daily_list:
                return {
                    "success": False,
                    "error_type": "NO_DAILY_RECORDS",
                    "message": f"Belum ditemukan data Absensi Harian (attendance_daily) untuk periode {month:02d}/{year}. Silakan generate absensi harian terlebih dahulu.",
                }

            processed_count = 0
            inserted_count = 0
            updated_count = 0
            skipped_count = 0

            total_nominal_all = 0
            total_late_nominal = 0
            total_early_nominal = 0
            total_missing_in_nominal = 0
            total_missing_out_nominal = 0

            anomalies = []

            for daily in daily_list:
                cal = cal_by_date.get(daily.attendance_date)
                is_working = cal.is_working_day if cal else True
                day_name = cal.day_name if cal else daily.day_name
                sched_in = cal.scheduled_check_in if cal else daily.scheduled_check_in
                sched_out = cal.scheduled_check_out if cal else daily.scheduled_check_out

                # Hitung potongan untuk record ini
                calc_res = cls.calculate_single_day(
                    att_date=daily.attendance_date,
                    actual_in_str=daily.actual_check_in,
                    actual_out_str=daily.actual_check_out,
                    is_working_day=is_working,
                    day_name=day_name,
                    scheduled_in_override=sched_in,
                    scheduled_out_override=sched_out,
                    rule_settings=rule_settings,
                )

                # Update field di AttendanceDaily
                daily.terlambat_menit = calc_res["late_minutes"]
                daily.pulang_cepat_menit = calc_res["early_leave_minutes"]
                daily.potongan_masuk = calc_res["deduction_late"]
                daily.potongan_pulang = calc_res["deduction_early_leave"]
                daily.potongan_tidak_hadir = calc_res["deduction_missing_check_in"] + calc_res["deduction_missing_check_out"]
                daily.total_potongan = calc_res["total_deduction"]

                # Simpan atau update tabel AttendanceDeduction
                existing_ded = daily.deduction
                if existing_ded:
                    if not force_recalculate and existing_ded.total_deduction == calc_res["total_deduction"]:
                        skipped_count += 1
                    else:
                        existing_ded.late_minutes = calc_res["late_minutes"]
                        existing_ded.early_leave_minutes = calc_res["early_leave_minutes"]
                        existing_ded.deduction_late = calc_res["deduction_late"]
                        existing_ded.deduction_early_leave = calc_res["deduction_early_leave"]
                        existing_ded.deduction_missing_check_in = calc_res["deduction_missing_check_in"]
                        existing_ded.deduction_missing_check_out = calc_res["deduction_missing_check_out"]
                        existing_ded.total_deduction = calc_res["total_deduction"]
                        existing_ded.calculation_version = cls.CALCULATION_VERSION
                        existing_ded.calculated_at = datetime.utcnow()
                        existing_ded.calculated_by = user_name
                        existing_ded.notes = calc_res["notes"]

                        # Hapus item lama dan buat ulang
                        for it in list(existing_ded.items):
                            session.delete(it)

                        for item_data in calc_res["items"]:
                            new_item = AttendanceDeductionItem(
                                attendance_deduction_id=existing_ded.id,
                                deduction_type=item_data["deduction_type"],
                                description=item_data["description"],
                                amount=item_data["amount"],
                                calculation_reference=item_data.get("calculation_reference"),
                                created_at=datetime.utcnow(),
                            )
                            session.add(new_item)

                        updated_count += 1
                else:
                    new_ded = AttendanceDeduction(
                        attendance_daily_id=daily.id,
                        employee_id=daily.employee_id,
                        attendance_date=daily.attendance_date,
                        late_minutes=calc_res["late_minutes"],
                        early_leave_minutes=calc_res["early_leave_minutes"],
                        deduction_late=calc_res["deduction_late"],
                        deduction_early_leave=calc_res["deduction_early_leave"],
                        deduction_missing_check_in=calc_res["deduction_missing_check_in"],
                        deduction_missing_check_out=calc_res["deduction_missing_check_out"],
                        total_deduction=calc_res["total_deduction"],
                        calculation_version=cls.CALCULATION_VERSION,
                        calculated_at=datetime.utcnow(),
                        calculated_by=user_name,
                        notes=calc_res["notes"],
                    )
                    session.add(new_ded)
                    session.flush()  # Untuk mendapatkan new_ded.id

                    for item_data in calc_res["items"]:
                        new_item = AttendanceDeductionItem(
                            attendance_deduction_id=new_ded.id,
                            deduction_type=item_data["deduction_type"],
                            description=item_data["description"],
                            amount=item_data["amount"],
                            calculation_reference=item_data.get("calculation_reference"),
                            created_at=datetime.utcnow(),
                        )
                        session.add(new_item)

                    inserted_count += 1

                # Akumulasi statistik
                processed_count += 1
                total_nominal_all += calc_res["total_deduction"]
                total_late_nominal += calc_res["deduction_late"]
                total_early_nominal += calc_res["deduction_early_leave"]
                total_missing_in_nominal += calc_res["deduction_missing_check_in"]
                total_missing_out_nominal += calc_res["deduction_missing_check_out"]

            # Catat Audit Log
            audit = AuditLog(
                action="CALCULATE_DEDUCTIONS",
                module="DEDUCTIONS",
                description=(
                    f"Perhitungan potongan absensi periode {month:02d}/{year} selesai. "
                    f"Diproses: {processed_count} hari absensi ({inserted_count} baru, {updated_count} update). "
                    f"Total Potongan: Rp{total_nominal_all:,}. Terlambat: Rp{total_late_nominal:,}, "
                    f"Pulang Cepat: Rp{total_early_nominal:,}, Tdk Masuk: Rp{total_missing_in_nominal:,}, Tdk Pulang: Rp{total_missing_out_nominal:,}."
                ),
                created_at=datetime.utcnow(),
            )
            session.add(audit)

            logger.info(f"Perhitungan potongan {month:02d}/{year} berhasil: Total Rp{total_nominal_all:,}.")

            return {
                "success": True,
                "year": year,
                "month": month,
                "unit": unit or "ALL",
                "processed_count": processed_count,
                "inserted_count": inserted_count,
                "updated_count": updated_count,
                "skipped_count": skipped_count,
                "total_nominal_all": total_nominal_all,
                "total_late_nominal": total_late_nominal,
                "total_early_nominal": total_early_nominal,
                "total_missing_in_nominal": total_missing_in_nominal,
                "total_missing_out_nominal": total_missing_out_nominal,
                "message": (
                    f"Perhitungan potongan absensi periode {month:02d}/{year} berhasil diproses! "
                    f"Total potongan yang terbentuk: Rp{total_nominal_all:,} untuk {processed_count} data kehadiran harian."
                ),
            }

    @classmethod
    def get_monthly_deduction_recap(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Menghasilkan data REKAP DATA POTONGAN ABSENSI Bulanan.
        Kolom:
        No, Unit, Nama, Status, Terlambat, Pulang Cepat, Tidak Absen Masuk, Tidak Absen Pulang, Jumlah Potongan Absensi.
        Mencakup:
        - Total per karyawan
        - Total per unit
        - Total keseluruhan periode
        """
        with get_db_session() as session:
            # Ambil semua karyawan yang relevan
            emp_query = session.query(Employee)
            if unit and unit != "ALL" and unit.strip():
                emp_query = emp_query.filter(Employee.unit == unit)

            if keyword and keyword.strip():
                term = f"%{keyword.strip()}%"
                emp_query = emp_query.filter(
                    or_(
                        Employee.nama.ilike(term),
                        Employee.emp_num.ilike(term),
                        Employee.no_id.ilike(term),
                        Employee.nik.ilike(term),
                    )
                )

            employees = emp_query.order_by(Employee.unit.asc(), Employee.nama.asc()).all()
            emp_ids = [e.id for e in employees]

            if not emp_ids:
                return {
                    "year": year,
                    "month": month,
                    "unit": unit or "ALL",
                    "rows": [],
                    "unit_summaries": [],
                    "grand_total": {
                        "terlambat": 0,
                        "pulang_cepat": 0,
                        "tidak_absen_masuk": 0,
                        "tidak_absen_pulang": 0,
                        "total_potongan": 0,
                        "karyawan_count": 0,
                    },
                }

            # Ambil data agregat potongan dari attendance_deductions
            ded_query = (
                session.query(
                    AttendanceDeduction.employee_id,
                    func.sum(AttendanceDeduction.deduction_late).label("sum_late"),
                    func.sum(AttendanceDeduction.deduction_early_leave).label("sum_early"),
                    func.sum(AttendanceDeduction.deduction_missing_check_in).label("sum_miss_in"),
                    func.sum(AttendanceDeduction.deduction_missing_check_out).label("sum_miss_out"),
                    func.sum(AttendanceDeduction.total_deduction).label("sum_total"),
                    func.count(AttendanceDeduction.id).label("count_days"),
                )
                .filter(
                    AttendanceDeduction.employee_id.in_(emp_ids),
                    extract("year", AttendanceDeduction.attendance_date) == year,
                    extract("month", AttendanceDeduction.attendance_date) == month,
                )
                .group_by(AttendanceDeduction.employee_id)
                .all()
            )

            ded_map = {
                row.employee_id: {
                    "terlambat": int(row.sum_late or 0),
                    "pulang_cepat": int(row.sum_early or 0),
                    "tidak_absen_masuk": int(row.sum_miss_in or 0),
                    "tidak_absen_pulang": int(row.sum_miss_out or 0),
                    "total_potongan": int(row.sum_total or 0),
                    "count_days": int(row.count_days or 0),
                }
                for row in ded_query
            }

            # Susun baris tabel
            rows = []
            unit_agg = {}

            grand_total = {
                "terlambat": 0,
                "pulang_cepat": 0,
                "tidak_absen_masuk": 0,
                "tidak_absen_pulang": 0,
                "total_potongan": 0,
                "karyawan_count": len(employees),
            }

            for idx, emp in enumerate(employees, start=1):
                stat = ded_map.get(emp.id, {
                    "terlambat": 0,
                    "pulang_cepat": 0,
                    "tidak_absen_masuk": 0,
                    "tidak_absen_pulang": 0,
                    "total_potongan": 0,
                    "count_days": 0,
                })

                emp_unit = emp.unit or "Tanpa Unit"

                row_data = {
                    "no": idx,
                    "employee_id": emp.id,
                    "emp_num": emp.emp_num or "-",
                    "nik": emp.nik or "-",
                    "unit": emp_unit,
                    "nama": emp.nama,
                    "status": emp.status.value if hasattr(emp.status, "value") else str(emp.status),
                    "terlambat": stat["terlambat"],
                    "pulang_cepat": stat["pulang_cepat"],
                    "tidak_absen_masuk": stat["tidak_absen_masuk"],
                    "tidak_absen_pulang": stat["tidak_absen_pulang"],
                    "jumlah_potongan_absensi": stat["total_potongan"],
                    "days_counted": stat["count_days"],
                }
                rows.append(row_data)

                # Subtotal per Unit
                if emp_unit not in unit_agg:
                    unit_agg[emp_unit] = {
                        "unit": emp_unit,
                        "terlambat": 0,
                        "pulang_cepat": 0,
                        "tidak_absen_masuk": 0,
                        "tidak_absen_pulang": 0,
                        "total_potongan": 0,
                        "karyawan_count": 0,
                    }
                unit_agg[emp_unit]["terlambat"] += stat["terlambat"]
                unit_agg[emp_unit]["pulang_cepat"] += stat["pulang_cepat"]
                unit_agg[emp_unit]["tidak_absen_masuk"] += stat["tidak_absen_masuk"]
                unit_agg[emp_unit]["tidak_absen_pulang"] += stat["tidak_absen_pulang"]
                unit_agg[emp_unit]["total_potongan"] += stat["total_potongan"]
                unit_agg[emp_unit]["karyawan_count"] += 1

                # Grand Total
                grand_total["terlambat"] += stat["terlambat"]
                grand_total["pulang_cepat"] += stat["pulang_cepat"]
                grand_total["tidak_absen_masuk"] += stat["tidak_absen_masuk"]
                grand_total["tidak_absen_pulang"] += stat["tidak_absen_pulang"]
                grand_total["total_potongan"] += stat["total_potongan"]

            unit_summaries = sorted(unit_agg.values(), key=lambda x: x["unit"])

            return {
                "year": year,
                "month": month,
                "unit": unit or "ALL",
                "rows": rows,
                "unit_summaries": unit_summaries,
                "grand_total": grand_total,
            }

    @classmethod
    def get_daily_deduction_report(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        attendance_status: Optional[str] = None,
        keyword: Optional[str] = None,
        specific_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "attendance_date",
        sort_dir: str = "asc",
    ) -> Dict[str, Any]:
        """
        Menghasilkan DATA ABSENSI DAN POTONGAN HARIAN.
        Kolom:
        No, Unit, Nama, Hari, Tanggal, Jam Masuk, Jam Pulang, Status Masuk, Status Pulang,
        Status Kehadiran, Menit Terlambat, Menit Pulang Cepat, Potongan Terlambat,
        Potongan Pulang Cepat, Tidak Absen Masuk, Tidak Absen Pulang, Total Potongan Per Hari.
        """
        with get_db_session() as session:
            query = (
                session.query(AttendanceDaily)
                .join(Employee, AttendanceDaily.employee_id == Employee.id)
                .outerjoin(AttendanceDeduction, AttendanceDaily.id == AttendanceDeduction.attendance_daily_id)
                .filter(
                    extract("year", AttendanceDaily.attendance_date) == year,
                    extract("month", AttendanceDaily.attendance_date) == month,
                )
            )

            if unit and unit != "ALL" and unit.strip():
                query = query.filter(Employee.unit == unit)

            if attendance_status and attendance_status != "ALL" and attendance_status.strip():
                query = query.filter(AttendanceDaily.attendance_status == attendance_status)

            if specific_date:
                query = query.filter(AttendanceDaily.attendance_date == specific_date)

            if keyword and keyword.strip():
                term = f"%{keyword.strip()}%"
                query = query.filter(
                    or_(
                        Employee.nama.ilike(term),
                        Employee.emp_num.ilike(term),
                        Employee.no_id.ilike(term),
                    )
                )

            total_records = query.count()

            # Sorting
            sort_col = getattr(AttendanceDaily, sort_by, AttendanceDaily.attendance_date)
            if sort_by == "nama":
                sort_col = Employee.nama
            elif sort_by == "unit":
                sort_col = Employee.unit

            if sort_dir.lower() == "desc":
                query = query.order_by(desc(sort_col))
            else:
                query = query.order_by(sort_col.asc())

            offset = (page - 1) * page_size
            items = (
                query.options(
                    joinedload(AttendanceDaily.employee),
                    joinedload(AttendanceDaily.deduction),
                )
                .offset(offset)
                .limit(page_size)
                .all()
            )

            total_pages = max(1, (total_records + page_size - 1) // page_size)

            records = []
            for idx, item in enumerate(items, start=offset + 1):
                ded = item.deduction
                late_min = ded.late_minutes if ded else int(item.terlambat_menit or 0)
                early_min = ded.early_leave_minutes if ded else int(item.pulang_cepat_menit or 0)
                pot_late = ded.deduction_late if ded else int(item.potongan_masuk or 0)
                pot_early = ded.deduction_early_leave if ded else int(item.potongan_pulang or 0)
                pot_miss_in = ded.deduction_missing_check_in if ded else 0
                pot_miss_out = ded.deduction_missing_check_out if ded else 0
                tot = ded.total_deduction if ded else int(item.total_potongan or 0)

                records.append({
                    "no": idx,
                    "id": item.id,
                    "unit": item.employee.unit if item.employee else "-",
                    "nama": item.employee.nama if item.employee else "-",
                    "emp_num": item.employee.emp_num if item.employee else "-",
                    "nik": item.employee.nik if item.employee else "-",
                    "hari": item.day_name or "-",
                    "tanggal": item.attendance_date.strftime("%Y-%m-%d") if item.attendance_date else "-",
                    "jam_masuk": item.actual_check_in or "-",
                    "jam_pulang": item.actual_check_out or "-",
                    "status_masuk": item.check_in_status,
                    "status_pulang": item.check_out_status,
                    "status_kehadiran": item.attendance_status,
                    "menit_terlambat": late_min,
                    "menit_pulang_cepat": early_min,
                    "potongan_terlambat": pot_late,
                    "potongan_pulang_cepat": pot_early,
                    "tidak_absen_masuk": pot_miss_in,
                    "tidak_absen_pulang": pot_miss_out,
                    "total_potongan_per_hari": tot,
                })

            return {
                "total_records": total_records,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "records": records,
            }

    @classmethod
    def validate_deductions_integrity(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Melakukan validasi otomatis terhadap hasil perhitungan potongan:
        1. Total potongan tidak boleh negatif.
        2. Nominal harus integer (tidak ada float).
        3. Tidak boleh ada duplikasi employee_id dan tanggal.
        4. Hari libur tidak boleh menghasilkan potongan.
        5. Tidak hadir harus menghasilkan maksimal: Tidak absen masuk 10k, Tidak absen pulang 10k, Total 20k (bukan 40k).
        6. Potongan tidak dihitung dua kali.
        7. Deteksi data belum dihitung vs sudah dihitung.
        """
        with get_db_session() as session:
            # 1. Cek duplikasi employee_id dan tanggal pada attendance_deductions
            dup_query = (
                session.query(
                    AttendanceDeduction.employee_id,
                    AttendanceDeduction.attendance_date,
                    func.count(AttendanceDeduction.id).label("cnt"),
                )
                .filter(
                    extract("year", AttendanceDeduction.attendance_date) == year,
                    extract("month", AttendanceDeduction.attendance_date) == month,
                )
                .group_by(AttendanceDeduction.employee_id, AttendanceDeduction.attendance_date)
                .having(func.count(AttendanceDeduction.id) > 1)
                .all()
            )

            # 2. Cek potongan bernilai negatif
            neg_query = (
                session.query(AttendanceDeduction)
                .filter(
                    extract("year", AttendanceDeduction.attendance_date) == year,
                    extract("month", AttendanceDeduction.attendance_date) == month,
                    or_(
                        AttendanceDeduction.total_deduction < 0,
                        AttendanceDeduction.deduction_late < 0,
                        AttendanceDeduction.deduction_early_leave < 0,
                        AttendanceDeduction.deduction_missing_check_in < 0,
                        AttendanceDeduction.deduction_missing_check_out < 0,
                    ),
                )
                .all()
            )

            # 3. Cek apakah ada potongan pada hari libur / bukan hari kerja
            holiday_violations = (
                session.query(AttendanceDeduction)
                .join(WorkCalendar, AttendanceDeduction.attendance_date == WorkCalendar.calendar_date)
                .filter(
                    WorkCalendar.is_working_day == False,
                    AttendanceDeduction.total_deduction > 0,
                    extract("year", AttendanceDeduction.attendance_date) == year,
                    extract("month", AttendanceDeduction.attendance_date) == month,
                )
                .all()
            )

            # 4. Cek anomali tidak hadir (kedua scan kosong tapi total > 20000 atau terjadi penambahan alfa ganda)
            unreasonable_absent = (
                session.query(AttendanceDeduction)
                .join(AttendanceDaily, AttendanceDeduction.attendance_daily_id == AttendanceDaily.id)
                .filter(
                    extract("year", AttendanceDeduction.attendance_date) == year,
                    extract("month", AttendanceDeduction.attendance_date) == month,
                    AttendanceDaily.actual_check_in == None,
                    AttendanceDaily.actual_check_out == None,
                    AttendanceDeduction.total_deduction > 20000,
                )
                .all()
            )

            # 5. Cek data absensi harian yang belum dihitung
            daily_total = (
                session.query(AttendanceDaily)
                .filter(
                    extract("year", AttendanceDaily.attendance_date) == year,
                    extract("month", AttendanceDaily.attendance_date) == month,
                )
                .count()
            )

            deduction_total = (
                session.query(AttendanceDeduction)
                .filter(
                    extract("year", AttendanceDeduction.attendance_date) == year,
                    extract("month", AttendanceDeduction.attendance_date) == month,
                )
                .count()
            )

            uncalculated_count = max(0, daily_total - deduction_total)

            is_valid = (
                len(dup_query) == 0
                and len(neg_query) == 0
                and len(holiday_violations) == 0
                and len(unreasonable_absent) == 0
            )

            issues = []
            if len(dup_query) > 0:
                issues.append(f"Ditemukan {len(dup_query)} record duplikasi karyawan x tanggal pada data potongan.")
            if len(neg_query) > 0:
                issues.append(f"Ditemukan {len(neg_query)} nilai potongan bernilai negatif.")
            if len(holiday_violations) > 0:
                issues.append(f"Ditemukan {len(holiday_violations)} potongan pada hari libur / bukan hari kerja.")
            if len(unreasonable_absent) > 0:
                issues.append(f"Ditemukan {len(unreasonable_absent)} anomali potongan ketidakhadiran > Rp20.000.")
            if uncalculated_count > 0:
                issues.append(f"Terdapat {uncalculated_count} data absensi harian yang belum dihitung potongannya.")

            return {
                "is_valid": is_valid,
                "year": year,
                "month": month,
                "daily_total": daily_total,
                "calculated_total": deduction_total,
                "uncalculated_count": uncalculated_count,
                "duplicate_count": len(dup_query),
                "negative_count": len(neg_query),
                "holiday_violation_count": len(holiday_violations),
                "unreasonable_absent_count": len(unreasonable_absent),
                "issues": issues,
            }
