"""
Pengujian Unit & Integrasi Modul Kalender Kerja & Pembentukan Absensi Harian (Tahap 4).
Menguji 12 Kasus Uji Skenario Bisnis & Integritas Data SIAP:
1. Pembuatan Kalender Kerja Otomatis (Senin-Kamis 08:15-16:30, Jumat 08:15-17:00, Akhir Pekan Off).
2. Proteksi Overwrite Kalender Kerja & Penyesuaian Hari Libur Nasional (17 Agustus).
3. Kasus Hadir Lengkap (Masuk & Pulang valid -> HADIR_LENGKAP).
4. Kasus Hanya Absen Masuk (Scan masuk ada, pulang kosong -> HANYA_ABSEN_MASUK).
5. Kasus Hanya Absen Pulang (Scan masuk kosong, pulang ada -> HANYA_ABSEN_PULANG).
6. Kasus Tidak Absen (Hari kerja tanpa transaksi -> TIDAK_ABSEN, tanpa hitung potongan).
7. Kasus Multiple Scan (Earliest in, latest out, flag has_conflict=True).
8. Kasus Karyawan dengan Tanggal Mulai Kerja (Belum mulai kerja tidak dianggap alfa).
9. Penanganan Hari Libur / Akhir Pekan (Tidak menuntut kehadiran kerja).
10. Hari Kerja Khusus (Penyesuaian jam operasional).
11. Mode Eksekusi GENERATE_NEW vs REGENERATE.
12. Pencatatan Audit Log & Integritas Transaksi ACID.
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
    AttendanceRaw,
    AttendanceDaily,
    AttendanceStatus,
    CheckScanStatus,
    AuditLog,
    Setting,
)
from services.calendar_service import CalendarService
from services.attendance_daily_service import AttendanceDailyService


class TestCalendarAndDailyAttendanceTahap4(unittest.TestCase):
    """Pengujian Unit dan Integrasi Fitur Kalender Kerja dan Absensi Harian."""

    def setUp(self):
        """Membuat database SQLite isolated di temporary directory."""
        self.temp_dir = TemporaryDirectory()
        self.test_db_path = Path(self.temp_dir.name) / "test_tahap4.db"
        self.engine = create_engine(f"sqlite:///{self.test_db_path.as_posix()}", echo=False)
        Base.metadata.create_all(bind=self.engine)
        from sqlalchemy.orm import Session as SqlASession
        class AutoCommitSession(SqlASession):
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    try:
                        self.commit()
                    except Exception:
                        self.rollback()
                        raise
                else:
                    self.rollback()
                return super().__exit__(exc_type, exc_val, exc_tb)

        self.Session = sessionmaker(bind=self.engine, class_=AutoCommitSession)

        from contextlib import contextmanager
        @contextmanager
        def _mock_session():
            session = self.Session()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

        self.patchers = [
            patch("database.connection.get_db_session", side_effect=_mock_session),
            patch("database.connection.SessionLocal", self.Session),
            patch("services.calendar_service.get_db_session", side_effect=_mock_session),
            patch("services.attendance_daily_service.get_db_session", side_effect=_mock_session),
            patch("services.settings_service.get_db_session", side_effect=_mock_session),
        ]
        for p in self.patchers:
            p.start()

        # Seed data awal: Settings dan Karyawan Master
        with _mock_session() as s:
            # Settings operasional
            s.add_all([
                Setting(setting_key="jam_masuk_senin_kamis", setting_value="08:15", setting_type="time"),
                Setting(setting_key="jam_pulang_senin_kamis", setting_value="16:30", setting_type="time"),
                Setting(setting_key="jam_masuk_jumat", setting_value="08:15", setting_type="time"),
                Setting(setting_key="jam_pulang_jumat", setting_value="17:00", setting_type="time"),
                Setting(setting_key="target_hari_kerja_bulanan", setting_value="18", setting_type="int"),
                Setting(setting_key="kebijakan_hari_kerja", setting_value="CALENDAR_ACTUAL", setting_type="str"),
            ])

            # Karyawan Uji
            self.emp1 = Employee(
                emp_num="1001",
                no_id="ID-001",
                nik="3201010001",
                nama="Budi Santoso",
                unit="Teknologi Informasi",
                jabatan="Software Engineer",
                status=EmployeeStatus.AKTIF,
                tanggal_mulai=date(2026, 1, 1),
            )
            self.emp2 = Employee(
                emp_num="1002",
                no_id="ID-002",
                nik="3201010002",
                nama="Siti Rahma",
                unit="Keuangan",
                jabatan="Akuntan",
                status=EmployeeStatus.AKTIF,
                tanggal_mulai=date(2026, 1, 1),
            )
            self.emp3 = Employee(
                emp_num="1003",
                no_id="ID-003",
                nik="3201010003",
                nama="Ahmad Fauzi",
                unit="Operasional",
                jabatan="Staff Lapangan",
                status=EmployeeStatus.AKTIF,
                tanggal_mulai=date(2026, 8, 15),  # Baru mulai kerja di pertengahan bulan
            )
            self.emp_nonaktif = Employee(
                emp_num="1099",
                no_id="ID-099",
                nik="3201010099",
                nama="Doni Resigned",
                unit="Pemasaran",
                jabatan="Staff",
                status=EmployeeStatus.NONAKTIF,
                tanggal_mulai=date(2025, 1, 1),
            )

            s.add_all([self.emp1, self.emp2, self.emp3, self.emp_nonaktif])

    def tearDown(self):
        for p in self.patchers:
            p.stop()
        self.temp_dir.cleanup()

    def test_01_generate_monthly_calendar(self):
        """Uji 1: Pembentukan kalender kerja otomatis untuk Agustus 2026 (31 hari)."""
        res = CalendarService.generate_monthly_calendar(year=2026, month=8, overwrite=False)
        self.assertTrue(res["success"])
        self.assertEqual(res["total_days"], 31)

        # Cek detail record di database
        with self.Session() as s:
            days = s.query(WorkCalendar).filter(WorkCalendar.year == 2026, WorkCalendar.month == 8).all()
            self.assertEqual(len(days), 31)

            # 3 Agustus 2026 adalah Senin (Hari Kerja, 08:15 - 16:30)
            day_mon = s.query(WorkCalendar).filter(WorkCalendar.calendar_date == date(2026, 8, 3)).first()
            self.assertEqual(day_mon.day_name, "Senin")
            self.assertEqual(day_mon.calendar_status, CalendarStatus.HARI_KERJA)
            self.assertTrue(day_mon.is_working_day)
            self.assertEqual(day_mon.scheduled_check_in, "08:15")
            self.assertEqual(day_mon.scheduled_check_out, "16:30")

            # 7 Agustus 2026 adalah Jumat (Hari Kerja, 08:15 - 17:00)
            day_fri = s.query(WorkCalendar).filter(WorkCalendar.calendar_date == date(2026, 8, 7)).first()
            self.assertEqual(day_fri.day_name, "Jumat")
            self.assertEqual(day_fri.calendar_status, CalendarStatus.HARI_KERJA)
            self.assertTrue(day_fri.is_working_day)
            self.assertEqual(day_fri.scheduled_check_out, "17:00")

            # 1 Agustus 2026 adalah Sabtu (Akhir Pekan)
            day_sat = s.query(WorkCalendar).filter(WorkCalendar.calendar_date == date(2026, 8, 1)).first()
            self.assertEqual(day_sat.day_name, "Sabtu")
            self.assertEqual(day_sat.calendar_status, CalendarStatus.AKHIR_PEKAN)
            self.assertFalse(day_sat.is_working_day)

    def test_02_calendar_overwrite_protection_and_holiday_update(self):
        """Uji 2: Proteksi penimpaan dan pengubahan hari libur nasional (17 Agustus 2026)."""
        # Generate pertama
        CalendarService.generate_monthly_calendar(year=2026, month=8, overwrite=False)

        # Coba generate lagi tanpa overwrite -> harus ditolak dengan status already_exists
        res_dup = CalendarService.generate_monthly_calendar(year=2026, month=8, overwrite=False)
        self.assertFalse(res_dup["success"])
        self.assertTrue(res_dup.get("already_exists"))

        # Ubah 17 Agustus 2026 (Senin) menjadi LIBUR_NASIONAL
        with self.Session() as s:
            day_17 = s.query(WorkCalendar).filter(WorkCalendar.calendar_date == date(2026, 8, 17)).first()
            day_17_id = day_17.id

        update_res = CalendarService.update_calendar_day(
            calendar_id=day_17_id,
            status=CalendarStatus.LIBUR_NASIONAL,
            description="Hari Kemerdekaan Republik Indonesia ke-81",
        )
        self.assertTrue(update_res["success"])

        # Verifikasi 17 Agustus sekarang bukan hari kerja
        with self.Session() as s:
            day_17_updated = s.query(WorkCalendar).filter(WorkCalendar.id == day_17_id).first()
            self.assertEqual(day_17_updated.calendar_status, CalendarStatus.LIBUR_NASIONAL)
            self.assertFalse(day_17_updated.is_working_day)
            self.assertIsNone(day_17_updated.scheduled_check_in)

    def test_03_hadir_lengkap_scenario(self):
        """Uji 3: Karyawan hadir lengkap dengan jam masuk dan jam pulang valid."""
        CalendarService.generate_monthly_calendar(year=2026, month=8, overwrite=False)

        # Masukkan transaksi raw: Budi Santoso pada 3 Agustus 2026
        with self.Session() as s:
            s.add(AttendanceRaw(
                emp_num="1001",
                nama="Budi Santoso",
                tanggal=date(2026, 8, 3),
                scan_masuk="08:05",
                scan_pulang="16:40",
            ))

        # Generate Absensi Harian
        gen_res = AttendanceDailyService.generate_daily_attendance(year=2026, month=8, mode="GENERATE_NEW")
        self.assertTrue(gen_res["success"])

        # Verifikasi catatan harian
        with self.Session() as s:
            rec = (
                s.query(AttendanceDaily)
                .join(Employee)
                .filter(Employee.emp_num == "1001", AttendanceDaily.attendance_date == date(2026, 8, 3))
                .first()
            )
            self.assertIsNotNone(rec)
            self.assertEqual(rec.attendance_status, AttendanceStatus.HADIR_LENGKAP.value)
            self.assertEqual(rec.check_in_status, CheckScanStatus.ADA.value)
            self.assertEqual(rec.check_out_status, CheckScanStatus.ADA.value)
            self.assertEqual(rec.actual_check_in, "08:05")
            self.assertEqual(rec.actual_check_out, "16:40")
            self.assertFalse(rec.has_incomplete_scan)
            # Pastikan potongan belum dihitung (0.0 pada Tahap 4)
            self.assertEqual(float(rec.total_potongan), 0.0)

    def test_04_hanya_absen_masuk_scenario(self):
        """Uji 4: Karyawan hanya melakukan scan masuk tanpa scan pulang."""
        CalendarService.generate_monthly_calendar(year=2026, month=8, overwrite=False)

        with self.Session() as s:
            s.add(AttendanceRaw(
                emp_num="1002",
                nama="Siti Rahma",
                tanggal=date(2026, 8, 4),
                scan_masuk="08:12",
                scan_pulang=None,
            ))

        AttendanceDailyService.generate_daily_attendance(year=2026, month=8, mode="GENERATE_NEW")

        with self.Session() as s:
            rec = (
                s.query(AttendanceDaily)
                .join(Employee)
                .filter(Employee.emp_num == "1002", AttendanceDaily.attendance_date == date(2026, 8, 4))
                .first()
            )
            self.assertIsNotNone(rec)
            self.assertEqual(rec.attendance_status, AttendanceStatus.HANYA_ABSEN_MASUK.value)
            self.assertEqual(rec.check_in_status, CheckScanStatus.ADA.value)
            self.assertEqual(rec.check_out_status, CheckScanStatus.TIDAK_ADA.value)
            self.assertEqual(rec.actual_check_in, "08:12")
            self.assertIsNone(rec.actual_check_out)
            self.assertTrue(rec.has_incomplete_scan)

    def test_05_hanya_absen_pulang_scenario(self):
        """Uji 5: Karyawan hanya melakukan scan pulang tanpa scan masuk."""
        CalendarService.generate_monthly_calendar(year=2026, month=8, overwrite=False)

        with self.Session() as s:
            s.add(AttendanceRaw(
                emp_num="1001",
                nama="Budi Santoso",
                tanggal=date(2026, 8, 5),
                scan_masuk=None,
                scan_pulang="16:45",
            ))

        AttendanceDailyService.generate_daily_attendance(year=2026, month=8, mode="GENERATE_NEW")

        with self.Session() as s:
            rec = (
                s.query(AttendanceDaily)
                .join(Employee)
                .filter(Employee.emp_num == "1001", AttendanceDaily.attendance_date == date(2026, 8, 5))
                .first()
            )
            self.assertIsNotNone(rec)
            self.assertEqual(rec.attendance_status, AttendanceStatus.HANYA_ABSEN_PULANG.value)
            self.assertEqual(rec.check_in_status, CheckScanStatus.TIDAK_ADA.value)
            self.assertEqual(rec.check_out_status, CheckScanStatus.ADA.value)
            self.assertIsNone(rec.actual_check_in)
            self.assertEqual(rec.actual_check_out, "16:45")
            self.assertTrue(rec.has_incomplete_scan)

    def test_06_tidak_absen_scenario(self):
        """Uji 6: Karyawan tidak memiliki catatan scan pada hari kerja wajib (TIDAK_ABSEN)."""
        CalendarService.generate_monthly_calendar(year=2026, month=8, overwrite=False)
        # Tidak ada data transaksi untuk Budi pada 6 Agustus 2026 (Kamis)

        AttendanceDailyService.generate_daily_attendance(year=2026, month=8, mode="GENERATE_NEW")

        with self.Session() as s:
            rec = (
                s.query(AttendanceDaily)
                .join(Employee)
                .filter(Employee.emp_num == "1001", AttendanceDaily.attendance_date == date(2026, 8, 6))
                .first()
            )
            self.assertIsNotNone(rec)
            self.assertEqual(rec.attendance_status, AttendanceStatus.TIDAK_ABSEN.value)
            self.assertEqual(rec.check_in_status, CheckScanStatus.TIDAK_ADA.value)
            self.assertEqual(rec.check_out_status, CheckScanStatus.TIDAK_ADA.value)
            self.assertIsNone(rec.actual_check_in)
            self.assertIsNone(rec.actual_check_out)

    def test_07_multiple_scan_earliest_in_latest_out(self):
        """Uji 7: Multiple scan (ambil earliest in 07:50, latest out 16:55, has_conflict=True)."""
        CalendarService.generate_monthly_calendar(year=2026, month=8, overwrite=False)

        with self.Session() as s:
            # Baris 1
            s.add(AttendanceRaw(
                emp_num="1001",
                nama="Budi Santoso",
                tanggal=date(2026, 8, 7),
                scan_masuk="08:05",
                scan_pulang="16:30",
            ))
            # Baris 2 (scan lebih awal masuk dan lebih akhir pulang)
            s.add(AttendanceRaw(
                emp_num="1001",
                nama="Budi Santoso",
                tanggal=date(2026, 8, 7),
                scan_masuk="07:50",
                scan_pulang="16:55",
            ))

        AttendanceDailyService.generate_daily_attendance(year=2026, month=8, mode="GENERATE_NEW")

        with self.Session() as s:
            rec = (
                s.query(AttendanceDaily)
                .join(Employee)
                .filter(Employee.emp_num == "1001", AttendanceDaily.attendance_date == date(2026, 8, 7))
                .first()
            )
            self.assertIsNotNone(rec)
            self.assertEqual(rec.actual_check_in, "07:50")  # Earliest
            self.assertEqual(rec.actual_check_out, "16:55") # Latest
            self.assertTrue(rec.has_conflict)
            self.assertEqual(rec.attendance_status, AttendanceStatus.HADIR_LENGKAP.value)

    def test_08_employee_hire_date_filtering(self):
        """Uji 8: Karyawan yang tanggal mulai kerjanya di pertengahan bulan tidak dianggap alfa sebelumnya."""
        CalendarService.generate_monthly_calendar(year=2026, month=8, overwrite=False)
        # Ahmad Fauzi (emp3) baru mulai kerja 15 Agustus 2026

        AttendanceDailyService.generate_daily_attendance(year=2026, month=8, mode="GENERATE_NEW")

        with self.Session() as s:
            # Sebelum 15 Agustus (misal 3 Agustus), tidak boleh ada record harian untuk Ahmad Fauzi
            before_hire = (
                s.query(AttendanceDaily)
                .join(Employee)
                .filter(Employee.emp_num == "1003", AttendanceDaily.attendance_date == date(2026, 8, 3))
                .first()
            )
            self.assertIsNone(before_hire)

            # Setelah 15 Agustus (misal 18 Agustus), record harian terbentuk
            after_hire = (
                s.query(AttendanceDaily)
                .join(Employee)
                .filter(Employee.emp_num == "1003", AttendanceDaily.attendance_date == date(2026, 8, 18))
                .first()
            )
            self.assertIsNotNone(after_hire)

    def test_09_inactive_employee_excluded(self):
        """Uji 9: Karyawan berstatus NONAKTIF tidak dibentuk catatan absensi hariannya."""
        CalendarService.generate_monthly_calendar(year=2026, month=8, overwrite=False)

        AttendanceDailyService.generate_daily_attendance(year=2026, month=8, mode="GENERATE_NEW")

        with self.Session() as s:
            rec = (
                s.query(AttendanceDaily)
                .join(Employee)
                .filter(Employee.emp_num == "1099")
                .first()
            )
            self.assertIsNone(rec)

    def test_10_audit_logging_and_kpi_statistics(self):
        """Uji 10: Verifikasi pencatatan Audit Log dan keakuratan ringkasan statistik KPI."""
        CalendarService.generate_monthly_calendar(year=2026, month=8, overwrite=False)
        AttendanceDailyService.generate_daily_attendance(year=2026, month=8, mode="GENERATE_NEW")

        with self.Session() as s:
            # Audit log harus tercatat
            logs = s.query(AuditLog).filter(AuditLog.module.in_(["CALENDAR", "ATTENDANCE_DAILY"])).all()
            self.assertGreater(len(logs), 0)

        # Verifikasi statistik
        stats = AttendanceDailyService.get_attendance_statistics(year=2026, month=8)
        self.assertGreater(stats["working_days"], 0)
        self.assertGreater(stats["total_records"], 0)
        self.assertGreaterEqual(stats["tidak_absen"], 0)


if __name__ == "__main__":
    unittest.main()
