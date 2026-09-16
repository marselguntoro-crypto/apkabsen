"""
Layanan Import dan Export Data Karyawan Excel/CSV untuk SIAP (Tahap 2).
Mendukung pemetaan kolom otomatis, validasi data, deteksi duplikasi ID/NIK,
preview sebelum eksekusi, opsi penanganan duplikasi (Lewati / Perbarui),
dan pencatatan riwayat transaksi ke ImportLog dan AuditLog.
"""
import os
import csv
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple

from database.connection import get_db_session
from database.models import Employee, EmployeeStatus, ImportLog, AuditLog
from utils.logger import get_logger
from utils.validators import validate_employee_payload

logger = get_logger("EmployeeImportService")

# Pemetaan sinonim nama kolom header Excel
HEADER_SYNONYMS = {
    "nama": ["nama", "nama karyawan", "nama lengkap", "employee name", "name", "karyawan"],
    "emp_num": ["emp num", "emp_num", "no pegawai", "nip", "nomor pegawai", "nik kantor", "emp id"],
    "no_id": ["no id", "no_id", "pin", "id mesin", "barcode", "badgenumber", "ac-no.", "enroll id", "id"],
    "nik": ["nik", "no ktp", "nomor ktp", "no. ktp", "national id"],
    "unit": ["unit", "unit kerja", "departemen", "department", "bagian", "divisi", "seksi"],
    "jabatan": ["jabatan", "position", "posisi", "title", "role"],
    "status": ["status", "status karyawan", "status kerja", "kepegawaian"],
    "email": ["email", "e-mail", "surel", "alamat email"],
    "tanggal_mulai": ["tanggal mulai", "tgl mulai", "tgl masuk", "hire date", "join date", "tanggal masuk"],
}


