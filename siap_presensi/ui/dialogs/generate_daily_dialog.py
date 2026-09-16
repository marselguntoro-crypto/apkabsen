"""
Dialog Eksekusi Pembentukan Absensi Harian (Generate Daily Attendance Dialog).
Menyediakan pemilihan mode pemrosesan, filter unit, serta konfirmasi eksekusi aman.
"""
from typing import Optional, Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QFrame,
    QMessageBox,
)
from config.settings import THEME


class GenerateDailyAttendanceDialog(QDialog):
    """Dialog konfigurasi dan eksekusi pembentukan absensi harian."""

    def __init__(self, year: int, month: int, month_name: str, units: list, parent=None):
        super().__init__(parent)
        self.year = year
        self.month = month
        self.month_name = month_name
        self.units = units
        self.selected_mode = "GENERATE_NEW"
        self.selected_unit = "ALL"

        self.setWindowTitle(f"Proses Absensi Harian - {self.month_name} {self.year}")
        self.setFixedWidth(500)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        h_lbl = QLabel(f"Pembentukan Absensi Harian: {self.month_name} {self.year}")
        h_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {THEME['NAVY_DARK']};")
        layout.addWidget(h_lbl)

        sub_lbl = QLabel(
            "Sistem akan memadukan Master Karyawan Aktif x Hari Kerja Kalender x Transaksi Absensi Mentah.\n"
            "Status kehadiran (Hadir Lengkap, Hanya Masuk, Hanya Pulang, Tidak Absen) akan dibentuk."
        )
        sub_lbl.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']}; line-height: 1.4;")
        layout.addWidget(sub_lbl)

        # Box Peringatan Tahap 4
        notice_box = QFrame()
        notice_box.setStyleSheet(f"""
            QFrame {{
                background-color: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        n_layout = QVBoxLayout(notice_box)
        n_lbl = QLabel("ℹ️ Catatan Tahap 4:\nProses ini fokus pada pencocokan data scan dan penentuan status kehadiran. Nominal potongan rupiah akan dihitung pada Tahap 5.")
        n_lbl.setStyleSheet("font-size: 11px; color: #166534; font-weight: 500;")
        n_lbl.setWordWrap(True)
        n_layout.addWidget(n_lbl)
        layout.addWidget(notice_box)

        # Mode Selection
        mode_box = QFrame()
        mode_box.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
            }}
        """)
        m_layout = QVBoxLayout(mode_box)
        m_layout.setContentsMargins(14, 12, 14, 12)
        m_layout.setSpacing(10)

        m_title = QLabel("Pilih Mode Pemrosesan:")
        m_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        m_layout.addWidget(m_title)

        self.btn_group = QButtonGroup(self)

        self.radio_new = QRadioButton("Hanya Data Baru (GENERATE_NEW)\nHanya memproses karyawan & hari kerja yang belum memiliki catatan harian.")
        self.radio_new.setChecked(True)
        self.btn_group.addButton(self.radio_new, 1)
        m_layout.addWidget(self.radio_new)

        self.radio_regen = QRadioButton("Bentuk Ulang Seluruh Periode (REGENERATE)\nMenghitung ulang status seluruh karyawan pada periode ini berdasarkan data mentah terbaru.")
        self.btn_group.addButton(self.radio_regen, 2)
        m_layout.addWidget(self.radio_regen)

        layout.addWidget(mode_box)

        # Filter Unit
        form = QFormLayout()
        self.unit_combo = QComboBox()
        self.unit_combo.addItem("Semua Unit Kerja", "ALL")
        for u in self.units:
            if u:
                self.unit_combo.addItem(u, u)
        form.addRow("Batasi ke Unit:", self.unit_combo)
        layout.addLayout(form)

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        btn_box.addStretch()

        cancel_btn = QPushButton("Batal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid {THEME['BORDER']};
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        self.process_btn = QPushButton("Mulai Proses")
        self.process_btn.setCursor(Qt.PointingHandCursor)
        self.process_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        self.process_btn.clicked.connect(self._on_confirm)
        btn_box.addWidget(self.process_btn)

        layout.addLayout(btn_box)

    def _on_confirm(self):
        if self.radio_regen.isChecked():
            self.selected_mode = "REGENERATE"
        else:
            self.selected_mode = "GENERATE_NEW"

        self.selected_unit = self.unit_combo.currentData()
        self.accept()
