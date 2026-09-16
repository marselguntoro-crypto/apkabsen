"""
Layanan Master Data Karyawan SIAP (Tahap 2).
Menyediakan operasi CRUD lengkap, pencarian kata kunci, multi-filter,
paginasi, deteksi duplikasi ID/NIK, soft delete (nonaktifkan), proteksi hapus permanen,
dan pencatatan audit trail aktivitas pengguna.
"""
import math
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import func, or_, desc, asc

from database.connection import get_db_session
from database.models import (
    Employee,
    EmployeeStatus,
    AttendanceRaw,
    AttendanceDaily,
    AuditLog,
)
from utils.logger import get_logger
from utils.validators import validate_employee_payload

logger = get_logger("EmployeeService")


class EmployeeService:
    """Service pengelola master data karyawan dan aturan integritas data."""

    @staticmethod
    def get_employees(
        search: str = "",
        unit: str = "",
        jabatan: str = "",
        status: str = "",
        page: int = 1,
        per_page: int = 15,
        sort_by: str = "nama",
        sort_dir: str = "asc",
    ) -> Dict[str, Any]:
        """
        Mengambil daftar karyawan dengan filter, pencarian, pengurutan, dan paginasi.
        """
        page = max(1, page)
        per_page = max(1, min(per_page, 200))

        with get_db_session() as session:
            query = session.query(Employee)

            # 1. Pencarian Kata Kunci (Nama, Emp Num, No ID, NIK)
            if search and search.strip():
                keyword = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        Employee.nama.ilike(keyword),
                        Employee.emp_num.ilike(keyword),
                        Employee.no_id.ilike(keyword),
                        Employee.nik.ilike(keyword),
                        Employee.unit.ilike(keyword),
                        Employee.jabatan.ilike(keyword),
                    )
                )

            # 2. Filter Unit / Departemen
            if unit and unit.strip() and unit != "Semua Unit":
                query = query.filter(Employee.unit == unit.strip())

            # 3. Filter Jabatan
            if jabatan and jabatan.strip() and jabatan != "Semua Jabatan":
                query = query.filter(Employee.jabatan == jabatan.strip())

            # 4. Filter Status
            if status and status.strip() and status != "Semua Status":
                status_clean = status.strip().upper()
                if status_clean in [EmployeeStatus.AKTIF.value, "AKTIF"]:
                    query = query.filter(Employee.status == EmployeeStatus.AKTIF)
                elif status_clean in [EmployeeStatus.NONAKTIF.value, "NONAKTIF"]:
                    query = query.filter(Employee.status == EmployeeStatus.NONAKTIF)

            # Hitung total hasil yang cocok
            total_records = query.count()
            total_pages = max(1, math.ceil(total_records / per_page))

            # 5. Pengurutan Data
            sort_column = getattr(Employee, sort_by, Employee.nama)
            if sort_dir.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

            # 6. Paginasi
            offset = (page - 1) * per_page
            items = query.offset(offset).limit(per_page).all()

            return {
                "items": [item.to_dict() for item in items],
                "total": total_records,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }

    @staticmethod
    def get_employee_by_id(emp_id: int) -> Optional[Dict[str, Any]]:
        """Mencari satu data karyawan berdasarkan ID primer."""
        with get_db_session() as session:
            emp = session.query(Employee).filter(Employee.id == emp_id).first()
            return emp.to_dict() if emp else None

    @staticmethod
    def check_duplicate(
        emp_num: Optional[str] = None,
        no_id: Optional[str] = None,
        nik: Optional[str] = None,
        exclude_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Memeriksa apakah No Pegawai (emp_num), No Mesin (no_id), atau NIK sudah digunakan.
        Mengembalikan (is_duplicate, conflict_field, conflict_info).
        """
        with get_db_session() as session:
            # Periksa emp_num
            if emp_num and str(emp_num).strip():
                val = str(emp_num).strip()
                q = session.query(Employee).filter(Employee.emp_num == val)
                if exclude_id:
                    q = q.filter(Employee.id != exclude_id)
                existing = q.first()
                if existing:
                    return True, "emp_num", f"No. Pegawai '{val}' sudah digunakan oleh karyawan: {existing.nama}"

            # Periksa no_id
            if no_id and str(no_id).strip():
                val = str(no_id).strip()
                q = session.query(Employee).filter(Employee.no_id == val)
                if exclude_id:
                    q = q.filter(Employee.id != exclude_id)
                existing = q.first()
                if existing:
                    return True, "no_id", f"No. ID / PIN '{val}' sudah digunakan oleh karyawan: {existing.nama}"

            # Periksa NIK (jika diisi)
            if nik and str(nik).strip():
                val = str(nik).strip()
                q = session.query(Employee).filter(Employee.nik == val)
                if exclude_id:
                    q = q.filter(Employee.id != exclude_id)
                existing = q.first()
                if existing:
                    return True, "nik", f"NIK '{val}' sudah digunakan oleh karyawan: {existing.nama}"

        return False, None, None

    @staticmethod
    def create_employee(data: dict, user_id: Optional[int] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Menambahkan data karyawan baru ke database.
        Mencakup validasi, deteksi duplikasi, dan pencatatan audit log.
        """
        # 1. Validasi Payload
        is_valid, errors = validate_employee_payload(data)
        if not is_valid:
            return False, None, "; ".join(errors)

        # 2. Cek Duplikasi
        emp_num = data.get("emp_num") or None
        no_id = data.get("no_id") or None
        nik = data.get("nik") or None
        is_dup, field, dup_msg = EmployeeService.check_duplicate(emp_num=emp_num, no_id=no_id, nik=nik)
        if is_dup:
            return False, None, dup_msg

        # 3. Parsing Tanggal Mulai
        tanggal_mulai = None
        tgl_str = data.get("tanggal_mulai")
        if tgl_str and str(tgl_str).strip() and str(tgl_str).strip() != "-":
            try:
                if isinstance(tgl_str, date):
                    tanggal_mulai = tgl_str
                else:
                    tanggal_mulai = datetime.strptime(str(tgl_str).strip(), "%Y-%m-%d").date()
            except ValueError:
                return False, None, "Format tanggal mulai harus YYYY-MM-DD."

        # 4. Parsing Status
        status_val = data.get("status", EmployeeStatus.AKTIF)
        if isinstance(status_val, str):
            status_val = EmployeeStatus.NONAKTIF if status_val.upper() == "NONAKTIF" else EmployeeStatus.AKTIF

        try:
            with get_db_session() as session:
                new_emp = Employee(
                    emp_num=str(emp_num).strip() if emp_num else None,
                    no_id=str(no_id).strip() if no_id else None,
                    nik=str(nik).strip() if nik else None,
                    nama=str(data.get("nama")).strip(),
                    unit=str(data.get("unit")).strip() if data.get("unit") else None,
                    jabatan=str(data.get("jabatan")).strip() if data.get("jabatan") else None,
                    email=str(data.get("email")).strip() if data.get("email") else None,
                    keterangan=str(data.get("keterangan")).strip() if data.get("keterangan") else None,
                    status=status_val,
                    tanggal_mulai=tanggal_mulai,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(new_emp)
                session.flush()

                # Audit Log
                audit = AuditLog(
                    user_id=user_id,
                    action="TAMBAH_KARYAWAN",
                    module="EMPLOYEES",
                    description=f"Menambahkan karyawan baru: '{new_emp.nama}' (ID: {new_emp.id}, Unit: {new_emp.unit or '-'}).",
                    created_at=datetime.utcnow(),
                )
                session.add(audit)

                result_dict = new_emp.to_dict()
                logger.info(f"Karyawan berhasil dibuat: {new_emp.nama} [ID: {new_emp.id}].")
                return True, result_dict, None
        except Exception as e:
            logger.error(f"Gagal menambahkan karyawan: {e}")
            return False, None, f"Terjadi kesalahan sistem saat menyimpan data: {str(e)}"

    @staticmethod
    def update_employee(emp_id: int, data: dict, user_id: Optional[int] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Memperbarui data karyawan yang sudah ada.
        """
        # 1. Validasi Payload
        is_valid, errors = validate_employee_payload(data)
        if not is_valid:
            return False, None, "; ".join(errors)

        # 2. Cek Duplikasi (Kecualikan ID sendiri)
        emp_num = data.get("emp_num") or None
        no_id = data.get("no_id") or None
        nik = data.get("nik") or None
        is_dup, field, dup_msg = EmployeeService.check_duplicate(emp_num=emp_num, no_id=no_id, nik=nik, exclude_id=emp_id)
        if is_dup:
            return False, None, dup_msg

        # 3. Parsing Tanggal Mulai
        tanggal_mulai = None
        tgl_str = data.get("tanggal_mulai")
        if tgl_str and str(tgl_str).strip() and str(tgl_str).strip() != "-":
            try:
                if isinstance(tgl_str, date):
                    tanggal_mulai = tgl_str
                else:
                    tanggal_mulai = datetime.strptime(str(tgl_str).strip(), "%Y-%m-%d").date()
            except ValueError:
                return False, None, "Format tanggal mulai harus YYYY-MM-DD."

        # 4. Parsing Status
        status_val = None
        if "status" in data and data["status"]:
            s = data["status"]
            if isinstance(s, EmployeeStatus):
                status_val = s
            else:
                status_val = EmployeeStatus.NONAKTIF if str(s).upper() == "NONAKTIF" else EmployeeStatus.AKTIF

        try:
            with get_db_session() as session:
                emp = session.query(Employee).filter(Employee.id == emp_id).first()
                if not emp:
                    return False, None, f"Karyawan dengan ID {emp_id} tidak ditemukan."

                # Update data
                emp.nama = str(data.get("nama")).strip()
                emp.emp_num = str(emp_num).strip() if emp_num else None
                emp.no_id = str(no_id).strip() if no_id else None
                emp.nik = str(nik).strip() if nik else None
                emp.unit = str(data.get("unit")).strip() if data.get("unit") else None
                emp.jabatan = str(data.get("jabatan")).strip() if data.get("jabatan") else None
                emp.email = str(data.get("email")).strip() if data.get("email") else None
                emp.keterangan = str(data.get("keterangan")).strip() if data.get("keterangan") else None
                emp.tanggal_mulai = tanggal_mulai
                if status_val:
                    emp.status = status_val
                emp.updated_at = datetime.utcnow()

                # Audit Log
                audit = AuditLog(
                    user_id=user_id,
                    action="EDIT_KARYAWAN",
                    module="EMPLOYEES",
                    description=f"Memperbarui data karyawan ID {emp.id} ('{emp.nama}', Unit: {emp.unit or '-'}).",
                    created_at=datetime.utcnow(),
                )
                session.add(audit)

                result_dict = emp.to_dict()
                logger.info(f"Karyawan ID {emp_id} berhasil diperbarui: {emp.nama}.")
                return True, result_dict, None
        except Exception as e:
            logger.error(f"Gagal memperbarui data karyawan ID {emp_id}: {e}")
            return False, None, f"Gagal memperbarui data: {str(e)}"

    @staticmethod
    def toggle_status(emp_id: int, user_id: Optional[int] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Mengubah status kepegawaian (Soft Delete: AKTIF <-> NONAKTIF).
        Karyawan nonaktif tetap tersimpan di database untuk menjaga riwayat absensi.
        """
        try:
            with get_db_session() as session:
                emp = session.query(Employee).filter(Employee.id == emp_id).first()
                if not emp:
                    return False, None, f"Karyawan ID {emp_id} tidak ditemukan."

                old_status = emp.status
                new_status = EmployeeStatus.NONAKTIF if old_status == EmployeeStatus.AKTIF else EmployeeStatus.AKTIF
                emp.status = new_status
                emp.updated_at = datetime.utcnow()

                action_name = "NONAKTIFKAN_KARYAWAN" if new_status == EmployeeStatus.NONAKTIF else "AKTIFKAN_KARYAWAN"
                audit = AuditLog(
                    user_id=user_id,
                    action=action_name,
                    module="EMPLOYEES",
                    description=f"Status karyawan '{emp.nama}' diubah dari {old_status.value} menjadi {new_status.value}.",
                    created_at=datetime.utcnow(),
                )
                session.add(audit)

                logger.info(f"Status karyawan '{emp.nama}' diubah menjadi {new_status.value}.")
                return True, new_status.value, None
        except Exception as e:
            logger.error(f"Gagal mengubah status karyawan ID {emp_id}: {e}")
            return False, None, str(e)

    @staticmethod
    def delete_employee(emp_id: int, user_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Menghapus karyawan secara permanen dengan proteksi integritas data relasi.
        Jika karyawan telah memiliki riwayat absensi (AttendanceRaw atau AttendanceDaily),
        penghapusan ditolak untuk melindungi data riwayat absensi & penggajian.
        """
        try:
            with get_db_session() as session:
                emp = session.query(Employee).filter(Employee.id == emp_id).first()
                if not emp:
                    return False, f"Karyawan dengan ID {emp_id} tidak ditemukan."

                # Periksa relasi di data absensi mentah & harian
                raw_count = session.query(func.count(AttendanceRaw.id)).filter(AttendanceRaw.employee_id == emp_id).scalar() or 0
                daily_count = session.query(func.count(AttendanceDaily.id)).filter(AttendanceDaily.employee_id == emp_id).scalar() or 0

                total_related = raw_count + daily_count
                if total_related > 0:
                    return False, (
                        f"Karyawan '{emp.nama}' tidak dapat dihapus permanen karena sudah memiliki {total_related} "
                        f"riwayat catatan absensi ({raw_count} scan mentah, {daily_count} kalkulasi harian).\n\n"
                        f"Untuk menjaga integritas rekapitulasi, silakan gunakan fitur 'Nonaktifkan Karyawan'."
                    )

                emp_name = emp.nama
                session.delete(emp)

                # Audit Log
                audit = AuditLog(
                    user_id=user_id,
                    action="HAPUS_KARYAWAN",
                    module="EMPLOYEES",
                    description=f"Menghapus permanen karyawan: '{emp_name}' (ID: {emp_id}).",
                    created_at=datetime.utcnow(),
                )
                session.add(audit)

                logger.info(f"Karyawan '{emp_name}' [ID: {emp_id}] berhasil dihapus permanen.")
                return True, None
        except Exception as e:
            logger.error(f"Gagal menghapus karyawan ID {emp_id}: {e}")
            return False, f"Gagal menghapus data karyawan: {str(e)}"

    @staticmethod
    def get_statistics() -> Dict[str, int]:
        """
        Mengambil statistik ringkas master data karyawan untuk kartu metrik header.
        - Total Karyawan
        - Karyawan Aktif
        - Karyawan Nonaktif
        - Belum Memiliki NIK
        """
        with get_db_session() as session:
            total = session.query(func.count(Employee.id)).scalar() or 0
            aktif = (
                session.query(func.count(Employee.id))
                .filter(Employee.status == EmployeeStatus.AKTIF)
                .scalar()
                or 0
            )
            nonaktif = (
                session.query(func.count(Employee.id))
                .filter(Employee.status == EmployeeStatus.NONAKTIF)
                .scalar()
                or 0
            )
            tanpa_nik = (
                session.query(func.count(Employee.id))
                .filter(or_(Employee.nik.is_(None), Employee.nik == ""))
                .scalar()
                or 0
            )

            return {
                "total_karyawan": total,
                "aktif": aktif,
                "nonaktif": nonaktif,
                "tanpa_nik": tanpa_nik,
            }

    @staticmethod
    def get_distinct_units() -> List[str]:
        """Mengambil daftar nama Unit/Departemen unik yang ada di database."""
        with get_db_session() as session:
            units = (
                session.query(Employee.unit)
                .filter(Employee.unit.isnot(None), Employee.unit != "")
                .distinct()
                .order_by(Employee.unit)
                .all()
            )
            return [u[0] for u in units if u[0]]

    @staticmethod
    def get_distinct_jabatans() -> List[str]:
        """Mengambil daftar Jabatan unik yang ada di database."""
        with get_db_session() as session:
            jabs = (
                session.query(Employee.jabatan)
                .filter(Employee.jabatan.isnot(None), Employee.jabatan != "")
                .distinct()
                .order_by(Employee.jabatan)
                .all()
            )
            return [j[0] for j in jabs if j[0]]
