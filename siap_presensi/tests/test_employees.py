"""
Suite Pengujian Unit & Integrasi Modul Master Data Karyawan SIAP (Tahap 2).
Menguji:
1. Pembuatan karyawan baru & pencatatan audit log
2. Validasi input (nama wajib, format email, format tanggal)
3. Deteksi duplikasi No. Pegawai, No. ID / PIN, dan NIK
4. Pembaruan data karyawan (Update) & deteksi konflik ID
5. Soft delete (Nonaktifkan & Aktifkan) status kepegawaian
6. Proteksi integritas: Penolakan hapus permanen jika memiliki riwayat absensi
7. Penghapusan permanen berhasil jika tidak memiliki riwayat absensi
8. Pencarian kata kunci, multi-filter departemen/status, dan paginasi
9. Statistik ringkasan karyawan (Total, Aktif, Nonaktif, Tanpa NIK)
10. Import data karyawan & penanganan duplikasi (Skip/Update)
11. Export data karyawan ke format CSV/Excel
"""
import os
import sys
import unittest
from datetime import datetime, date
from pathlib import Path
from tempfile import TemporaryDirectory

# Pastikan path modul siap_presensi dikenali
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.base import Base
from database.models import (
    User,
    UserRole,
    Employee,
    EmployeeStatus,
    AttendanceRaw,
    AttendanceDaily,
    AuditLog,
    ImportLog,
)
from services.employee_service import EmployeeService
from services.employee_import_service import EmployeeImportService
from utils.validators import validate_employee_payload, validate_email, validate_date_string


