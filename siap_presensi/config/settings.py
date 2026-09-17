"""
Konfigurasi Sistem SIAP (Sistem Informasi Administrasi Presensi).
Mengatur path file lokal, koneksi database SQLite, identitas aplikasi,
dan nilai default sistem.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Deteksi root path aplikasi (mendukung eksekusi script biasa dan bundle PyInstaller)
if getattr(sys, "frozen", False):
    # Dijalankan sebagai EXE hasil PyInstaller
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    # Dijalankan sebagai script python
    BASE_DIR = Path(__file__).resolve().parent.parent

# Load file .env jika ada
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Identitas Aplikasi
APP_NAME = os.getenv("APP_NAME", "SIAP")
APP_FULL_NAME = os.getenv("APP_FULL_NAME", "Sistem Informasi Administrasi Presensi")
APP_SUBTITLE = os.getenv("APP_SUBTITLE", "Sistem Pengelolaan Absensi dan Potongan Karyawan")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DB_VERSION = "1.0.0"
APP_YEAR = "2026"
APP_DEVELOPER = "Tim Pengembang SIAP"
APP_ORGANIZATION = "Universitas / Instansi Pengguna"
APP_LICENSE = "Proprietary / Hak Cipta Dilindungi"


def get_user_data_dir() -> Path:
    """
    Menentukan lokasi folder data pengguna yang sesuai untuk Windows & runtime produksi.
    Memisahkan binary instalasi (Program Files) dari data mutable pengguna:
    1. SIAP_DATA_DIR (Environment variable override jika disetel)
    2. Portable Mode: SIAP_PORTABLE_MODE=1 atau file siap_portable.flag di BASE_DIR
    3. Windows OS atau mode frozen PyInstaller: %LOCALAPPDATA%\\SIAP
    4. Default dev fallback: BASE_DIR / "data"
    """
    if os.getenv("SIAP_DATA_DIR"):
        return Path(os.getenv("SIAP_DATA_DIR")).resolve()

    if os.getenv("SIAP_PORTABLE_MODE") == "1" or (BASE_DIR / "siap_portable.flag").exists():
        return BASE_DIR / "data"

    if sys.platform == "win32" or getattr(sys, "frozen", False) or os.getenv("LOCALAPPDATA"):
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "SIAP"
        return Path.home() / "AppData" / "Local" / "SIAP"

    return BASE_DIR / "data"


# Struktur Direktori Runtime (Terpisah & Aman untuk Windows non-admin)
DATA_DIR = get_user_data_dir()
DB_DIR = DATA_DIR / "database"
BACKUP_DIR = DATA_DIR / "backups"
LOGS_DIR = DATA_DIR / "logs"
EXPORTS_DIR = DATA_DIR / "exports"
CONFIG_DIR = DATA_DIR / "config"
ASSETS_DIR = BASE_DIR / "assets"

# Konfigurasi Database SQLite
DB_NAME = "siap_presensi.db"
DB_PATH = DB_DIR / DB_NAME
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# Kredensial Awal untuk Seed Database
INITIAL_ADMIN_USERNAME = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD", "Admin@SIAP2025")
INITIAL_ADMIN_NAME = os.getenv("INITIAL_ADMIN_NAME", "Administrator Utama")

INITIAL_OPERATOR_USERNAME = os.getenv("INITIAL_OPERATOR_USERNAME", "operator")
INITIAL_OPERATOR_PASSWORD = os.getenv("INITIAL_OPERATOR_PASSWORD", "Operator@SIAP2025")
INITIAL_OPERATOR_NAME = os.getenv("INITIAL_OPERATOR_NAME", "Petugas Presensi")

# Pengaturan Default Sistem (Sesuai Spesifikasi Tahap 1)
DEFAULT_SETTINGS = {
    # Pengaturan Hari Kerja
    "target_hari_kerja_bulanan": {
        "value": "18",
        "description": "Target hari kerja bulanan sebagai acuan kehadiran",
        "type": "int"
    },
    "kebijakan_hari_kerja": {
        "value": "CALENDAR_ACTUAL",
        "description": "Kebijakan perhitungan hari kerja (CALENDAR_ACTUAL / MONTHLY_TARGET)",
        "type": "str"
    },
    "zona_waktu": {
        "value": "Asia/Jakarta",
        "description": "Zona waktu operasional sistem (WIB / UTC+7)",
        "type": "str"
    },
    # Jam Operasional: Senin - Kamis
    "jam_masuk_senin_kamis": {
        "value": "08:15",
        "description": "Jam masuk operasional Senin - Kamis (HH:MM)",
        "type": "time"
    },
    "jam_pulang_senin_kamis": {
        "value": "16:30",
        "description": "Jam pulang operasional Senin - Kamis (HH:MM)",
        "type": "time"
    },
    # Jam Operasional: Jumat
    "jam_masuk_jumat": {
        "value": "08:15",
        "description": "Jam masuk operasional Jumat (HH:MM)",
        "type": "time"
    },
    "jam_pulang_jumat": {
        "value": "17:00",
        "description": "Jam pulang operasional Jumat (HH:MM)",
        "type": "time"
    },
    # Tarif Potongan (Rupiah)
    "potongan_terlambat_sd_1jam": {
        "value": "7500",
        "description": "Nominal potongan terlambat <= 1 jam (Rp)",
        "type": "int"
    },
    "potongan_terlambat_gt_1jam": {
        "value": "10000",
        "description": "Nominal potongan terlambat > 1 jam (Rp)",
        "type": "int"
    },
    "potongan_pulang_cepat": {
        "value": "10000",
        "description": "Nominal potongan pulang sebelum waktunya (Rp)",
        "type": "int"
    },
    "potongan_tidak_absen_masuk": {
        "value": "10000",
        "description": "Nominal potongan tidak scan masuk (Rp)",
        "type": "int"
    },
    "potongan_tidak_absen_pulang": {
        "value": "10000",
        "description": "Nominal potongan tidak scan pulang (Rp)",
        "type": "int"
    },
    "potongan_tidak_hadir": {
        "value": "20000",
        "description": "Nominal potongan tidak hadir / alfa per hari (Rp)",
        "type": "int"
    },
}

# Palet Tema UI Profesional
THEME = {
    "NAVY_DARK": "#0f172a",
    "NAVY_PRIMARY": "#1e293b",
    "NAVY_LIGHT": "#334155",
    "BLUE_PRIMARY": "#1d4ed8",
    "BLUE_HOVER": "#2563eb",
    "BLUE_LIGHT": "#eff6ff",
    "BLUE_ACCENT": "#38bdf8",
    "BG_PAGE": "#f1f5f9",
    "BG_CARD": "#ffffff",
    "BORDER": "#e2e8f0",
    "TEXT_MAIN": "#0f172a",
    "TEXT_MUTED": "#64748b",
    "SUCCESS": "#16a34a",
    "WARNING": "#d97706",
    "DANGER": "#dc2626",
}


def ensure_directories() -> dict:
    """
    Memastikan semua folder penting aplikasi tersedia otomatis:
    database, logs, backups, exports, config, dan assets.
    Mengembalikan dictionary jalur direktori yang telah dipastikan.
    """
    directories = {
        "data": DATA_DIR,
        "database": DB_DIR,
        "backups": BACKUP_DIR,
        "logs": LOGS_DIR,
        "exports": EXPORTS_DIR,
        "config": CONFIG_DIR,
        "assets": ASSETS_DIR,
    }
    for name, directory in directories.items():
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Gagal membuat direktori {name} di {directory}: {e}", file=sys.stderr)
    return directories
