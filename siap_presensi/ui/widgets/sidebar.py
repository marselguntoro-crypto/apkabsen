"""
Komponen Navigasi Sidebar untuk Aplikasi Desktop SIAP.
Menyediakan navigasi menu sesuai Role (Admin / Operator),
indikator aktif, status pengguna, dan tombol logout.
"""
from typing import Dict, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QButtonGroup,
    QSpacerItem,
    QSizePolicy,
)
from config.settings import THEME, APP_NAME, APP_SUBTITLE, APP_VERSION
from database.models import UserRole


class Sidebar(QFrame):
    """Sidebar navigasi utama dengan kontrol hak akses berbasis Role."""

    menu_selected = Signal(int, str)  # (page_index, menu_key)
    logout_requested = Signal()
    about_requested = Signal()

    def __init__(self, user_role: UserRole = UserRole.ADMIN, parent=None):
        super().__init__(parent)
        self.user_role = user_role
        self.setObjectName("SidebarFrame")
        self.setFixedWidth(260)
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.nav_buttons: Dict[int, QPushButton] = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 20)
        layout.setSpacing(8)

        # Header Logo & Judul Aplikasi
        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(2)

        logo_title = QLabel(APP_NAME)
        logo_title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: 1px;
        """)
        brand_layout.addWidget(logo_title)

        app_desc = QLabel("Sistem Presensi & Potongan")
        app_desc.setStyleSheet(f"""
            font-size: 11px;
            color: {THEME['BLUE_ACCENT']};
            font-weight: 500;
        """)
        brand_layout.addWidget(app_desc)

        layout.addLayout(brand_layout)

        # Garis Pembatas
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {THEME['NAVY_LIGHT']}; height: 1px; margin: 12px 0;")
        layout.addWidget(separator)

        # Definisi Daftar Menu Navigasi
        # (index, key, label, icon_char, admin_only)
        menu_items = [
            (0, "dashboard", "Dashboard Utama", "📊", False),
            (1, "karyawan", "Data Karyawan", "👥", False),
            (2, "import", "Import Absensi", "📥", False),
            (3, "absensi", "Data Absensi", "🕒", False),
            (4, "kalender", "Kalender Kerja", "📅", False),
            (5, "potongan", "Perhitungan Potongan", "💰", False),
            (6, "laporan", "Laporan & Rekap", "📋", False),
            (7, "pengaturan", "Pengaturan Sistem", "⚙️", True),   # Khusus Admin
            (8, "backup", "Backup Database", "💾", True),        # Khusus Admin
        ]

        # Buat Tombol Menu
        for idx, key, label, icon, admin_only in menu_items:
            # Jika role OPERATOR dan menu khusus admin, sembunyikan
            if admin_only and self.user_role != UserRole.ADMIN:
                continue

            btn = QPushButton(f"  {icon}  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(42)
            btn.setStyleSheet(self._button_style())

            # Hubungkan sinyal klik
            btn.clicked.connect(lambda checked, i=idx, k=key: self._on_menu_clicked(i, k))

            self.button_group.addButton(btn, idx)
            self.nav_buttons[idx] = btn
            layout.addWidget(btn)

        # Pilih default menu Dashboard (index 0)
        if 0 in self.nav_buttons:
            self.nav_buttons[0].setChecked(True)

        # Spacer fleksibel untuk mendorong tombol logout ke bagian bawah
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Divider sebelum Footer
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"background-color: {THEME['NAVY_LIGHT']}; height: 1px; margin: 8px 0;")
        layout.addWidget(sep2)

        # Tombol Tentang Aplikasi
        about_btn = QPushButton("  ℹ️  Tentang SIAP")
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.setFixedHeight(36)
        about_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #94a3b8;
                font-size: 12px;
                font-weight: 500;
                text-align: left;
                padding-left: 12px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME['NAVY_LIGHT']};
                color: #ffffff;
            }}
        """)
        about_btn.clicked.connect(self.about_requested.emit)
        layout.addWidget(about_btn)

        # Tombol Logout
        logout_btn = QPushButton("  🚪  Keluar (Logout)")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(40)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #fca5a5;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                padding-left: 12px;
                border-radius: 6px;
                border: 1px solid #7f1d1d;
            }}
            QPushButton:hover {{
                background-color: #991b1b;
                color: #ffffff;
            }}
        """)
        logout_btn.clicked.connect(self.logout_requested.emit)
        layout.addWidget(logout_btn)

        # Info Versi Aplikasi
        version_lbl = QLabel(f"Versi {APP_VERSION}")
        version_lbl.setAlignment(Qt.AlignCenter)
        version_lbl.setStyleSheet("font-size: 11px; color: #64748b; margin-top: 8px;")
        layout.addWidget(version_lbl)

        # Container Style
        self.setStyleSheet(f"""
            QFrame#SidebarFrame {{
                background-color: {THEME['NAVY_PRIMARY']};
                border-right: 1px solid {THEME['NAVY_DARK']};
            }}
        """)

    def _button_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: transparent;
                color: #cbd5e1;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                padding-left: 12px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME['NAVY_LIGHT']};
                color: #ffffff;
            }}
            QPushButton:checked {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                font-weight: 600;
            }}
        """

    def _on_menu_clicked(self, page_index: int, menu_key: str):
        self.menu_selected.emit(page_index, menu_key)

    def set_active_index(self, index: int):
        """Memperbarui visual tombol menu yang aktif."""
        if index in self.nav_buttons:
            self.nav_buttons[index].setChecked(True)
