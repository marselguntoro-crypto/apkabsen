"""
Jendela Login Pengguna Aplikasi Desktop SIAP.
Menyediakan autentikasi akun Administrator dan Operator,
validasi kredensial, feedback error yang jelas, serta transisi ke Main Window.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QMessageBox,
)
from config.settings import THEME, APP_NAME, APP_FULL_NAME, APP_SUBTITLE, APP_VERSION
from database.models import User
from services.auth_service import AuthService
from utils.logger import get_logger

logger = get_logger("LoginWindow")


class LoginWindow(QWidget):
    """Jendela dialog login utama aplikasi SIAP."""

    login_success = Signal(User)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Login - {APP_NAME} {APP_FULL_NAME}")
        self.setFixedSize(460, 580)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {THEME['BG_PAGE']};")

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Kartu Kontainer Login
        card = QFrame()
        card.setFixedWidth(400)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['BG_CARD']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 12px;
                padding: 24px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)

        # Header Logo & Judul
        title_box = QVBoxLayout()
        title_box.setAlignment(Qt.AlignCenter)
        title_box.setSpacing(4)

        logo_lbl = QLabel(APP_NAME)
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 900;
            color: {THEME['NAVY_DARK']};
            letter-spacing: 2px;
        """)
        title_box.addWidget(logo_lbl)

        full_name_lbl = QLabel(APP_FULL_NAME)
        full_name_lbl.setAlignment(Qt.AlignCenter)
        full_name_lbl.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 700;
            color: {THEME['BLUE_PRIMARY']};
        """)
        title_box.addWidget(full_name_lbl)

        sub_lbl = QLabel(APP_SUBTITLE)
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet(f"""
            font-size: 11px;
            color: {THEME['TEXT_MUTED']};
        """)
        sub_lbl.setWordWrap(True)
        title_box.addWidget(sub_lbl)

        card_layout.addLayout(title_box)

        # Garis Pemisah
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color: {THEME['BORDER']}; height: 1px; margin: 6px 0;")
        card_layout.addWidget(divider)

        # Banner Pesan Error (Tersembunyi secara default)
        self.error_banner = QLabel("")
        self.error_banner.setStyleSheet(f"""
            background-color: #fef2f2;
            color: {THEME['DANGER']};
            border: 1px solid #fecaca;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 500;
        """)
        self.error_banner.setWordWrap(True)
        self.error_banner.setVisible(False)
        card_layout.addWidget(self.error_banner)

        # Form Input Username
        lbl_username = QLabel("Username")
        lbl_username.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {THEME['TEXT_MAIN']};")
        card_layout.addWidget(lbl_username)

        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Masukkan username akun")
        self.input_username.setFixedHeight(38)
        self.input_username.setStyleSheet(self._input_style())
        self.input_username.returnPressed.connect(self._on_login_clicked)
        card_layout.addWidget(self.input_username)

        # Form Input Password
        lbl_password = QLabel("Password")
        lbl_password.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {THEME['TEXT_MAIN']};")
        card_layout.addWidget(lbl_password)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Masukkan password")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setFixedHeight(38)
        self.input_password.setStyleSheet(self._input_style())
        self.input_password.returnPressed.connect(self._on_login_clicked)
        card_layout.addWidget(self.input_password)

        # Tombol Login
        self.btn_login = QPushButton("Masuk ke Sistem")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setFixedHeight(42)
        self.btn_login.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                font-size: 14px;
                font-weight: 700;
                border-radius: 6px;
                border: none;
                margin-top: 6px;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
            QPushButton:pressed {{
                background-color: #1e40af;
            }}
        """)
        self.btn_login.clicked.connect(self._on_login_clicked)
        card_layout.addWidget(self.btn_login)

        # Petunjuk Kredensial Awal untuk Development
        hint_box = QFrame()
        hint_box.setStyleSheet(f"""
            background-color: #f8fafc;
            border: 1px dashed {THEME['BORDER']};
            border-radius: 6px;
            padding: 8px;
            margin-top: 6px;
        """)
        hint_layout = QVBoxLayout(hint_box)
        hint_layout.setContentsMargins(6, 6, 6, 6)
        hint_layout.setSpacing(2)

        hint_title = QLabel("🔑 Akun Bawaan Sistem:")
        hint_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {THEME['NAVY_PRIMARY']};")
        hint_layout.addWidget(hint_title)

        hint_admin = QLabel("• Admin: admin / Admin@SIAP2025")
        hint_admin.setStyleSheet("font-size: 11px; color: #475569;")
        hint_layout.addWidget(hint_admin)

        hint_op = QLabel("• Operator: operator / Operator@SIAP2025")
        hint_op.setStyleSheet("font-size: 11px; color: #475569;")
        hint_layout.addWidget(hint_op)

        card_layout.addWidget(hint_box)

        main_layout.addWidget(card)

        # Versi di luar card
        ver_label = QLabel(f"Aplikasi Desktop SIAP - Versi {APP_VERSION}")
        ver_label.setAlignment(Qt.AlignCenter)
        ver_label.setStyleSheet("font-size: 11px; color: #94a3b8; margin-top: 10px;")
        main_layout.addWidget(ver_label)

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                background-color: #ffffff;
                color: {THEME['TEXT_MAIN']};
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME['BLUE_PRIMARY']};
                background-color: #f8fafc;
            }}
        """

    def _on_login_clicked(self):
        """Memproses aksi tombol login."""
        username = self.input_username.text().strip()
        password = self.input_password.text()

        self.error_banner.setVisible(False)

        if not username or not password:
            self._show_error("Harap isi username dan password.")
            return

        success, user, err_msg = AuthService.authenticate(username, password)
        if success and user:
            logger.info(f"Otorisasi sukses untuk akun '{username}'. Membuka Main Window.")
            self.login_success.emit(user)
        else:
            self._show_error(err_msg or "Username atau password salah.")

    def _show_error(self, message: str):
        """Menampilkan pesan error pada banner."""
        self.error_banner.setText(message)
        self.error_banner.setVisible(True)

    def reset_fields(self):
        """Mengosongkan form login saat pengguna logout."""
        self.input_username.clear()
        self.input_password.clear()
        self.error_banner.setVisible(False)
        self.input_username.setFocus()
