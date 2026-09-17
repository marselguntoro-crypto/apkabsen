"""
Pengujian Unit & Integrasi Tahap 6: Deployment, Finalisasi Database & Windows Installer.
SIAP - Sistem Informasi Administrasi Presensi (v1.0.0).

Verifikasi:
1. DatabaseInitializer (Inisialisasi bersih, idempotensi, migrasi, pre-migration backup, versi).
2. Resolusi Jalur Folder Pengguna Windows (%LOCALAPPDATA%\\SIAP).
3. First-Run Setup & Proteksi Kredensial Awal.
4. Integritas Berkas Build Packaging (SIAP.spec, build_windows.bat, clean_build.bat).
5. Integritas Berkas Installer Windows (SIAP_Setup.iss).
6. Integritas Asset Ikon & Buku Panduan Pengguna PDF.
"""
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text
from database.base import Base
from database.initializer import DatabaseInitializer
from database.models import User, UserRole, Setting
from config.settings import (
    APP_VERSION,
    DB_VERSION,
    get_user_data_dir,
    ensure_directories,
)
from services.auth_service import AuthService


class TestPhase6Deployment(unittest.TestCase):
    """Pengujian Komprehensif Deployment, Inisialisasi Database, dan Artefak Rilis Windows."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_user_data_directory_resolution(self):
        """Uji resolusi folder data pengguna Windows dan opsi override."""
        # 1. Test environment variable override
        custom_dir = self.temp_path / "CustomSIAPData"
        with patch.dict(os.environ, {"SIAP_DATA_DIR": str(custom_dir)}):
            resolved = get_user_data_dir()
            self.assertEqual(resolved, custom_dir)

        # 2. Test portable mode
        with patch.dict(os.environ, {"SIAP_PORTABLE_MODE": "1"}, clear=True):
            resolved = get_user_data_dir()
            self.assertEqual(resolved, PROJECT_ROOT / "data")

        # 3. Test Windows LOCALAPPDATA simulation
        fake_local_appdata = self.temp_path / "AppData" / "Local"
        with patch.dict(os.environ, {"LOCALAPPDATA": str(fake_local_appdata), "SIAP_DATA_DIR": ""}, clear=True):
            resolved = get_user_data_dir()
            self.assertEqual(resolved, fake_local_appdata / "SIAP")

    def test_02_database_initializer_clean_and_idempotent(self):
        """Uji DatabaseInitializer: inisialisasi awal dan eksekusi berulang yang aman (idempotent)."""
        db_file = self.temp_path / "test_init.db"
        test_engine = create_engine(f"sqlite:///{db_file.as_posix()}", echo=False)

        with patch("database.initializer.DB_PATH", db_file), \
             patch("database.initializer.BACKUP_DIR", self.temp_path / "backups"):

            # 1. Inisialisasi pertama (database baru)
            res1 = DatabaseInitializer.initialize(test_engine)
            self.assertTrue(res1["success"])
            self.assertTrue(res1["is_new"])
            self.assertEqual(res1["version"], DB_VERSION)

            # Periksa tabel penting
            info1 = DatabaseInitializer.get_database_info(test_engine)
            required_tables = ["users", "employees", "work_calendars", "attendance_raw", "attendance_daily", "attendance_deductions", "settings", "audit_logs"]
            for tbl in required_tables:
                self.assertIn(tbl, info1["tables"])

            # Periksa versi tercatat
            with test_engine.connect() as conn:
                v_db = conn.execute(text("SELECT value FROM settings WHERE key='database_version'")).scalar()
                v_app = conn.execute(text("SELECT value FROM settings WHERE key='app_version'")).scalar()
                self.assertEqual(v_db, DB_VERSION)
                self.assertEqual(v_app, APP_VERSION)

            # 2. Inisialisasi kedua (idempotent run pada database yang sudah ada)
            res2 = DatabaseInitializer.initialize(test_engine)
            self.assertTrue(res2["success"])
            self.assertFalse(res2["is_new"])

            # Verifikasi user tidak terduplikasi
            with test_engine.connect() as conn:
                admin_count = conn.execute(text("SELECT COUNT(*) FROM users WHERE username='admin'")).scalar()
                self.assertEqual(admin_count, 1)

            # Verifikasi pembuatan backup pra-migrasi saat re-initialize
            backups = list((self.temp_path / "backups").glob("pre_migration_backup_*.db"))
            self.assertGreaterEqual(len(backups), 1)

    def test_03_first_run_admin_password_detection(self):
        """Uji deteksi akun admin bawaan pabrik untuk pemicuan First-Run Wizard."""
        admin_user = User(
            id=1,
            username="admin",
            password_hash=AuthService.hash_password("Admin@SIAP2025"),
            full_name="Administrator Utama",
            role=UserRole.ADMIN,
        )
        self.assertTrue(AuthService.is_initial_admin_password(admin_user))

        # Setelah password diganti
        admin_user.password_hash = AuthService.hash_password("NewPasswordSecure123!")
        self.assertFalse(AuthService.is_initial_admin_password(admin_user))

    def test_04_pyinstaller_spec_and_build_scripts(self):
        """Uji ketersediaan dan sintaks berkas PyInstaller spec dan script packaging Windows."""
        spec_path = PROJECT_ROOT / "SIAP.spec"
        self.assertTrue(spec_path.exists(), "SIAP.spec harus tersedia di root project.")

        spec_content = spec_path.read_text(encoding="utf-8")
        self.assertIn("main.py", spec_content)
        self.assertIn("console=False", spec_content, "Aplikasi desktop harus berjalan tanpa terminal hitam (console=False).")
        self.assertIn("SIAP.ico", spec_content)
        self.assertIn("PySide6", spec_content)
        self.assertIn("openpyxl", spec_content)
        self.assertIn("reportlab", spec_content)

        # Periksa script build batch
        build_bat = PROJECT_ROOT / "build_windows.bat"
        clean_bat = PROJECT_ROOT / "clean_build.bat"
        self.assertTrue(build_bat.exists(), "build_windows.bat harus tersedia.")
        self.assertTrue(clean_bat.exists(), "clean_build.bat harus tersedia.")

        build_content = build_bat.read_text(encoding="utf-8")
        self.assertIn("pytest", build_content, "Script build harus menjalankan pytest sebelum kompilasi.")
        self.assertIn("pyinstaller", build_content)
        self.assertIn("dist\\SIAP\\SIAP.exe", build_content)

    def test_05_inno_setup_script(self):
        """Uji ketersediaan dan integritas script installer Inno Setup."""
        iss_path = PROJECT_ROOT / "installer" / "SIAP_Setup.iss"
        self.assertTrue(iss_path.exists(), "installer/SIAP_Setup.iss harus tersedia.")

        iss_content = iss_path.read_text(encoding="utf-8")
        self.assertIn("AppName \"SIAP\"", iss_content)
        self.assertIn("AppVersion \"1.0.0\"", iss_content)
        self.assertIn("ArchitecturesInstallIn64BitMode=x64compatible", iss_content)
        self.assertIn("{autopf}\\{#MyAppName}", iss_content)
        self.assertIn("SIAP_Setup_v1.0.0", iss_content)
        self.assertIn("{localappdata}\\SIAP", iss_content, "Installer harus menjamin direktori data pengguna terpisah dan terlindungi.")

    def test_06_branding_assets_and_manual_pdf(self):
        """Uji ketersediaan icon aplikasi SIAP.ico/png dan buku panduan resmi PDF."""
        icon_ico = PROJECT_ROOT / "assets" / "icons" / "SIAP.ico"
        icon_png = PROJECT_ROOT / "assets" / "icons" / "SIAP.png"
        manual_pdf = PROJECT_ROOT / "PANDUAN_PENGGUNA_SIAP.pdf"

        self.assertTrue(icon_ico.exists(), "assets/icons/SIAP.ico harus ada.")
        self.assertTrue(icon_png.exists(), "assets/icons/SIAP.png harus ada.")
        self.assertTrue(manual_pdf.exists(), "PANDUAN_PENGGUNA_SIAP.pdf harus berhasil dibuat.")
        self.assertGreater(manual_pdf.stat().st_size, 10000, "Ukuran file PDF buku panduan harus valid (>10KB).")


if __name__ == "__main__":
    unittest.main()
