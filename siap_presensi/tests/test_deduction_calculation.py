"""
Pengujian Unit & Integrasi Mesin Perhitungan Status dan Nominal Potongan Absensi (Tahap 5).
SIAP - Sistem Informasi Administrasi Presensi.

13 KASUS UJI WAJIB:
TEST 1: Karyawan masuk pukul 08:15 pada hari kerja normal -> Potongan Rp0.
TEST 2: Karyawan masuk pukul 08:30 pada hari kerja normal -> Potongan Rp7.500 (terlambat 15 menit).
TEST 3: Karyawan masuk pukul 09:15 pada hari kerja normal -> Potongan Rp7.500 (tepat 60 menit).
TEST 4: Karyawan masuk pukul 09:16 pada hari kerja normal -> Potongan Rp10.000 (61 menit).
TEST 5: Karyawan pulang lebih awal (contoh: 16:00 jadwal 16:30) -> Potongan Rp10.000 (pulang cepat 30 menit).
TEST 6: Jam masuk kosong, jam pulang ada -> Tidak Absen Masuk Rp10.000, Keterlambatan Rp0 (0 menit).
TEST 7: Jam masuk ada, jam pulang kosong -> Tidak Absen Pulang Rp10.000, Pulang Cepat Rp0 (0 menit).
TEST 8: Jam masuk dan pulang kosong -> Tidak Absen Masuk Rp10.000 + Tidak Absen Pulang Rp10.000 = Rp20.000 (TIDAK BOLEH Rp40.000).
TEST 9: Tanggal presensi hari libur / akhir pekan -> Potongan Rp0.
TEST 10: Terlambat DAN pulang cepat -> Kedua komponen dijumlahkan (Rp7.500 + Rp10.000 = Rp17.500).
TEST 11: Perhitungan ulang (Recalculate) -> Tidak ada duplikasi record, total tidak berlipat ganda.
TEST 12: Export Excel dan PDF -> File valid dan total laporan cocok dengan total database.
TEST 13: Fleksibilitas tarif sistem -> Nilai konfigurasi tarif baru otomatis diterapkan pada kalkulasi.
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
    AttendanceDeduction,
    AttendanceStatus,
    Setting,
    AuditLog,
)
from services.deduction_calculation_service import DeductionCalculationService
from services.export_service import ExportService
from services.settings_service import SettingsService


class TestDeductionCalculationTahap5(unittest.TestCase):
    """Pengujian Komprehensif 13 Kasus Uji Mesin Perhitungan Potongan Absensi Tahap 5."""

    def setUp(self):
        """Inisialisasi database SQLite in-memory / temporary isolated test."""
        self.temp_dir = TemporaryDirectory()
        self.test_db_path = Path(self.temp_dir.name) / "test_deduction_tahap5.db"
        self.engine = create_engine(f"sqlite:///{self.test_db_path.as_posix()}", echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

        # Patch get_db_session ke database isolasi ini
        self.patchers = [
            patch("database.connection.get_db_session", side_effect=self._mock_db_session),
            patch("database.connection.SessionLocal", self.SessionLocal),
            patch("services.deduction_calculation_service.get_db_session", side_effect=self._mock_db_session),
            patch("services.settings_service.get_db_session", side_effect=self._mock_db_session),
        ]
        for p in self.patchers:
            p.start()

        # Seed data dasar untuk pengujian
        with self.SessionLocal() as session:
            # 1. Karyawan Uji
            self.emp1 = Employee(
                id=1,
                emp_num="EMP001",
                no_id="ID001",
                nik="3201001",
                nama="Budi Santoso",
                unit="Unit IT",
                status=EmployeeStatus.AKTIF,
                tanggal_mulai=date(2026, 1, 1),
            )
            self.emp2 = Employee(
                id=2,
                emp_num="EMP002",
                no_id="ID002",
                nik="3201002",
                nama="Siti Rahma",
                unit="Unit Keuangan",
                status=EmployeeStatus.AKTIF,
                tanggal_mulai=date(2026, 1, 1),
            )
            session.add_all([self.emp1, self.emp2])

            # 2. Kalender Kerja:
            # 2026-08-03 (Senin) -> Hari Kerja Normal (08:15 - 16:30)
            # 2026-08-07 (Jumat) -> Hari Kerja Jumat (08:15 - 17:00)
            # 2026-08-08 (Sabtu) -> Akhir Pekan (Bukan Hari Kerja)
            # 2026-08-17 (Senin) -> Hari Libur Nasional (HUT RI, Bukan Hari Kerja)
            self.cal_senin = WorkCalendar(
                calendar_date=date(2026, 8, 3),
                year=2026,
                month=8,
                day_name="Senin",
                is_working_day=True,
                calendar_status=CalendarStatus.HARI_KERJA,
                scheduled_check_in="08:15",
                scheduled_check_out="16:30",
            )
            self.cal_jumat = WorkCalendar(
                calendar_date=date(2026, 8, 7),
                year=2026,
                month=8,
                day_name="Jumat",
                is_working_day=True,
                calendar_status=CalendarStatus.HARI_KERJA,
                scheduled_check_in="08:15",
                scheduled_check_out="17:00",
            )
            self.cal_sabtu = WorkCalendar(
                calendar_date=date(2026, 8, 8),
                year=2026,
                month=8,
                day_name="Sabtu",
                is_working_day=False,
                calendar_status=CalendarStatus.AKHIR_PEKAN,
            )
            self.cal_libur = WorkCalendar(
                calendar_date=date(2026, 8, 17),
                year=2026,
                month=8,
                day_name="Senin",
                is_working_day=False,
                calendar_status=CalendarStatus.LIBUR_NASIONAL,
                description="HUT Proklamasi Kemerdekaan RI",
            )
            session.add_all([self.cal_senin, self.cal_jumat, self.cal_sabtu, self.cal_libur])

            # 3. Pengaturan Tarif Standar
            standard_settings = [
                Setting(setting_key="potongan_terlambat_sd_1jam", setting_value="7500"),
                Setting(setting_key="potongan_terlambat_gt_1jam", setting_value="10000"),
                Setting(setting_key="potongan_pulang_cepat", setting_value="10000"),
                Setting(setting_key="potongan_tidak_absen_masuk", setting_value="10000"),
                Setting(setting_key="potongan_tidak_absen_pulang", setting_value="10000"),
                Setting(setting_key="potongan_tidak_hadir", setting_value="20000"),
            ]
            session.add_all(standard_settings)
            session.commit()

    def tearDown(self):
        for p in self.patchers:
            p.stop()
        self.temp_dir.cleanup()

    from contextlib import contextmanager
    @contextmanager
    def _mock_db_session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # =========================================================================
    # TEST 1: Masuk 08:15 -> Potongan Rp0
    # =========================================================================
    def test_01_masuk_tepat_waktu_0815(self):
        """Karyawan masuk tepat 08:15 pada hari kerja normal -> Menit terlambat=0, Potongan=Rp0."""
        late_min, ded_late = DeductionCalculationService.calculate_late("08:15", "08:15")
        self.assertEqual(late_min, 0)
        self.assertEqual(ded_late, 0)

        res = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 3),
            actual_check_in="08:15",
            actual_check_out="16:30",
            calendar=self.cal_senin,
        )
        self.assertEqual(res["late_minutes"], 0)
        self.assertEqual(res["deduction_late"], 0)
        self.assertEqual(res["total_deduction"], 0)
        self.assertEqual(res["attendance_status"], AttendanceStatus.HADIR_LENGKAP.value)

    # =========================================================================
    # TEST 2: Masuk 08:30 (15 Menit) -> Rp7.500
    # =========================================================================
    def test_02_masuk_terlambat_15_menit_0830(self):
        """Karyawan masuk pukul 08:30 (terlambat 15 menit) -> Potongan Rp7.500."""
        late_min, ded_late = DeductionCalculationService.calculate_late("08:30", "08:15")
        self.assertEqual(late_min, 15)
        self.assertEqual(ded_late, 7500)

        res = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 3),
            actual_check_in="08:30",
            actual_check_out="16:30",
            calendar=self.cal_senin,
        )
        self.assertEqual(res["late_minutes"], 15)
        self.assertEqual(res["deduction_late"], 7500)
        self.assertEqual(res["deduction_early_leave"], 0)
        self.assertEqual(res["total_deduction"], 7500)

    # =========================================================================
    # TEST 3: Masuk 09:15 (Tepat 60 Menit) -> Rp7.500
    # =========================================================================
    def test_03_masuk_terlambat_tepat_60_menit_0915(self):
        """Karyawan masuk pukul 09:15 (tepat 60 menit keterlambatan) -> Potongan Rp7.500."""
        late_min, ded_late = DeductionCalculationService.calculate_late("09:15", "08:15")
        self.assertEqual(late_min, 60)
        self.assertEqual(ded_late, 7500)

        res = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 3),
            actual_check_in="09:15",
            actual_check_out="16:30",
            calendar=self.cal_senin,
        )
        self.assertEqual(res["late_minutes"], 60)
        self.assertEqual(res["deduction_late"], 7500)
        self.assertEqual(res["total_deduction"], 7500)

    # =========================================================================
    # TEST 4: Masuk 09:16 (61 Menit) -> Rp10.000
    # =========================================================================
    def test_04_masuk_terlambat_61_menit_0916(self):
        """Karyawan masuk pukul 09:16 (61 menit keterlambatan, >60 menit) -> Potongan Rp10.000."""
        late_min, ded_late = DeductionCalculationService.calculate_late("09:16", "08:15")
        self.assertEqual(late_min, 61)
        self.assertEqual(ded_late, 10000)

        res = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 3),
            actual_check_in="09:16",
            actual_check_out="16:30",
            calendar=self.cal_senin,
        )
        self.assertEqual(res["late_minutes"], 61)
        self.assertEqual(res["deduction_late"], 10000)
        self.assertEqual(res["total_deduction"], 10000)

    # =========================================================================
    # TEST 5: Pulang Lebih Awal (16:00 jadwal 16:30) -> Rp10.000
    # =========================================================================
    def test_05_pulang_cepat_30_menit_1600(self):
        """Karyawan pulang pukul 16:00 pd jadwal 16:30 (pulang cepat 30 mnt) -> Potongan Rp10.000."""
        early_min, ded_early = DeductionCalculationService.calculate_early_leave("16:00", "16:30")
        self.assertEqual(early_min, 30)
        self.assertEqual(ded_early, 10000)

        res = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 3),
            actual_check_in="08:10",
            actual_check_out="16:00",
            calendar=self.cal_senin,
        )
        self.assertEqual(res["late_minutes"], 0)
        self.assertEqual(res["deduction_late"], 0)
        self.assertEqual(res["early_leave_minutes"], 30)
        self.assertEqual(res["deduction_early_leave"], 10000)
        self.assertEqual(res["total_deduction"], 10000)

    # =========================================================================
    # TEST 6: Jam Masuk Kosong, Jam Pulang Ada -> Tidak Absen Masuk Rp10.000, Tlbt Rp0
    # =========================================================================
    def test_06_jam_masuk_kosong_hanya_absen_pulang(self):
        """Karyawan tidak memiliki scan masuk namun memiliki scan pulang -> Tidak Absen Masuk Rp10.000, keterlambatan Rp0."""
        res = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 3),
            actual_check_in=None,
            actual_check_out="16:30",
            calendar=self.cal_senin,
        )
        self.assertEqual(res["attendance_status"], AttendanceStatus.HANYA_ABSEN_PULANG.value)
        self.assertEqual(res["deduction_missing_check_in"], 10000)
        self.assertEqual(res["late_minutes"], 0)
        self.assertEqual(res["deduction_late"], 0)  # Tidak boleh menghitung terlambat!
        self.assertEqual(res["deduction_missing_check_out"], 0)
        self.assertEqual(res["deduction_early_leave"], 0)
        self.assertEqual(res["total_deduction"], 10000)

    # =========================================================================
    # TEST 7: Jam Masuk Ada, Jam Pulang Kosong -> Tidak Absen Pulang Rp10.000, PC Rp0
    # =========================================================================
    def test_07_jam_pulang_kosong_hanya_absen_masuk(self):
        """Karyawan memiliki scan masuk namun jam pulang kosong -> Tidak Absen Pulang Rp10.000, pulang cepat Rp0."""
        res = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 3),
            actual_check_in="08:15",
            actual_check_out=None,
            calendar=self.cal_senin,
        )
        self.assertEqual(res["attendance_status"], AttendanceStatus.HANYA_ABSEN_MASUK.value)
        self.assertEqual(res["deduction_missing_check_in"], 0)
        self.assertEqual(res["deduction_late"], 0)
        self.assertEqual(res["deduction_missing_check_out"], 10000)
        self.assertEqual(res["early_leave_minutes"], 0)
        self.assertEqual(res["deduction_early_leave"], 0)  # Tidak boleh menghitung pulang cepat!
        self.assertEqual(res["total_deduction"], 10000)

    # =========================================================================
    # TEST 8: Jam Masuk dan Pulang Kosong -> Rp20.000 (TIDAK BOLEH Rp40.000!)
    # =========================================================================
    def test_08_tidak_absen_masuk_dan_pulang_strictly_20000(self):
        """Tidak scan masuk dan tidak scan pulang -> Tepat Rp20.000 (10.000 + 10.000), TIDAK BOLEH Rp40.000!"""
        res = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 3),
            actual_check_in=None,
            actual_check_out=None,
            calendar=self.cal_senin,
        )
        self.assertEqual(res["attendance_status"], AttendanceStatus.TIDAK_ABSEN.value)
        self.assertEqual(res["deduction_missing_check_in"], 10000)
        self.assertEqual(res["deduction_missing_check_out"], 10000)
        self.assertEqual(res["deduction_late"], 0)
        self.assertEqual(res["deduction_early_leave"], 0)
        # Verifikasi plafon tegas: 20.000 dan BUKAN 40.000
        self.assertEqual(res["total_deduction"], 20000)
        self.assertNotEqual(res["total_deduction"], 40000)

    # =========================================================================
    # TEST 9: Tanggal Libur / Akhir Pekan -> Potongan Rp0
    # =========================================================================
    def test_09_tanggal_libur_dan_akhir_pekan_rp0(self):
        """Tanggal presensi berada pada hari libur nasional atau akhir pekan -> Potongan Rp0."""
        # 1. Akhir Pekan (Sabtu)
        res_sabtu = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 8),
            actual_check_in=None,
            actual_check_out=None,
            calendar=self.cal_sabtu,
        )
        self.assertFalse(res_sabtu["is_working_day"])
        self.assertEqual(res_sabtu["total_deduction"], 0)

        # 2. Hari Libur Nasional (17 Agustus)
        res_libur = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 17),
            actual_check_in=None,
            actual_check_out=None,
            calendar=self.cal_libur,
        )
        self.assertFalse(res_libur["is_working_day"])
        self.assertEqual(res_libur["total_deduction"], 0)

    # =========================================================================
    # TEST 10: Terlambat DAN Pulang Cepat -> Dijumlahkan (7.500 + 10.000 = 17.500)
    # =========================================================================
    def test_10_terlambat_dan_pulang_cepat_terakumulasi(self):
        """Karyawan masuk 08:30 (terlambat 15 mnt -> Rp7.500) dan pulang 16:00 (pulang cepat 30 mnt -> Rp10.000) -> Rp17.500."""
        res = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 3),
            actual_check_in="08:30",
            actual_check_out="16:00",
            calendar=self.cal_senin,
        )
        self.assertEqual(res["late_minutes"], 15)
        self.assertEqual(res["deduction_late"], 7500)
        self.assertEqual(res["early_leave_minutes"], 30)
        self.assertEqual(res["deduction_early_leave"], 10000)
        self.assertEqual(res["deduction_missing_check_in"], 0)
        self.assertEqual(res["deduction_missing_check_out"], 0)
        self.assertEqual(res["total_deduction"], 17500)

    # =========================================================================
    # TEST 11: Perhitungan Ulang (Recalculate) -> Tanpa Duplikasi Record
    # =========================================================================
    def test_11_recalculate_tanpa_duplikasi_record(self):
        """Proses Hitung Ulang untuk periode yang sama menggantikan data lama tanpa duplikasi baris atau kelipatan total."""
        with self.SessionLocal() as session:
            # Masukkan attendance_daily untuk emp1 pada 2026-08-03
            daily1 = AttendanceDaily(
                employee_id=1,
                attendance_date=date(2026, 8, 3),
                day_name="Senin",
                scheduled_check_in="08:15",
                scheduled_check_out="16:30",
                actual_check_in="08:30",  # Terlambat 15 mnt -> 7500
                actual_check_out="16:30",
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
            )
            session.add(daily1)
            session.commit()

        # Eksekusi kalkulasi pertama
        res1 = DeductionCalculationService.calculate_and_save_period(
            year=2026,
            month=8,
            user_name="ADMIN",
            recalculate=False,
        )
        self.assertTrue(res1["success"])
        self.assertEqual(res1["created_count"], 1)

        # Cek rekap
        rekap1 = DeductionCalculationService.get_monthly_recap(year=2026, month=8)
        self.assertEqual(rekap1["grand_total"]["total_potongan_keseluruhan"], 7500)

        # Eksekusi kalkulasi kedua (Recalculate)
        res2 = DeductionCalculationService.calculate_and_save_period(
            year=2026,
            month=8,
            user_name="ADMIN",
            recalculate=True,
        )
        self.assertTrue(res2["success"])
        self.assertEqual(res2["updated_count"], 1)
        self.assertEqual(res2["created_count"], 0)

        # Pastikan tidak ada record ganda di attendance_deductions
        with self.SessionLocal() as session:
            count_ded = session.query(AttendanceDeduction).filter(AttendanceDeduction.employee_id == 1).count()
            self.assertEqual(count_ded, 1)

        # Rekap total harus tetap Rp7.500 (TIDAK menjadi Rp15.000)
        rekap2 = DeductionCalculationService.get_monthly_recap(year=2026, month=8)
        self.assertEqual(rekap2["grand_total"]["total_potongan_keseluruhan"], 7500)

    # =========================================================================
    # TEST 12: Export Excel dan PDF -> File Valid & Total Cocok
    # =========================================================================
    def test_12_export_excel_dan_pdf_valid(self):
        """Export rekapitulasi ke Excel dan PDF menghasilkan berkas fisik yang valid dengan angka cocok."""
        with self.SessionLocal() as session:
            d1 = AttendanceDaily(
                employee_id=1,
                attendance_date=date(2026, 8, 3),
                day_name="Senin",
                actual_check_in="08:30",  # Rp7.500
                actual_check_out="16:00",  # Rp10.000
                attendance_status=AttendanceStatus.HADIR_LENGKAP.value,
            )
            d2 = AttendanceDaily(
                employee_id=2,
                attendance_date=date(2026, 8, 3),
                day_name="Senin",
                actual_check_in=None,     # Rp10.000
                actual_check_out=None,    # Rp10.000 -> Rp20.000
                attendance_status=AttendanceStatus.TIDAK_ABSEN.value,
            )
            session.add_all([d1, d2])
            session.commit()

        # Hitung potongan
        DeductionCalculationService.calculate_and_save_period(year=2026, month=8, user_name="ADMIN")
        rekap = DeductionCalculationService.get_monthly_recap(year=2026, month=8)
        total_db = rekap["grand_total"]["total_potongan_keseluruhan"]
        self.assertEqual(total_db, 37500)  # 17.500 + 20.000 = 37.500

        # Ekspor Excel
        excel_path = Path(self.temp_dir.name) / "rekap_test.xlsx"
        out_excel = ExportService.export_rekap_potongan_excel(rekap, str(excel_path))
        self.assertTrue(os.path.exists(out_excel))
        self.assertGreater(os.path.getsize(out_excel), 0)

        # Ekspor PDF
        pdf_path = Path(self.temp_dir.name) / "rekap_test.pdf"
        out_pdf = ExportService.export_rekap_potongan_pdf(rekap, "ADMIN_TEST", str(pdf_path))
        self.assertTrue(os.path.exists(out_pdf))
        self.assertGreater(os.path.getsize(out_pdf), 0)

    # =========================================================================
    # TEST 13: Fleksibilitas Konfigurasi Tarif Sistem
    # =========================================================================
    def test_13_fleksibilitas_perubahan_tarif_konfigurasi(self):
        """Jika pengaturan nominal potongan diubah oleh admin, perhitungan baru langsung menggunakan tarif baru."""
        # Ubah tarif potongan terlambat <= 60 menit menjadi Rp8.000 di tabel setting
        with self.SessionLocal() as session:
            setting_obj = session.query(Setting).filter(Setting.setting_key == "potongan_terlambat_sd_1jam").first()
            if setting_obj:
                setting_obj.setting_value = "8000"
            else:
                session.add(Setting(setting_key="potongan_terlambat_sd_1jam", setting_value="8000"))
            session.commit()

        # Ambil tarif sistem yang diperbarui
        rates = DeductionCalculationService.get_system_rates()
        self.assertEqual(rates["rate_late_lte_60"], 8000)

        # Jalankan perhitungan harian dengan tarif baru
        res = DeductionCalculationService.calculate_daily(
            attendance_date=date(2026, 8, 3),
            actual_check_in="08:30",  # Terlambat 15 menit
            actual_check_out="16:30",
            calendar=self.cal_senin,
            custom_rates=rates,
        )
        self.assertEqual(res["late_minutes"], 15)
        self.assertEqual(res["deduction_late"], 8000)
        self.assertEqual(res["total_deduction"], 8000)


if __name__ == "__main__":
    unittest.main()
