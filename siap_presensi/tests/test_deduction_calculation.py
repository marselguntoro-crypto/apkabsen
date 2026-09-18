"""
Pengujian Komprehensif Mesin Perhitungan Potongan Absensi & Pelaporan (Tahap 5).
Menguji 17 Kasus Uji Skenario Bisnis, Integritas Data, dan Layanan Export SIAP:
1. Keterlambatan <= 1 jam (Rp7.500)
2. Keterlambatan > 1 jam (Rp10.000)
3. Pulang Cepat (Rp10.000)
4. Tidak Absen Masuk (Rp10.000)
5. Tidak Absen Pulang (Rp10.000)
6. Tidak Absen Masuk dan Pulang (Maksimal Rp20.000, anti-double counting)
7. Tepat Waktu (Rp0)
8. Kombinasi Terlambat dan Pulang Cepat (Rp7.500 + Rp10.000 = Rp17.500)
9. Hari Libur / Akhir Pekan (Rp0)
10. Karyawan Non-Aktif (Diabaikan / Rp0)
11. Toleransi Keterlambatan (Berdasarkan konfigurasi)
12. Hitung Ulang (Force Recalculate) tanpa duplikasi data
13. Rekap Potongan Bulanan & Subtotal Unit
14. Grand Total Rekapitulasi Potongan
15. Laporan Detail Absensi Harian & Filter
16. Validasi Integritas Data (Anti-negatif, konsistensi integer Rupiah)
17. Layanan Export Excel & PDF
"""
import os
import sys
import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.base import Base
from database.models import (
    User,
    UserRole,
    Employee,
    EmployeeStatus,
    WorkCalendar,
    CalendarStatus,
    AttendanceDaily,
    AttendanceStatus,
    CheckScanStatus,
    AttendanceDeduction,
    AttendanceDeductionItem,
    AuditLog,
    Setting,
)
from services.deduction_calculation_service import DeductionCalculationService
from services.export_service import ExportService


