"""
Dialog Tentang Aplikasi (About Application) untuk SIAP.
Menampilkan identitas resmi sistem, versi, tahun, pengembang, lisensi,
serta diagnosa lokasi direktori runtime Windows (%LOCALAPPDATA%\\SIAP).
"""
import sys
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QScrollArea,
    QWidget,
)
from config.settings import (
    THEME,
    APP_NAME,
    APP_FULL_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    DB_VERSION,
    APP_YEAR,
    APP_DEVELOPER,
    APP_ORGANIZATION,
    APP_LICENSE,
    DATA_DIR,
    DB_PATH,
    BACKUP_DIR,
    LOGS_DIR,
    EXPORTS_DIR,
    ASSETS_DIR,
)


class AboutDialog(QDialog):
    """Dialog informasi Tentang Aplikasi SIAP."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Tentang {APP_NAME}")
        self.setFixedSize(620, 560)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Branding
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['NAVY_DARK']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        h_layout = QVBoxLayout(header_frame)
        h_layout.setContentsMargins(16, 16, 16, 16)
        h_layout.setSpacing(4)

        app_title = QLabel(APP_NAME)
        app_title.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: 800; letter-spacing: 1px;")
        h_layout.addWidget(app_title)

        app_full = QLabel(APP_FULL_NAME)
        app_full.setStyleSheet(f"color: {THEME['BLUE_ACCENT']}; font-size: 13px; font-weight: 600;")
        h_layout.addWidget(app_full)

        app_sub = QLabel(APP_SUBTITLE)
        app_sub.setStyleSheet("color: #94a3b8; font-size: 11px;")
        h_layout.addWidget(app_sub)

        layout.addWidget(header_frame)

        # Scrollable Detail Information
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(14)

        # 1. Spesifikasi Rilis
        spec_frame = self._create_section_frame("📋  Spesifikasi Rilis & Versi")
        spec_grid = QGridLayout()
        spec_grid.setSpacing(8)

        spec_items = [
            ("Versi Aplikasi", f"v{APP_VERSION} (Final Production Build)"),
            ("Versi Skema Database", f"v{DB_VERSION}"),
            ("Tahun Rilis", APP_YEAR),
            ("Arsitektur Target", "Windows 10 & 11 (64-bit Architecture)"),
            ("Framework UI", "PySide6 (Qt for Python)"),
            ("Mesin Database", "SQLite 3 with WAL & Foreign Keys"),
            ("Pengembang", APP_DEVELOPER),
            ("Instansi", APP_ORGANIZATION),
            ("Lisensi", APP_LICENSE),
        ]

        for row, (lbl, val) in enumerate(spec_items):
            l = QLabel(f"{lbl}:")
            l.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {THEME['TEXT_MUTED']};")
            v = QLabel(val)
            v.setStyleSheet(f"font-weight: 500; font-size: 12px; color: {THEME['TEXT_MAIN']};")
            spec_grid.addWidget(l, row, 0)
            spec_grid.addWidget(v, row, 1)

        spec_frame.layout().addLayout(spec_grid)
        content_layout.addWidget(spec_frame)

        # 2. Lokasi Direktori Sistem Windows
        path_frame = self._create_section_frame("📂  Lokasi Direktori Runtime Pengguna")
        path_grid = QGridLayout()
        path_grid.setSpacing(8)

        paths = [
            ("Folder Utama Data", str(DATA_DIR)),
            ("Database Aktif", str(DB_PATH)),
            ("Pencadangan (Backups)", str(BACKUP_DIR)),
            ("Berkas Log (Logs)", str(LOGS_DIR)),
            ("Ekspor Laporan (Exports)", str(EXPORTS_DIR)),
        ]

        for row, (lbl, val) in enumerate(paths):
            l = QLabel(f"{lbl}:")
            l.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {THEME['TEXT_MUTED']};")
            v = QLabel(val)
            v.setWordWrap(True)
            v.setStyleSheet(f"font-family: Consolas, monospace; font-size: 11px; color: {THEME['BLUE_PRIMARY']};")
            path_grid.addWidget(l, row, 0)
            path_grid.addWidget(v, row, 1)

        path_frame.layout().addLayout(path_grid)
        content_layout.addWidget(path_frame)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Footer Tombol Aksi
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        open_folder_btn = QPushButton("📁  Buka Folder Data SIAP")
        open_folder_btn.setFixedHeight(36)
        open_folder_btn.setCursor(Qt.PointingHandCursor)
        open_folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f1f5f9;
                color: {THEME['NAVY_DARK']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #e2e8f0;
            }}
        """)
        open_folder_btn.clicked.connect(self._open_data_folder)
        btn_layout.addWidget(open_folder_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Tutup")
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 24px;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _create_section_frame(self, title_text: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        v = QVBoxLayout(frame)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(10)

        t = QLabel(title_text)
        t.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        v.addWidget(t)
        return frame

    def _open_data_folder(self):
        """Membuka folder runtime data pengguna di Windows Explorer."""
        try:
            folder_url = QUrl.fromLocalFile(str(DATA_DIR))
            QDesktopServices.openUrl(folder_url)
        except Exception:
            try:
                if sys.platform == "win32":
                    subprocess.Popen(["explorer", str(DATA_DIR)])
            except Exception:
                pass
