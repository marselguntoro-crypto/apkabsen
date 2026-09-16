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
            "total_potongan": 0.0,
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
                    # Fallback ke konfigurasi target hari kerja bulanan
                    target_str = SettingsService.get("target_hari_kerja_bulanan", "18")
                    stats["total_hari_kerja"] = int(target_str) if target_str.isdigit() else 18

                # 3. Statistik Absensi Harian untuk periode (Bulan & Tahun)
                daily_query = session.query(AttendanceDaily).filter(
                    extract("month", AttendanceDaily.attendance_date) == month,
                    extract("year", AttendanceDaily.attendance_date) == year,
                )

                # Total Hadir (Memiliki scan masuk atau hadir lengkap)
                stats["total_hadir"] = (
                    daily_query.filter(
                        (AttendanceDaily.attendance_status == AttendanceStatus.HADIR_LENGKAP.value)
                        | (AttendanceDaily.attendance_status == AttendanceStatus.HANYA_ABSEN_MASUK.value)
                        | (AttendanceDaily.actual_check_in.isnot(None))
                    ).count()
                )

                # Total Alfa (Tidak absen / tidak hadir)
                stats["total_alfa"] = (
                    daily_query.filter(
                        (AttendanceDaily.attendance_status == AttendanceStatus.TIDAK_ABSEN.value)
                        | (AttendanceDaily.potongan_tidak_hadir > 0)
                    ).count()
                )

                # Terlambat
                stats["total_terlambat"] = (
                    daily_query.filter(AttendanceDaily.terlambat_menit > 0).count()
                )

                # Pulang Cepat
                stats["total_pulang_cepat"] = (
                    daily_query.filter(AttendanceDaily.pulang_cepat_menit > 0).count()
                )

                # Total Potongan Rupiah
                total_potongan = (
                    session.query(func.sum(AttendanceDaily.total_potongan))
                    .filter(
                        extract("month", AttendanceDaily.tanggal) == month,
                        extract("year", AttendanceDaily.tanggal) == year,
                    )
                    .scalar()
                ) or 0.0

                stats["total_potongan"] = float(total_potongan)
                stats["formatted_potongan"] = DashboardService.format_rupiah(float(total_potongan))

        except Exception as e:
            logger.error(f"Gagal mengambil statistik dashboard periode {month}/{year}: {e}")

        return stats

    @staticmethod
    def format_rupiah(amount: float) -> str:
        """Memformat angka menjadi format mata uang Rupiah standar (contoh: Rp 150.000)."""
        rounded = int(round(amount))
        formatted = f"{rounded:,}".replace(",", ".")
        return f"Rp {formatted}"