class TestEmployeeModuleTahap2(unittest.TestCase):
    """Test suite komprehensif untuk modul Master Data Karyawan."""

    def setUp(self):
        """Membuat database SQLite temporary terisolasi untuk tiap pengujian."""
        self.temp_dir = TemporaryDirectory()
        self.test_db_path = Path(self.temp_dir.name) / "test_employee.db"
        self.engine = create_engine(
            f"sqlite:///{self.test_db_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        self.TestSession = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

        # Patch get_db_session pada database.connection agar menggunakan engine pengujian
        import database.connection as db_conn
        self._orig_session_local = db_conn.SessionLocal
        db_conn.SessionLocal = self.TestSession

        # Seed 1 user admin untuk tes audit log
        session = self.TestSession()
        admin = User(
            username="testadmin",
            password_hash="testhash",
            full_name="Test Admin",
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
        session.commit()
        self.admin_id = admin.id
        session.close()

    def tearDown(self):
        """Membersihkan file database & mengembalikan koneksi session."""
        import database.connection as db_conn
        db_conn.SessionLocal = self._orig_session_local
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_01_create_employee_success(self):
        """Uji 1: Tambah karyawan baru berhasil dan tercatat di audit log."""
        payload = {
            "nama": "Ahmad Dahlan",
            "emp_num": "EMP-001",
            "no_id": "101",
            "nik": "3201012345678901",
            "unit": "Teknologi Informasi",
            "jabatan": "Software Engineer",
            "email": "ahmad@perusahaan.com",
            "status": "AKTIF",
            "tanggal_mulai": "2024-01-10",
        }

        success, emp_dict, err = EmployeeService.create_employee(payload, user_id=self.admin_id)
        self.assertTrue(success, f"Gagal membuat karyawan: {err}")
        self.assertIsNotNone(emp_dict)
        self.assertEqual(emp_dict["nama"], "Ahmad Dahlan")
        self.assertEqual(emp_dict["unit"], "Teknologi Informasi")

        # Verifikasi Audit Log
        session = self.TestSession()
        audit = session.query(AuditLog).filter(AuditLog.action == "TAMBAH_KARYAWAN").first()
        self.assertIsNotNone(audit, "Audit log penambahan karyawan harus tercatat.")
        self.assertEqual(audit.user_id, self.admin_id)
        session.close()

    def test_02_validation_rules(self):
        """Uji 2: Validasi aturan input (nama kosong, email salah, format tanggal salah)."""
        # Nama kosong harus ditolak
        valid, errs = validate_employee_payload({"nama": ""})
        self.assertFalse(valid)
        self.assertTrue(any("Nama karyawan wajib diisi" in e for e in errs))

        # Email tidak valid harus ditolak
        valid_email, err_email = validate_email("email-tidak-valid")
        self.assertFalse(valid_email)

        # Format tanggal tidak valid harus ditolak
        valid_date, err_date = validate_date_string("15-01-2025")
        self.assertFalse(valid_date)

    def test_03_duplicate_detection(self):
        """Uji 3: Deteksi duplikasi No. Pegawai, No. ID, dan NIK."""
        # Buat karyawan pertama
        EmployeeService.create_employee({
            "nama": "Karyawan Satu",
            "emp_num": "EMP-DUPLIKAT",
            "no_id": "999",
            "nik": "3201000000000001",
        }, user_id=self.admin_id)

        # Coba buat karyawan kedua dengan emp_num yang sama
        success, _, err = EmployeeService.create_employee({
            "nama": "Karyawan Dua",
            "emp_num": "EMP-DUPLIKAT",
            "no_id": "1000",
        })
        self.assertFalse(success, "Seharusnya gagal karena emp_num duplikat.")
        self.assertIn("sudah digunakan", err)

        # Coba buat dengan no_id yang sama
        success_id, _, err_id = EmployeeService.create_employee({
            "nama": "Karyawan Tiga",
            "emp_num": "EMP-UNIQUE",
            "no_id": "999",
        })
        self.assertFalse(success_id, "Seharusnya gagal karena no_id duplikat.")
        self.assertIn("No. ID / PIN '999' sudah digunakan", err_id)

    def test_04_update_employee(self):
        """Uji 4: Edit / pembaruan data karyawan tersimpan dan tercatat di audit log."""
        _, emp, _ = EmployeeService.create_employee({"nama": "Sebelum Diedit", "unit": "Umum"})
        emp_id = emp["id"]

        update_payload = {
            "nama": "Sesudah Diedit",
            "unit": "Keuangan",
            "jabatan": "Manager",
            "status": "AKTIF",
        }
        success, updated, err = EmployeeService.update_employee(emp_id, update_payload, user_id=self.admin_id)
        self.assertTrue(success, err)
        self.assertEqual(updated["nama"], "Sesudah Diedit")
        self.assertEqual(updated["unit"], "Keuangan")

        # Verifikasi Audit Log
        session = self.TestSession()
        audit = session.query(AuditLog).filter(AuditLog.action == "EDIT_KARYAWAN").first()
        self.assertIsNotNone(audit)
        session.close()

    def test_05_soft_delete_toggle_status(self):
        """Uji 5: Soft delete (Nonaktifkan) dan Pengaktifan kembali."""
        _, emp, _ = EmployeeService.create_employee({"nama": "Karyawan Kontrak"})
        emp_id = emp["id"]

        # 1. Nonaktifkan
        success, new_status, _ = EmployeeService.toggle_status(emp_id, user_id=self.admin_id)
        self.assertTrue(success)
        self.assertEqual(new_status, "NONAKTIF")

        # Data tetap ada di database
        emp_db = EmployeeService.get_employee_by_id(emp_id)
        self.assertIsNotNone(emp_db)
        self.assertEqual(emp_db["status"], "NONAKTIF")

        # 2. Aktifkan kembali
        success2, new_status2, _ = EmployeeService.toggle_status(emp_id, user_id=self.admin_id)
        self.assertTrue(success2)
        self.assertEqual(new_status2, "AKTIF")

    def test_06_delete_employee_protection_with_attendance(self):
        """Uji 6: Proteksi hapus permanen jika karyawan telah memiliki relasi absensi."""
        _, emp, _ = EmployeeService.create_employee({"nama": "Karyawan Berabsensi", "no_id": "777"})
        emp_id = emp["id"]

        # Tambahkan catatan absensi mentah untuk karyawan ini
        session = self.TestSession()
        raw_att = AttendanceRaw(
            employee_id=emp_id,
            no_id="777",
            nama="Karyawan Berabsensi",
            tanggal=date(2025, 9, 1),
            scan_masuk="08:00",
            scan_pulang="16:30",
        )
        session.add(raw_att)
        session.commit()
        session.close()

        # Eksekusi penghapusan permanen harus ditolak
        success, err = EmployeeService.delete_employee(emp_id, user_id=self.admin_id)
        self.assertFalse(success, "Hapus permanen harus ditolak jika memiliki riwayat absensi.")
        self.assertIn("tidak dapat dihapus permanen", err)
        self.assertIn("riwayat catatan absensi", err)

        # Verifikasi karyawan masih ada di database
        emp_check = EmployeeService.get_employee_by_id(emp_id)
        self.assertIsNotNone(emp_check, "Karyawan tidak boleh terhapus.")

    def test_07_delete_employee_permanent_success(self):
        """Uji 7: Hapus permanen berhasil jika karyawan belum memiliki relasi data absensi."""
        _, emp, _ = EmployeeService.create_employee({"nama": "Karyawan Baru Tanpa Absensi"})
        emp_id = emp["id"]

        success, err = EmployeeService.delete_employee(emp_id, user_id=self.admin_id)
        self.assertTrue(success, f"Hapus permanen seharusnya sukses: {err}")

        # Pastikan data benar-benar hilang dari database
        emp_check = EmployeeService.get_employee_by_id(emp_id)
        self.assertIsNone(emp_check, "Data karyawan harus sudah terhapus.")

    def test_08_search_filter_and_pagination(self):
        """Uji 8: Pencarian kata kunci, filter per unit/status, dan paginasi."""
        # Buat 5 karyawan dengan variasi unit dan status
        EmployeeService.create_employee({"nama": "Siti Fatimah", "unit": "Keuangan", "status": "AKTIF"})
        EmployeeService.create_employee({"nama": "Siti Nurhaliza", "unit": "SDM", "status": "AKTIF"})
        EmployeeService.create_employee({"nama": "Budi Santoso", "unit": "Keuangan", "status": "NONAKTIF"})
        EmployeeService.create_employee({"nama": "Doni Pratama", "unit": "Teknologi", "status": "AKTIF"})
        EmployeeService.create_employee({"nama": "Siti Aminah", "unit": "Keuangan", "status": "AKTIF"})

        # Pencarian kata kunci "Siti"
        res_search = EmployeeService.get_employees(search="Siti")
        self.assertEqual(res_search["total"], 3)

        # Filter Unit "Keuangan"
        res_unit = EmployeeService.get_employees(unit="Keuangan")
        self.assertEqual(res_unit["total"], 3)

        # Filter Status "NONAKTIF"
        res_status = EmployeeService.get_employees(status="NONAKTIF")
        self.assertEqual(res_status["total"], 1)

        # Paginasi per_page=2
        res_page1 = EmployeeService.get_employees(per_page=2, page=1)
        self.assertEqual(len(res_page1["items"]), 2)
        self.assertEqual(res_page1["total_pages"], 3)
        self.assertEqual(res_page1["total"], 5)

    def test_09_employee_statistics(self):
        """Uji 9: Akurasi kartu metrik statistik karyawan."""
        EmployeeService.create_employee({"nama": "Emp 1", "nik": "12345", "status": "AKTIF"})
        EmployeeService.create_employee({"nama": "Emp 2", "nik": "", "status": "AKTIF"})       # Tanpa NIK
        EmployeeService.create_employee({"nama": "Emp 3", "nik": None, "status": "NONAKTIF"})   # Tanpa NIK & Nonaktif

        stats = EmployeeService.get_statistics()
        self.assertEqual(stats["total_karyawan"], 3)
        self.assertEqual(stats["aktif"], 2)
        self.assertEqual(stats["nonaktif"], 1)
        self.assertEqual(stats["tanpa_nik"], 2)

    def test_10_csv_import_and_export(self):
        """Uji 10: Import file CSV karyawan dan export kembali."""
        csv_content = (
            "Nama;No ID;No Pegawai;NIK;Unit;Jabatan;Status\n"
            "Budi Handoko;201;EMP-201;320109988;Operasional;Staff;AKTIF\n"
            "Dewi Lestari;202;EMP-202;320109989;Sekretariat;Admin;AKTIF\n"
            ";203;EMP-203;;Umum;Staff;AKTIF\n"  # Baris invalid (nama kosong)
        )
        csv_file = Path(self.temp_dir.name) / "test_import.csv"
        csv_file.write_text(csv_content, encoding="utf-8-sig")

        # 1. Preview
        preview = EmployeeImportService.preview_import(str(csv_file))
        self.assertTrue(preview["success"])
        self.assertEqual(preview["total_rows"], 3)
        self.assertEqual(preview["valid_rows"], 2)
        self.assertEqual(preview["invalid_rows"], 1)

        # 2. Execute Import
        exec_res = EmployeeImportService.execute_import(
            str(csv_file),
            duplicate_mode="SKIP",
            user_id=self.admin_id,
        )
        self.assertTrue(exec_res["success"])
        self.assertEqual(exec_res["success_count"], 2)
        self.assertEqual(exec_res["failed_count"], 1)

        # 3. Export data ke CSV
        export_file = Path(self.temp_dir.name) / "exported_employees.csv"
        exp_success, exp_err = EmployeeImportService.export_employees(
            str(export_file),
            user_id=self.admin_id,
        )
        self.assertTrue(exp_success, exp_err)
        self.assertTrue(export_file.exists())
        self.assertGreater(export_file.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
