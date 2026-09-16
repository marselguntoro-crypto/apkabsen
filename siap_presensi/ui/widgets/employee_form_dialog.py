"""
Dialog Form Tambah & Edit Master Data Karyawan SIAP (Tahap 2).
Menyediakan antarmuka input yang rapi, validasi field wajib,
pemilihan tanggal mulai kerja, dan status aktif/nonaktif.
"""
from typing import Optional, Dict, Any
from datetime import datetime, date
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTextEdit,
    QPushButton,
    QFrame,
    QMessageBox,
)
from config.settings import THEME
from utils.validators import validate_employee_payload


class EmployeeFormDialog(QDialog):
    """Dialog modal untuk membuat atau mengedit data karyawan."""

    def __init__(self, parent=None, employee_data: Optional[Dict[str, Any]] = None, unit_suggestions: Optional[list] = None):
        super().__init__(parent)
        self.employee_data = employee_data
        self.is_edit_mode = employee_data is not None
        self.unit_suggestions = unit_suggestions or []

        self.setWindowTitle("Edit Data Karyawan" if self.is_edit_mode else "Tambah Karyawan Baru")
        self.setFixedSize(580, 640)
        self.setModal(True)
        self._init_ui()

        if self.is_edit_mode and self.employee_data:
            self._populate_data(self.employee_data)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. Header Dialog
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        title_lbl = QLabel("Edit Profil Karyawan" if self.is_edit_mode else "Tambah Karyawan Baru")
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {THEME['NAVY_PRIMARY']};")
        header_layout.addWidget(title_lbl)

        sub_lbl = QLabel("Pastikan identitas (No. ID / PIN atau No. Pegawai) diisi untuk integrasi mesin absensi.")
        sub_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
        header_layout.addWidget(sub_lbl)

        layout.addLayout(header_layout)

        # Garis Pembatas
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #e2e8f0; height: 1px; margin: 4px 0;")
        layout.addWidget(sep)

        # 2. Form Grid Fields
        form_grid = QGridLayout()
        form_grid.setSpacing(10)
        form_grid.setColumnStretch(0, 1)
        form_grid.setColumnStretch(1, 1)

        input_style = """
            QLineEdit, QComboBox, QDateEdit, QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                color: #0f172a;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
                border: 1.5px solid #2563eb;
                background-color: #f8fafc;
            }
        """
        self.setStyleSheet(input_style)

        # Field: Nama Lengkap (Wajib)
        lbl_nama = QLabel("Nama Lengkap Karyawan *")
        lbl_nama.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        self.txt_nama = QLineEdit()
        self.txt_nama.setPlaceholderText("Contoh: Budi Santoso, S.Kom")
        form_grid.addWidget(lbl_nama, 0, 0, 1, 2)
        form_grid.addWidget(self.txt_nama, 1, 0, 1, 2)

        # Field: No ID Mesin / PIN (Penting untuk absensi)
        lbl_no_id = QLabel("No. ID / PIN Mesin Absensi")
        lbl_no_id.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        self.txt_no_id = QLineEdit()
        self.txt_no_id.setPlaceholderText("Contoh: 1001 atau 00125")
        form_grid.addWidget(lbl_no_id, 2, 0)
        form_grid.addWidget(self.txt_no_id, 3, 0)

        # Field: No Pegawai / NIP
        lbl_emp_num = QLabel("No. Pegawai / NIP")
        lbl_emp_num.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        self.txt_emp_num = QLineEdit()
        self.txt_emp_num.setPlaceholderText("Contoh: EMP-2025-001")
        form_grid.addWidget(lbl_emp_num, 2, 1)
        form_grid.addWidget(self.txt_emp_num, 3, 1)

        # Field: NIK KTP
        lbl_nik = QLabel("Nomor Induk Kependudukan (NIK)")
        lbl_nik.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        self.txt_nik = QLineEdit()
        self.txt_nik.setPlaceholderText("16 digit NIK KTP (opsional)")
        form_grid.addWidget(lbl_nik, 4, 0)
        form_grid.addWidget(self.txt_nik, 5, 0)

        # Field: Unit / Departemen
        lbl_unit = QLabel("Unit / Departemen Kerja")
        lbl_unit.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        self.cmb_unit = QComboBox()
        self.cmb_unit.setEditable(True)
        self.cmb_unit.addItem("")  # Pilihan kosong
        for u in self.unit_suggestions:
            if u:
                self.cmb_unit.addItem(u)
        form_grid.addWidget(lbl_unit, 4, 1)
        form_grid.addWidget(self.cmb_unit, 5, 1)

        # Field: Jabatan
        lbl_jabatan = QLabel("Jabatan / Posisi")
        lbl_jabatan.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        self.txt_jabatan = QLineEdit()
        self.txt_jabatan.setPlaceholderText("Contoh: Staff Keuangan, Supervisor")
        form_grid.addWidget(lbl_jabatan, 6, 0)
        form_grid.addWidget(self.txt_jabatan, 7, 0)

        # Field: Email
        lbl_email = QLabel("Alamat Email")
        lbl_email.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("contoh: budi@instansi.go.id")
        form_grid.addWidget(lbl_email, 6, 1)
        form_grid.addWidget(self.txt_email, 7, 1)

        # Field: Status Kepegawaian
        lbl_status = QLabel("Status Kepegawaian")
        lbl_status.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["AKTIF", "NONAKTIF"])
        form_grid.addWidget(lbl_status, 8, 0)
        form_grid.addWidget(self.cmb_status, 9, 0)

        # Field: Tanggal Mulai Kerja
        lbl_tgl = QLabel("Tanggal Mulai Kerja")
        lbl_tgl.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        self.dt_mulai = QDateEdit()
        self.dt_mulai.setCalendarPopup(True)
        self.dt_mulai.setDate(QDate.currentDate())
        self.dt_mulai.setDisplayFormat("yyyy-MM-dd")
        form_grid.addWidget(lbl_tgl, 8, 1)
        form_grid.addWidget(self.dt_mulai, 9, 1)

        # Field: Keterangan Tambahan
        lbl_ket = QLabel("Catatan Tambahan")
        lbl_ket.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        self.txt_keterangan = QTextEdit()
        self.txt_keterangan.setPlaceholderText("Informasi tambahan mengenai karyawan (opsional)...")
        self.txt_keterangan.setFixedHeight(60)
        form_grid.addWidget(lbl_ket, 10, 0, 1, 2)
        form_grid.addWidget(self.txt_keterangan, 11, 0, 1, 2)

        layout.addLayout(form_grid)

        # Error display banner
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("font-size: 11px; color: #dc2626; font-weight: 600;")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setVisible(False)
        layout.addWidget(self.lbl_error)

        # 3. Action Buttons Footer
        layout.addStretch()
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)

        self.btn_cancel = QPushButton("Batal")
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
                color: #1e293b;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_cancel)

        footer_layout.addStretch()

        self.btn_save = QPushButton("Simpan Perubahan" if self.is_edit_mode else "Simpan Karyawan")
        self.btn_save.setFixedHeight(36)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        self.btn_save.clicked.connect(self._on_save_clicked)
        footer_layout.addWidget(self.btn_save)

        layout.addLayout(footer_layout)

    def _populate_data(self, data: Dict[str, Any]):
        """Mengisi nilai form dari objek data yang diedit."""
        self.txt_nama.setText(data.get("nama") or "")
        self.txt_emp_num.setText(data.get("emp_num") or "")
        self.txt_no_id.setText(data.get("no_id") or "")
        self.txt_nik.setText(data.get("nik") or "")

        unit_val = data.get("unit") or ""
        if unit_val and unit_val != "-":
            idx = self.cmb_unit.findText(unit_val)
            if idx >= 0:
                self.cmb_unit.setCurrentIndex(idx)
            else:
                self.cmb_unit.setEditText(unit_val)

        jab_val = data.get("jabatan") or ""
        self.txt_jabatan.setText(jab_val if jab_val != "-" else "")

        email_val = data.get("email") or ""
        self.txt_email.setText(email_val if email_val != "-" else "")

        status_val = data.get("status") or "AKTIF"
        self.cmb_status.setCurrentText(status_val)

        tgl_str = data.get("tanggal_mulai")
        if tgl_str and tgl_str != "-":
            try:
                dt = datetime.strptime(tgl_str, "%Y-%m-%d")
                self.dt_mulai.setDate(QDate(dt.year, dt.month, dt.day))
            except Exception:
                pass

        self.txt_keterangan.setPlainText(data.get("keterangan") or "")

    def get_form_data(self) -> Dict[str, Any]:
        """Mengambil data hasil input form."""
        q_date = self.dt_mulai.date()
        date_str = f"{q_date.year():04d}-{q_date.month():02d}-{q_date.day():02d}"

        return {
            "nama": self.txt_nama.text().strip(),
            "emp_num": self.txt_emp_num.text().strip(),
            "no_id": self.txt_no_id.text().strip(),
            "nik": self.txt_nik.text().strip(),
            "unit": self.cmb_unit.currentText().strip(),
            "jabatan": self.txt_jabatan.text().strip(),
            "email": self.txt_email.text().strip(),
            "status": self.cmb_status.currentText(),
            "tanggal_mulai": date_str,
            "keterangan": self.txt_keterangan.toPlainText().strip(),
        }

    def _on_save_clicked(self):
        """Validasi client-side sebelum konfirmasi accept."""
        data = self.get_form_data()
        is_valid, errors = validate_employee_payload(data)
        if not is_valid:
            self.lbl_error.setText("• " + "\n• ".join(errors))
            self.lbl_error.setVisible(True)
            return

        self.lbl_error.setVisible(False)
        self.accept()
