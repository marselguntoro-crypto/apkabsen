"""
Jendela Utama (Main Window) Aplikasi Desktop SIAP.
Mengintegrasikan Sidebar Navigasi Kiri, Header Pengguna,
dan Stacked Widget Konten Antarhalaman (Dashboard, Pengaturan, Backup, dan Placeholder Modul).
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QLabel,
    QPushButton,
    QFrame,
    QMessageBox,
)
from config.settings import THEME, APP_NAME, APP_FULL_NAME, APP_SUBTITLE
from database.models import User, UserRole
from services.auth_service import AuthService, CurrentSession
from ui.widgets.sidebar import Sidebar
from ui.dashboard_page import DashboardPage
from ui.employees_page import EmployeesPage
from ui.import_module_page import ImportModulePage
from ui.raw_attendance_page import RawAttendancePage
from ui.attendance_hub_page import AttendanceHubPage
from ui.calendar_page import CalendarPage
from ui.deduction_calculation_page import DeductionCalculationPage
from ui.reports_hub_page import ReportsHubPage
from ui.settings_page import SettingsPage
from ui.backup_page import BackupPage
from ui.placeholder_page import PlaceholderPage


class MainWindow(QMainWindow):
    """Jendela kerja utama aplikasi SIAP."""

    logout_signal = Signal()

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle(f"{APP_NAME} - {APP_FULL_NAME}")
        self.resize(1366, 768)
        self.setMinimumSize(1024, 640)
        self._init_ui()

    def _init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout horizontal utama: Sidebar (Kiri) + Konten (Kanan)
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Sidebar Kiri
        self.sidebar = Sidebar(user_role=self.user.role, parent=self)
        self.sidebar.menu_selected.connect(self._on_navigation)
        self.sidebar.logout_requested.connect(self._on_logout_requested)
        root_layout.addWidget(self.sidebar)

        # 2. Area Konten Kanan: Header Atas + Stacked Pages
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 2a. Header Atas
        header_bar = self._create_header_bar()
        content_layout.addWidget(header_bar)

        # 2b. QStackedWidget untuk navigasi halaman
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {THEME['BG_PAGE']};")

        # Inisialisasi Halaman
        self.page_dashboard = DashboardPage(self)
        self.page_karyawan = EmployeesPage(self, user=self.user)
        self.page_import = ImportModulePage(self, user=self.user)
        self.page_absensi = AttendanceHubPage(self, user=self.user)
        self.page_kalender = CalendarPage(self, user=self.user)
        self.page_potongan = DeductionCalculationPage(self, user=self.user)
        self.page_laporan = ReportsHubPage(self, user=self.user)
        self.page_settings = SettingsPage(self)
        self.page_backup = BackupPage(self)

        # Tambahkan ke Stack sesuai index (0 s/d 8)
        self.stack.addWidget(self.page_dashboard)   # Index 0
        self.stack.addWidget(self.page_karyawan)    # Index 1
        self.stack.addWidget(self.page_import)      # Index 2
        self.stack.addWidget(self.page_absensi)     # Index 3
        self.stack.addWidget(self.page_kalender)    # Index 4
        self.stack.addWidget(self.page_potongan)    # Index 5
        self.stack.addWidget(self.page_laporan)     # Index 6
        self.stack.addWidget(self.page_settings)    # Index 7
        self.stack.addWidget(self.page_backup)      # Index 8

        content_layout.addWidget(self.stack)
        root_layout.addWidget(content_container)

    def _create_header_bar(self) -> QFrame:
        """Membuat bar header atas dengan identitas pengguna dan tombol logout cepat."""
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border-bottom: 1px solid {THEME['BORDER']};
            }}
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 10, 24, 10)

        # Judul Halaman Aktif / Breadcrumb
        self.breadcrumb_lbl = QLabel("Dashboard Utama")
        self.breadcrumb_lbl.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {THEME['NAVY_DARK']};
        """)
        h_layout.addWidget(self.breadcrumb_lbl)

        h_layout.addStretch()

        # Profil Pengguna
        user_info_box = QHBoxLayout()
        user_info_box.setSpacing(10)

        # Badge Role
        role_text = self.user.role.value
        role_color = THEME["BLUE_PRIMARY"] if self.user.role == UserRole.ADMIN else "#059669"
        role_bg = THEME["BLUE_LIGHT"] if self.user.role == UserRole.ADMIN else "#ecfdf5"

        role_badge = QLabel(f"  {role_text}  ")
        role_badge.setStyleSheet(f"""
            background-color: {role_bg};
            color: {role_color};
            font-size: 11px;
            font-weight: 700;
            border-radius: 4px;
            padding: 4px 6px;
            border: 1px solid {role_color}40;
        """)
        user_info_box.addWidget(role_badge)

        # Nama Lengkap Pengguna
        name_lbl = QLabel(self.user.full_name)
        name_lbl.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: {THEME['TEXT_MAIN']};
        """)
        user_info_box.addWidget(name_lbl)

        h_layout.addLayout(user_info_box)
        return header

    def _on_navigation(self, page_index: int, menu_key: str):
        """Menangani perpindahan halaman antar menu."""
        # Proteksi halaman khusus Admin (Index 7: Pengaturan, Index 8: Backup)
        if (page_index == 7 or page_index == 8) and self.user.role != UserRole.ADMIN:
            QMessageBox.warning(self, "Akses Ditolak", "Halaman ini hanya dapat diakses oleh Administrator.")
            return

        self.stack.setCurrentIndex(page_index)

        # Update label judul di header
        titles = {
            0: "Dashboard Utama",
            1: "Data Master Karyawan",
            2: "Import Berkas Absensi Mesin",
            3: "Data Transaksi Absensi (Mentah & Harian)",
            4: "Kalender Kerja & Jam Operasional",
            5: "Perhitungan Potongan Absensi",
            6: "Laporan & Rekapitulasi Presensi",
            7: "Pengaturan Sistem & Parameter",
            8: "Pencadangan Database (Backup)",
        }
        self.breadcrumb_lbl.setText(titles.get(page_index, "SIAP"))

        # Segarkan data halaman saat navigasi
        if page_index == 0:
            self.page_dashboard.refresh_data()
        elif page_index == 3:
            if hasattr(self.page_absensi, "page_daily"):
                self.page_absensi.page_daily.refresh_data()
            if hasattr(self.page_absensi, "page_raw"):
                self.page_absensi.page_raw.refresh_data()
        elif page_index == 4:
            self.page_kalender.refresh_calendar()
        elif page_index == 5:
            self.page_potongan.load_preview_data()
        elif page_index == 6:
            self.page_laporan.refresh_recap()
            self.page_laporan.refresh_daily()

    def _on_logout_requested(self):
        """Konfirmasi logout pengguna."""
        reply = QMessageBox.question(
            self,
            "Konfirmasi Logout",
            "Apakah Anda yakin ingin keluar dari sistem SIAP?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            AuthService.logout()
            self.logout_signal.emit()
            self.close()
