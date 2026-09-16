"""
Modul validasi input aplikasi SIAP.
Menyediakan validasi format jam, nominal potongan, kredensial, dan rentang nilai.
"""
import re
from typing import Tuple, Optional


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """Validasi username pengguna."""
    if not username or not username.strip():
        return False, "Username tidak boleh kosong."
    username = username.strip()
    if len(username) < 3:
        return False, "Username minimal 3 karakter."
    if len(username) > 50:
        return False, "Username maksimal 50 karakter."
    if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
        return False, "Username hanya boleh mengandung huruf, angka, garis bawah (_), titik (.), dan strip (-)."
    return True, None


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """Validasi kekuatan password pengguna."""
    if not password:
        return False, "Password tidak boleh kosong."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."
    if len(password) > 100:
        return False, "Password maksimal 100 karakter."
    return True, None


def validate_time_format(time_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validasi string jam dengan format HH:MM (24-jam).
    Contoh valid: '08:15', '16:30', '17:00'.
    """
    if not time_str or not time_str.strip():
        return False, "Waktu tidak boleh kosong."
    time_str = time_str.strip()
    match = re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", time_str)
    if not match:
        return False, "Format jam harus HH:MM (contoh: 08:15 atau 16:30)."
    return True, None


def validate_positive_integer(value_str: str, field_name: str = "Nilai") -> Tuple[bool, Optional[int], Optional[str]]:
    """Validasi integer non-negatif (contoh: tarif potongan rupiah)."""
    if not value_str or not str(value_str).strip():
        return False, None, f"{field_name} tidak boleh kosong."
    val_cleaned = str(value_str).strip().replace(".", "").replace(",", "")
    try:
        val = int(val_cleaned)
        if val < 0:
            return False, None, f"{field_name} tidak boleh bernilai negatif."
        return True, val, None
    except ValueError:
        return False, None, f"{field_name} harus berupa angka bulat yang valid."


def validate_target_days(value_str: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Validasi target hari kerja bulanan (antara 1 s/d 31 hari)."""
    success, val, err = validate_positive_integer(value_str, "Target hari kerja")
    if not success:
        return False, None, err
    if val < 1 or val > 31:
        return False, None, "Target hari kerja bulanan harus antara 1 sampai 31 hari."
    return True, val, None


def validate_email(email_str: str) -> Tuple[bool, Optional[str]]:
    """Validasi format alamat email jika diisi."""
    if not email_str or not email_str.strip():
        return True, None  # Email bersifat opsional
    email_str = email_str.strip()
    if len(email_str) > 150:
        return False, "Email tidak boleh melebihi 150 karakter."
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, email_str):
        return False, "Format email tidak valid (contoh: nama@perusahaan.com)."
    return True, None


def validate_date_string(date_str: str) -> Tuple[bool, Optional[str]]:
    """Validasi format tanggal YYYY-MM-DD jika diisi."""
    if not date_str or not date_str.strip():
        return True, None  # Tanggal bersifat opsional
    date_str = date_str.strip()
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return True, None
    except ValueError:
        return False, "Format tanggal harus YYYY-MM-DD (contoh: 2025-01-15)."


def validate_employee_payload(data: dict) -> Tuple[bool, list]:
    """
    Validasi seluruh payload input master data karyawan.
    Mengembalikan tuple (is_valid, error_list).
    """
    errors = []

    # 1. Validasi Nama (Wajib)
    nama = str(data.get("nama", "")).strip()
    if not nama:
        errors.append("Nama karyawan wajib diisi.")
    elif len(nama) < 2:
        errors.append("Nama karyawan minimal 2 karakter.")
    elif len(nama) > 150:
        errors.append("Nama karyawan maksimal 150 karakter.")

    # 2. Validasi Identitas (Minimal salah satu dari emp_num, no_id, atau nik dianjurkan)
    emp_num = str(data.get("emp_num", "")).strip()
    if emp_num and len(emp_num) > 50:
        errors.append("No. Pegawai (emp_num) maksimal 50 karakter.")

    no_id = str(data.get("no_id", "")).strip()
    if no_id and len(no_id) > 50:
        errors.append("No. Mesin / Barcode (no_id) maksimal 50 karakter.")

    nik = str(data.get("nik", "")).strip()
    if nik and len(nik) > 50:
        errors.append("NIK maksimal 50 karakter.")

    # 3. Unit / Departemen
    unit = str(data.get("unit", "")).strip()
    if unit and len(unit) > 100:
        errors.append("Unit/Departemen maksimal 100 karakter.")

    # 4. Jabatan
    jabatan = str(data.get("jabatan", "")).strip()
    if jabatan and len(jabatan) > 100:
        errors.append("Jabatan maksimal 100 karakter.")

    # 5. Email (Opsional)
    email = str(data.get("email", "")).strip()
    if email:
        valid_email, email_err = validate_email(email)
        if not valid_email:
            errors.append(email_err)

    # 6. Tanggal Mulai (Opsional)
    tgl_mulai = str(data.get("tanggal_mulai", "")).strip()
    if tgl_mulai and tgl_mulai != "-":
        valid_date, date_err = validate_date_string(tgl_mulai)
        if not valid_date:
            errors.append(date_err)

    return len(errors) == 0, errors
