"""
Definisi Model Database SQLAlchemy untuk Aplikasi SIAP.
Mencakup Users, Employees, AttendanceRaw, AttendanceDaily,
Calendar, Settings, ImportLogs, dan AuditLogs.
"""
import enum
from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    Numeric,
    ForeignKey,
    Enum,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from .base import Base


class UserRole(str, enum.Enum):
    """Role hak akses sistem."""
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"


class EmployeeStatus(str, enum.Enum):
    """Status kepegawaian."""
    AKTIF = "AKTIF"
    NONAKTIF = "NONAKTIF"


class CalendarStatus(str, enum.Enum):
    """Status hari pada kalender kerja."""
    HARI_KERJA = "HARI_KERJA"
    AKHIR_PEKAN = "AKHIR_PEKAN"
    LIBUR = "LIBUR"
    HARI_KERJA_KHUSUS = "HARI_KERJA_KHUSUS"
    CUTI_BERSAMA = "CUTI_BERSAMA"
    LIBUR_NASIONAL = "LIBUR_NASIONAL"


class AttendanceStatus(str, enum.Enum):
    """Status kehadiran harian karyawan."""
    HADIR_LENGKAP = "HADIR_LENGKAP"
    HANYA_ABSEN_MASUK = "HANYA_ABSEN_MASUK"
    HANYA_ABSEN_PULANG = "HANYA_ABSEN_PULANG"
    TIDAK_ABSEN = "TIDAK_ABSEN"
    DATA_BERMASALAH = "DATA_BERMASALAH"


class CheckScanStatus(str, enum.Enum):
    """Status ketercukupan scan presensi masuk atau pulang."""
    ADA = "ADA"
    TIDAK_ADA = "TIDAK_ADA"


