"""
Manajemen Koneksi Database SQLite dan Session SQLAlchemy untuk SIAP.
Mengaktifkan PRAGMA foreign_keys dan WAL mode untuk integritas data.
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from config.settings import DATABASE_URL, ensure_directories
from .base import Base

# Buat engine SQLAlchemy untuk SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    pool_pre_ping=True,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Mengaktifkan foreign key enforcement dan WAL mode pada SQLite.
    Sangat penting agar integritas relasi antar tabel terjaga.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


# Factory Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager untuk transaksi database yang aman.
    Otomatis rollback jika terjadi exception, dan menutup session saat selesai.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> dict:
    """
    Inisialisasi direktori dan tabel database melalui DatabaseInitializer.
    Mengeksekusi pembuatan tabel jika belum ada, backup pra-migrasi, migrasi, dan seed data awal.
    """
    from .initializer import DatabaseInitializer
    res = DatabaseInitializer.initialize(engine)
    if not res.get("success"):
        raise RuntimeError(res.get("error", "Database initialization failed"))
    return res
