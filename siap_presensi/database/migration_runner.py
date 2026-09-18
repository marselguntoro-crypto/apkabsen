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


def run_phase5_migrations(engine):
    """
    Menjalankan migrasi DDL untuk Tahap 5:
    1. Memastikan tabel attendance_deductions dan attendance_deduction_items tersedia.
    2. Membuat indeks komposit untuk optimasi performa rekap bulanan dan integritas data.
    """
    with engine.connect() as conn:
        try:
            # 1. Buat tabel attendance_deductions jika belum ada
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS attendance_deductions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attendance_daily_id INTEGER NOT NULL UNIQUE,
                    employee_id INTEGER NOT NULL,
                    attendance_date DATE NOT NULL,
                    late_minutes INTEGER NOT NULL DEFAULT 0,
                    early_leave_minutes INTEGER NOT NULL DEFAULT 0,
                    deduction_late INTEGER NOT NULL DEFAULT 0,
                    deduction_early_leave INTEGER NOT NULL DEFAULT 0,
                    deduction_missing_check_in INTEGER NOT NULL DEFAULT 0,
                    deduction_missing_check_out INTEGER NOT NULL DEFAULT 0,
                    total_deduction INTEGER NOT NULL DEFAULT 0,
                    calculation_version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
                    calculated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    calculated_by VARCHAR(100) DEFAULT 'SYSTEM',
                    notes TEXT,
                    FOREIGN KEY (attendance_daily_id) REFERENCES attendance_daily (id) ON DELETE CASCADE,
                    FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
                    UNIQUE (employee_id, attendance_date)
                )
            """))

            # 2. Buat tabel attendance_deduction_items jika belum ada
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS attendance_deduction_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attendance_deduction_id INTEGER NOT NULL,
                    deduction_type VARCHAR(50) NOT NULL,
                    description VARCHAR(255) NOT NULL,
                    amount INTEGER NOT NULL DEFAULT 0,
                    calculation_reference VARCHAR(255),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (attendance_deduction_id) REFERENCES attendance_deductions (id) ON DELETE CASCADE
                )
            """))

            # 3. Indeks pendukung performa rekap dan pelaporan
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deduction_emp_date ON attendance_deductions (employee_id, attendance_date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deduction_total ON attendance_deductions (total_deduction)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deduction_item_type ON attendance_deduction_items (deduction_type)"))

            conn.commit()
            logger.info("Migrasi skema Tahap 5 (attendance_deductions & attendance_deduction_items) berhasil.")
        except Exception as e:
            logger.warning(f"Catatan migrasi Tahap 5: {e}")
