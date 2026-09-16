"""
Dialog Pemilihan Worksheet Excel untuk Aplikasi Desktop SIAP.
Ditampilkan jika berkas .xlsx memiliki lebih dari satu sheet.
"""
from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QFrame,
)
from config.settings import THEME


class WorksheetSelectionDialog(QDialog):
    """Dialog modal untuk memilih lembar kerja (worksheet) Excel."""

    def __init__(self, sheet_names: List[str], parent=None):
        super().__init__(parent)
        self.sheet_names = sheet_names
        self.selected_sheet: Optional[str] = sheet_names[0] if sheet_names else None

        self.setWindowTitle("Pilih Lembar Kerja (Worksheet) Excel")
        self.setFixedSize(440, 380)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Info
        title_lbl = QLabel("Pilih Worksheet Data Absensi")
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(
            "File Excel memiliki beberapa lembar kerja. Silakan pilih sheet "
            "yang berisi tabel transaksi absensi yang ingin di-import:"
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        layout.addWidget(desc_lbl)

        # List Widget Nama Sheet
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
                background-color: #ffffff;
                padding: 6px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: 6px;
                margin-bottom: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {THEME['BLUE_LIGHT']};
                color: {THEME['BLUE_PRIMARY']};
                font-weight: 600;
            }}
            QListWidget::item:hover:!selected {{
                background-color: #f1f5f9;
            }}
        """)

        for name in self.sheet_names:
            self.list_widget.addItem(f"📄  {name}")

        if self.sheet_names:
            self.list_widget.setCurrentRow(0)

        self.list_widget.doubleClicked.connect(self._on_confirm)
        layout.addWidget(self.list_widget)

        # Tombol Aksi Bawah
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Batal")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedHeight(38)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: #f1f5f9;
                color: {THEME['TEXT_MAIN']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #e2e8f0; }}
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_select = QPushButton("Pilih Worksheet Ini")
        self.btn_select.setCursor(Qt.PointingHandCursor)
        self.btn_select.setFixedHeight(38)
        self.btn_select.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {THEME['BLUE_HOVER']}; }}
        """)
        self.btn_select.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.btn_select)

        layout.addLayout(btn_layout)

    def _on_confirm(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            # Hilangkan icon prefix
            text = current_item.text().replace("📄  ", "").strip()
            self.selected_sheet = text
            self.accept()
