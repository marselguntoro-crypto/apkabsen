"""
Modul Layanan Validasi Import Absensi Excel untuk Aplikasi SIAP.
Mencakup:
1. Deteksi dan normalisasi header kolom secara adaptif.
2. Validasi kolom wajib (Nama, Tanggal) dan identitas (Emp Num, No. ID).
3. Identifikasi karyawan di database dengan prioritas bertingkat:
   (1) Emp Num. + No. ID.
   (2) Emp Num.
   (3) No. ID.
4. Validasi tanggal presisi tinggi (DD/MM/YYYY day-first).
5. Validasi jam scan masuk dan pulang (kosong diperbolehkan untuk data mentah).
6. Penandaan status baris: VALID, INVALID, DUPLICATE, NOT_FOUND.
"""
import re
from typing import Dict, Any, List, Tuple, Optional, Set
from datetime import date
from sqlalchemy.orm import Session
from database.models import Employee, EmployeeStatus
from utils.date_parser import parse_date_value, format_date_display
from utils.time_parser import parse_time_value, format_time_display
from utils.duplicate_detector import check_in_file_duplicates, check_database_duplicates
from utils.logger import get_logger

logger = get_logger("ImportValidationService")


# Kamus sinonim header kolom untuk normalisasi
HEADER_SYNONYMS = {
    "emp_num": [
        "emp num.", "emp num", "emp_num", "empnum",
        "no pegawai", "no. pegawai", "nomor pegawai", "nip", "no_pegawai"
    ],
    "no_id": [
        "no. id.", "no. id", "no_id", "noid", "no id",
        "pin", "id mesin", "id_mesin", "pin mesin", "no id."
    ],
    "nik": [
        "nik", "no. nik", "nomor induk kependudukan", "no ktp", "no_ktp"
    ],
    "nama": [
        "nama", "nama karyawan", "nama lengkap", "employee name",
        "nama pegawai", "nama_karyawan"
    ],
    "tanggal": [
        "tanggal", "date", "tgl", "tgl.", "tanggal scan", "tgl scan"
    ],
    "scan_masuk": [
        "scan masuk", "scan_masuk", "jam masuk", "jam_masuk",
        "masuk", "check in", "check_in", "in", "waktu masuk"
    ],
    "scan_pulang": [
        "scan pulang", "scan_pulang", "jam pulang", "jam_pulang",
        "pulang", "check out", "check_out", "out", "waktu pulang"
    ],
}


def normalize_header_string(header: str) -> str:
    """Normalisasi string header: lowercase, hilangkan spasi ganda, titik dan strip."""
    if not header:
        return ""
    # Ganti newline dan spasi ganda
    cleaned = re.sub(r"\s+", " ", str(header).strip().lower())
    return cleaned


def map_excel_headers(raw_headers: List[str]) -> Tuple[Dict[str, str], List[str], List[str]]:
    """
    Memetakan header berkas Excel ke field internal SIAP.

    Returns:
        (mapped_fields, missing_required_fields, warnings)
        - mapped_fields: {internal_field_key: original_excel_header}
        - missing_required_fields: list nama kolom wajib yang tidak ditemukan
        - warnings: catatan jika ada identitas yang tidak lengkap
    """
    mapped: Dict[str, str] = {}
    normalized_to_original = {normalize_header_string(h): h for h in raw_headers}

    for target_key, synonyms in HEADER_SYNONYMS.items():
        for syn in synonyms:
            # 1. Cek kecocokan eksak normalisasi
            if syn in normalized_to_original:
                mapped[target_key] = normalized_to_original[syn]
                break
            # 2. Cek variasi tanda titik atau underscore
            syn_no_punct = syn.replace(".", "").replace("_", "").replace(" ", "")
            for norm_key, orig in normalized_to_original.items():
                norm_no_punct = norm_key.replace(".", "").replace("_", "").replace(" ", "")
                if syn_no_punct == norm_no_punct:
                    mapped[target_key] = orig
                    break
            if target_key in mapped:
                break

    # Validasi Kolom Wajib
    missing_required = []
    if "nama" not in mapped:
        missing_required.append("Nama")
    if "tanggal" not in mapped:
        missing_required.append("Tanggal")

    warnings = []
    # Validasi Kolom Identitas (Emp Num atau No ID harus ada salah satu)
    if "emp_num" not in mapped and "no_id" not in mapped:
        warnings.append("Kolom identitas (Emp Num. atau No. ID.) tidak ditemukan. Pencocokan akan mengandalkan nama karyawan.")

    # Validasi Kolom Jam Scan
    if "scan_masuk" not in mapped and "scan_pulang" not in mapped:
        warnings.append("Kolom Scan Masuk maupun Scan Pulang tidak ditemukan di berkas.")

    return mapped, missing_required, warnings


