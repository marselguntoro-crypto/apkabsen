"""
Modul Hub Data Absensi (AttendanceHubPage) untuk SIAP.
Menyediakan antarmuka bertab untuk:
- Tab 1: Data Absensi Mentah (Raw Scans - attendance_raw)
- Tab 2: Absensi Harian & Kehadiran (Daily Attendance - attendance_daily)
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
from ui.raw_attendance_page import RawAttendancePage
from ui.daily_attendance_page import DailyAttendancePage


class AttendanceHubPage(QWidget):
    """Container tab ganda untuk Data Mentah Absensi dan Absensi Harian Terpadu."""

    def __init__(self, parent=None, user: Optional[User] = None):
        super().__init__(parent)
        self.user = user
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {THEME['BG_PAGE']};
            }}
            QTabBar::tab {{
                background-color: #e2e8f0;
                color: #475569;
                font-weight: 700;
                font-size: 13px;
                padding: 12px 24px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {THEME['BG_PAGE']};
                color: {THEME['BLUE_PRIMARY']};
                border-bottom: 2px solid {THEME['BLUE_PRIMARY']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #cbd5e1;
            }}
        """)

        # Tab 1: Absensi Harian (Tahap 4)
        self.page_daily = DailyAttendancePage(self, user=self.user)
        self.tab_widget.addTab(self.page_daily, "📋  Absensi Harian (Daily Records)")

        # Tab 2: Data Mentah (Tahap 3)
        self.page_raw = RawAttendancePage(self, user=self.user)
        self.tab_widget.addTab(self.page_raw, "🕒  Data Mentah Absensi (Raw Scans)")

        layout.addWidget(self.tab_widget)
