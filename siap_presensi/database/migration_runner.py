"""
Migration Runner Otomatis untuk Transisi Antar-Tahap Pengembangan SIAP.
Memastikan skema tabel work_calendars dan attendance_daily termigrasi dengan aman di SQLite.
"""
from sqlalchemy import text
from utils.logger import get_logger

logger = get_logger("MigrationRunner")


def run_phase4_migrations(engine):
    """
    Menjalankan migrasi DDL untuk Tahap 4 jika tabel attendance_daily atau work_calendars
    memerlukan kolom baru pada SQLite yang sudah ada.
    """
    with engine.connect() as conn:
        # 1. Periksa kolom-kolom pada attendance_daily
        try:
            result = conn.execute(text("PRAGMA table_info(attendance_daily)"))
            columns = [row[1] for row in result.fetchall()]
            
            # Jika tabel sudah ada tapi belum memiliki attendance_date
            if columns and "attendance_date" not in columns:
                logger.info("Migrasi skema attendance_daily Tahap 4 dimulai...")
                
                # Tambahkan kolom-kolom baru yang dibutuhkan
                columns_to_add = [
                    ("attendance_date", "DATE"),
                    ("calendar_id", "INTEGER"),
                    ("day_name", "VARCHAR(20)"),
                    ("scheduled_check_in", "VARCHAR(10)"),
                    ("scheduled_check_out", "VARCHAR(10)"),
                    ("actual_check_in", "VARCHAR(10)"),
                    ("actual_check_out", "VARCHAR(10)"),
                    ("check_in_status", "VARCHAR(20) DEFAULT 'TIDAK_ADA'"),
                    ("check_out_status", "VARCHAR(20) DEFAULT 'TIDAK_ADA'"),
                    ("attendance_status", "VARCHAR(50) DEFAULT 'TIDAK_ABSEN'"),
                    ("source_raw_in_id", "INTEGER"),
                    ("source_raw_out_id", "INTEGER"),
                    ("has_incomplete_scan", "BOOLEAN DEFAULT 0"),
                    ("has_conflict", "BOOLEAN DEFAULT 0"),
                    ("is_manually_adjusted", "BOOLEAN DEFAULT 0"),
                    ("notes", "TEXT"),
                    ("generated_at", "DATETIME"),
                    ("generated_by", "VARCHAR(100)"),
                ]
                
                for col_name, col_type in columns_to_add:
                    if col_name not in columns:
                        conn.execute(text(f"ALTER TABLE attendance_daily ADD COLUMN {col_name} {col_type}"))
                        logger.info(f"Kolom {col_name} berhasil ditambahkan ke attendance_daily.")

                # Sinkronisasi data lama jika ada: tanggal -> attendance_date
                if "tanggal" in columns:
                    conn.execute(text("UPDATE attendance_daily SET attendance_date = tanggal WHERE attendance_date IS NULL"))
                if "hari" in columns:
                    conn.execute(text("UPDATE attendance_daily SET day_name = hari WHERE day_name IS NULL"))
                if "jam_masuk" in columns:
                    conn.execute(text("UPDATE attendance_daily SET actual_check_in = jam_masuk WHERE actual_check_in IS NULL"))
                if "jam_pulang" in columns:
                    conn.execute(text("UPDATE attendance_daily SET actual_check_out = jam_pulang WHERE actual_check_out IS NULL"))
                
                conn.commit()
                logger.info("Migrasi attendance_daily Tahap 4 selesai dengan sukses.")
        except Exception as e:
            logger.warning(f"Catatan migrasi attendance_daily: {e}")