class User(Base):
    """
    Tabel Users untuk autentikasi dan otorisasi sistem.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole, name="user_roles"), nullable=False, default=UserRole.OPERATOR)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relasi
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}' role='{self.role.value}'>"


class Employee(Base):
    """
    Tabel Master Karyawan.
    Catatan: NIK dapat bernilai kosong pada beberapa format mesin absensi,
    sehingga identifikasi dapat menggunakan kombinasi emp_num atau no_id.
    """
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emp_num = Column(String(50), nullable=True, index=True)
    no_id = Column(String(50), nullable=True, index=True)
    nik = Column(String(50), nullable=True, index=True)
    nama = Column(String(150), nullable=False, index=True)
    unit = Column(String(100), nullable=True, index=True)
    jabatan = Column(String(100), nullable=True, index=True)
    email = Column(String(150), nullable=True)
    keterangan = Column(Text, nullable=True)
    status = Column(Enum(EmployeeStatus, name="employee_status"), default=EmployeeStatus.AKTIF, nullable=False)
    tanggal_mulai = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relasi
    raw_attendances = relationship("AttendanceRaw", back_populates="employee")
    daily_attendances = relationship("AttendanceDaily", back_populates="employee", cascade="all, delete-orphan")
    deductions = relationship("AttendanceDeduction", back_populates="employee", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_emp_identity", "emp_num", "no_id"),
    )

    def to_dict(self) -> dict:
        """Konversi objek Employee ke representasi dictionary."""
        return {
            "id": self.id,
            "emp_num": self.emp_num or "",
            "no_id": self.no_id or "",
            "nik": self.nik or "",
            "nama": self.nama,
            "unit": self.unit or "-",
            "jabatan": self.jabatan or "-",
            "email": self.email or "-",
            "keterangan": self.keterangan or "",
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "tanggal_mulai": self.tanggal_mulai.strftime("%Y-%m-%d") if self.tanggal_mulai else "-",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "-",
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else "-",
        }

    def __repr__(self) -> str:
        return f"<Employee id={self.id} nama='{self.nama}' status='{self.status.value}'>"


class AttendanceRaw(Base):
    """
    Tabel Penampungan Data Mentah Hasil Scan Absensi (Excel Import pada Tahap 2).
    """
    __tablename__ = "attendance_raw"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    emp_num = Column(String(50), nullable=True)
    no_id = Column(String(50), nullable=True)
    nik = Column(String(50), nullable=True)
    nama = Column(String(150), nullable=False)
    tanggal = Column(Date, nullable=False, index=True)
    scan_masuk = Column(String(10), nullable=True)
    scan_pulang = Column(String(10), nullable=True)
    source_file = Column(String(255), nullable=True)
    import_batch_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relasi
    employee = relationship("Employee", back_populates="raw_attendances")

    def to_dict(self) -> dict:
        """Konversi objek AttendanceRaw ke representasi dictionary."""
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "emp_num": self.emp_num or "-",
            "no_id": self.no_id or "-",
            "nik": self.nik or "-",
            "nama": self.nama,
            "tanggal": self.tanggal.strftime("%Y-%m-%d") if self.tanggal else "-",
            "scan_masuk": self.scan_masuk or "-",
            "scan_pulang": self.scan_pulang or "-",
            "source_file": self.source_file or "-",
            "import_batch_id": self.import_batch_id or "-",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "-",
        }

    def __repr__(self) -> str:
        return f"<AttendanceRaw id={self.id} nama='{self.nama}' tanggal={self.tanggal}>"


class WorkCalendar(Base):
    """
    Tabel Kalender Kerja Bulanan dan Status Hari (work_calendars).
    Mengatur status hari kerja, akhir pekan, libur nasional, cuti bersama,
    serta jam operasional terjadwal (check-in / check-out).
    """
    __tablename__ = "work_calendars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    calendar_date = Column(Date, unique=True, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    day_name = Column(String(20), nullable=False)
    calendar_status = Column(Enum(CalendarStatus, name="calendar_status_enum"), default=CalendarStatus.HARI_KERJA, nullable=False, index=True)
    is_working_day = Column(Boolean, default=True, nullable=False, index=True)
    scheduled_check_in = Column(String(10), nullable=True)   # Format HH:MM (misal "08:15")
    scheduled_check_out = Column(String(10), nullable=True)  # Format HH:MM (misal "16:30" / "17:00")
    description = Column(String(255), nullable=True)
    is_special_day = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)

    # Relasi
    daily_attendances = relationship("AttendanceDaily", back_populates="calendar")

    # Properti Kompatibilitas
    @property
    def tanggal(self) -> date:
        return self.calendar_date

    @property
    def hari(self) -> str:
        return self.day_name

    @property
    def status(self) -> CalendarStatus:
        return self.calendar_status

    @property
    def jam_masuk(self) -> str:
        return self.scheduled_check_in

    @property
    def jam_pulang(self) -> str:
        return self.scheduled_check_out

    @property
    def keterangan(self) -> str:
        return self.description

    def to_dict(self) -> dict:
        """Konversi objek WorkCalendar ke representasi dictionary."""
        return {
            "id": self.id,
            "calendar_date": self.calendar_date.strftime("%Y-%m-%d") if self.calendar_date else "",
            "tanggal": self.calendar_date.strftime("%Y-%m-%d") if self.calendar_date else "",
            "year": self.year,
            "month": self.month,
            "day_name": self.day_name,
            "hari": self.day_name,
            "calendar_status": self.calendar_status.value if hasattr(self.calendar_status, "value") else str(self.calendar_status),
            "status": self.calendar_status.value if hasattr(self.calendar_status, "value") else str(self.calendar_status),
            "is_working_day": self.is_working_day,
            "scheduled_check_in": self.scheduled_check_in or "-",
            "scheduled_check_out": self.scheduled_check_out or "-",
            "jam_masuk": self.scheduled_check_in or "-",
            "jam_pulang": self.scheduled_check_out or "-",
            "description": self.description or "",
            "keterangan": self.description or "",
            "is_special_day": self.is_special_day,
            "created_by": self.created_by or "SYSTEM",
            "updated_by": self.updated_by or "-",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "-",
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else "-",
        }

    def __repr__(self) -> str:
        return f"<WorkCalendar {self.calendar_date} ({self.calendar_status.value if hasattr(self.calendar_status, 'value') else self.calendar_status}) is_work={self.is_working_day}>"


# Alias backward compatibility
Calendar = WorkCalendar


class AttendanceDaily(Base):
    """
    Tabel Absensi Harian Karyawan (attendance_daily).
    Menghubungkan Master Karyawan AKTIF x Tanggal Hari Kerja x Data Mentah (attendance_raw).
    Mendukung status: HADIR_LENGKAP, HANYA_ABSEN_MASUK, HANYA_ABSEN_PULANG, TIDAK_ABSEN, DATA_BERMASALAH.
    """
    __tablename__ = "attendance_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_date = Column(Date, nullable=False, index=True)
    calendar_id = Column(Integer, ForeignKey("work_calendars.id", ondelete="SET NULL"), nullable=True, index=True)
    day_name = Column(String(20), nullable=True)

    # Jam Terjadwal (dari Kalender Kerja)
    scheduled_check_in = Column(String(10), nullable=True)
    scheduled_check_out = Column(String(10), nullable=True)

    # Jam Aktual (dari attendance_raw)
    actual_check_in = Column(String(10), nullable=True)
    actual_check_out = Column(String(10), nullable=True)

    # Status Presensi
    check_in_status = Column(String(20), default="TIDAK_ADA", nullable=False, index=True)   # ADA / TIDAK_ADA
    check_out_status = Column(String(20), default="TIDAK_ADA", nullable=False, index=True)  # ADA / TIDAK_ADA
    attendance_status = Column(String(50), default="TIDAK_ABSEN", nullable=False, index=True) # HADIR_LENGKAP, HANYA_ABSEN_MASUK, HANYA_ABSEN_PULANG, TIDAK_ABSEN, DATA_BERMASALAH

    # Referensi Sumber Data Mentah
    source_raw_in_id = Column(Integer, ForeignKey("attendance_raw.id", ondelete="SET NULL"), nullable=True)
    source_raw_out_id = Column(Integer, ForeignKey("attendance_raw.id", ondelete="SET NULL"), nullable=True)

    # Flag Kualitas Data
    has_incomplete_scan = Column(Boolean, default=False, nullable=False)
    has_conflict = Column(Boolean, default=False, nullable=False)
    is_manually_adjusted = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)

    # Metadata Proses
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_by = Column(String(100), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(String(100), nullable=True)

    # Kolom Penampung Kalkulasi Potongan (Akan dihitung pada Tahap 5)
    terlambat_menit = Column(Integer, default=0, nullable=False)
    pulang_cepat_menit = Column(Integer, default=0, nullable=False)
    potongan_masuk = Column(Numeric(12, 2), default=0.0, nullable=False)
    potongan_pulang = Column(Numeric(12, 2), default=0.0, nullable=False)
    potongan_tidak_hadir = Column(Numeric(12, 2), default=0.0, nullable=False)
    total_potongan = Column(Numeric(12, 2), default=0.0, nullable=False)

    # Relasi
    employee = relationship("Employee", back_populates="daily_attendances")
    calendar = relationship("WorkCalendar", back_populates="daily_attendances")
    raw_in = relationship("AttendanceRaw", foreign_keys=[source_raw_in_id])
    raw_out = relationship("AttendanceRaw", foreign_keys=[source_raw_out_id])
    deduction = relationship("AttendanceDeduction", back_populates="attendance_daily", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("employee_id", "attendance_date", name="uq_emp_attendance_date"),
        Index("idx_daily_emp_date", "employee_id", "attendance_date"),
        Index("idx_daily_status", "attendance_status"),
        Index("idx_daily_check_in", "check_in_status"),
        Index("idx_daily_check_out", "check_out_status"),
    )

    # Properti Kompatibilitas
    @property
    def tanggal(self) -> date:
        return self.attendance_date

    @property
    def hari(self) -> str:
        return self.day_name or ""

    @property
    def jam_masuk(self) -> str:
        return self.actual_check_in or ""

    @property
    def jam_pulang(self) -> str:
        return self.actual_check_out or ""

    @property
    def status_masuk(self) -> str:
        return self.check_in_status

    @property
    def status_pulang(self) -> str:
        return self.check_out_status

    def to_dict(self) -> dict:
        """Konversi objek AttendanceDaily ke representasi dictionary."""
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "emp_num": self.employee.emp_num if self.employee else "-",
            "no_id": self.employee.no_id if self.employee else "-",
            "nik": self.employee.nik if self.employee else "-",
            "nama": self.employee.nama if self.employee else "-",
            "unit": self.employee.unit if self.employee else "-",
            "jabatan": self.employee.jabatan if self.employee else "-",
            "attendance_date": self.attendance_date.strftime("%Y-%m-%d") if self.attendance_date else "",
            "tanggal": self.attendance_date.strftime("%Y-%m-%d") if self.attendance_date else "",
            "day_name": self.day_name or "-",
            "hari": self.day_name or "-",
            "scheduled_check_in": self.scheduled_check_in or "-",
            "scheduled_check_out": self.scheduled_check_out or "-",
            "actual_check_in": self.actual_check_in or "-",
            "actual_check_out": self.actual_check_out or "-",
            "check_in_status": self.check_in_status,
            "check_out_status": self.check_out_status,
            "attendance_status": self.attendance_status,
            "has_incomplete_scan": self.has_incomplete_scan,
            "has_conflict": self.has_conflict,
            "is_manually_adjusted": self.is_manually_adjusted,
            "notes": self.notes or "",
            "generated_at": self.generated_at.strftime("%Y-%m-%d %H:%M:%S") if self.generated_at else "-",
            "generated_by": self.generated_by or "-",
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else "-",
        }

    def __repr__(self) -> str:
        return f"<AttendanceDaily emp_id={self.employee_id} date={self.attendance_date} status={self.attendance_status}>"


class Setting(Base):
    """
    Tabel Penyimpanan Konfigurasi Sistem (Target Hari Kerja, Jam Operasional, Tarif Potongan).
    """
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(Text, nullable=False)
    setting_type = Column(String(50), nullable=True, default="str")
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Setting key='{self.setting_key}' value='{self.setting_value}'>"


class ImportLog(Base):
    """
    Tabel Riwayat Import Berkas Absensi.
    """
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    import_batch_id = Column(String(100), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    file_name = Column(String(255), nullable=False)
    import_type = Column(String(50), nullable=False)
    total_rows = Column(Integer, default=0, nullable=False)
    success_rows = Column(Integer, default=0, nullable=False)
    failed_rows = Column(Integer, default=0, nullable=False)
    duplicate_rows = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    error_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        """Konversi riwayat import log ke format dictionary."""
        return {
            "id": self.id,
            "import_batch_id": self.import_batch_id or f"BATCH-{self.id:04d}",
            "user_id": self.user_id,
            "file_name": self.file_name,
            "import_type": self.import_type,
            "total_rows": self.total_rows,
            "success_rows": self.success_rows,
            "failed_rows": self.failed_rows,
            "duplicate_rows": self.duplicate_rows,
            "status": self.status,
            "error_details": self.error_details or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "-",
        }

    def __repr__(self) -> str:
        return f"<ImportLog batch='{self.import_batch_id}' file='{self.file_name}' status='{self.status}'>"


class AuditLog(Base):
    """
    Tabel Audit Trail aktivitas pengguna untuk kepatuhan dan pelacakan riwayat.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    module = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relasi
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog action='{self.action}' module='{self.module}' created_at={self.created_at}>"