class EmployeeImportService:
    """Layanan pemrosesan file Excel dan CSV master karyawan."""

    @staticmethod
    def _normalize_header(header: str) -> str:
        """Membersihkan teks header untuk pencocokan sinonim."""
        return str(header).strip().lower().replace("_", " ").replace("-", " ")

    @classmethod
    def detect_column_mapping(cls, raw_headers: List[str]) -> Dict[str, Optional[int]]:
        """
        Mendeteksi indeks kolom dari daftar header file Excel berdasarkan kamus sinonim.
        """
        mapping: Dict[str, Optional[int]] = {key: None for key in HEADER_SYNONYMS}

        for col_idx, raw_header in enumerate(raw_headers):
            cleaned = cls._normalize_header(raw_header)
            for standard_key, synonyms in HEADER_SYNONYMS.items():
                if mapping[standard_key] is None and cleaned in synonyms:
                    mapping[standard_key] = col_idx
                    break

        return mapping

    @classmethod
    def read_file_rows(cls, file_path: str) -> Tuple[List[str], List[List[Any]], Optional[str]]:
        """
        Membaca header dan baris data dari file .xlsx, .xls, atau .csv.
        Mengembalikan (headers, rows, error_message).
        """
        if not os.path.exists(file_path):
            return [], [], f"Berkas tidak ditemukan: {file_path}"

        ext = os.path.splitext(file_path)[1].lower()

        # 1. Format Excel (.xlsx / .xls)
        if ext in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
            try:
                import openpyxl
                wb = openpyxl.load_workbook(file_path, data_only=True)
                sheet = wb.active
                all_rows = list(sheet.iter_rows(values_only=True))
                if not all_rows:
                    return [], [], "File Excel kosong tanpa lembar data."

                headers = [str(c or "").strip() for c in all_rows[0]]
                data_rows = [list(r) for r in all_rows[1:] if any(c is not None and str(c).strip() != "" for c in r)]
                return headers, data_rows, None
            except ImportError:
                # Coba via pandas jika openpyxl belum terhubung
                try:
                    import pandas as pd
                    df = pd.read_excel(file_path)
                    headers = [str(c).strip() for c in df.columns]
                    data_rows = df.values.tolist()
                    return headers, data_rows, None
                except Exception as e:
                    return [], [], f"Gagal membaca format Excel: {str(e)}"
            except Exception as e:
                return [], [], f"Gagal membaca file Excel: {str(e)}"

        # 2. Format CSV (.csv)
        elif ext == ".csv":
            try:
                with open(file_path, mode="r", encoding="utf-8-sig") as f:
                    # Deteksi delimiter (koma atau titik koma)
                    sample = f.read(2048)
                    f.seek(0)
                    delimiter = ";" if sample.count(";") > sample.count(",") else ","
                    reader = csv.reader(f, delimiter=delimiter)
                    all_rows = [row for row in reader if any(c.strip() for c in row)]

                if not all_rows:
                    return [], [], "File CSV kosong tanpa data."

                headers = [str(c).strip() for c in all_rows[0]]
                data_rows = all_rows[1:]
                return headers, data_rows, None
            except Exception as e:
                return [], [], f"Gagal membaca file CSV: {str(e)}"

        else:
            return [], [], f"Format berkas '{ext}' tidak didukung. Harap gunakan .xlsx atau .csv."

    @classmethod
    def preview_import(cls, file_path: str) -> Dict[str, Any]:
        """
        Melakukan pra-pemeriksaan data sebelum benar-benar diimport ke database.
        Mendeteksi baris valid, duplikasi terhadap database, dan kesalahan format.
        """
        headers, data_rows, err = cls.read_file_rows(file_path)
        if err:
            return {"success": False, "error": err}

        mapping = cls.detect_column_mapping(headers)
        if mapping.get("nama") is None:
            return {
                "success": False,
                "error": "Kolom 'Nama Karyawan' tidak ditemukan dalam file. Pastikan terdapat header seperti 'Nama' atau 'Nama Karyawan'.",
                "headers_found": headers,
            }

        # Muat identitas yang sudah ada di database untuk deteksi duplikasi cepat
        with get_db_session() as session:
            existing_emps = session.query(Employee.id, Employee.emp_num, Employee.no_id, Employee.nik, Employee.nama).all()
            existing_emp_nums = {e.emp_num: (e.id, e.nama) for e in existing_emps if e.emp_num}
            existing_no_ids = {e.no_id: (e.id, e.nama) for e in existing_emps if e.no_id}
            existing_niks = {e.nik: (e.id, e.nama) for e in existing_emps if e.nik}

        preview_items = []
        valid_count = 0
        dup_count = 0
        invalid_count = 0

        # Set pelacak duplikasi internal antar-baris di dalam file Excel itu sendiri
        seen_in_file_emp_num = set()
        seen_in_file_no_id = set()

        for idx, row in enumerate(data_rows):
            row_num = idx + 2  # Menghitung baris Excel (baris 1 adalah header)

            def get_val(key):
                col_idx = mapping.get(key)
                if col_idx is not None and col_idx < len(row):
                    val = row[col_idx]
                    if val is None:
                        return ""
                    # Handle float converted integers dari Excel (misal 1001.0 -> "1001")
                    if isinstance(val, float) and val.is_integer():
                        return str(int(val)).strip()
                    return str(val).strip()
                return ""

            nama = get_val("nama")
            emp_num = get_val("emp_num")
            no_id = get_val("no_id")
            nik = get_val("nik")
            unit = get_val("unit")
            jabatan = get_val("jabatan")
            email = get_val("email")
            status_str = get_val("status") or "AKTIF"
            tanggal_mulai = get_val("tanggal_mulai")

            row_errors = []
            is_duplicate = False
            duplicate_info = ""
            existing_db_id = None

            # Validasi Nama
            if not nama:
                row_errors.append("Nama kosong")

            # Cek Duplikasi ke Database
            if emp_num and emp_num in existing_emp_nums:
                is_duplicate = True
                existing_db_id = existing_emp_nums[emp_num][0]
                duplicate_info = f"No. Pegawai '{emp_num}' sudah dimiliki '{existing_emp_nums[emp_num][1]}'"
            elif no_id and no_id in existing_no_ids:
                is_duplicate = True
                existing_db_id = existing_no_ids[no_id][0]
                duplicate_info = f"No. ID '{no_id}' sudah dimiliki '{existing_no_ids[no_id][1]}'"
            elif nik and nik in existing_niks:
                is_duplicate = True
                existing_db_id = existing_niks[nik][0]
                duplicate_info = f"NIK '{nik}' sudah dimiliki '{existing_niks[nik][1]}'"

            # Cek Duplikasi dalam File Sendiri
            if emp_num:
                if emp_num in seen_in_file_emp_num:
                    row_errors.append(f"Duplikat No. Pegawai '{emp_num}' ganda dalam file")
                seen_in_file_emp_num.add(emp_num)

            if no_id:
                if no_id in seen_in_file_no_id:
                    row_errors.append(f"Duplikat No. ID '{no_id}' ganda dalam file")
                seen_in_file_no_id.add(no_id)

            status_item = "VALID"
            if row_errors:
                status_item = "INVALID"
                invalid_count += 1
            elif is_duplicate:
                status_item = "DUPLIKAT"
                dup_count += 1
            else:
                valid_count += 1

            preview_items.append({
                "row_number": row_num,
                "nama": nama,
                "emp_num": emp_num,
                "no_id": no_id,
                "nik": nik,
                "unit": unit or "-",
                "jabatan": jabatan or "-",
                "email": email or "-",
                "status": "NONAKTIF" if "NON" in status_str.upper() else "AKTIF",
                "tanggal_mulai": tanggal_mulai or "-",
                "import_status": status_item,
                "errors": "; ".join(row_errors),
                "duplicate_info": duplicate_info,
                "existing_id": existing_db_id,
            })

        return {
            "success": True,
            "total_rows": len(data_rows),
            "valid_rows": valid_count,
            "duplicate_rows": dup_count,
            "invalid_rows": invalid_count,
            "column_mapping": mapping,
            "headers_found": headers,
            "items": preview_items,
        }

    @classmethod
    def execute_import(
        cls,
        file_path: str,
        duplicate_mode: str = "SKIP",  # "SKIP" atau "UPDATE"
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Mengeksekusi import data ke dalam database.
        Mencatat status ke tabel ImportLog dan AuditLog.
        """
        preview = cls.preview_import(file_path)
        if not preview.get("success"):
            return preview

        items = preview["items"]
        file_name = os.path.basename(file_path)

        success_count = 0
        failed_count = 0
        skipped_dup_count = 0
        updated_dup_count = 0

        try:
            with get_db_session() as session:
                for item in items:
                    # Lewati jika baris data tidak valid
                    if item["import_status"] == "INVALID":
                        failed_count += 1
                        continue

                    # Penanganan duplikat
                    if item["import_status"] == "DUPLIKAT":
                        if duplicate_mode.upper() == "SKIP":
                            skipped_dup_count += 1
                            continue
                        elif duplicate_mode.upper() == "UPDATE" and item.get("existing_id"):
                            # Perbarui karyawan yang ada
                            emp = session.query(Employee).filter(Employee.id == item["existing_id"]).first()
                            if emp:
                                emp.nama = item["nama"]
                                if item["unit"] and item["unit"] != "-":
                                    emp.unit = item["unit"]
                                if item["jabatan"] and item["jabatan"] != "-":
                                    emp.jabatan = item["jabatan"]
                                if item["email"] and item["email"] != "-":
                                    emp.email = item["email"]
                                emp.updated_at = datetime.utcnow()
                                updated_dup_count += 1
                                success_count += 1
                            continue

                    # Data Baru (VALID)
                    tanggal_mulai = None
                    if item["tanggal_mulai"] and item["tanggal_mulai"] != "-":
                        try:
                            tanggal_mulai = datetime.strptime(item["tanggal_mulai"], "%Y-%m-%d").date()
                        except Exception:
                            tanggal_mulai = None

                    status_enum = EmployeeStatus.NONAKTIF if item["status"] == "NONAKTIF" else EmployeeStatus.AKTIF

                    new_emp = Employee(
                        emp_num=item["emp_num"] or None,
                        no_id=item["no_id"] or None,
                        nik=item["nik"] or None,
                        nama=item["nama"],
                        unit=item["unit"] if item["unit"] != "-" else None,
                        jabatan=item["jabatan"] if item["jabatan"] != "-" else None,
                        email=item["email"] if item["email"] != "-" else None,
                        status=status_enum,
                        tanggal_mulai=tanggal_mulai,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    session.add(new_emp)
                    success_count += 1

                # Catat ke tabel ImportLog
                import_log = ImportLog(
                    file_name=file_name,
                    import_type="EMPLOYEES",
                    total_rows=len(items),
                    success_rows=success_count,
                    failed_rows=failed_count,
                    duplicate_rows=skipped_dup_count + updated_dup_count,
                    status="SUCCESS" if failed_count == 0 else "PARTIAL_SUCCESS",
                    error_details=f"Sukses: {success_count}, Duplikat dilewati: {skipped_dup_count}, Duplikat diperbarui: {updated_dup_count}, Gagal: {failed_count}",
                    created_at=datetime.utcnow(),
                )
                session.add(import_log)

                # Catat ke tabel AuditLog
                audit = AuditLog(
                    user_id=user_id,
                    action="IMPORT_KARYAWAN",
                    module="EMPLOYEES",
                    description=(
                        f"Import data karyawan dari '{file_name}': {success_count} berhasil dimasukkan/diperbarui, "
                        f"{skipped_dup_count} duplikat dilewati, {failed_count} baris gagal."
                    ),
                    created_at=datetime.utcnow(),
                )
                session.add(audit)

            logger.info(f"Import karyawan selesai: {success_count} berhasil, {failed_count} gagal dari '{file_name}'.")

            return {
                "success": True,
                "file_name": file_name,
                "total_rows": len(items),
                "success_count": success_count,
                "failed_count": failed_count,
                "skipped_count": skipped_dup_count,
                "updated_count": updated_dup_count,
                "message": (
                    f"Import selesai! Berhasil memproses {success_count} data karyawan.\n"
                    f"- Ditambahkan / Diperbarui: {success_count}\n"
                    f"- Duplikat Dilewati: {skipped_dup_count}\n"
                    f"- Data Tidak Valid: {failed_count}"
                ),
            }
        except Exception as e:
            logger.error(f"Gagal mengeksekusi import data karyawan: {e}")
            return {
                "success": False,
                "error": f"Terjadi kesalahan saat menyimpan data import ke database: {str(e)}",
            }

    @staticmethod
    def export_employees(
        target_file_path: str,
        unit: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Mengekspor data karyawan ke file Excel (.xlsx) atau CSV (.csv).
        Dapat difilter berdasarkan unit, status, dan kata kunci pencarian.
        """
        try:
            from services.employee_service import EmployeeService
            # Ambil seluruh data sesuai filter tanpa batas paginasi
            result = EmployeeService.get_employees(
                search=search or "",
                unit=unit or "",
                status=status or "",
                page=1,
                per_page=100000,
            )
            employees = result.get("items", [])

            ext = os.path.splitext(target_file_path)[1].lower()

            headers = [
                "No",
                "No. ID / PIN",
                "No. Pegawai",
                "NIK",
                "Nama Lengkap",
                "Unit / Departemen",
                "Jabatan",
                "Email",
                "Status",
                "Tanggal Mulai",
                "Waktu Dibuat",
            ]

            rows_data = []
            for idx, emp in enumerate(employees, 1):
                rows_data.append([
                    idx,
                    emp.get("no_id") or "-",
                    emp.get("emp_num") or "-",
                    emp.get("nik") or "-",
                    emp.get("nama"),
                    emp.get("unit") or "-",
                    emp.get("jabatan") or "-",
                    emp.get("email") or "-",
                    emp.get("status"),
                    emp.get("tanggal_mulai") or "-",
                    emp.get("created_at") or "-",
                ])

            if ext == ".csv":
                # Tulis format CSV
                with open(target_file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f, delimiter=";")
                    writer.writerow(headers)
                    writer.writerows(rows_data)
            else:
                # Upayakan export ke Excel .xlsx dengan openpyxl
                try:
                    import openpyxl
                    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = "Master Karyawan SIAP"

                    # Header Styling
                    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
                    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Dark Blue
                    center_align = Alignment(horizontal="center", vertical="center")
                    left_align = Alignment(horizontal="left", vertical="center")
                    thin_border = Border(
                        left=Side(style="thin", color="E2E8F0"),
                        right=Side(style="thin", color="E2E8F0"),
                        top=Side(style="thin", color="E2E8F0"),
                        bottom=Side(style="thin", color="E2E8F0"),
                    )

                    # Tulis Header
                    ws.append(headers)
                    for col_num in range(1, len(headers) + 1):
                        cell = ws.cell(row=1, column=col_num)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = center_align
                        cell.border = thin_border
                    ws.row_dimensions[1].height = 28

                    # Tulis Baris Data
                    for row_idx, r_data in enumerate(rows_data, start=2):
                        ws.append(r_data)
                        for col_num in range(1, len(headers) + 1):
                            cell = ws.cell(row=row_idx, column=col_num)
                            cell.font = Font(name="Segoe UI", size=10)
                            cell.border = thin_border
                            if col_num in [1, 2, 3, 4, 9, 10]:
                                cell.alignment = center_align
                            else:
                                cell.alignment = left_align

                    # Auto-fit Column Width
                    for col in ws.columns:
                        max_len = max(len(str(cell.value or "")) for cell in col)
                        col_letter = col[0].column_letter
                        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

                    wb.save(target_file_path)
                except ImportError:
                    # Fallback ke format CSV jika openpyxl tidak ada
                    with open(target_file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f, delimiter=";")
                        writer.writerow(headers)
                        writer.writerows(rows_data)

            # Audit Log
            with get_db_session() as session:
                audit = AuditLog(
                    user_id=user_id,
                    action="EXPORT_KARYAWAN",
                    module="EMPLOYEES",
                    description=f"Export data master karyawan ({len(employees)} baris) ke file '{os.path.basename(target_file_path)}'.",
                    created_at=datetime.utcnow(),
                )
                session.add(audit)

            logger.info(f"Export data karyawan berhasil: {len(employees)} baris diekspor ke {target_file_path}.")
            return True, None
        except Exception as e:
            logger.error(f"Gagal mengekspor data karyawan: {e}")
            return False, f"Terjadi kesalahan saat mengekspor data: {str(e)}"
