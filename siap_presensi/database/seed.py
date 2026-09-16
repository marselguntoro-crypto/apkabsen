"""
Modul Seed Data Awal Database SIAP.
Mengisi akun Administrator & Operator bawaan serta pengaturan default sistem.
"""
from datetime import datetime
from config.settings import (
    INITIAL_ADMIN_USERNAME,
    INITIAL_ADMIN_PASSWORD,
    INITIAL_ADMIN_NAME,
    INITIAL_OPERATOR_USERNAME,
    INITIAL_OPERATOR_PASSWORD,
    INITIAL_OPERATOR_NAME,
    DEFAULT_SETTINGS,
)
from database.base import Base
from database.models import User, UserRole, Setting, AuditLog
from services.auth_service import hash_password
from utils.logger import get_logger

logger = get_logger("DatabaseSeed")


def seed_initial_data(session=None):
    """
    Melakukan seeding data awal ke database jika tabel belum memiliki data master.
    Dapat menerima session yang sudah ada atau membuat session baru.
    """
    from database.connection import get_db_session

    def _execute_seed(db_session):
        # 1. Seeding Akun Pengguna (Jika belum ada user sama sekali)
        existing_users_count = db_session.query(User).count()
        if existing_users_count == 0:
            logger.info("Database kosong terdeteksi. Memulai seeding user default...")

            admin_user = User(
                username=INITIAL_ADMIN_USERNAME,
                password_hash=hash_password(INITIAL_ADMIN_PASSWORD),
                full_name=INITIAL_ADMIN_NAME,
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db_session.add(admin_user)

            operator_user = User(
                username=INITIAL_OPERATOR_USERNAME,
                password_hash=hash_password(INITIAL_OPERATOR_PASSWORD),
                full_name=INITIAL_OPERATOR_NAME,
                role=UserRole.OPERATOR,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db_session.add(operator_user)
            db_session.flush()

            # Catat Audit Log
            audit = AuditLog(
                user_id=admin_user.id,
                action="INITIAL_SEED",
                module="SYSTEM",
                description="Inisialisasi akun Administrator dan Operator bawaan sistem.",
                created_at=datetime.utcnow(),
            )
            db_session.add(audit)
            logger.info(f"Akun pengguna berhasil di-seed: {INITIAL_ADMIN_USERNAME} (ADMIN) & {INITIAL_OPERATOR_USERNAME} (OPERATOR).")

        # 2. Seeding Tabel Settings (Isi key default jika belum tersimpan)
        for key, config in DEFAULT_SETTINGS.items():
            existing_setting = db_session.query(Setting).filter(Setting.setting_key == key).first()
            if not existing_setting:
                new_setting = Setting(
                    setting_key=key,
                    setting_value=str(config["value"]),
                    description=config.get("description", ""),
                    updated_at=datetime.utcnow(),
                )
                db_session.add(new_setting)
                logger.info(f"Pengaturan sistem '{key}' di-seed dengan nilai default: {config['value']}")

    if session is not None:
        _execute_seed(session)
    else:
        with get_db_session() as db_session:
            _execute_seed(db_session)
