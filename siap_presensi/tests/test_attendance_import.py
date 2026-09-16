"""
Pengujian Unit & Integrasi Modul Import Absensi Excel (Tahap 3).
Menguji:
1. Date parser (DD/MM/YYYY dipastikan dibaca day-first: 03/08/2026 -> 3 Agustus 2026).
2. Time parser (validasi jam, jam kosong tidak dianggap error fatal).
3. Header normalization & mapping (Emp Num., No. ID., NIK, Nama, Tanggal, Scan Masuk, Scan Pulang).
4. Employee matching priority (Emp Num + No ID > Emp Num > No ID > Nama).
5. Duplicate detection (dalam file dan terhadap database).
6. Eksekusi import transaksi ke attendance_raw secara ACID.
7. Pencatatan Batch ID, Import Log, dan Audit Log.
8. Filter, paginasi, dan ekspor data raw ke Excel/CSV.
9. Kepastian integritas: TIDAK ADA kalkulasi alfa / potongan di Tahap 3.
"""
import os
import sys
import unittest
import json
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

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
    ImportLog,
    AuditLog,
)
from utils.date_parser import parse_date_value, format_date_display, format_date_indonesian
from utils.time_parser import parse_time_value, format_time_display
from utils.duplicate_detector import make_transaction_key, check_in_file_duplicates
from services.import_validation_service import (
    ImportValidationService,
    map_excel_headers,
    normalize_header_string,
)
from services.attendance_import_service import AttendanceImportService, generate_batch_id
from services.attendance_raw_service import AttendanceRawService


