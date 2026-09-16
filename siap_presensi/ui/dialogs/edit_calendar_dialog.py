"""
Dialog Pengubahan Status Tanggal Kalender Kerja (Edit Calendar Day Dialog).
Memungkinkan Admin/Operator untuk mengubah status hari kerja, libur nasional,
cuti bersama, akhir pekan, jam operasional terjadwal, dan catatan.
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
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QFrame,
)
from config.settings import THEME
from database.models import CalendarStatus
from services.calendar_service import CalendarService


class EditCalendarDayDialog(QDialog):
    """Dialog edit status tanggal kalender kerja."""

    def __init__(self, day_data: Dict[str, Any], user_name: str = "ADMIN", parent=None):
        super().__init__(parent)
        self.day_data = day_data
        self.user_name = user_name
        self.setWindowTitle(f"Ubah Status Kalender - {day_data.get('tanggal', '')}")
        self.setFixedWidth(460)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel(f"Penyesuaian Hari: {self.day_data.get('day_name', '')}, {self.day_data.get('tanggal', '')}")
        header.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        layout.addWidget(header)

        sub = QLabel("Ubah status hari kerja, libur, atau sesuaikan jam operasional khusus.")
        sub.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        layout.addWidget(sub)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color: {THEME['BORDER']};")
        layout.addWidget(divider)

        # Form
        form = QFormLayout()
        form.setSpacing(12)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "HARI_KERJA",
            "AKHIR_PEKAN",
            "LIBUR",
            "HARI_KERJA_KHUSUS",
            "CUTI_BERSAMA",
            "LIBUR_NASIONAL",
        ])
        cur_status = self.day_data.get("calendar_status", "HARI_KERJA")
        idx = self.status_combo.findText(cur_status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        form.addRow("Status Kalender:", self.status_combo)

        # Jam Masuk
        self.in_input = QLineEdit()
        self.in_input.setPlaceholderText("HH:MM (misal 08:15)")
        raw_in = self.day_data.get("scheduled_check_in", "")
        self.in_input.setText(raw_in if raw_in != "-" else "08:15")
        form.addRow("Jam Masuk Terjadwal:", self.in_input)

        # Jam Pulang
        self.out_input = QLineEdit()
        self.out_input.setPlaceholderText("HH:MM (misal 16:30 atau 17:00)")
        raw_out = self.day_data.get("scheduled_check_out", "")
        self.out_input.setText(raw_out if raw_out != "-" else "16:30")
        form.addRow("Jam Pulang Terjadwal:", self.out_input)

        # Keterangan
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Alasan penyesuaian (misal: Hari Kemerdekaan RI, Cuti Bersama Idul Fitri)")
        self.desc_input.setFixedHeight(70)
        self.desc_input.setText(self.day_data.get("description", ""))
        form.addRow("Keterangan:", self.desc_input)

        layout.addLayout(form)

        # Trigger update field visibilitas
        self._on_status_changed(self.status_combo.currentText())

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

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
            QPushButton:hover {{
                background-color: #e2e8f0;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Simpan Perubahan")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: white;
                border: none;
                padding: 8px 18px;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        save_btn.clicked.connect(self._save_changes)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_status_changed(self, text: str):
        """Aktifkan/nonaktifkan jam operasional sesuai tipe status hari."""
        is_working = text in ["HARI_KERJA", "HARI_KERJA_KHUSUS"]
        self.in_input.setEnabled(is_working)
        self.out_input.setEnabled(is_working)
        if not is_working:
            self.in_input.setStyleSheet("background-color: #f8fafc; color: #94a3b8;")
            self.out_input.setStyleSheet("background-color: #f8fafc; color: #94a3b8;")
        else:
            self.in_input.setStyleSheet("background-color: white; color: #0f172a;")
            self.out_input.setStyleSheet("background-color: white; color: #0f172a;")

    def _save_changes(self):
        status_str = self.status_combo.currentText()
        try:
            status_enum = CalendarStatus[status_str]
        except KeyError:
            status_enum = CalendarStatus.HARI_KERJA

        in_val = self.in_input.text().strip() if self.in_input.isEnabled() else None
        out_val = self.out_input.text().strip() if self.out_input.isEnabled() else None
        desc_val = self.desc_input.toPlainText().strip()

        calendar_id = self.day_data.get("id")
        if not calendar_id:
            QMessageBox.critical(self, "Kesalahan", "ID Kalender tidak valid.")
            return

        res = CalendarService.update_calendar_day(
            calendar_id=calendar_id,
            status=status_enum,
            check_in=in_val,
            check_out=out_val,
            description=desc_val,
            updated_by=self.user_name,
        )

        if res.get("success"):
            QMessageBox.information(self, "Berhasil", res.get("message", "Perubahan berhasil disimpan."))
            self.accept()
        else:
            QMessageBox.critical(self, "Gagal", res.get("message", "Gagal menyimpan perubahan."))
