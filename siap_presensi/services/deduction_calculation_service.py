"""
Layanan Perhitungan Status dan Nominal Potongan Absensi (Tahap 5).
SIAP - Sistem Informasi Administrasi Presensi.

Aturan Utama:
1. Sumber data: Master Karyawan, Kalender Kerja, attendance_daily, dan Pengaturan Sistem.
   Data attendance_raw TIDAK BOLEH diubah.
2. Jam Kerja Standar:
   - Senin - Kamis: Masuk 08:15 WIB, Pulang 16:30 WIB
   - Jumat: Masuk 08:15 WIB, Pulang 17:00 WIB
   - Sabtu & Minggu: Bukan hari kerja (default)
3. Nominal Potongan:
   - Masuk tepat waktu (<= 08:15): Rp0
   - Terlambat <= 60 menit: Rp7.500
   - Terlambat > 60 menit: Rp10.000
   - Pulang cepat: Rp10.000
   - Tidak absen masuk: Rp10.000
   - Tidak absen pulang: Rp10.000
   - Tidak absen masuk & pulang: Rp10.000 + Rp10.000 = Rp20.000 (TIDAK BOLEH ada tambahan Alfa Rp20.000 lagi)
   - Hari libur / Bukan hari kerja: Rp0
4. Mencegah Double Counting:
   - Jam masuk kosong: Tidak dihitung sebagai keterlambatan, melainkan Tidak Absen Masuk.
   - Jam pulang kosong: Tidak dihitung sebagai pulang cepat, melainkan Tidak Absen Pulang.
   - Unique constraint pada attendance_deductions memastikan 1 attendance_daily hanya memiliki 1 rincian perhitungan.
   - Recalculate menggantikan data lama secara atomik dalam database transaction.
"""
from datetime import date, datetime
import calendar as py_calendar
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session, joinedload

from database.connection import get_db_session
from database.models import (
    Employee,
    EmployeeStatus,
    WorkCalendar,
    CalendarStatus,
    AttendanceDaily,
    AttendanceDeduction,
    AttendanceStatus,
    AuditLog,
    Setting,
)
from services.settings_service import SettingsService
from utils.logger import get_logger
from utils.time_parser import parse_time_str

logger = get_logger("DeductionCalculationService")


