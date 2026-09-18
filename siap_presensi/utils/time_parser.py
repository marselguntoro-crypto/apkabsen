"""
Modul Time Parser untuk Standarisasi Waktu Scan Masuk & Scan Pulang SIAP.
Menangani:
- Objek datetime.time / datetime.datetime
- Nilai jam pecahan Excel (misal 0.329861 -> 07:55:00)
- Format string: HH:MM:SS, HH:MM, H:MM:SS, H:MM
- Jam kosong (Scan Masuk / Pulang kosong diperbolehkan untuk data mentah dan BUKAN error)
- Format string tidak valid (misal "abc" atau "25:70")
"""
from datetime import datetime, time
from typing import Tuple, Optional, Union
import re


def parse_time_value(val: Union[str, int, float, time, datetime, None]) -> Tuple[Optional[str], bool, Optional[str]]:
    """
    Melakukan parsing jam scan ke format standar HH:MM:SS.

    Returns:
        (time_str, is_empty, error_message)
        - Jika kosong: (None, True, None) -> Valid, data mentah dibiarkan kosong tanpa status alfa
        - Jika valid: ("07:54:00", False, None)
        - Jika invalid: (None, False, "Format jam tidak valid.")
    """
    if val is None:
        return None, True, None

    # 1. Jika sudah berupa objek time
    if isinstance(val, time):
        return val.strftime("%H:%M:%S"), False, None

    # 2. Jika berupa objek datetime
    if isinstance(val, datetime):
        return val.time().strftime("%H:%M:%S"), False, None

    # 3. Jika berupa bilangan float (Excel fraction of day, 0.0 s/d 1.0)
    if isinstance(val, float):
        if 0.0 <= val <= 1.0:
            total_seconds = int(round(val * 86400))
            hours = (total_seconds // 3600) % 24
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}", False, None

    # 4. String parsing
    str_val = str(val).strip()
    if not str_val or str_val.lower() in ("nan", "none", "null", "-", "", "none:none:none"):
        return None, True, None

    # Jika string mengandung tanggal (misal "2026-08-03 07:54:00")
    if " " in str_val:
        str_val = str_val.split(" ")[-1].strip()

    # Pisahkan komponen jam
    parts = str_val.split(":")
    if len(parts) not in (2, 3):
        return None, False, "Format jam tidak valid."

    try:
        hour = int(parts[0].strip())
        minute = int(parts[1].strip())
        second = int(parts[2].strip()) if len(parts) == 3 else 0

        if not (0 <= hour <= 23):
            return None, False, f"Nilai jam ({hour}) di luar batas (0-23)."
        if not (0 <= minute <= 59):
            return None, False, f"Nilai menit ({minute}) di luar batas (0-59)."
        if not (0 <= second <= 59):
            return None, False, f"Nilai detik ({second}) di luar batas (0-59)."

        return f"{hour:02d}:{minute:02d}:{second:02d}", False, None
    except ValueError:
        return None, False, "Format jam tidak valid."
    except Exception:
        return None, False, "Format jam tidak valid."


def format_time_display(val: Optional[str]) -> str:
    """Mengembalikan jam untuk tampilan ringkas atau strip '-' jika kosong."""
    if not val or val == "-":
        return "-"
    return val


def parse_time_str(val: Optional[str]) -> Optional[str]:
    """
    Ekstrak format jam ringkas HH:MM dari berbagai format input waktu.
    Mengembalikan None jika input kosong atau tidak valid.
    """
    if not val:
        return None
    time_str, is_empty, err = parse_time_value(val)
    if is_empty or err or not time_str:
        return None
    # Ambil HH:MM
    parts = time_str.split(":")
    return f"{int(parts[0]):02d}:{int(parts[1]):02d}"


def time_to_minutes(val: Union[str, time, datetime, None]) -> Optional[int]:
    """
    Mengonversi representasi waktu ke total menit dari 00:00 (0 - 1439).
    Contoh: "08:15" -> 495, "16:30" -> 990.
    Mengembalikan None jika waktu tidak valid atau kosong.
    """
    if val is None:
        return None
    time_str, is_empty, err = parse_time_value(val)
    if is_empty or err or not time_str:
        return None
    try:
        parts = time_str.split(":")
        h = int(parts[0])
        m = int(parts[1])
        return h * 60 + m
    except Exception:
        return None
