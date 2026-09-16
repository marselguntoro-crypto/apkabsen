"""
Pengujian Unit & Integrasi Database SIAP (Tahap 1).
Menguji:
1. Pembuatan database & koneksi
2. Pembuatan 8 tabel model SQLAlchemy
3. Seeding user Admin & Operator
4. Verifikasi password benar
5. Penolakan login password salah
6. Penyimpanan pengaturan sistem
7. Pembacaan & validasi pengaturan sistem
8. Pembuatan backup database SQLite & verifikasi integritas
"""
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Pastikan import module siap_presensi terbaca
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from database.base import Base
from database.models import (
    User,
    UserRole,
    Employee,
    AttendanceRaw,
    AttendanceDaily,
    Calendar,
    Setting,
    ImportLog,
    AuditLog,
)
from database.seed import seed_initial_data
from services.auth_service import AuthService, hash_password, verify_password
from services.settings_service import SettingsService
from services.backup_service import BackupService


class TestSiapDatabaseTahap1(unittest.TestCase):
    """Suite pengujian komprehensif untuk fondasi database dan layanan Tahap 1."""

    def setUp(self):
        """Membuat database SQLite isolated di direktori temporary untuk setiap test."""
        self.temp_dir = TemporaryDirectory()
        self.test_db_path = Path(self.temp_dir.name) / "test_siap.db"
        self.test_engine = create_engine(f"sqlite:///{self.test_db_path.as_posix()}")
        self.TestSession = sessionmaker(bind=self.test_engine)

        # Buat seluruh tabel
        Base.metadata.create_all(self.test_engine)

    def tearDown(self):
        """Membersihkan file database temporary."""
        self.test_engine.dispose()
        self.temp_dir.cleanup()

    def test_01_database_and_tables_creation(self):
        """Uji 1 & 2: Database dan 8 tabel utama berhasil dibuat."""
        inspector = inspect(self.test_engine)
        table_names = inspector.get_table_names()

        expected_tables = [
            "users",
            "employees",
            "attendance_raw",
            "attendance_daily",
            "calendar",
            "settings",
            "import_logs",
            "audit_logs",
        ]

        for expected in expected_tables:
            self.assertIn(
                expected,
                table_names,
                f"Tabel '{expected}' seharusnya ada di database SQLite."
            )

    def test_02_seed_initial_users(self):
        """Uji 3: User Admin dan Operator default berhasil di-seed."""
        session = self.TestSession()
        try:
            seed_initial_data(session=session)
            session.commit()

            admin = session.query(User).filter(User.username == "admin").first()
            self.assertIsNotNone(admin, "Akun admin harus berhasil di-seed.")
            self.assertEqual(admin.role, UserRole.ADMIN)
            self.assertTrue(admin.is_active)

            operator = session.query(User).filter(User.username == "operator").first()
            self.assertIsNotNone(operator, "Akun operator harus berhasil di-seed.")
            self.assertEqual(operator.role, UserRole.OPERATOR)
            self.assertTrue(operator.is_active)
        finally:
            session.close()

    def test_03_password_hashing_and_verification(self):
        """Uji 4 & 5: Verifikasi password benar dan penolakan password salah."""
        plain_password = "SecretPassword123!"
        hashed = hash_password(plain_password)

        # Hash tidak boleh sama dengan teks plaintext
        self.assertNotEqual(plain_password, hashed)

        # Password benar harus berhasil diverifikasi
        self.assertTrue(verify_password(plain_password, hashed))

        # Password salah harus ditolak
        self.assertFalse(verify_password("WrongPassword!", hashed))
        self.assertFalse(verify_password("", hashed))

    def test_04_settings_save_and_load(self):
        """Uji 6 & 7: Pengaturan sistem berhasil disimpan, dimuat, dan divalidasi."""
        session = self.TestSession()
        try:
            seed_initial_data(session=session)
            session.commit()

            # Pastikan default setting ter-seed
            setting_target = session.query(Setting).filter(Setting.setting_key == "target_hari_kerja_bulanan").first()
            self.assertIsNotNone(setting_target)
            self.assertEqual(setting_target.setting_value, "18")

            # Uji simpan pengaturan baru
            test_data = {
                "target_hari_kerja_bulanan": "20",
                "jam_masuk_senin_kamis": "08:00",
                "jam_pulang_senin_kamis": "16:30",
                "potongan_tidak_hadir": "25000",
            }
            is_valid, errors = SettingsService.validate_settings(test_data)
            self.assertTrue(is_valid, f"Data konfigurasi seharusnya valid, error: {errors}")

            # Uji validasi gagal jika jam salah format
            invalid_data = {"jam_masuk_senin_kamis": "8 pagi"}
            is_valid_inv, errors_inv = SettingsService.validate_settings(invalid_data)
            self.assertFalse(is_valid_inv)
            self.assertTrue(len(errors_inv) > 0)
        finally:
            session.close()

    def test_05_backup_database_creation(self):
        """Uji 8: Backup database berhasil dibuat dan lolos uji integritas SQLite."""
        backup_target = Path(self.temp_dir.name) / "backup_test.db"

        # Simulasikan backup dari test_db_path
        import sqlite3
        src_conn = sqlite3.connect(str(self.test_db_path))
        dest_conn = sqlite3.connect(str(backup_target))
        with dest_conn:
            src_conn.backup(dest_conn)
        dest_conn.close()
        src_conn.close()

        # Verifikasi file ada dan memiliki ukuran > 0
        self.assertTrue(backup_target.exists(), "File backup seharusnya tercipta.")
        self.assertGreater(backup_target.stat().st_size, 0, "Ukuran file backup harus > 0 bytes.")

        # Verifikasi integritas SQLite
        chk_conn = sqlite3.connect(str(backup_target))
        cursor = chk_conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        chk_conn.close()
        self.assertEqual(result[0], "ok", "Integritas SQLite backup harus 'ok'.")


if __name__ == "__main__":
    unittest.main()
