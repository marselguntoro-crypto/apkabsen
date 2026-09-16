"""
Titik Masuk Utama (Entry Point) Aplikasi Desktop SIAP.
SISTEM INFORMASI ADMINISTRASI PRESENSI
Mengatur inisialisasi database SQLite, lifecycle Qt Application,
penanganan unhandled exception hook, dan alur autentikasi login.
"""
import os
import sys
import traceback
from pathlib import Path

# Pastikan direktori root project masuk ke sys.path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from config.settings import (
    APP_NAME,
    APP_FULL_NAME,
    APP_VERSION,
    ensure_directories,
)
from database.connection import init_db
from database.models import User
from services.auth_service import AuthService
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from utils.logger import setup_logger, get_logger

# Inisialisasi Logger
ensure_directories()
logger = setup_logger("SIAP")


def exception_hook(exctype, value, tb):
    """
    Menangkap dan mencatat setiap unhandled exception ke file data/logs/app.log
    untuk mencegah crash hening pada sistem operasi Windows.
    """
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    logger.critical(f"Unhandled Exception terdeteksi:\n{error_msg}")
    print(error_msg, file=sys.stderr)

    # Tampilkan pesan ramah jika GUI masih aktif
    if QApplication.instance():
        QMessageBox.critical(
            None,
            "Terjadi Kesalahan Sistem",
            f"Aplikasi mendeteksi error tak terduga:\n{value}\n\n"
            "Detail lengkap telah dicatat di berkas data/logs/app.log.",
        )


class ApplicationController:
    """Mengelola siklus hidup jendela Login dan Jendela Utama."""

    def __init__(self):
        self.login_window = LoginWindow()
        self.main_window = None

        # Hubungkan sinyal login berhasil
        self.login_window.login_success.connect(self.show_main_window)

    def start(self):
        """Memulai aplikasi dengan menampilkan dialog login."""
        self.login_window.show()

    def show_main_window(self, user: User):
        """Membuka MainWindow setelah autentikasi sukses."""
        self.login_window.hide()

        # Inisialisasi Main Window sesuai role pengguna
        self.main_window = MainWindow(user=user)
        self.main_window.logout_signal.connect(self.show_login_window)
        self.main_window.show()

        # Peringatan keamanan jika akun admin masih memakai password default
        if AuthService.is_initial_admin_password(user):
            QMessageBox.information(
                self.main_window,
                "Peringatan Keamanan",
                "Perhatian: Akun Administrator saat ini masih menggunakan kata sandi bawaan awal "
                "(Admin@SIAP2025).\nDisarankan untuk mengganti kata sandi demi keamanan operasional."
            )

    def show_login_window(self):
        """Menampilkan kembali dialog login setelah logout."""
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        self.login_window.reset_fields()
        self.login_window.show()


def main():
    """Fungsi utama bootstrap sistem."""
    sys.excepthook = exception_hook

    logger.info("==================================================")
    logger.info(f"Memulai {APP_NAME} - {APP_FULL_NAME} (v{APP_VERSION})")
    logger.info("==================================================")

    # Inisialisasi database SQLite dan seed konfigurasi default
    try:
        logger.info("Memeriksa status dan skema database SQLite...")
        init_db()
        logger.info("Database SQLite siap digunakan.")
    except Exception as e:
        logger.critical(f"Gagal menginisialisasi database SQLite: {e}")
        print(f"[FATAL] Gagal menginisialisasi database SQLite: {e}", file=sys.stderr)
        return 1

    # Buat instance QApplication
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(f"{APP_NAME} - {APP_FULL_NAME}")
    app.setOrganizationName("SIAP Developer")

    # Terapkan font standar antarmuka desktop (Segoe UI pada Windows)
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)

    # Jalankan Controller
    controller = ApplicationController()
    controller.start()

    logger.info("Antarmuka aplikasi desktop berhasil dibuka.")
    exit_code = app.exec()
    logger.info(f"Aplikasi SIAP ditutup dengan exit code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
