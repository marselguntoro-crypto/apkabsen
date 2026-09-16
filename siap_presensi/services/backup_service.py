"""
Layanan Backup Database SQLite SIAP.
Menggunakan SQLite Online Backup API untuk memastikan konsistensi transaksi
tanpa menghentikan atau menghapus database utama.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, List, Dict

from config.settings import DB_PATH, BACKUP_DIR, ensure_directories
from database.connection import get_db_session
from database.models import AuditLog
from utils.logger import get_logger

logger = get_logger("BackupService")


class BackupService:
    """Service untuk pencadangan (backup) dan pemeliharaan file database SQLite."""

    @staticmethod
    def generate_backup_filename() -> str:
        """Menghasilkan nama file backup otomatis: backup_siap_YYYYMMDD_HHMMSS.db"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_siap_{timestamp}.db"

    @staticmethod
    def create_backup(
        target_path: Optional[Path] = None,
        user_id: Optional[int] = None
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Membuat salinan cadangan database siap_presensi.db secara aman.
        Jika target_path tidak ditentukan, file akan disimpan di folder data/backups/.
        Menggunakan SQLite Online Backup API untuk integritas transaksi.
        """
        ensure_directories()

        if not DB_PATH.exists():
            msg = f"Database utama tidak ditemukan pada lokasi: {DB_PATH}"
            logger.error(msg)
            return False, msg, None

        if target_path is None:
            filename = BackupService.generate_backup_filename()
            dest_file = BACKUP_DIR / filename
        else:
            dest_file = Path(target_path)
            if dest_file.is_dir():
                dest_file = dest_file / BackupService.generate_backup_filename()

        try:
            # Pastikan direktori tujuan tersedia
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            # Eksekusi SQLite Online Backup API (Aman terhadap WAL & Concurrent Read/Write)
            src_conn = sqlite3.connect(str(DB_PATH))
            dest_conn = sqlite3.connect(str(dest_file))

            with dest_conn:
                src_conn.backup(dest_conn, pages=100, sleep=0.01)

            dest_conn.close()
            src_conn.close()

            # Validasi hasil backup (Ukuran berkas & Integrity Check)
            if not dest_file.exists() or dest_file.stat().st_size == 0:
                msg = "Gagal memverifikasi file backup: Berkas kosong atau tidak terbuat."
                logger.error(msg)
                return False, msg, None

            # Cek integritas file backup
            test_conn = sqlite3.connect(str(dest_file))
            cursor = test_conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            integrity_result = cursor.fetchone()
            test_conn.close()

            if not integrity_result or integrity_result[0] != "ok":
                msg = f"Uji integritas backup gagal: {integrity_result}"
                logger.error(msg)
                return False, msg, None

            file_size_kb = dest_file.stat().st_size / 1024
            success_msg = f"Backup database berhasil dibuat: {dest_file.name} ({file_size_kb:.1f} KB)"
            logger.info(success_msg)

            # Catat Audit Log
            try:
                with get_db_session() as session:
                    audit = AuditLog(
                        user_id=user_id,
                        action="BACKUP_DATABASE",
                        module="DATABASE",
                        description=f"Pencadangan database berhasil ke file: {dest_file.name}",
                        created_at=datetime.utcnow(),
                    )
                    session.add(audit)
            except Exception as e_audit:
                logger.warning(f"Gagal mencatat audit log backup: {e_audit}")

            return True, success_msg, dest_file

        except Exception as e:
            error_msg = f"Terjadi kesalahan saat proses backup database: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    @staticmethod
    def get_existing_backups() -> List[Dict[str, str]]:
        """Mengambil daftar riwayat file backup yang ada di data/backups/."""
        ensure_directories()
        backups = []
        try:
            for file in sorted(BACKUP_DIR.glob("backup_siap_*.db"), reverse=True):
                stat = file.stat()
                backups.append({
                    "filename": file.name,
                    "filepath": str(file),
                    "size_kb": f"{stat.st_size / 1024:.1f} KB",
                    "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                })
        except Exception as e:
            logger.error(f"Gagal membaca folder backup: {e}")
        return backups