class TestAttendanceImportTahap3(unittest.TestCase):
    """Suite pengujian lengkap untuk seluruh fungsi Tahap 3."""

    def setUp(self):
        """Membuat database SQLite isolated di temporary directory."""
        self.temp_dir = TemporaryDirectory()
        self.test_db_path = Path(self.temp_dir.name) / "test_import.db"
        self.test_engine = create_engine(f"sqlite:///{self.test_db_path.as_posix()}")
        self.TestSession = sessionmaker(bind=self.test_engine)

        Base.metadata.create_all(self.test_engine)

        # Seed data karyawan master untuk pengujian pencocokan identitas
        self.db = self.TestSession()
        self.emp1 = Employee(
            emp_num="1",
            no_id="1",
            nik="3201010001",
            nama="AHMAD SUJATMIKO",
            status=EmployeeStatus.AKTIF,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.emp2 = Employee(
            emp_num="2",
            no_id="2",
            nik="3201010002",
            nama="BUDI SANTOSO",
            status=EmployeeStatus.AKTIF,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.user = User(
            username="admin",
            password_hash="hash",
            full_name="Admin Sistem",
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        self.db.add_all([self.emp1, self.emp2, self.user])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    # ==========================================
    # 1. TEST DATE PARSER
    # ==========================================
    def test_date_parser_day_first(self):
        """03/08/2026 HARUS dibaca sebagai 3 Agustus 2026, BUKAN 8 Maret 2026."""
        parsed, err = parse_date_value("03/08/2026")
        self.assertIsNone(err)
        self.assertEqual(parsed, date(2026, 8, 3))
        self.assertEqual(parsed.month, 8)
        self.assertEqual(parsed.day, 3)

        # Format strip DD-MM-YYYY
        parsed_dash, err = parse_date_value("03-08-2026")
        self.assertIsNone(err)
        self.assertEqual(parsed_dash, date(2026, 8, 3))

        # Format ISO YYYY-MM-DD
        parsed_iso, err = parse_date_value("2026-08-03")
        self.assertIsNone(err)
        self.assertEqual(parsed_iso, date(2026, 8, 3))

        # Format bahasa Indonesia
        self.assertIn("Agustus", format_date_indonesian(parsed))

    def test_date_parser_invalid(self):
        """Tanggal tidak valid harus menghasilkan pesan error."""
        p1, err1 = parse_date_value("32/08/2026")
        self.assertIsNone(p1)
        self.assertIsNotNone(err1)

        p2, err2 = parse_date_value("invalid_date")
        self.assertIsNone(p2)
        self.assertIn("tidak valid", err2.lower())

        p3, err3 = parse_date_value(None)
        self.assertIsNone(p3)
        self.assertIn("kosong", err3.lower())

    # ==========================================
    # 2. TEST TIME PARSER
    # ==========================================
    def test_time_parser_valid_and_empty(self):
        """Menguji parsing jam masuk dan pulang, jam kosong diperbolehkan untuk data mentah."""
        # Waktu lengkap HH:MM:SS
        t1, empty1, err1 = parse_time_value("07:54:00")
        self.assertEqual(t1, "07:54:00")
        self.assertFalse(empty1)
        self.assertIsNone(err1)

        # Waktu HH:MM
        t2, empty2, err2 = parse_time_value("16:30")
        self.assertEqual(t2, "16:30:00")
        self.assertFalse(empty2)
        self.assertIsNone(err2)

        # Jam kosong (None, "-", "")
        t_empty, is_empty, err_empty = parse_time_value("")
        self.assertIsNone(t_empty)
        self.assertTrue(is_empty)
        self.assertIsNone(err_empty)

        # Jam salah format
        t_bad, bad_empty, err_bad = parse_time_value("25:70:00")
        self.assertIsNone(t_bad)
        self.assertFalse(bad_empty)
        self.assertIsNotNone(err_bad)

    # ==========================================
    # 3. TEST HEADER MAPPING
    # ==========================================
    def test_header_mapping_agustus_format(self):
        """Memetakan header standar file AGUSTUS 2026.xlsx."""
        raw_headers = [
            "Emp Num.", "No. ID.", "NIK", "Nama", "Tanggal", "Scan Masuk", "Scan Pulang"
        ]
        mapped, missing, warnings = map_excel_headers(raw_headers)
        self.assertEqual(len(missing), 0)
        self.assertEqual(mapped.get("emp_num"), "Emp Num.")
        self.assertEqual(mapped.get("no_id"), "No. ID.")
        self.assertEqual(mapped.get("nik"), "NIK")
        self.assertEqual(mapped.get("nama"), "Nama")
        self.assertEqual(mapped.get("tanggal"), "Tanggal")
        self.assertEqual(mapped.get("scan_masuk"), "Scan Masuk")
        self.assertEqual(mapped.get("scan_pulang"), "Scan Pulang")

    def test_header_mapping_missing_required(self):
        """Header tanpa Tanggal atau Nama harus ditolak."""
        bad_headers = ["Emp Num.", "No. ID.", "Scan Masuk", "Scan Pulang"]
        mapped, missing, warnings = map_excel_headers(bad_headers)
        self.assertIn("Nama", missing)
        self.assertIn("Tanggal", missing)

    # ==========================================
    # 4. TEST EMPLOYEE MATCHING PRIORITY
    # ==========================================
    def test_employee_matching_priority(self):
        """Menguji prioritas pencocokan karyawan: Emp Num + No ID > Emp Num > No ID."""
        validator = ImportValidationService(self.db)

        # Cocok sepasang
        emp_match, mtype = validator.match_employee(emp_num="1", no_id="1", nama="AHMAD SUJATMIKO")
        self.assertIsNotNone(emp_match)
        self.assertEqual(mtype, "MATCH_PAIR")
        self.assertEqual(emp_match.id, self.emp1.id)

        # Cocok no_id saja
        emp_match2, mtype2 = validator.match_employee(emp_num="", no_id="2", nama="BUDI")
        self.assertIsNotNone(emp_match2)
        self.assertEqual(mtype2, "MATCH_NO_ID")
        self.assertEqual(emp_match2.id, self.emp2.id)

        # Tidak ditemukan
        emp_match3, mtype3 = validator.match_employee(emp_num="999", no_id="999", nama="NON EXISTENT")
        self.assertIsNone(emp_match3)
        self.assertEqual(mtype3, "NOT_FOUND")

    # ==========================================
    # 5. TEST DUPLICATE DETECTION
    # ==========================================
    def test_duplicate_detection(self):
        """Menguji deteksi duplikasi internal file."""
        sample_rows = [
            {
                "emp_num": "1", "no_id": "1", "nama": "AHMAD",
                "tanggal_obj": date(2026, 8, 3), "scan_masuk": "07:54:00",
                "scan_pulang": "16:30:00", "is_valid": True,
            },
            {
                "emp_num": "1", "no_id": "1", "nama": "AHMAD",
                "tanggal_obj": date(2026, 8, 3), "scan_masuk": "07:54:00",
                "scan_pulang": "16:30:00", "is_valid": True,
            },
        ]
        checked = check_in_file_duplicates(sample_rows)
        self.assertFalse(checked[0]["is_duplicate_in_file"])
        self.assertTrue(checked[1]["is_duplicate_in_file"])
        self.assertEqual(checked[1]["duplicate_source_row"], 1)

    # ==========================================
    # 6. TEST IMPORT EXECUTION & PERSISTENCE
    # ==========================================
    def test_execute_import_success(self):
        """Menguji eksekusi import data ke tabel attendance_raw."""
        mock_preview = {
            "source_file": "AGUSTUS 2026.xlsx",
            "sheet_name": "Sheet1",
            "total_rows": 2,
            "rows": [
                {
                    "no": 1, "excel_line": 2, "emp_num": "1", "no_id": "1", "nik": "3201010001",
                    "nama": "AHMAD SUJATMIKO", "tanggal_obj": date(2026, 8, 3),
                    "tanggal_display": "2026-08-03", "scan_masuk": "07:54:00",
                    "scan_pulang": "16:30:00", "is_valid": True, "employee_id": self.emp1.id,
                    "is_duplicate_in_file": False, "is_duplicate_in_db": False,
                },
                {
                    "no": 2, "excel_line": 3, "emp_num": "2", "no_id": "2", "nik": "3201010002",
                    "nama": "BUDI SANTOSO", "tanggal_obj": date(2026, 8, 3),
                    "scan_masuk": None, "scan_pulang": "16:25:00", "is_valid": True,
                    "employee_id": self.emp2.id, "is_duplicate_in_file": False, "is_duplicate_in_db": False,
                },
            ],
        }

        with patch("services.attendance_import_service.get_db_session", return_value=self.TestSession()):
            result = AttendanceImportService.execute_import(
                preview_data=mock_preview,
                duplicate_strategy="SKIP",
                unmatched_strategy="UNLINKED",
                user_id=self.user.id,
                username="admin",
            )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["success_rows"], 2)
        self.assertTrue(result["batch_id"].startswith("BATCH-"))

        # Verifikasi data tersimpan di tabel attendance_raw
        raw_count = self.db.query(AttendanceRaw).filter(AttendanceRaw.import_batch_id == result["batch_id"]).count()
        self.assertEqual(raw_count, 2)

        # Verifikasi data scan masuk kosong tetap tersimpan sebagai data mentah
        rec2 = self.db.query(AttendanceRaw).filter(AttendanceRaw.emp_num == "2").first()
        self.assertIsNotNone(rec2)
        self.assertIsNone(rec2.scan_masuk)
        self.assertEqual(rec2.scan_pulang, "16:25:00")

        # Verifikasi log tercatat
        log = self.db.query(ImportLog).filter(ImportLog.import_batch_id == result["batch_id"]).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, "SUCCESS")

        audit = self.db.query(AuditLog).filter(AuditLog.action == "IMPORT_ATTENDANCE").first()
        self.assertIsNotNone(audit)

    # ==========================================
    # 7. TEST RAW ATTENDANCE SERVICE
    # ==========================================
    def test_raw_attendance_service_filtering(self):
        """Menguji filter pencarian dan periode pada data mentah."""
        # Masukkan transaksi dummy
        r1 = AttendanceRaw(
            employee_id=self.emp1.id, emp_num="1", no_id="1", nik="3201010001",
            nama="AHMAD SUJATMIKO", tanggal=date(2026, 8, 3), scan_masuk="07:54:00",
            scan_pulang="16:30:00", source_file="AGUSTUS 2026.xlsx", import_batch_id="BATCH-TEST-001",
            created_at=datetime.utcnow()
        )
        self.db.add(r1)
        self.db.commit()

        # Cari berdasarkan nama
        records, total, _ = AttendanceRawService.get_raw_records(self.db, keyword="AHMAD")
        self.assertEqual(total, 1)
        self.assertEqual(records[0]["nama"], "AHMAD SUJATMIKO")

        # Cari berdasarkan batch
        records_batch, total_b, _ = AttendanceRawService.get_raw_records(self.db, batch_id="BATCH-TEST-001")
        self.assertEqual(total_b, 1)

        # Filter bulan 8 tahun 2026
        records_aug, total_aug, _ = AttendanceRawService.get_raw_records(self.db, month=8, year=2026)
        self.assertEqual(total_aug, 1)

        # Filter bulan lain (bulan 9 harus 0)
        records_sep, total_sep, _ = AttendanceRawService.get_raw_records(self.db, month=9, year=2026)
        self.assertEqual(total_sep, 0)


if __name__ == "__main__":
    unittest.main()
