"""
Modul Date Parser untuk Standarisasi Tanggal Transaksi Absensi SIAP.
Menangani berbagai format tanggal Excel:
- DD/MM/YYYY (Contoh: 03/08/2026 -> 3 Agustus 2026, bukan 8 Maret 2026)
- DD-MM-YYYY
- YYYY-MM-DD
- YYYY/MM/DD
- Objek datetime.date / datetime.datetime
- Bilangan serial tanggal bawaan Excel (serial number)
"""
from datetime import datetime, date, timedelta
from typing import Tuple, Optional, Union
import re


EXCEL_EPOCH = date(1899, 12, 30)


def parse_date_value(val: Union[str, int, float, date, datetime, None]) -> Tuple[Optional[date], Optional[str]]:
    """
    Melakukan parsing tanggal secara konsisten dan aman.

    Returns:
        (date_obj, None) jika valid.
        (None, "Keterangan error") jika tanggal tidak valid atau kosong.
    """
    if val is None:
        return None, "Tanggal kosong."

    # 1. Jika sudah berupa objek date atau datetime
    if isinstance(val, datetime):
        return val.date(), None
    if isinstance(val, date):
        return val, None

    # 2. Jika berupa Excel serial date number (misal 46237)
    if isinstance(val, (int, float)):
        try:
            val_float = float(val)
            # Batasan wajar nomor serial Excel (antara tahun 1990 s/d 2100)
            if 32874 <= val_float <= 73050:
                parsed_date = EXCEL_EPOCH + timedelta(days=int(val_float))
                return parsed_date, None
            return None, "Tanggal tidak valid (serial number di luar rentang)."
        except Exception:
            return None, "Tanggal tidak valid."

    # 3. String parsing
    str_val = str(val).strip()
    if not str_val or str_val.lower() in ("nan", "none", "null", "-", ""):
        return None, "Tanggal kosong."

    # Jika string memiliki bagian jam (misal "2026-08-03 00:00:00" atau "03/08/2026 07:54:00")
    if " " in str_val:
        str_val = str_val.split(" ")[0].strip()
    if "T" in str_val:
        str_val = str_val.split("T")[0].strip()

    # Pisahkan komponen menggunakan pemisah /, -, atau .
    parts = re.split(r"[/.\-]", str_val)
    if len(parts) != 3:
        return None, "Tanggal tidak valid."

    try:
        p0, p1, p2 = parts[0].strip(), parts[1].strip(), parts[2].strip()

        # Kasus A: Format YYYY-MM-DD atau YYYY/MM/DD (Komponen pertama 4 digit tahun)
        if len(p0) == 4 and p0.isdigit():
            year = int(p0)
            month = int(p1)
            day = int(p2)
        # Kasus B: Format DD/MM/YYYY atau DD-MM-YYYY (Komponen terakhir 4 digit tahun)
        # Sesuai instruksi wajib: 03/08/2026 HARUS dibaca sebagai 3 Agustus 2026
        elif len(p2) == 4 and p2.isdigit():
            day = int(p0)
            month = int(p1)
            year = int(p2)
        # Kasus C: 2 digit tahun (misal 03/08/26)
        elif len(p2) == 2 and p2.isdigit():
            day = int(p0)
            month = int(p1)
            year = 2000 + int(p2)
        else:
            return None, "Tanggal tidak valid."

        # Validasi batas kalender
        if year < 1970 or year > 2100:
            return None, f"Tahun {year} di luar rentang valid (1970-2100)."
        if month < 1 or month > 12:
            return None, f"Bulan {month} tidak valid."
        if day < 1 or day > 31:
            return None, f"Hari {day} tidak valid."

        # Validasi keberadaan tanggal pada kalender (termasuk tahun kabisat)
        res_date = date(year, month, day)
        return res_date, None
    except ValueError:
        return None, "Tanggal tidak valid."
    except Exception:
        return None, "Tanggal tidak valid."


def format_date_display(dt: Optional[date]) -> str:
    """Format tanggal ke string standar ISO YYYY-MM-DD untuk database/tampilan."""
    if not dt:
        return "-"
    return dt.strftime("%Y-%m-%d")


def format_date_indonesian(dt: Optional[date]) -> str:
    """Format tanggal ke bahasa Indonesia, misal: 03 Agustus 2026."""
    if not dt:
        return "-"
    bulan_indo = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    return f"{dt.day:02d} {bulan_indo[dt.month]} {dt.year}"


def parse_flexible_date(val: Union[str, int, float, date, datetime, None]) -> Optional[date]:
    """Alias untuk parse_date_value yang langsung mengembalikan Optional[date]."""
    d, _ = parse_date_value(val)
    return d


format_indonesian_date = format_date_indonesian

