"""
Database Initializer untuk SIAP (Sistem Informasi Administrasi Presensi).
Mengelola siklus hidup inisialisasi database SQLite:
1. Pembuatan folder database otomatis.
2. Pembuatan database jika belum ada.
3. Pembuatan backup pra-migrasi jika database lama sudah ada.
4. Eksekusi migrasi skema secara aman dan idempoten.
5. Verifikasi foreign keys, journal mode WAL, dan indeks query penting.
6. Verifikasi dan pencatatan versi database.
7. Seeding data awal secara aman tanpa duplikasi.
"""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

from config.settings import (
    DB_PATH,
    BACKUP_DIR,
    DB_VERSION,
    APP_VERSION,
    ensure_directories,
)
from database.base import Base
from database.migration_runner import run_phase4_migrations, run_phase5_migrations
from database.seed import seed_initial_data
from utils.logger import get_logger

logger = get_logger("DatabaseInitializer")


class DatabaseInitializer:
    """Kelas pengelola inisialisasi dan verifikasi integritas database SQLite SIAP."""

    @classmethod
    def create_pre_migration_backup(cls, db_path: Path) -> Path:
        """
        Membuat salinan cadangan (backup) otomatis sebelum menjalankan migrasi skema.
        Mencegah risiko kehilangan atau kerusakan data jika migrasi mengalami kendala.
        """
        ensure_directories()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"pre_migration_backup_{timestamp}.db"
        backup_filepath = BACKUP_DIR / backup_filename

        try:
            shutil.copy2(db_path, backup_filepath)
            logger.info(f"Backup pra-migrasi berhasil dibuat: {backup_filepath.name}")
            return backup_filepath
        except Exception as e:
            logger.warning(f"Gagal membuat backup pra-migrasi: {e}")
            return None

    @classmethod
    def ensure_indexes(cls, engine: Engine):
        """Memastikan seluruh index penting untuk kecepatan pencarian tersedia."""
        with engine.begin() as conn:
            indexes = [
                ("idx_employees_emp_num", "employees", "emp_num"),
                ("idx_employees_is_active", "employees", "is_active"),
                ("idx_attendance_raw_emp_date", "attendance_raw", "emp_num, tanggal"),
                ("idx_attendance_daily_date", "attendance_daily", "attendance_date"),
                ("idx_attendance_daily_emp_date", "attendance_daily", "employee_id, attendance_date"),
                ("idx_work_calendars_date", "work_calendars", "calendar_date"),
                ("idx_audit_logs_created_at", "audit_logs", "created_at"),
            ]
            for idx_name, tbl_name, cols in indexes:
                try:
                    conn.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tbl_name} ({cols})"))
                except Exception as e:
                    logger.debug(f"Info index {idx_name}: {e}")

    @classmethod
    def get_database_info(cls, engine: Engine) -> Dict[str, Any]:
        """Mengambil informasi diagnostik status database."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Cek PRAGMA foreign keys dan journal mode
        with engine.connect() as conn:
            fk_res = conn.execute(text("PRAGMA foreign_keys")).scalar()
            journal_res = conn.execute(text("PRAGMA journal_mode")).scalar()

        return {
            "tables": tables,
            "table_count": len(tables),
            "foreign_keys_enabled": bool(fk_res),
            "journal_mode": str(journal_res).upper(),
            "database_path": str(DB_PATH),
        }

    @classmethod
    def record_version(cls, engine: Engine):
        """Mencatat versi database dan aplikasi ke tabel settings."""
        try:
            with engine.begin() as conn:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(text("""
                    INSERT INTO settings (key, value, description, updated_at, updated_by)
                    VALUES ('database_version', :v, 'Versi skema database SIAP', :now, 'SYSTEM')
                    ON CONFLICT(key) DO UPDATE SET value = :v, updated_at = :now
                """), {"v": DB_VERSION, "now": now_str})

                conn.execute(text("""
                    INSERT INTO settings (key, value, description, updated_at, updated_by)
                    VALUES ('app_version', :v, 'Versi aplikasi SIAP', :now, 'SYSTEM')
                    ON CONFLICT(key) DO UPDATE SET value = :v, updated_at = :now
                """), {"v": APP_VERSION, "now": now_str})
        except Exception as e:
            logger.warning(f"Gagal mencatat versi database: {e}")

    @classmethod
    def initialize(cls, engine: Engine) -> Dict[str, Any]:
        """
        Fungsi utama bootstrap database.
        Aman dipanggil berulang kali (idempotent).
        """
        ensure_directories()
        is_new = not DB_PATH.exists()

        logger.info("Memulai inisialisasi database melalui DatabaseInitializer...")
        if is_new:
            logger.info(f"Database baru akan dibuat di: {DB_PATH}")
        else:
            logger.info(f"Database eksisting ditemukan di: {DB_PATH}")
            # Buat backup pra-migrasi untuk proteksi
            cls.create_pre_migration_backup(DB_PATH)

        try:
            # 1. Pastikan seluruh tabel terdefinisi
            Base.metadata.create_all(bind=engine)

            # 2. Jalankan skrip migrasi berjenjang
            run_phase4_migrations(engine)
            run_phase5_migrations(engine)

            # 3. Buat indeks performa jika belum ada
            cls.ensure_indexes(engine)

            # 4. Seed data pengguna awal (Admin & Operator) dan konfigurasi bawaan
            from sqlalchemy.orm import sessionmaker
            LocalSession = sessionmaker(bind=engine)
            with LocalSession() as s:
                seed_initial_data(session=s)

            # 5. Catat versi database
            cls.record_version(engine)

            # 6. Ambil info diagnosa akhir
            info = cls.get_database_info(engine)
            logger.info(
                f"Inisialisasi database sukses. "
                f"Total tabel: {info['table_count']}, WAL Mode: {info['journal_mode']}, FK: {info['foreign_keys_enabled']}"
            )

            return {
                "success": True,
                "is_new": is_new,
                "version": DB_VERSION,
                "database_path": str(DB_PATH),
                "info": info,
                "message": "Database SQLite berhasil diinisialisasi dan siap digunakan.",
            }

        except Exception as e:
            err_msg = f"Inisialisasi database gagal: {e}"
            logger.critical(err_msg, exc_info=True)
            return {
                "success": False,
                "is_new": is_new,
                "version": DB_VERSION,
                "database_path": str(DB_PATH),
                "error": str(e),
                "message": err_msg,
            }
