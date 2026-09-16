"""
Modul Duplicate Detector untuk Transaksi Absensi Mentah SIAP.
Mendeteksi potensi duplikasi:
1. Duplikat internal di dalam berkas Excel yang sama.
2. Duplikat terhadap data yang sudah tersimpan di tabel attendance_raw database.
Aturan deteksi:
- Memeriksa identitas karyawan (emp_num, no_id, atau nama), tanggal, jam masuk, dan jam pulang.
- Seorang karyawan DAPAT memiliki lebih dari 1 transaksi pada tanggal yang sama jika waktu scan berbeda.
- Transaksi dianggap duplikat eksak HANYA jika identitas, tanggal, jam masuk, dan jam pulang bernilai identik.
- Menghasilkan opsi resolusi: SKIP (lewati), INSERT (simpan transaksi baru), REVIEW (tinjau manual).
"""
from typing import Dict, Any, List, Set, Tuple, Optional
from datetime import date
from sqlalchemy.orm import Session
from database.models import AttendanceRaw


class DuplicateResolution:
    SKIP = "SKIP"       # Lewati baris yang duplikat
    INSERT = "INSERT"   # Tetap simpan sebagai transaksi baru
    REVIEW = "REVIEW"   # Tinjau manual / pending


def make_transaction_key(
    emp_num: Optional[str],
    no_id: Optional[str],
    nama: str,
    tgl: Optional[date],
    scan_masuk: Optional[str],
    scan_pulang: Optional[str],
) -> str:
    """
    Membuat hash key unik untuk identifikasi transaksi eksak:
    (Identitas Karyawan) + (Tanggal) + (Scan Masuk) + (Scan Pulang)
    """
    # Normalisasi identitas karyawan
    emp_key = (emp_num or "").strip().lower()
    id_key = (no_id or "").strip().lower()
    nama_key = (nama or "").strip().lower()

    identity_str = f"{emp_key}|{id_key}|{nama_key}"
    tgl_str = tgl.strftime("%Y-%m-%d") if tgl else "NO_DATE"
    masuk_str = (scan_masuk or "-").strip()
    pulang_str = (scan_pulang or "-").strip()

    return f"{identity_str}::{tgl_str}::{masuk_str}::{pulang_str}"


def check_in_file_duplicates(parsed_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Memeriksa duplikasi internal dalam satu file Excel.
    Menandai baris dengan flag `is_duplicate_in_file: True` dan `duplicate_source_row: idx`.
    """
    seen_keys: Dict[str, int] = {}  # key -> row_index

    for idx, row in enumerate(parsed_rows, 1):
        if not row.get("is_valid", False):
            row["is_duplicate_in_file"] = False
            continue

        key = make_transaction_key(
            emp_num=row.get("emp_num"),
            no_id=row.get("no_id"),
            nama=row.get("nama", ""),
            tgl=row.get("tanggal_obj"),
            scan_masuk=row.get("scan_masuk"),
            scan_pulang=row.get("scan_pulang"),
        )

        if key in seen_keys:
            prev_row_num = seen_keys[key]
            row["is_duplicate_in_file"] = True
            row["duplicate_source_row"] = prev_row_num
            row["duplicate_message"] = f"Duplikat dengan baris {prev_row_num} di dalam file yang sama."
        else:
            seen_keys[key] = idx
            row["is_duplicate_in_file"] = False

    return parsed_rows


def check_database_duplicates(
    db_session: Session,
    parsed_rows: List[Dict[str, Any]],
    employee_id_map: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    """
    Memeriksa apakah transaksi sudah pernah tersimpan di tabel attendance_raw database.
    """
    # Kumpulkan tanggal-tanggal yang ada pada baris import untuk query batch yang efisien
    dates_to_check: Set[date] = set()
    for row in parsed_rows:
        if row.get("tanggal_obj"):
            dates_to_check.add(row["tanggal_obj"])

    if not dates_to_check:
        return parsed_rows

    # Ambil catatan existing di attendance_raw pada tanggal-tanggal tersebut
    existing_records = (
        db_session.query(AttendanceRaw)
        .filter(AttendanceRaw.tanggal.in_(list(dates_to_check)))
        .all()
    )

    existing_db_keys: Set[str] = set()
    for rec in existing_records:
        rec_key = make_transaction_key(
            emp_num=rec.emp_num,
            no_id=rec.no_id,
            nama=rec.nama,
            tgl=rec.tanggal,
            scan_masuk=rec.scan_masuk,
            scan_pulang=rec.scan_pulang,
        )
        existing_db_keys.add(rec_key)

    # Tandai baris yang cocok dengan existing_db_keys
    for row in parsed_rows:
        if not row.get("is_valid", False):
            row["is_duplicate_in_db"] = False
            continue

        key = make_transaction_key(
            emp_num=row.get("emp_num"),
            no_id=row.get("no_id"),
            nama=row.get("nama", ""),
            tgl=row.get("tanggal_obj"),
            scan_masuk=row.get("scan_masuk"),
            scan_pulang=row.get("scan_pulang"),
        )

        if key in existing_db_keys:
            row["is_duplicate_in_db"] = True
            row["duplicate_message"] = "Duplikat: Transaksi dengan waktu scan yang sama persis sudah ada di database."
        else:
            row["is_duplicate_in_db"] = False

    return parsed_rows