class AttendanceDeduction(Base):
    """
    Tabel Rincian Potongan Absensi Harian (attendance_deductions) - Tahap 5.
    Menyimpan rincian keterlambatan, pulang cepat, tidak absen masuk/pulang,
    dan total nominal potongan dalam integer Rupiah (mencegah floating point error).
    Dilengkapi unique constraint untuk mencegah double counting.
    """
    __tablename__ = "attendance_deductions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    attendance_daily_id = Column(Integer, ForeignKey("attendance_daily.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_date = Column(Date, nullable=False, index=True)

    late_minutes = Column(Integer, default=0, nullable=False)
    early_leave_minutes = Column(Integer, default=0, nullable=False)

    deduction_late = Column(Integer, default=0, nullable=False)               # Nominal Rp integer
    deduction_early_leave = Column(Integer, default=0, nullable=False)        # Nominal Rp integer
    deduction_missing_check_in = Column(Integer, default=0, nullable=False)   # Nominal Rp integer
    deduction_missing_check_out = Column(Integer, default=0, nullable=False)  # Nominal Rp integer
    total_deduction = Column(Integer, default=0, nullable=False)              # Nominal Rp integer (Sum of above)

    calculation_version = Column(String(50), default="1.0.0", nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    calculated_by = Column(String(100), default="SYSTEM", nullable=True)
    notes = Column(Text, nullable=True)

    # Relasi
    attendance_daily = relationship("AttendanceDaily", back_populates="deduction")
    employee = relationship("Employee", back_populates="deductions")

    __table_args__ = (
        UniqueConstraint("attendance_daily_id", name="uq_deduction_daily_id"),
        UniqueConstraint("employee_id", "attendance_date", name="uq_deduction_emp_date"),
        Index("idx_deduction_emp_date", "employee_id", "attendance_date"),
        Index("idx_deduction_date", "attendance_date"),
    )

    def to_dict(self) -> dict:
        """Konversi objek AttendanceDeduction ke representasi dictionary."""
        return {
            "id": self.id,
            "attendance_daily_id": self.attendance_daily_id,
            "employee_id": self.employee_id,
            "attendance_date": self.attendance_date.strftime("%Y-%m-%d") if self.attendance_date else "",
            "late_minutes": self.late_minutes,
            "early_leave_minutes": self.early_leave_minutes,
            "deduction_late": self.deduction_late,
            "deduction_early_leave": self.deduction_early_leave,
            "deduction_missing_check_in": self.deduction_missing_check_in,
            "deduction_missing_check_out": self.deduction_missing_check_out,
            "total_deduction": self.total_deduction,
            "calculation_version": self.calculation_version,
            "calculated_at": self.calculated_at.strftime("%Y-%m-%d %H:%M:%S") if self.calculated_at else "-",
            "calculated_by": self.calculated_by or "-",
            "notes": self.notes or "",
        }

    def __repr__(self) -> str:
        return f"<AttendanceDeduction emp_id={self.employee_id} date={self.attendance_date} total={self.total_deduction}>"

