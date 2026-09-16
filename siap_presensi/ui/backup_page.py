"""
Halaman Backup Database SIAP.
Menyediakan fitur pencadangan database SQLite secara aman,
pemilihan lokasi berkas, riwayat file backup, dan placeholder restore.
"""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QScrollArea,
)
from config.settings import THEME, DB_PATH
from services.auth_service import CurrentSession
from services.backup_service import BackupService


class BackupPage(QWidget):
    """Halaman Backup dan Manajemen Cadangan Database SQLite."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh_backups_table()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {THEME['BG_PAGE']};")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # 1. Header
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        title = QLabel("Pencadangan Database (Backup)")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        subtitle = QLabel("Cadangkan database siap_presensi.db secara lokal untuk menjaga keamanan dan kesinambungan data.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {THEME['TEXT_MUTED']};")
        header_box.addWidget(title)
        header_box.addWidget(subtitle)
        layout.addLayout(header_box)

        # 2. Card Eksekusi Backup
        action_card = QFrame()
        action_card.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['BG_CARD']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        action_layout = QVBoxLayout(action_card)
        action_layout.setSpacing(12)

        card_title = QLabel("💾  Buat Cadangan Database Baru")
        card_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        action_layout.addWidget(card_title)

        info_lbl = QLabel(
            f"Database Sumber: {DB_PATH.resolve()}\n"
            "Nama File Otomatis: backup_siap_YYYYMMDD_HHMMSS.db\n"
            "Mekanisme: SQLite Online Backup API (Integritas Terjamin & Tanpa Menghentikan Sistem)"
        )
        info_lbl.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']}; line-height: 1.5;")
        action_layout.addWidget(info_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.backup_default_btn = QPushButton("🚀  Backup ke Folder Default (data/backups/)")
        self.backup_default_btn.setCursor(Qt.PointingHandCursor)
        self.backup_default_btn.setFixedHeight(40)
        self.backup_default_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                padding: 0 20px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        self.backup_default_btn.clicked.connect(self._on_backup_default)
        btn_row.addWidget(self.backup_default_btn)

        self.backup_custom_btn = QPushButton("📁  Pilih Lokasi Simpan Lain...")
        self.backup_custom_btn.setCursor(Qt.PointingHandCursor)
        self.backup_custom_btn.setFixedHeight(40)
        self.backup_custom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {THEME['TEXT_MAIN']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #f1f5f9;
            }}
        """)
        self.backup_custom_btn.clicked.connect(self._on_backup_custom)
        btn_row.addWidget(self.backup_custom_btn)

        btn_row.addStretch()

        # Tombol Restore (Placeholder)
        self.restore_btn = QPushButton("🔄  Restore Database (Tahap 2)")
        self.restore_btn.setCursor(Qt.PointingHandCursor)
        self.restore_btn.setFixedHeight(40)
        self.restore_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f8fafc;
                color: #94a3b8;
                border: 1px dashed #cbd5e1;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #f1f5f9;
                color: #64748b;
            }}
        """)
        self.restore_btn.clicked.connect(self._on_restore_placeholder)
        btn_row.addWidget(self.restore_btn)

        action_layout.addLayout(btn_row)
        layout.addWidget(action_card)

        # 3. Tabel Riwayat Backup
        history_card = QFrame()
        history_card.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['BG_CARD']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        history_layout = QVBoxLayout(history_card)
        history_layout.setSpacing(12)

        tbl_header = QHBoxLayout()
        tbl_title = QLabel("📋  Daftar Berkas Cadangan (data/backups/)")
        tbl_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        tbl_header.addWidget(tbl_title)
        tbl_header.addStretch()

        refresh_tbl_btn = QPushButton("🔄 Segarkan")
        refresh_tbl_btn.setCursor(Qt.PointingHandCursor)
        refresh_tbl_btn.setFixedHeight(30)
        refresh_tbl_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {THEME['BLUE_PRIMARY']};
                border: 1px solid {THEME['BLUE_PRIMARY']};
                border-radius: 4px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_LIGHT']};
            }}
        """)
        refresh_tbl_btn.clicked.connect(self.refresh_backups_table)
        tbl_header.addWidget(refresh_tbl_btn)
        history_layout.addLayout(tbl_header)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Nama File", "Ukuran", "Waktu Pembuatan", "Lokasi Lengkap"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: #f1f5f9;
                font-weight: 700;
                color: {THEME['TEXT_MAIN']};
                border: none;
                border-bottom: 1px solid {THEME['BORDER']};
                padding: 8px;
            }}
        """)
        history_layout.addWidget(self.table)

        layout.addWidget(history_card)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def refresh_backups_table(self):
        """Memuat daftar file cadangan di tabel."""
        backups = BackupService.get_existing_backups()
        self.table.setRowCount(len(backups))

        for row_idx, item in enumerate(backups):
            self.table.setItem(row_idx, 0, QTableWidgetItem(item["filename"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item["size_kb"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(item["created_at"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(item["filepath"]))

    def _on_backup_default(self):
        user_id = CurrentSession.get_instance().user_id
        success, message, path = BackupService.create_backup(user_id=user_id)
        if success:
            QMessageBox.information(self, "Backup Berhasil", f"✅ {message}")
            self.refresh_backups_table()
        else:
            QMessageBox.critical(self, "Backup Gagal", f"❌ {message}")

    def _on_backup_custom(self):
        filename = BackupService.generate_backup_filename()
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan File Backup Database",
            filename,
            "SQLite Database (*.db);;All Files (*)"
        )
        if save_path:
            user_id = CurrentSession.get_instance().user_id
            success, message, path = BackupService.create_backup(target_path=Path(save_path), user_id=user_id)
            if success:
                QMessageBox.information(self, "Backup Berhasil", f"✅ {message}\n\nTersimpan di:\n{save_path}")
                self.refresh_backups_table()
            else:
                QMessageBox.critical(self, "Backup Gagal", f"❌ {message}")

    def _on_restore_placeholder(self):
        QMessageBox.information(
            self,
            "Informasi Fitur Restore",
            "Fitur Restore Database secara penuh akan diaktifkan pada Tahap berikutnya dengan "
            "mekanisme verifikasi skema, locking database, dan fallback pemulihan otomatis."
        )
