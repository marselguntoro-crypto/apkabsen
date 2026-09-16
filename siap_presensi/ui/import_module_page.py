"""
Modul Kontainer Import Absensi Terpadu untuk SIAP.
Menggabungkan:
- Tab 1: Unggah & Import Absensi Excel (ImportAttendancePage)
- Tab 2: Riwayat Batch Import (ImportHistoryPage)
"""
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)
from config.settings import THEME
from database.models import User
from ui.import_attendance_page import ImportAttendancePage
from ui.import_history_page import ImportHistoryPage


class ImportModulePage(QWidget):
    """Kontainer tab untuk modul import absensi dan riwayat batch."""

    def __init__(self, parent=None, user: Optional[User] = None):
        super().__init__(parent)
        self.user = user
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {THEME['BG_PAGE']};
            }}
            QTabBar::tab {{
                background-color: #F1F5F9;
                color: {THEME['TEXT_MUTED']};
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                background-color: #ffffff;
                color: {THEME['BLUE_PRIMARY']};
                border-bottom: 2px solid {THEME['BLUE_PRIMARY']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #E2E8F0;
            }}
        """)

        self.page_upload = ImportAttendancePage(self, user=self.user)
        self.page_history = ImportHistoryPage(self, user=self.user)

        self.tabs.addTab(self.page_upload, "  📥  Unggah & Import Absensi  ")
        self.tabs.addTab(self.page_history, "  📜  Riwayat Batch Import  ")

        # Saat berpindah ke tab riwayat, segarkan data secara otomatis
        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tabs)

    def _on_tab_changed(self, idx: int):
        if idx == 1:
            self.page_history.refresh_history()