class TestDeductionCalculationTahap5(unittest.TestCase):
    """Pengujian Unit & Integrasi 17 Kasus Uji Mesin Potongan Absensi."""

    def setUp(self):
        """Siapkan SQLite in-memory / temporary isolated database."""
        self.temp_dir = TemporaryDirectory()
        self.test_db_path = Path(self.temp_dir.name) / "test_deductions.db"
        self.engine = create_engine(f"sqlite:///{self.test_db_path.as_posix()}", echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.SessionFactory = sessionmaker(bind=self.engine)

        self.db_patcher = patch("database.connection.get_db_session")
        self.mock_get_db_session = self.db_patcher.start()
        self.mock_get_db_session.side_effect = lambda: self.SessionFactory()

        self._seed_initial_data()

    def tearDown(self):
        self.db_patcher.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def _seed_initial_data(self):
        with self.SessionFactory() as session:
            # Setting default
            session.add_all([
                Setting(key="potongan_terlambat_ringan", value="7500", description="Late <= 1 hr"),
                Setting(key="potongan_terlambat_berat", value="10000", description="Late > 1 hr"),
                Setting(key="potongan_pulang_cepat", value="10000", description="Early leave"),
                Setting(key="potongan_tidak_scan_masuk", value="10000", description="Missing in"),
                Setting(key="potongan_tidak_scan_pulang", value="10000", description="Missing out"),
                Setting(key="potongan_alfa_harian", value="20000", description="Max absent day"),
                Setting(key="toleransi_terlambat_menit", value="0", description="Grace period"),
            ])

            # Kalender 1-5 Agustus 2026 (1-4 Kerja, 5 Libur)
            for d in range(1, 6):
                dt = date(2026, 8, d)
                is_work = (d != 5)
                session.add(WorkCalendar(
                    date=dt,
                    day_name="Hari",
                    year=2026,
                    month=8,
                    is_working_day=is_work,
                    start_time="08:15:00" if is_work else None,
                    end_time="16:30:00" if is_work else None,
                    status=CalendarStatus.KERJA if is_work else CalendarStatus.LIBUR_NASIONAL,
                    description="Operasional" if is_work else "Libur Uji",
                ))

            # Karyawan
            emp1 = Employee(
                id="EMP001",
                nik="198501012010011001",
                nip="198501012010011001",
                name="Ahmad Fauzi",
                unit="Sekretariat",
                position="Staff Administrasi",
                status=EmployeeStatus.AKTIF,
            )
            emp2 = Employee(
                id="EMP002",
                nik="199002022015022002",
                nip="199002022015022002",
                name="Budi Santoso",
                unit="Keuangan",
                position="Bendahara",
                status=EmployeeStatus.AKTIF,
            )
            emp3 = Employee(
                id="EMP003",
                nik="199203032018031003",
                nip="199203032018031003",
                name="Citra Lestari",
                unit="Sekretariat",
                position="Staff HRD",
                status=EmployeeStatus.NON_AKTIF,
            )
            session.add_all([emp1, emp2, emp3])
            session.commit()

    # KASUS 1: Keterlambatan <= 1 jam (Rp7.500)
    def test_01_keterlambatan_kurang_sama_dengan_satu_jam(self):
        with self.SessionFactory() as session:
            daily = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 1),
                scheduled_in="08:15:00",
                scheduled_out="16:30:00",
                actual_check_in="08:45:00",  # Terlambat 30 menit
                actual_check_out="16:30:00",
                check_in_status=CheckScanStatus.LATE.value,
                check_out_status=CheckScanStatus.ON_TIME.value,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
                terlambat_menit=30,
                pulang_cepat_menit=0,
                is_working_day=True,
            )
            session.add(daily)
            session.commit()

            ded = DeductionCalculationService.calculate_daily_deduction(daily.id, session=session)
            self.assertIsNotNone(ded)
            self.assertEqual(ded.deduction_late, 7500)
            self.assertEqual(ded.deduction_early_leave, 0)
            self.assertEqual(ded.total_deduction, 7500)

    # KASUS 2: Keterlambatan > 1 jam (Rp10.000)
    def test_02_keterlambatan_lebih_dari_satu_jam(self):
        with self.SessionFactory() as session:
            daily = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 2),
                scheduled_in="08:15:00",
                scheduled_out="16:30:00",
                actual_check_in="09:30:00",  # Terlambat 75 menit
                actual_check_out="16:30:00",
                check_in_status=CheckScanStatus.LATE.value,
                check_out_status=CheckScanStatus.ON_TIME.value,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
                terlambat_menit=75,
                pulang_cepat_menit=0,
                is_working_day=True,
            )
            session.add(daily)
            session.commit()

            ded = DeductionCalculationService.calculate_daily_deduction(daily.id, session=session)
            self.assertEqual(ded.deduction_late, 10000)
            self.assertEqual(ded.total_deduction, 10000)

    # KASUS 3: Pulang Cepat (Rp10.000)
    def test_03_pulang_cepat(self):
        with self.SessionFactory() as session:
            daily = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 3),
                scheduled_in="08:15:00",
                scheduled_out="16:30:00",
                actual_check_in="08:15:00",
                actual_check_out="16:00:00",  # Pulang cepat 30 menit
                check_in_status=CheckScanStatus.ON_TIME.value,
                check_out_status=CheckScanStatus.EARLY_LEAVE.value,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
                terlambat_menit=0,
                pulang_cepat_menit=30,
                is_working_day=True,
            )
            session.add(daily)
            session.commit()

            ded = DeductionCalculationService.calculate_daily_deduction(daily.id, session=session)
            self.assertEqual(ded.deduction_early_leave, 10000)
            self.assertEqual(ded.total_deduction, 10000)

    # KASUS 4: Tidak Absen Masuk (Rp10.000)
    def test_04_tidak_absen_masuk(self):
        with self.SessionFactory() as session:
            daily = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 4),
                scheduled_in="08:15:00",
                scheduled_out="16:30:00",
                actual_check_in=None,  # Tidak scan masuk
                actual_check_out="16:30:00",
                check_in_status=CheckScanStatus.MISSING.value,
                check_out_status=CheckScanStatus.ON_TIME.value,
                attendance_status=AttendanceStatus.HANYA_ABSEN_PULANG.value,
                terlambat_menit=0,
                pulang_cepat_menit=0,
                is_working_day=True,
            )
            session.add(daily)
            session.commit()

            ded = DeductionCalculationService.calculate_daily_deduction(daily.id, session=session)
            self.assertEqual(ded.deduction_missing_check_in, 10000)
            self.assertEqual(ded.deduction_missing_check_out, 0)
            self.assertEqual(ded.total_deduction, 10000)

    # KASUS 5: Tidak Absen Pulang (Rp10.000)
    def test_05_tidak_absen_pulang(self):
        with self.SessionFactory() as session:
            daily = AttendanceDaily(
                employee_id="EMP002",
                employee_name="Budi Santoso",
                attendance_date=date(2026, 8, 1),
                scheduled_in="08:15:00",
                scheduled_out="16:30:00",
                actual_check_in="08:10:00",
                actual_check_out=None,  # Tidak scan pulang
                check_in_status=CheckScanStatus.ON_TIME.value,
                check_out_status=CheckScanStatus.MISSING.value,
                attendance_status=AttendanceStatus.HANYA_ABSEN_MASUK.value,
                terlambat_menit=0,
                pulang_cepat_menit=0,
                is_working_day=True,
            )
            session.add(daily)
            session.commit()

            ded = DeductionCalculationService.calculate_daily_deduction(daily.id, session=session)
            self.assertEqual(ded.deduction_missing_check_in, 0)
            self.assertEqual(ded.deduction_missing_check_out, 10000)
            self.assertEqual(ded.total_deduction, 10000)

    # KASUS 6: Tidak Absen Masuk dan Pulang (Maksimal Rp20.000, no double counting)
    def test_06_tidak_absen_masuk_dan_pulang_maksimal_20rb(self):
        with self.SessionFactory() as session:
            daily = AttendanceDaily(
                employee_id="EMP002",
                employee_name="Budi Santoso",
                attendance_date=date(2026, 8, 2),
                scheduled_in="08:15:00",
                scheduled_out="16:30:00",
                actual_check_in=None,
                actual_check_out=None,
                check_in_status=CheckScanStatus.MISSING.value,
                check_out_status=CheckScanStatus.MISSING.value,
                attendance_status=AttendanceStatus.TIDAK_ABSEN.value,
                terlambat_menit=0,
                pulang_cepat_menit=0,
                is_working_day=True,
            )
            session.add(daily)
            session.commit()

            ded = DeductionCalculationService.calculate_daily_deduction(daily.id, session=session)
            self.assertEqual(ded.deduction_missing_check_in, 10000)
            self.assertEqual(ded.deduction_missing_check_out, 10000)
            self.assertEqual(ded.total_deduction, 20000)
            # Pastikan tidak ada double counting menjadi 40.000
            self.assertLessEqual(ded.total_deduction, 20000)

    # KASUS 7: Tepat Waktu (Rp0)
    def test_07_hadir_tepat_waktu_tanpa_potongan(self):
        with self.SessionFactory() as session:
            daily = AttendanceDaily(
                employee_id="EMP002",
                employee_name="Budi Santoso",
                attendance_date=date(2026, 8, 3),
                scheduled_in="08:15:00",
                scheduled_out="16:30:00",
                actual_check_in="08:05:00",
                actual_check_out="16:35:00",
                check_in_status=CheckScanStatus.ON_TIME.value,
                check_out_status=CheckScanStatus.ON_TIME.value,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
                terlambat_menit=0,
                pulang_cepat_menit=0,
                is_working_day=True,
            )
            session.add(daily)
            session.commit()

            ded = DeductionCalculationService.calculate_daily_deduction(daily.id, session=session)
            self.assertEqual(ded.total_deduction, 0)
            self.assertEqual(len(ded.items), 0)

    # KASUS 8: Kombinasi Terlambat dan Pulang Cepat (Rp7.500 + Rp10.000 = Rp17.500)
    def test_08_kombinasi_terlambat_dan_pulang_cepat(self):
        with self.SessionFactory() as session:
            daily = AttendanceDaily(
                employee_id="EMP002",
                employee_name="Budi Santoso",
                attendance_date=date(2026, 8, 4),
                scheduled_in="08:15:00",
                scheduled_out="16:30:00",
                actual_check_in="08:45:00",  # Terlambat 30 menit (7.500)
                actual_check_out="16:00:00",  # Pulang cepat 30 menit (10.000)
                check_in_status=CheckScanStatus.LATE.value,
                check_out_status=CheckScanStatus.EARLY_LEAVE.value,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
                terlambat_menit=30,
                pulang_cepat_menit=30,
                is_working_day=True,
            )
            session.add(daily)
            session.commit()

            ded = DeductionCalculationService.calculate_daily_deduction(daily.id, session=session)
            self.assertEqual(ded.deduction_late, 7500)
            self.assertEqual(ded.deduction_early_leave, 10000)
            self.assertEqual(ded.total_deduction, 17500)
            self.assertEqual(len(ded.items), 2)

    # KASUS 9: Hari Libur / Akhir Pekan (Rp0)
    def test_09_hari_libur_akhir_pekan_tidak_dipotong(self):
        with self.SessionFactory() as session:
            daily = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 5),  # Tanggal 5 adalah hari libur di seed data
                scheduled_in=None,
                scheduled_out=None,
                actual_check_in=None,
                actual_check_out=None,
                check_in_status=CheckScanStatus.ON_TIME.value,
                check_out_status=CheckScanStatus.ON_TIME.value,
                attendance_status=AttendanceStatus.LIBUR.value,
                is_working_day=False,
            )
            session.add(daily)
            session.commit()

            ded = DeductionCalculationService.calculate_daily_deduction(daily.id, session=session)
            self.assertEqual(ded.total_deduction, 0)

    # KASUS 10: Karyawan Non-Aktif (Diabaikan)
    def test_10_karyawan_non_aktif_diabaikan(self):
        with self.SessionFactory() as session:
            daily = AttendanceDaily(
                employee_id="EMP003",  # Citra Lestari (NON_AKTIF)
                employee_name="Citra Lestari",
                attendance_date=date(2026, 8, 1),
                is_working_day=True,
            )
            session.add(daily)
            session.commit()

            ded = DeductionCalculationService.calculate_daily_deduction(daily.id, session=session)
            self.assertEqual(ded.total_deduction, 0)

    # KASUS 11: Toleransi Keterlambatan
    def test_11_toleransi_keterlambatan(self):
        with self.SessionFactory() as session:
            # Set toleransi terlambat = 15 menit
            setting = session.query(Setting).filter(Setting.key == "toleransi_terlambat_menit").first()
            setting.value = "15"
            session.commit()

            # Karyawan terlambat 10 menit (masih dalam toleransi 15 menit)
            daily = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 1),
                scheduled_in="08:15:00",
                scheduled_out="16:30:00",
                actual_check_in="08:25:00",
                actual_check_out="16:30:00",
                check_in_status=CheckScanStatus.LATE.value,
                check_out_status=CheckScanStatus.ON_TIME.value,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
                terlambat_menit=10,
                pulang_cepat_menit=0,
                is_working_day=True,
            )
            session.add(daily)
            session.commit()

            ded = DeductionCalculationService.calculate_daily_deduction(daily.id, session=session)
            self.assertEqual(ded.deduction_late, 0)
            self.assertEqual(ded.total_deduction, 0)

    # KASUS 12: Hitung Ulang (Force Recalculate) tanpa duplikasi
    def test_12_hitung_ulang_force_recalculate_tanpa_duplikasi(self):
        with self.SessionFactory() as session:
            daily = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 1),
                scheduled_in="08:15:00",
                scheduled_out="16:30:00",
                actual_check_in="08:45:00",
                actual_check_out="16:30:00",
                check_in_status=CheckScanStatus.LATE.value,
                check_out_status=CheckScanStatus.ON_TIME.value,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
                terlambat_menit=30,
                is_working_day=True,
            )
            session.add(daily)
            session.commit()

        # Hitung pertama
        res1 = DeductionCalculationService.calculate_period_deductions(2026, 8, force_recalculate=False)
        self.assertTrue(res1["success"])

        # Hitung ulang kedua dengan force_recalculate=True
        res2 = DeductionCalculationService.calculate_period_deductions(2026, 8, force_recalculate=True)
        self.assertTrue(res2["success"])

        # Pastikan hanya ada 1 baris AttendanceDeduction untuk record harian tersebut
        with self.SessionFactory() as session:
            count = session.query(AttendanceDeduction).filter(AttendanceDeduction.attendance_daily_id == daily.id).count()
            self.assertEqual(count, 1)

    # KASUS 13: Rekap Potongan Bulanan & Subtotal Unit
    def test_13_rekap_potongan_bulanan_dan_subtotal_unit(self):
        with self.SessionFactory() as session:
            d1 = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 1),
                terlambat_menit=30,
                is_working_day=True,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
            )
            d2 = AttendanceDaily(
                employee_id="EMP002",
                employee_name="Budi Santoso",
                attendance_date=date(2026, 8, 1),
                pulang_cepat_menit=30,
                is_working_day=True,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
            )
            session.add_all([d1, d2])
            session.commit()

        DeductionCalculationService.calculate_period_deductions(2026, 8, force_recalculate=True)
        recap = DeductionCalculationService.get_monthly_deduction_recap(2026, 8)

        self.assertEqual(len(recap["rows"]), 2)
        self.assertIn("Keuangan", recap["subtotals_by_unit"])
        self.assertIn("Sekretariat", recap["subtotals_by_unit"])
        self.assertEqual(recap["subtotals_by_unit"]["Sekretariat"]["terlambat"], 7500)
        self.assertEqual(recap["subtotals_by_unit"]["Keuangan"]["pulang_cepat"], 10000)

    # KASUS 14: Grand Total Rekapitulasi Potongan
    def test_14_rekap_grand_total_dan_karyawan_count(self):
        with self.SessionFactory() as session:
            d1 = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 1),
                terlambat_menit=30,
                is_working_day=True,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
            )
            session.add(d1)
            session.commit()

        DeductionCalculationService.calculate_period_deductions(2026, 8, force_recalculate=True)
        recap = DeductionCalculationService.get_monthly_deduction_recap(2026, 8)
        gt = recap["grand_total"]

        self.assertEqual(gt["total_potongan"], 7500)
        self.assertEqual(gt["terlambat"], 7500)
        self.assertEqual(gt["karyawan_count"], 1)

    # KASUS 15: Laporan Detail Absensi Harian & Filter
    def test_15_laporan_detail_harian_dan_filter(self):
        with self.SessionFactory() as session:
            d1 = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 1),
                scheduled_in="08:15:00",
                scheduled_out="16:30:00",
                actual_check_in="08:45:00",
                actual_check_out="16:30:00",
                check_in_status=CheckScanStatus.LATE.value,
                check_out_status=CheckScanStatus.ON_TIME.value,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
                terlambat_menit=30,
                is_working_day=True,
            )
            session.add(d1)
            session.commit()

        DeductionCalculationService.calculate_period_deductions(2026, 8, force_recalculate=True)
        rep = DeductionCalculationService.get_daily_deduction_report(2026, 8, unit="Sekretariat")

        self.assertEqual(rep["total_records"], 1)
        rec = rep["records"][0]
        self.assertEqual(rec["nama"], "Ahmad Fauzi")
        self.assertEqual(rec["potongan_terlambat"], 7500)
        self.assertEqual(rec["total_potongan_per_hari"], 7500)

    # KASUS 16: Validasi Integritas Data (Anti-negatif, konsistensi)
    def test_16_validasi_integritas_anti_negatif_dan_konsistensi(self):
        with self.SessionFactory() as session:
            d1 = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 1),
                terlambat_menit=30,
                is_working_day=True,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
            )
            session.add(d1)
            session.commit()

        DeductionCalculationService.calculate_period_deductions(2026, 8, force_recalculate=True)
        val = DeductionCalculationService.validate_deductions_integrity(2026, 8)

        self.assertTrue(val["is_valid"])
        self.assertEqual(len(val["issues"]), 0)
        self.assertEqual(val["calculated_total"], 7500)

    # KASUS 17: Layanan Export Excel & PDF
    def test_17_export_excel_dan_pdf_service(self):
        with self.SessionFactory() as session:
            d1 = AttendanceDaily(
                employee_id="EMP001",
                employee_name="Ahmad Fauzi",
                attendance_date=date(2026, 8, 1),
                terlambat_menit=30,
                is_working_day=True,
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
            )
            session.add(d1)
            session.commit()

        DeductionCalculationService.calculate_period_deductions(2026, 8, force_recalculate=True)

        # Test Export Rekap Excel
        excel_recap = ExportService.export_rekap_potongan_excel(2026, 8)
        self.assertTrue(os.path.exists(excel_recap))
        self.assertGreater(os.path.getsize(excel_recap), 1000)

        # Test Export Rekap PDF
        pdf_recap = ExportService.export_rekap_potongan_pdf(2026, 8)
        self.assertTrue(os.path.exists(pdf_recap))
        self.assertGreater(os.path.getsize(pdf_recap), 1000)

        # Test Export Detail Excel
        excel_detail = ExportService.export_detail_absensi_excel(2026, 8)
        self.assertTrue(os.path.exists(excel_detail))
        self.assertGreater(os.path.getsize(excel_detail), 1000)

        # Test Export Detail PDF
        pdf_detail = ExportService.export_detail_absensi_pdf(2026, 8)
        self.assertTrue(os.path.exists(pdf_detail))
        self.assertGreater(os.path.getsize(pdf_detail), 1000)


if __name__ == "__main__":
    unittest.main()