class DeductionCalculationService:
    """Layanan terpusat untuk perhitungan status dan nominal potongan absensi."""

    CURRENT_CALCULATION_VERSION = "5.0.0"

    # Default Rules (Rupiah)
    DEFAULT_RATE_LATE_LTE_60 = 7500
    DEFAULT_RATE_LATE_GT_60 = 10000
    DEFAULT_RATE_EARLY_LEAVE = 10000
    DEFAULT_RATE_MISSING_CHECK_IN = 10000
    DEFAULT_RATE_MISSING_CHECK_OUT = 10000

    @classmethod
    def get_system_rates(cls) -> Dict[str, int]:
        """Mengambil konfigurasi nominal potongan dari tabel settings atau default."""
        settings = SettingsService.get_all()
        try:
            rate_late_lte_60 = int(settings.get("potongan_terlambat_sd_1jam", cls.DEFAULT_RATE_LATE_LTE_60))
        except (ValueError, TypeError):
            rate_late_lte_60 = cls.DEFAULT_RATE_LATE_LTE_60

        try:
            rate_late_gt_60 = int(settings.get("potongan_terlambat_gt_1jam", cls.DEFAULT_RATE_LATE_GT_60))
        except (ValueError, TypeError):
            rate_late_gt_60 = cls.DEFAULT_RATE_LATE_GT_60

        try:
            rate_early = int(settings.get("potongan_pulang_cepat", cls.DEFAULT_RATE_EARLY_LEAVE))
        except (ValueError, TypeError):
            rate_early = cls.DEFAULT_RATE_EARLY_LEAVE

        try:
            rate_missing_in = int(settings.get("potongan_tidak_absen_masuk", cls.DEFAULT_RATE_MISSING_CHECK_IN))
        except (ValueError, TypeError):
            rate_missing_in = cls.DEFAULT_RATE_MISSING_CHECK_IN

        try:
            rate_missing_out = int(settings.get("potongan_tidak_absen_pulang", cls.DEFAULT_RATE_MISSING_CHECK_OUT))
        except (ValueError, TypeError):
            rate_missing_out = cls.DEFAULT_RATE_MISSING_CHECK_OUT

        return {
            "rate_late_lte_60": max(0, rate_late_lte_60),
            "rate_late_gt_60": max(0, rate_late_gt_60),
            "rate_early_leave": max(0, rate_early),
            "rate_missing_check_in": max(0, rate_missing_in),
            "rate_missing_check_out": max(0, rate_missing_out),
        }

    @staticmethod
    def _time_to_minutes(time_str: Optional[str]) -> Optional[int]:
        """Konversi string jam HH:MM atau HH:MM:SS ke menit sejak tengah malam."""
        if not time_str or not time_str.strip() or time_str.strip() == "-":
            return None
        parsed = parse_time_str(time_str)
        if not parsed:
            return None
        return parsed.hour * 60 + parsed.minute

    @classmethod
    def calculate_late(
        cls,
        actual_check_in: Optional[str],
        scheduled_check_in: str,
        rate_lte_60: int = DEFAULT_RATE_LATE_LTE_60,
        rate_gt_60: int = DEFAULT_RATE_LATE_GT_60,
    ) -> Tuple[int, int]:
        """
        Menghitung menit keterlambatan dan nominal potongan keterlambatan.
        Aturan:
        - Jika jam masuk kosong -> bukan keterlambatan, return (0, 0).
        - Jika jam masuk <= jam jadwal -> 0 menit, Rp0.
        - Jika terlambat <= 60 menit -> diff menit, rate_lte_60 (Rp7.500).
        - Jika terlambat > 60 menit -> diff menit, rate_gt_60 (Rp10.000).
        """
        actual_m = cls._time_to_minutes(actual_check_in)
        sched_m = cls._time_to_minutes(scheduled_check_in)

        if actual_m is None or sched_m is None:
            return 0, 0

        if actual_m <= sched_m:
            return 0, 0

        late_minutes = actual_m - sched_m
        if late_minutes <= 60:
            return late_minutes, rate_lte_60
        else:
            return late_minutes, rate_gt_60

    @classmethod
    def calculate_early_leave(
        cls,
        actual_check_out: Optional[str],
        scheduled_check_out: str,
        rate_early: int = DEFAULT_RATE_EARLY_LEAVE,
    ) -> Tuple[int, int]:
        """
        Menghitung menit pulang cepat dan nominal potongan pulang cepat.
        Aturan:
        - Jika jam pulang kosong -> bukan pulang cepat, return (0, 0).
        - Jika jam pulang >= jam jadwal -> 0 menit, Rp0.
        - Jika pulang lebih awal -> diff menit, rate_early (Rp10.000).
        """
        actual_m = cls._time_to_minutes(actual_check_out)
        sched_m = cls._time_to_minutes(scheduled_check_out)

        if actual_m is None or sched_m is None:
            return 0, 0

        if actual_m >= sched_m:
            return 0, 0

        early_minutes = sched_m - actual_m
        return early_minutes, rate_early

    @classmethod
    def calculate_missing_check_in(
        cls,
        actual_check_in: Optional[str],
        is_working_day: bool,
        rate_missing: int = DEFAULT_RATE_MISSING_CHECK_IN,
    ) -> int:
        """Menghitung potongan jika tidak ada scan masuk pada hari kerja."""
        if not is_working_day:
            return 0
        if not actual_check_in or not actual_check_in.strip() or actual_check_in.strip() == "-":
            return rate_missing
        return 0

    @classmethod
    def calculate_missing_check_out(
        cls,
        actual_check_out: Optional[str],
        is_working_day: bool,
        rate_missing: int = DEFAULT_RATE_MISSING_CHECK_OUT,
    ) -> int:
        """Menghitung potongan jika tidak ada scan pulang pada hari kerja."""
        if not is_working_day:
            return 0
        if not actual_check_out or not actual_check_out.strip() or actual_check_out.strip() == "-":
            return rate_missing
        return 0

    @classmethod
    def calculate_daily(
        cls,
        attendance_date: date,
        actual_check_in: Optional[str],
        actual_check_out: Optional[str],
        calendar: Optional[WorkCalendar] = None,
        custom_rates: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Perhitungan komprehensif harian untuk satu catatan kehadiran.
        Mematuhi aturan validasi kalender, pemisahan komponen, dan pencegahan double counting.
        """
        rates = custom_rates or cls.get_system_rates()

        # 1. Periksa Status Hari Kalender Kerja
        # Hari 0=Senin, 1=Selasa, 2=Rabu, 3=Kamis, 4=Jumat, 5=Sabtu, 6=Minggu
        weekday = attendance_date.weekday()
        is_weekend = weekday in (5, 6)

        if calendar is not None:
            is_working_day = calendar.is_working_day
            sched_in = calendar.scheduled_check_in or ("08:15" if not is_weekend else None)
            if weekday == 4:  # Jumat
                sched_out = calendar.scheduled_check_out or "17:00"
            else:
                sched_out = calendar.scheduled_check_out or "16:30"
            day_status = calendar.calendar_status.value if hasattr(calendar.calendar_status, "value") else str(calendar.calendar_status)
        else:
            is_working_day = not is_weekend
            sched_in = "08:15" if is_working_day else None
            sched_out = ("17:00" if weekday == 4 else "16:30") if is_working_day else None
            day_status = "HARI_KERJA" if is_working_day else "AKHIR_PEKAN"

        # 2. Jika Bukan Hari Kerja
        if not is_working_day:
            return {
                "is_working_day": False,
                "attendance_status": "BUKAN_HARI_KERJA",
                "scheduled_check_in": sched_in,
                "scheduled_check_out": sched_out,
                "actual_check_in": actual_check_in,
                "actual_check_out": actual_check_out,
                "late_minutes": 0,
                "early_leave_minutes": 0,
                "deduction_late": 0,
                "deduction_early_leave": 0,
                "deduction_missing_check_in": 0,
                "deduction_missing_check_out": 0,
                "total_deduction": 0,
                "notes": f"Bukan hari kerja ({day_status}). Potongan Rp0.",
            }

        # 3. Hari Kerja: Analisis Ketersediaan Scan
        has_in = bool(actual_check_in and actual_check_in.strip() and actual_check_in.strip() != "-")
        has_out = bool(actual_check_out and actual_check_out.strip() and actual_check_out.strip() != "-")

        sched_in_str = sched_in or "08:15"
        sched_out_str = sched_out or ("17:00" if weekday == 4 else "16:30")

        # Kasus A: Keduanya Kosong (TIDAK_ABSEN)
        if not has_in and not has_out:
            ded_missing_in = rates["rate_missing_check_in"]
            ded_missing_out = rates["rate_missing_check_out"]
            total = ded_missing_in + ded_missing_out  # Tepat Rp20.000
            return {
                "is_working_day": True,
                "attendance_status": AttendanceStatus.TIDAK_ABSEN.value,
                "scheduled_check_in": sched_in_str,
                "scheduled_check_out": sched_out_str,
                "actual_check_in": None,
                "actual_check_out": None,
                "late_minutes": 0,
                "early_leave_minutes": 0,
                "deduction_late": 0,
                "deduction_early_leave": 0,
                "deduction_missing_check_in": ded_missing_in,
                "deduction_missing_check_out": ded_missing_out,
                "total_deduction": total,
                "notes": "Tidak scan masuk & pulang. Dikenakan potongan Tidak Absen Masuk + Tidak Absen Pulang (Total Rp20.000).",
            }

        # Kasus B: Hanya Scan Masuk (HANYA_ABSEN_MASUK)
        if has_in and not has_out:
            late_m, ded_late = cls.calculate_late(
                actual_check_in,
                sched_in_str,
                rates["rate_late_lte_60"],
                rates["rate_late_gt_60"],
            )
            ded_missing_in = 0
            ded_missing_out = rates["rate_missing_check_out"]
            ded_early = 0
            early_m = 0
            total = ded_late + ded_missing_out

            notes = f"Hanya scan masuk ({actual_check_in}). "
            if ded_late > 0:
                notes += f"Terlambat {late_m} mnt (Rp{ded_late:,}). "
            notes += f"Tidak scan pulang (Rp{ded_missing_out:,})."

            return {
                "is_working_day": True,
                "attendance_status": AttendanceStatus.HANYA_ABSEN_MASUK.value,
                "scheduled_check_in": sched_in_str,
                "scheduled_check_out": sched_out_str,
                "actual_check_in": actual_check_in,
                "actual_check_out": None,
                "late_minutes": late_m,
                "early_leave_minutes": early_m,
                "deduction_late": ded_late,
                "deduction_early_leave": ded_early,
                "deduction_missing_check_in": ded_missing_in,
                "deduction_missing_check_out": ded_missing_out,
                "total_deduction": total,
                "notes": notes,
            }

        # Kasus C: Hanya Scan Pulang (HANYA_ABSEN_PULANG)
        if not has_in and has_out:
            early_m, ded_early = cls.calculate_early_leave(
                actual_check_out,
                sched_out_str,
                rates["rate_early_leave"],
            )
            ded_missing_in = rates["rate_missing_check_in"]
            ded_missing_out = 0
            ded_late = 0
            late_m = 0
            total = ded_missing_in + ded_early

            notes = f"Hanya scan pulang ({actual_check_out}). "
            notes += f"Tidak scan masuk (Rp{ded_missing_in:,}). "
            if ded_early > 0:
                notes += f"Pulang cepat {early_m} mnt (Rp{ded_early:,})."

            return {
                "is_working_day": True,
                "attendance_status": AttendanceStatus.HANYA_ABSEN_PULANG.value,
                "scheduled_check_in": sched_in_str,
                "scheduled_check_out": sched_out_str,
                "actual_check_in": None,
                "actual_check_out": actual_check_out,
                "late_minutes": late_m,
                "early_leave_minutes": early_m,
                "deduction_late": ded_late,
                "deduction_early_leave": ded_early,
                "deduction_missing_check_in": ded_missing_in,
                "deduction_missing_check_out": ded_missing_out,
                "total_deduction": total,
                "notes": notes,
            }

        # Kasus D: Hadir Lengkap (HADIR_LENGKAP)
        late_m, ded_late = cls.calculate_late(
            actual_check_in,
            sched_in_str,
            rates["rate_late_lte_60"],
            rates["rate_late_gt_60"],
        )
        early_m, ded_early = cls.calculate_early_leave(
            actual_check_out,
            sched_out_str,
            rates["rate_early_leave"],
        )
        ded_missing_in = 0
        ded_missing_out = 0
        total = ded_late + ded_early

        notes = f"Hadir Lengkap ({actual_check_in} - {actual_check_out}). "
        if ded_late > 0:
            notes += f"Terlambat {late_m} mnt (Rp{ded_late:,}). "
        if ded_early > 0:
            notes += f"Pulang cepat {early_m} mnt (Rp{ded_early:,}). "
        if total == 0:
            notes += "Tepat waktu, tidak ada potongan (Rp0)."

        return {
            "is_working_day": True,
            "attendance_status": AttendanceStatus.HADIR_LENGKAP.value,
            "scheduled_check_in": sched_in_str,
            "scheduled_check_out": sched_out_str,
            "actual_check_in": actual_check_in,
            "actual_check_out": actual_check_out,
            "late_minutes": late_m,
            "early_leave_minutes": early_m,
            "deduction_late": ded_late,
            "deduction_early_leave": ded_early,
            "deduction_missing_check_in": ded_missing_in,
            "deduction_missing_check_out": ded_missing_out,
            "total_deduction": total,
            "notes": notes,
        }

    @classmethod
    def get_calculation_preview(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        employee_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Menyajikan ringkasan pra-perhitungan sebelum pengguna menyetujui proses:
        - Periode
        - Jumlah Karyawan Aktif
        - Jumlah Hari Kerja
        - Jumlah Record Harian yang akan diproses
        - Jumlah Data Bermasalah
        - Status Perhitungan Sebelumnya (apakah sudah pernah dihitung)
        """
        with get_db_session() as session:
            # 1. Hitung Hari Kerja pada Kalender
            working_days_count = (
                session.query(WorkCalendar)
                .filter(
                    WorkCalendar.year == year,
                    WorkCalendar.month == month,
                    WorkCalendar.is_working_day == True,
                )
                .count()
            )

            # 2. Hitung Karyawan Aktif
            emp_q = session.query(Employee).filter(Employee.status == EmployeeStatus.AKTIF)
            if unit and unit != "ALL" and unit.strip():
                emp_q = emp_q.filter(Employee.unit == unit)
            if employee_id:
                emp_q = emp_q.filter(Employee.id == employee_id)
            employees = emp_q.all()
            employee_ids = [e.id for e in employees]

            start_date = date(year, month, 1)
            end_date = date(year, month, py_calendar.monthrange(year, month)[1])

            # 3. Hitung Catatan attendance_daily
            daily_q = session.query(AttendanceDaily).filter(
                AttendanceDaily.attendance_date >= start_date,
                AttendanceDaily.attendance_date <= end_date,
            )
            if employee_ids:
                daily_q = daily_q.filter(AttendanceDaily.employee_id.in_(employee_ids))

            total_daily_records = daily_q.count()

            # Data Bermasalah
            problematic_count = daily_q.filter(
                or_(
                    AttendanceDaily.attendance_status == AttendanceStatus.DATA_BERMASALAH.value,
                    AttendanceDaily.has_conflict == True,
                )
            ).count()

            # Periksa apakah sudah ada data di attendance_deductions
            calculated_count = (
                session.query(AttendanceDeduction)
                .filter(
                    AttendanceDeduction.attendance_date >= start_date,
                    AttendanceDeduction.attendance_date <= end_date,
                )
            )
            if employee_ids:
                calculated_count = calculated_count.filter(AttendanceDeduction.employee_id.in_(employee_ids))
            existing_deduction_count = calculated_count.count()

            return {
                "year": year,
                "month": month,
                "period_label": f"{month:02d}/{year}",
                "unit": unit or "SEMUA UNIT",
                "employee_count": len(employees),
                "working_days_count": working_days_count,
                "total_daily_records": total_daily_records,
                "problematic_count": problematic_count,
                "existing_deduction_count": existing_deduction_count,
                "is_already_calculated": existing_deduction_count > 0,
                "can_proceed": total_daily_records > 0,
                "message": (
                    "Data absensi harian siap diproses."
                    if total_daily_records > 0
                    else "Belum ada data absensi harian pada periode ini. Silakan generate Absensi Harian terlebih dahulu di menu Data Absensi."
                ),
            }

    @classmethod
    def calculate_and_save_period(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        employee_id: Optional[int] = None,
        user_name: str = "ADMIN",
        recalculate: bool = True,
    ) -> Dict[str, Any]:
        """
        Mengeksekusi perhitungan status dan nominal potongan absensi secara atomik (ACID).
        - Mengambil konfigurasi tarif sistem.
        - Memproses setiap record attendance_daily yang relevan.
        - Menyimpan ke tabel attendance_deductions (upsert/replace bersih).
        - Memperbarui kolom penampung kalkulasi di attendance_daily.
        - Mencatat log audit.
        - Rollback otomatis jika ada error.
        """
        rates = cls.get_system_rates()

        with get_db_session() as session:
            # 1. Ambil Kalender Bulan Bersangkutan (cache dictionary berdasarkan tanggal)
            calendars = (
                session.query(WorkCalendar)
                .filter(WorkCalendar.year == year, WorkCalendar.month == month)
                .all()
            )
            calendar_map = {c.calendar_date: c for c in calendars}

            # 2. Ambil Karyawan Aktif
            emp_q = session.query(Employee).filter(Employee.status == EmployeeStatus.AKTIF)
            if unit and unit != "ALL" and unit.strip():
                emp_q = emp_q.filter(Employee.unit == unit)
            if employee_id:
                emp_q = emp_q.filter(Employee.id == employee_id)
            employees = emp_q.all()
            emp_ids = [e.id for e in employees]

            if not emp_ids:
                return {
                    "success": False,
                    "message": "Tidak ditemukan data karyawan aktif untuk diproses.",
                    "total_processed": 0,
                    "total_deduction_all": 0,
                }

            start_date = date(year, month, 1)
            end_date = date(year, month, py_calendar.monthrange(year, month)[1])

            # 3. Ambil Catatan Absensi Harian
            daily_records: List[AttendanceDaily] = (
                session.query(AttendanceDaily)
                .filter(
                    AttendanceDaily.attendance_date >= start_date,
                    AttendanceDaily.attendance_date <= end_date,
                    AttendanceDaily.employee_id.in_(emp_ids),
                )
                .order_by(AttendanceDaily.attendance_date.asc(), AttendanceDaily.employee_id.asc())
                .all()
            )

            if not daily_records:
                return {
                    "success": False,
                    "message": f"Tidak ditemukan data attendance_daily untuk periode {month:02d}/{year}. Silakan jalankan pembentukan absensi harian terlebih dahulu.",
                    "total_processed": 0,
                    "total_deduction_all": 0,
                }

            # 4. Ambil catatan potongan yang sudah ada untuk periode ini (untuk recalculate / update)
            daily_ids = [d.id for d in daily_records]
            existing_deductions = (
                session.query(AttendanceDeduction)
                .filter(AttendanceDeduction.attendance_daily_id.in_(daily_ids))
                .all()
            )
            deduction_map = {ded.attendance_daily_id: ded for ded in existing_deductions}

            # 5. Proses Perhitungan Setiap Record
            processed_count = 0
            created_count = 0
            updated_count = 0
            grand_total_deduction = 0

            for daily in daily_records:
                cal = calendar_map.get(daily.attendance_date)
                calc_result = cls.calculate_daily(
                    attendance_date=daily.attendance_date,
                    actual_check_in=daily.actual_check_in,
                    actual_check_out=daily.actual_check_out,
                    calendar=cal,
                    custom_rates=rates,
                )

                # Update status kehadiran di daily jika sebelumnya belum sesuai
                if calc_result["attendance_status"] != "BUKAN_HARI_KERJA":
                    daily.attendance_status = calc_result["attendance_status"]

                # Update kolom kalkulasi di tabel attendance_daily untuk sinkronisasi
                daily.terlambat_menit = calc_result["late_minutes"]
                daily.pulang_cepat_menit = calc_result["early_leave_minutes"]
                daily.potongan_masuk = float(calc_result["deduction_missing_check_in"] + calc_result["deduction_late"])
                daily.potongan_pulang = float(calc_result["deduction_missing_check_out"] + calc_result["deduction_early_leave"])
                daily.potongan_tidak_hadir = float(
                    calc_result["deduction_missing_check_in"] + calc_result["deduction_missing_check_out"]
                    if calc_result["attendance_status"] == AttendanceStatus.TIDAK_ABSEN.value
                    else 0
                )
                daily.total_potongan = float(calc_result["total_deduction"])
                daily.updated_at = datetime.utcnow()
                daily.updated_by = user_name

                # Simpan / update di tabel attendance_deductions
                existing_ded = deduction_map.get(daily.id)
                if existing_ded:
                    existing_ded.employee_id = daily.employee_id
                    existing_ded.attendance_date = daily.attendance_date
                    existing_ded.late_minutes = calc_result["late_minutes"]
                    existing_ded.early_leave_minutes = calc_result["early_leave_minutes"]
                    existing_ded.deduction_late = calc_result["deduction_late"]
                    existing_ded.deduction_early_leave = calc_result["deduction_early_leave"]
                    existing_ded.deduction_missing_check_in = calc_result["deduction_missing_check_in"]
                    existing_ded.deduction_missing_check_out = calc_result["deduction_missing_check_out"]
                    existing_ded.total_deduction = calc_result["total_deduction"]
                    existing_ded.calculation_version = cls.CURRENT_CALCULATION_VERSION
                    existing_ded.calculated_at = datetime.utcnow()
                    existing_ded.calculated_by = user_name
                    existing_ded.notes = calc_result["notes"]
                    updated_count += 1
                else:
                    new_ded = AttendanceDeduction(
                        attendance_daily_id=daily.id,
                        employee_id=daily.employee_id,
                        attendance_date=daily.attendance_date,
                        late_minutes=calc_result["late_minutes"],
                        early_leave_minutes=calc_result["early_leave_minutes"],
                        deduction_late=calc_result["deduction_late"],
                        deduction_early_leave=calc_result["deduction_early_leave"],
                        deduction_missing_check_in=calc_result["deduction_missing_check_in"],
                        deduction_missing_check_out=calc_result["deduction_missing_check_out"],
                        total_deduction=calc_result["total_deduction"],
                        calculation_version=cls.CURRENT_CALCULATION_VERSION,
                        calculated_at=datetime.utcnow(),
                        calculated_by=user_name,
                        notes=calc_result["notes"],
                    )
                    session.add(new_ded)
                    deduction_map[daily.id] = new_ded
                    created_count += 1

                processed_count += 1
                grand_total_deduction += calc_result["total_deduction"]

            # 6. Catat Log Audit Trail
            action_type = "RECALCULATE_DEDUCTION" if recalculate and updated_count > 0 else "CALCULATE_DEDUCTION"
            audit = AuditLog(
                action=action_type,
                module="POTONGAN_ABSENSI",
                description=(
                    f"Perhitungan potongan absensi periode {month:02d}/{year} ({unit or 'SEMUA UNIT'}): "
                    f"{processed_count} data diproses ({created_count} baru, {updated_count} diperbarui). "
                    f"Total potongan Rp{grand_total_deduction:,}."
                ),
            )
            session.add(audit)
            session.commit()

            logger.info(
                f"Perhitungan potongan selesai untuk periode {month:02d}/{year}: "
                f"{processed_count} data, total Rp{grand_total_deduction:,}"
            )

            return {
                "success": True,
                "message": (
                    f"Berhasil menghitung potongan absensi periode {month:02d}/{year}!\n"
                    f"Total {processed_count} data diproses ({created_count} baru, {updated_count} dihitung ulang).\n"
                    f"Total nominal potongan: Rp{grand_total_deduction:,}."
                ),
                "total_processed": processed_count,
                "created_count": created_count,
                "updated_count": updated_count,
                "total_deduction_all": grand_total_deduction,
                "year": year,
                "month": month,
            }

    @classmethod
    def get_monthly_recap(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Menyediakan data Rekapitulasi Potongan Bulanan per Karyawan.
        Kolom wajib:
        - No
        - Unit
        - Nama
        - Status (Kepegawaian)
        - Terlambat (Total Rp)
        - Pulang Cepat (Total Rp)
        - Tidak Absen Masuk (Total Rp)
        - Tidak Absen Pulang (Total Rp)
        - Jumlah Potongan Absensi (Total Rp)
        Menghitung total per unit dan total seluruh karyawan.
        """
        with get_db_session() as session:
            # Ambil karyawan aktif yang sesuai filter
            emp_q = session.query(Employee).filter(Employee.status == EmployeeStatus.AKTIF)
            if unit and unit != "ALL" and unit.strip():
                emp_q = emp_q.filter(Employee.unit == unit)
            if search and search.strip():
                term = f"%{search.strip()}%"
                emp_q = emp_q.filter(
                    or_(
                        Employee.nama.ilike(term),
                        Employee.emp_num.ilike(term),
                        Employee.nik.ilike(term),
                    )
                )
            employees = emp_q.order_by(Employee.unit.asc(), Employee.nama.asc()).all()
            emp_map = {e.id: e for e in employees}
            emp_ids = list(emp_map.keys())

            if not emp_ids:
                return {
                    "year": year,
                    "month": month,
                    "unit_filter": unit or "ALL",
                    "items": [],
                    "unit_totals": {},
                    "grand_total": {
                        "total_karyawan": 0,
                        "total_terlambat": 0,
                        "total_pulang_cepat": 0,
                        "total_tidak_absen_masuk": 0,
                        "total_tidak_absen_pulang": 0,
                        "total_potongan_keseluruhan": 0,
                    },
                }

            start_date = date(year, month, 1)
            end_date = date(year, month, py_calendar.monthrange(year, month)[1])

            # Ambil seluruh attendance_deductions untuk karyawan ini di bulan & tahun ini
            deductions: List[AttendanceDeduction] = (
                session.query(AttendanceDeduction)
                .filter(
                    AttendanceDeduction.attendance_date >= start_date,
                    AttendanceDeduction.attendance_date <= end_date,
                    AttendanceDeduction.employee_id.in_(emp_ids),
                )
                .all()
            )

            # Kelompokkan potongan per employee_id
            emp_totals = defaultdict(lambda: {
                "terlambat": 0,
                "pulang_cepat": 0,
                "tidak_absen_masuk": 0,
                "tidak_absen_pulang": 0,
                "total": 0,
                "count_days": 0,
            })

            for ded in deductions:
                t = emp_totals[ded.employee_id]
                t["terlambat"] += ded.deduction_late
                t["pulang_cepat"] += ded.deduction_early_leave
                t["tidak_absen_masuk"] += ded.deduction_missing_check_in
                t["tidak_absen_pulang"] += ded.deduction_missing_check_out
                t["total"] += ded.total_deduction
                t["count_days"] += 1

            # Bentuk List Baris Rekap
            items = []
            unit_totals = defaultdict(lambda: {
                "employee_count": 0,
                "total_terlambat": 0,
                "total_pulang_cepat": 0,
                "total_tidak_absen_masuk": 0,
                "total_tidak_absen_pulang": 0,
                "total_potongan": 0,
            })

            grand_terlambat = 0
            grand_pulang_cepat = 0
            grand_missing_in = 0
            grand_missing_out = 0
            grand_total_potongan = 0

            for idx, emp in enumerate(employees, start=1):
                t = emp_totals[emp.id]
                item_unit = emp.unit or "Tanpa Unit"
                emp_status_str = emp.status.value if hasattr(emp.status, "value") else str(emp.status)

                row = {
                    "no": idx,
                    "employee_id": emp.id,
                    "emp_num": emp.emp_num or "-",
                    "no_id": emp.no_id or "-",
                    "nik": emp.nik or "-",
                    "nama": emp.nama,
                    "unit": item_unit,
                    "status": emp_status_str,
                    "terlambat": t["terlambat"],
                    "pulang_cepat": t["pulang_cepat"],
                    "tidak_absen_masuk": t["tidak_absen_masuk"],
                    "tidak_absen_pulang": t["tidak_absen_pulang"],
                    "jumlah_potongan": t["total"],
                    # Representasi terformat
                    "terlambat_formatted": f"Rp{t['terlambat']:,}",
                    "pulang_cepat_formatted": f"Rp{t['pulang_cepat']:,}",
                    "tidak_absen_masuk_formatted": f"Rp{t['tidak_absen_masuk']:,}",
                    "tidak_absen_pulang_formatted": f"Rp{t['tidak_absen_pulang']:,}",
                    "jumlah_potongan_formatted": f"Rp{t['total']:,}",
                }
                items.append(row)

                # Akumulasi Unit
                u = unit_totals[item_unit]
                u["employee_count"] += 1
                u["total_terlambat"] += t["terlambat"]
                u["total_pulang_cepat"] += t["pulang_cepat"]
                u["total_tidak_absen_masuk"] += t["tidak_absen_masuk"]
                u["total_tidak_absen_pulang"] += t["tidak_absen_pulang"]
                u["total_potongan"] += t["total"]

                # Akumulasi Grand Total
                grand_terlambat += t["terlambat"]
                grand_pulang_cepat += t["pulang_cepat"]
                grand_missing_in += t["tidak_absen_masuk"]
                grand_missing_out += t["tidak_absen_pulang"]
                grand_total_potongan += t["total"]

            return {
                "year": year,
                "month": month,
                "unit_filter": unit or "ALL",
                "items": items,
                "unit_totals": dict(unit_totals),
                "grand_total": {
                    "total_karyawan": len(employees),
                    "total_terlambat": grand_terlambat,
                    "total_pulang_cepat": grand_pulang_cepat,
                    "total_tidak_absen_masuk": grand_missing_in,
                    "total_tidak_absen_pulang": grand_missing_out,
                    "total_potongan_keseluruhan": grand_total_potongan,
                    "total_terlambat_formatted": f"Rp{grand_terlambat:,}",
                    "total_pulang_cepat_formatted": f"Rp{grand_pulang_cepat:,}",
                    "total_tidak_absen_masuk_formatted": f"Rp{grand_missing_in:,}",
                    "total_tidak_absen_pulang_formatted": f"Rp{grand_missing_out:,}",
                    "total_potongan_keseluruhan_formatted": f"Rp{grand_total_potongan:,}",
                },
            }

    @classmethod
    def get_daily_details(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        search: Optional[str] = None,
        date_filter: Optional[date] = None,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Menyajikan Laporan Rincian Absensi dan Potongan Harian (Bagian 9 Spesifikasi).
        Kolom:
        - No
        - Unit
        - Nama
        - Hari
        - Tanggal
        - Jam Masuk
        - Jam Pulang
        - Status Masuk
        - Status Pulang
        - Status Kehadiran
        - Menit Terlambat
        - Menit Pulang Cepat
        - Potongan Terlambat
        - Potongan Pulang Cepat
        - Tidak Absen Masuk
        - Tidak Absen Pulang
        - Total Potongan Per Hari
        """
        start_date = date(year, month, 1)
        end_date = date(year, month, py_calendar.monthrange(year, month)[1])

        with get_db_session() as session:
            q = (
                session.query(AttendanceDaily, AttendanceDeduction, Employee)
                .join(Employee, AttendanceDaily.employee_id == Employee.id)
                .outerjoin(AttendanceDeduction, AttendanceDaily.id == AttendanceDeduction.attendance_daily_id)
                .filter(
                    AttendanceDaily.attendance_date >= start_date,
                    AttendanceDaily.attendance_date <= end_date,
                )
            )

            if unit and unit != "ALL" and unit.strip():
                q = q.filter(Employee.unit == unit)

            if search and search.strip():
                term = f"%{search.strip()}%"
                q = q.filter(
                    or_(
                        Employee.nama.ilike(term),
                        Employee.emp_num.ilike(term),
                        Employee.nik.ilike(term),
                    )
                )

            if date_filter:
                q = q.filter(AttendanceDaily.attendance_date == date_filter)

            if status_filter and status_filter != "ALL":
                q = q.filter(AttendanceDaily.attendance_status == status_filter)

            records = q.order_by(AttendanceDaily.attendance_date.asc(), Employee.nama.asc()).all()

            results = []
            for idx, (daily, ded, emp) in enumerate(records, start=1):
                late_m = ded.late_minutes if ded else (daily.terlambat_menit or 0)
                early_m = ded.early_leave_minutes if ded else (daily.pulang_cepat_menit or 0)
                ded_late = ded.deduction_late if ded else 0
                ded_early = ded.deduction_early_leave if ded else 0
                ded_miss_in = ded.deduction_missing_check_in if ded else 0
                ded_miss_out = ded.deduction_missing_check_out if ded else 0
                total_ded = ded.total_deduction if ded else int(daily.total_potongan or 0)

                row = {
                    "no": idx,
                    "id": daily.id,
                    "employee_id": emp.id,
                    "unit": emp.unit or "-",
                    "nama": emp.nama,
                    "hari": daily.day_name or daily.attendance_date.strftime("%A"),
                    "tanggal": daily.attendance_date.strftime("%Y-%m-%d"),
                    "jam_masuk": daily.actual_check_in or "-",
                    "jam_pulang": daily.actual_check_out or "-",
                    "status_masuk": daily.check_in_status,
                    "status_pulang": daily.check_out_status,
                    "status_kehadiran": daily.attendance_status,
                    "menit_terlambat": late_m,
                    "menit_pulang_cepat": early_m,
                    "potongan_terlambat": ded_late,
                    "potongan_pulang_cepat": ded_early,
                    "tidak_absen_masuk": ded_miss_in,
                    "tidak_absen_pulang": ded_miss_out,
                    "total_potongan": total_ded,
                    # Format Rupiah
                    "potongan_terlambat_formatted": f"Rp{ded_late:,}",
                    "potongan_pulang_cepat_formatted": f"Rp{ded_early:,}",
                    "tidak_absen_masuk_formatted": f"Rp{ded_miss_in:,}",
                    "tidak_absen_pulang_formatted": f"Rp{ded_miss_out:,}",
                    "total_potongan_formatted": f"Rp{total_ded:,}",
                    "notes": ded.notes if ded else (daily.notes or ""),
                }
                results.append(row)

            return results

    @classmethod
    def validate_calculation_integrity(cls, year: int, month: int) -> Dict[str, Any]:
        """
        Validasi integritas data perhitungan (Memenuhi Bagian 10):
        1. Tidak hadir penuh = Rp20.000 (tidak ada Alfa ganda).
        2. Hari libur = Rp0.
        3. Tidak absen masuk tidak menghitung keterlambatan.
        4. Tidak absen pulang tidak menghitung pulang cepat.
        5. Nominal tidak ada yang bernilai negatif.
        6. Satu attendance_daily hanya memiliki 1 rincian perhitungan.
        """
        issues = []
        start_date = date(year, month, 1)
        end_date = date(year, month, py_calendar.monthrange(year, month)[1])

        with get_db_session() as session:
            deductions: List[AttendanceDeduction] = (
                session.query(AttendanceDeduction)
                .join(AttendanceDaily, AttendanceDeduction.attendance_daily_id == AttendanceDaily.id)
                .filter(
                    AttendanceDeduction.attendance_date >= start_date,
                    AttendanceDeduction.attendance_date <= end_date,
                )
                .all()
            )

            # Cek duplikasi daily_id
            seen_daily_ids = set()
            for ded in deductions:
                if ded.attendance_daily_id in seen_daily_ids:
                    issues.append(f"Duplikasi record perhitungan pada attendance_daily_id={ded.attendance_daily_id}")
                seen_daily_ids.add(ded.attendance_daily_id)

                # Validasi nilai non-negatif
                if (
                    ded.deduction_late < 0
                    or ded.deduction_early_leave < 0
                    or ded.deduction_missing_check_in < 0
                    or ded.deduction_missing_check_out < 0
                    or ded.total_deduction < 0
                ):
                    issues.append(f"Ditemukan nominal negatif pada deduction id={ded.id}")

                # Validasi jumlah total komponen
                sum_components = (
                    ded.deduction_late
                    + ded.deduction_early_leave
                    + ded.deduction_missing_check_in
                    + ded.deduction_missing_check_out
                )
                if sum_components != ded.total_deduction:
                    issues.append(
                        f"Inkonsistensi total pada deduction id={ded.id}: komponen={sum_components}, total={ded.total_deduction}"
                    )

                # Validasi rule: jika missing check in -> late_minutes harus 0 dan deduction_late harus 0
                if ded.deduction_missing_check_in > 0 and (ded.late_minutes > 0 or ded.deduction_late > 0):
                    issues.append(f"Double counting terlambat saat scan masuk kosong pada deduction id={ded.id}")

                # Validasi rule: jika missing check out -> early_leave_minutes harus 0 dan deduction_early_leave harus 0
                if ded.deduction_missing_check_out > 0 and (ded.early_leave_minutes > 0 or ded.deduction_early_leave > 0):
                    issues.append(f"Double counting pulang cepat saat scan pulang kosong pada deduction id={ded.id}")

                # Validasi rule: jika tidak absen keduanya -> total harus <= 20.000 (tidak boleh 40.000)
                if ded.deduction_missing_check_in > 0 and ded.deduction_missing_check_out > 0:
                    if ded.total_deduction > 20000:
                        issues.append(
                            f"Total ketidakhadiran melebihi Rp20.000 (terindikasi double counting alfa) pada id={ded.id}: total={ded.total_deduction}"
                        )

            return {
                "is_valid": len(issues) == 0,
                "total_checked": len(deductions),
                "issue_count": len(issues),
                "issues": issues,
            }