class ImportValidationService:
    """Layanan validasi baris transaksi absensi Excel."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self._employee_cache: Dict[str, Optional[Employee]] = {}
        self._preload_employees()

    def _preload_employees(self):
        """Memuat seluruh data master karyawan ke memori untuk pencocokan cepat tanpa query N kali."""
        employees = self.db.query(Employee).all()
        self.employees_by_pair: Dict[Tuple[str, str], Employee] = {}
        self.employees_by_emp_num: Dict[str, Employee] = {}
        self.employees_by_no_id: Dict[str, Employee] = {}
        self.employees_by_name: Dict[str, Employee] = {}

        for emp in employees:
            e_num = (emp.emp_num or "").strip()
            n_id = (emp.no_id or "").strip()
            nama = emp.nama.strip().lower()

            if e_num and n_id:
                self.employees_by_pair[(e_num, n_id)] = emp
            if e_num:
                self.employees_by_emp_num[e_num] = emp
            if n_id:
                self.employees_by_no_id[n_id] = emp
            if nama:
                self.employees_by_name[nama] = emp

    def match_employee(self, emp_num: Optional[str], no_id: Optional[str], nama: str) -> Tuple[Optional[Employee], str]:
        """
        Mencocokkan baris data dengan master employees sesuai aturan prioritas:
        1. Emp Num. + No. ID.
        2. Emp Num.
        3. No. ID.
        4. Nama (opsional sebagai informasi fallback jika unik)
        """
        e_num = (emp_num or "").strip()
        n_id = (no_id or "").strip()
        clean_nama = (nama or "").strip().lower()

        # Prioritas 1: Emp Num. + No. ID.
        if e_num and n_id and (e_num, n_id) in self.employees_by_pair:
            return self.employees_by_pair[(e_num, n_id)], "MATCH_PAIR"

        # Prioritas 2: Emp Num.
        if e_num and e_num in self.employees_by_emp_num:
            return self.employees_by_emp_num[e_num], "MATCH_EMP_NUM"

        # Prioritas 3: No. ID.
        if n_id and n_id in self.employees_by_no_id:
            return self.employees_by_no_id[n_id], "MATCH_NO_ID"

        # Prioritas 4: Nama eksak
        if clean_nama and clean_nama in self.employees_by_name:
            return self.employees_by_name[clean_nama], "MATCH_NAME"

        return None, "NOT_FOUND"

    def validate_rows(
        self,
        raw_rows: List[Dict[str, Any]],
        header_mapping: Dict[str, str],
        source_filename: str = ""
    ) -> Dict[str, Any]:
        """
        Melakukan validasi lengkap seluruh baris transaksi Excel.
        """
        validated_rows = []
        total_rows = len(raw_rows)
        valid_count = 0
        invalid_count = 0
        duplicate_count = 0
        empty_jam_count = 0
        unmatched_employee_count = 0

        # Ambil nama kolom asli dari hasil mapping
        col_emp = header_mapping.get("emp_num")
        col_id = header_mapping.get("no_id")
        col_nik = header_mapping.get("nik")
        col_nama = header_mapping.get("nama")
        col_tgl = header_mapping.get("tanggal")
        col_masuk = header_mapping.get("scan_masuk")
        col_pulang = header_mapping.get("scan_pulang")

        for row_idx, row in enumerate(raw_rows, 1):
            excel_line_number = row_idx + 1  # Baris 1 adalah header di Excel

            # Ekstrak nilai sel mentah
            raw_emp = str(row.get(col_emp, "") or "").strip() if col_emp else ""
            raw_id = str(row.get(col_id, "") or "").strip() if col_id else ""
            raw_nik = str(row.get(col_nik, "") or "").strip() if col_nik else ""
            raw_nama = str(row.get(col_nama, "") or "").strip() if col_nama else ""
            raw_tgl = row.get(col_tgl) if col_tgl else None
            raw_masuk = row.get(col_masuk) if col_masuk else None
            raw_pulang = row.get(col_pulang) if col_pulang else None

            # Bersihkan tanda desimal jika terbaca float (misal "1.0" -> "1")
            if raw_emp.endswith(".0") and raw_emp[:-2].isdigit():
                raw_emp = raw_emp[:-2]
            if raw_id.endswith(".0") and raw_id[:-2].isdigit():
                raw_id = raw_id[:-2]
            if raw_nik.endswith(".0") and raw_nik[:-2].isdigit():
                raw_nik = raw_nik[:-2]

            row_errors: List[str] = []
            row_warnings: List[str] = []

            # 1. Validasi Nama (Wajib & Pertahankan karakter asli tanpa pemotongan / forced uppercase)
            if not raw_nama:
                row_errors.append("Nama karyawan wajib diisi.")

            # 2. Validasi Tanggal (DD/MM/YYYY day-first, YYYY-MM-DD, dll.)
            parsed_date, date_err = parse_date_value(raw_tgl)
            if date_err:
                row_errors.append(date_err)

            # 3. Validasi Jam Masuk & Pulang
            time_masuk_str, masuk_empty, masuk_err = parse_time_value(raw_masuk)
            if masuk_err:
                row_errors.append(f"Scan Masuk: {masuk_err}")

            time_pulang_str, pulang_empty, pulang_err = parse_time_value(raw_pulang)
            if pulang_err:
                row_errors.append(f"Scan Pulang: {pulang_err}")

            if masuk_empty and pulang_empty:
                empty_jam_count += 1
                row_warnings.append("Scan masuk dan scan pulang keduanya kosong.")
            elif masuk_empty:
                empty_jam_count += 1
                row_warnings.append("Scan masuk kosong (transaksi tetap disimpan).")
            elif pulang_empty:
                empty_jam_count += 1
                row_warnings.append("Scan pulang kosong (transaksi tetap disimpan).")

            # 4. Pencocokan Karyawan
            matched_emp, match_type = self.match_employee(raw_emp, raw_id, raw_nama)
            employee_id = matched_emp.id if matched_emp else None
            if not matched_emp:
                unmatched_employee_count += 1
                row_warnings.append("Karyawan tidak ditemukan di Master Data Karyawan.")

            # Tentukan status baris
            is_valid = len(row_errors) == 0
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1

            status_text = "VALID" if is_valid else "INVALID"
            if is_valid and not matched_emp:
                status_text = "TIDAK DITEMUKAN"
            elif is_valid and (masuk_empty or pulang_empty):
                status_text = "VALID (JAM KOSONG)"

            # Kompilasi keterangan gabungan
            keterangan_list = row_errors + row_warnings
            keterangan = "; ".join(keterangan_list) if keterangan_list else "Data siap di-import."

            validated_rows.append({
                "no": row_idx,
                "excel_line": excel_line_number,
                "emp_num": raw_emp,
                "no_id": raw_id,
                "nik": raw_nik,
                "nama": raw_nama,
                "tanggal_raw": str(raw_tgl or ""),
                "tanggal_obj": parsed_date,
                "tanggal_display": format_date_display(parsed_date),
                "scan_masuk_raw": str(raw_masuk or ""),
                "scan_masuk": time_masuk_str,
                "scan_masuk_display": format_time_display(time_masuk_str),
                "scan_pulang_raw": str(raw_pulang or ""),
                "scan_pulang": time_pulang_str,
                "scan_pulang_display": format_time_display(time_pulang_str),
                "is_valid": is_valid,
                "status": status_text,
                "errors": row_errors,
                "warnings": row_warnings,
                "keterangan": keterangan,
                "employee_id": employee_id,
                "matched_emp_nama": matched_emp.nama if matched_emp else None,
                "matched_type": match_type,
                "is_duplicate_in_file": False,
                "is_duplicate_in_db": False,
                "has_empty_jam": masuk_empty or pulang_empty,
            })

        # 5. Jalankan Deteksi Duplikat (Internal file & Database)
        validated_rows = check_in_file_duplicates(validated_rows)
        validated_rows = check_database_duplicates(self.db, validated_rows)

        # Hitung ulang jumlah duplikat dan sesuaikan status
        for r in validated_rows:
            if r["is_duplicate_in_file"] or r["is_duplicate_in_db"]:
                duplicate_count += 1
                if r["is_valid"]:
                    r["status"] = "DUPLIKAT"
                    msg = r.get("duplicate_message", "Transaksi terdeteksi duplikat.")
                    r["keterangan"] = f"{msg} | {r['keterangan']}".strip(" |")

        return {
            "source_file": source_filename,
            "total_rows": total_rows,
            "valid_rows_count": valid_count,
            "invalid_rows_count": invalid_count,
            "duplicate_rows_count": duplicate_count,
            "empty_jam_count": empty_jam_count,
            "unmatched_employee_count": unmatched_employee_count,
            "rows": validated_rows,
            "header_mapping": header_mapping,
        }
