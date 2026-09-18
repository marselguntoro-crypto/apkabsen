"""
Layanan Dashboard Statistik SIAP.
Menghitung metrik kehadiran, ketidakhadiran, pelanggaran jam kerja,
dan akumulasi potongan berdasarkan filter periode bulan dan tahun.
Menampilkan kondisi data riil (0 jika belum ada data).
"""
from datetime import date
from typing import Dict, Any
from sqlalchemy import func, extract

from database.connection import get_db_session
from database.models import (
    Employee,
    EmployeeStatus,
    AttendanceDaily,
    AttendanceStatus,
    AttendanceDeduction,
    WorkCalendar,
    CalendarStatus,
)
from services.settings_service import SettingsService
from utils.logger import get_logger

logger = get_logger("DashboardService")


class DashboardService:
    """Service penyedia data analitik dan statistik dashboard."""

    @staticmethod
    def get_summary_statistics(month: int, year: int) -> Dict[str, Any]:
        """
        Mengambil ringkasan statistik untuk periode bulan dan tahun tertentu.
        Menghasilkan data riil dari database SQLite (menampilkan 0 jika masih kosong).
        """
        stats = {
            "month": month,
            "year": year,
            "total_karyawan": 0,
            "total_hari_kerja": 0,
            "total_hadir": 0,
            "total_alfa": 0,
            "total_terlambat": 0,
            "total_pulang_cepat": 0,
            "total_potongan": 0,
            "nominal_terlambat": 0,
            "nominal_pulang_cepat": 0,
            "nominal_tidak_absen_masuk": 0,
            "nominal_tidak_absen_pulang": 0,
            "formatted_potongan": "Rp 0",
        }

        try:
            with get_db_session() as session:
                # 1. Total Karyawan Aktif
                total_karyawan = (
                    session.query(func.count(Employee.id))
                    .filter(Employee.status == EmployeeStatus.AKTIF)
                    .scalar()
                ) or 0
                stats["total_karyawan"] = total_karyawan

                # 2. Total Hari Kerja (Dari kalender atau fallback ke target settings)
                calendar_work_days = (
                    session.query(func.count(WorkCalendar.id))
                    .filter(
                        WorkCalendar.month == month,
                        WorkCalendar.year == year,
                        WorkCalendar.is_working_day == True,
                    )
                    .scalar()
                ) or 0

                if calendar_work_days > 0:
                    stats["total_hari_kerja"] = calendar_work_days
                else:
                    target_str = SettingsService.get("target_hari_kerja_bulanan", "18")
                    stats["total_hari_kerja"] = int(target_str) if target_str.isdigit() else 18

                # 3. Statistik Absensi Harian untuk periode (Bulan & Tahun)
                daily_query = session.query(AttendanceDaily).filter(
                    extract("month", AttendanceDaily.attendance_date) == month,
                    extract("year", AttendanceDaily.attendance_date) == year,
                )

                stats["total_hadir"] = (
                    daily_query.filter(
                        (AttendanceDaily.attendance_status == AttendanceStatus.HADIR_LENGKAP.value)
                        | (AttendanceDaily.attendance_status == AttendanceStatus.HANYA_ABSEN_MASUK.value)
                        | (AttendanceDaily.actual_check_in.isnot(None))
                    ).count()
                )

                stats["total_alfa"] = (
                    daily_query.filter(
                        (AttendanceDaily.attendance_status == AttendanceStatus.TIDAK_ABSEN.value)
                        | (AttendanceDaily.potongan_tidak_hadir > 0)
                    ).count()
                )

                stats["total_terlambat"] = (
                    daily_query.filter(AttendanceDaily.terlambat_menit > 0).count()
                )

                stats["total_pulang_cepat"] = (
                    daily_query.filter(AttendanceDaily.pulang_cepat_menit > 0).count()
                )

                # 4. Total Potongan Rupiah dari AttendanceDeduction (Presisi Integer)
                ded_stats = (
                    session.query(
                        func.sum(AttendanceDeduction.total_deduction).label("sum_total"),
                        func.sum(AttendanceDeduction.deduction_late).label("sum_late"),
                        func.sum(AttendanceDeduction.deduction_early_leave).label("sum_early"),
                        func.sum(AttendanceDeduction.deduction_missing_check_in).label("sum_miss_in"),
                        func.sum(AttendanceDeduction.deduction_missing_check_out).label("sum_miss_out"),
                    )
                    .filter(
                        extract("month", AttendanceDeduction.attendance_date) == month,
                        extract("year", AttendanceDeduction.attendance_date) == year,
                    )
                    .first()
                )

                if ded_stats and ded_stats.sum_total is not None:
                    stats["total_potongan"] = int(ded_stats.sum_total)
                    stats["nominal_terlambat"] = int(ded_stats.sum_late or 0)
                    stats["nominal_pulang_cepat"] = int(ded_stats.sum_early or 0)
                    stats["nominal_tidak_absen_masuk"] = int(ded_stats.sum_miss_in or 0)
                    stats["nominal_tidak_absen_pulang"] = int(ded_stats.sum_miss_out or 0)
                else:
                    # Fallback ke AttendanceDaily
                    total_pot = (
                        session.query(func.sum(AttendanceDaily.total_potongan))
                        .filter(
                            extract("month", AttendanceDaily.attendance_date) == month,
                            extract("year", AttendanceDaily.attendance_date) == year,
                        )
                        .scalar()
                    ) or 0
                    stats["total_potongan"] = int(total_pot)

                stats["formatted_potongan"] = DashboardService.format_rupiah(stats["total_potongan"])

        except Exception as e:
            logger.error(f"Gagal mengambil statistik dashboard periode {month}/{year}: {e}")

        return stats

    @staticmethod
    def format_rupiah(amount: float) -> str:
        """Memformat angka menjadi format mata uang Rupiah standar (contoh: Rp 150.000)."""
        rounded = int(round(amount))
        formatted = f"{rounded:,}".replace(",", ".")
        return f"Rp {formatted}"
