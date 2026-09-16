"""
Modul Logging Aplikasi SIAP.
Menyimpan log rotasi ke data/logs/app.log dan stream console.
Memiliki proteksi terhadap kebocoran kata sandi dan kredensial sensitif.
"""
import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config.settings import LOGS_DIR, ensure_directories

_logger = None

# Pola regex untuk menyensor potensi token / kata sandi jika tidak sengaja tercetak
SENSITIVE_PATTERNS = [
    re.compile(r"(password[\"']?\s*[:=]\s*[\"']?)([^\"'\s,]+)([\"']?)", re.IGNORECASE),
    re.compile(r"(pass[\"']?\s*[:=]\s*[\"']?)([^\"'\s,]+)([\"']?)", re.IGNORECASE),
    re.compile(r"(token[\"']?\s*[:=]\s*[\"']?)([^\"'\s,]+)([\"']?)", re.IGNORECASE),
]


class SafeFormatter(logging.Formatter):
    """Formatter yang membersihkan informasi sensitif seperti password."""
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        sanitized = original
        for pattern in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(r"\1******\3", sanitized)
        return sanitized


def setup_logger(name: str = "SIAP", log_file: Path = None, level: int = logging.INFO) -> logging.Logger:
    """Menginisialisasi logger tunggal aplikasi."""
    global _logger
    if _logger is not None:
        return _logger

    ensure_directories()
    if log_file is None:
        log_file = LOGS_DIR / "app.log"

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Bersihkan handler sebelumnya jika ada
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = SafeFormatter(
        fmt="[%(asctime)s] [%(levelname)-7s] [%(name)s] [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler dengan rotasi 5MB x 5 file cadangan
    try:
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"[LOGGER WARNING] Gagal membuka log file di {log_file}: {e}")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _logger = logger
    return _logger


def get_logger(name: str = "SIAP") -> logging.Logger:
    """Mengambil instance logger yang sudah dikonfigurasi."""
    global _logger
    if _logger is None:
        return setup_logger(name)
    return logging.getLogger(name)
