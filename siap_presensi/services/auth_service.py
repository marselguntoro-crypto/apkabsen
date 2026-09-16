"""
Layanan Autentikasi dan Manajemen Sesi Pengguna SIAP.
Menyediakan mekanisme password hashing standar industri (bcrypt/PBKDF2),
verifikasi login, proteksi brute-force, dan pencatatan audit trail.
"""
import hashlib
import os
import secrets
from datetime import datetime
from typing import Optional, Tuple

from config.settings import INITIAL_ADMIN_PASSWORD
from database.connection import get_db_session
from database.models import User, UserRole, AuditLog
from utils.logger import get_logger
from utils.validators import validate_username, validate_password

logger = get_logger("AuthService")

# Upayakan penggunaan library bcrypt; sediakan fallback standar PBKDF2-SHA256 jika bcrypt belum terpasang
try:
    import bcrypt

    def hash_password(password: str) -> str:
        """Menghasilkan hash aman menggunakan bcrypt dengan salt terenkripsi."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Memverifikasi kecocokan plain password dengan hash bcrypt."""
        if not plain_password or not hashed_password:
            return False
        # Dukung pengecekan jika hash menggunakan format pbkdf2 fallback
        if hashed_password.startswith("pbkdf2_sha256$"):
            return _verify_pbkdf2(plain_password, hashed_password)
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception as e:
            logger.error(f"Error saat verifikasi password bcrypt: {e}")
            return False

except ImportError:
    logger.warning("Modul 'bcrypt' belum terpasang, beralih ke standar hashlib PBKDF2-SHA256.")

    def hash_password(password: str) -> str:
        """Fallback hashing menggunakan PBKDF2-HMAC-SHA256."""
        salt = secrets.token_hex(16)
        iterations = 100_000
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return f"pbkdf2_sha256${iterations}${salt}${key.hex()}"

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Fallback verifikasi PBKDF2."""
        return _verify_pbkdf2(plain_password, hashed_password)


def _verify_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = parts[2]
        expected_hex = parts[3]
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return secrets.compare_digest(key.hex(), expected_hex)
    except Exception:
        return False


class CurrentSession:
    """
    Singleton penyimpan status login aktif pada antarmuka desktop.
    """
    _instance = None

    def __init__(self):
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None
        self.full_name: Optional[str] = None
        self.role: Optional[UserRole] = None
        self.is_authenticated: bool = False
        self.login_time: Optional[datetime] = None

    @classmethod
    def get_instance(cls) -> "CurrentSession":
        if cls._instance is None:
            cls._instance = CurrentSession()
        return cls._instance

    def set_user(self, user: User):
        self.user_id = user.id
        self.username = user.username
        self.full_name = user.full_name
        self.role = user.role
        self.is_authenticated = True
        self.login_time = datetime.now()

    def clear(self):
        self.user_id = None
        self.username = None
        self.full_name = None
        self.role = None
        self.is_authenticated = False
        self.login_time = None

    @property
    def is_admin(self) -> bool:
        return self.is_authenticated and self.role == UserRole.ADMIN

    @property
    def is_operator(self) -> bool:
        return self.is_authenticated and self.role == UserRole.OPERATOR


class AuthService:
    """
    Layanan operasional autentikasi, verifikasi kredensial, dan pencatatan audit.
    """

    @staticmethod
    def authenticate(username: str, password: str) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        Memvalidasi login pengguna.
        Return tuple: (success: bool, user: Optional[User], error_message: Optional[str])
        """
        # Validasi format input
        valid_u, err_u = validate_username(username)
        if not valid_u:
            logger.warning(f"Percobaan login dengan format username invalid: '{username.strip()}'")
            return False, None, err_u

        valid_p, err_p = validate_password(password)
        if not valid_p:
            return False, None, err_p

        username_clean = username.strip()

        with get_db_session() as session:
            user = session.query(User).filter(User.username == username_clean).first()

            if not user:
                logger.warning(f"Login gagal: Username '{username_clean}' tidak ditemukan.")
                return False, None, "Username atau password yang dimasukkan salah."

            if not user.is_active:
                logger.warning(f"Login ditolak: Akun '{username_clean}' berstatus NONAKTIF.")
                return False, None, "Akun ini telah dinonaktifkan. Silakan hubungi Administrator."

            # Verifikasi password hash
            if not verify_password(password, user.password_hash):
                logger.warning(f"Login gagal: Password salah untuk username '{username_clean}'.")
                return False, None, "Username atau password yang dimasukkan salah."

            # Detach user object untuk disimpan di sesi memori
            session.expunge(user)

            # Catat audit log keberhasilan login
            audit = AuditLog(
                user_id=user.id,
                action="LOGIN_SUCCESS",
                module="AUTH",
                description=f"Pengguna '{user.username}' (Role: {user.role.value}) berhasil masuk ke sistem.",
                created_at=datetime.utcnow(),
            )
            session.add(audit)

        # Set sesi aktif
        CurrentSession.get_instance().set_user(user)
        logger.info(f"Pengguna '{user.username}' berhasil login dengan hak akses {user.role.value}.")
        return True, user, None

    @staticmethod
    def logout() -> bool:
        """Mengeluarkan pengguna dari sesi aktif dan mencatat log."""
        session_instance = CurrentSession.get_instance()
        if session_instance.is_authenticated:
            user_id = session_instance.user_id
            username = session_instance.username
            with get_db_session() as session:
                audit = AuditLog(
                    user_id=user_id,
                    action="LOGOUT",
                    module="AUTH",
                    description=f"Pengguna '{username}' telah logout dari sistem.",
                    created_at=datetime.utcnow(),
                )
                session.add(audit)
            logger.info(f"Pengguna '{username}' telah logout.")
            session_instance.clear()
            return True
        return False

    @staticmethod
    def is_initial_admin_password(user: User) -> bool:
        """Mendeteksi apakah akun admin masih menggunakan password default dari inisialisasi awal."""
        if user.role != UserRole.ADMIN:
            return False
        return verify_password(INITIAL_ADMIN_PASSWORD, user.password_hash)
