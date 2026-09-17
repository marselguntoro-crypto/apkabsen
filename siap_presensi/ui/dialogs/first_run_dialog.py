"""
Dialog Setup Awal (First-Run Setup) dan Panduan Cepat SIAP.
Muncul saat Administrator login pertama kali atau masih menggunakan kata sandi default awal.
Memfasilitasi pembaruan kata sandi awal demi keamanan dan memberikan ringkasan panduan alur kerja.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QMessageBox,
    QTextBrowser,
)
from config.settings import THEME, APP_NAME, APP_FULL_NAME, APP_VERSION
from database.models import User
from services.auth_service import AuthService


class FirstRunSetupDialog(QDialog):
    """Dialog setup awal pengguna baru & penggantian password default."""

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle(f"Selamat Datang di {APP_NAME} - Konfigurasi Awal")
        self.setFixedSize(580, 520)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header Selamat Datang
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['NAVY_DARK']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        h_layout = QVBoxLayout(header_frame)
        h_layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel(f"🎉  Selamat Datang di {APP_NAME}")
        title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: 700;")
        h_layout.addWidget(title)

        subtitle = QLabel(f"{APP_FULL_NAME} (Versi {APP_VERSION})")
        subtitle.setStyleSheet(f"color: {THEME['BLUE_ACCENT']}; font-size: 12px; font-weight: 500;")
        h_layout.addWidget(subtitle)

        layout.addWidget(header_frame)

        # Panduan Singkat Alur Operasional
        guide_box = QTextBrowser()
        guide_box.setFixedHeight(140)
        guide_box.setStyleSheet(f"""
            QTextBrowser {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                color: {THEME['TEXT_MAIN']};
            }}
        """)
        guide_box.setHtml(f"""
            <b>Panduan Singkat Alur Kerja Operasional:</b>
            <ol style="margin-top: 4px; margin-bottom: 4px; padding-left: 20px;">
                <li><b>Master Karyawan:</b> Pastikan nomor ID/PIN fingerprint karyawan sesuai data master.</li>
                <li><b>Kalender Kerja:</b> Generate jadwal hari kerja bulanan dan tandai tanggal libur nasional.</li>
                <li><b>Import Berkas Scan:</b> Unggah file Excel (.xlsx/.xls) hasil export mesin fingerprint.</li>
                <li><b>Pembentukan Absensi & Hitung Potongan:</b> Proses data mentah menjadi absensi harian dan nominal denda keterlambatan/ketidakhadiran secara otomatis.</li>
                <li><b>Laporan & Backup:</b> Ekspor rekapitulasi ke Excel/PDF dan lakukan pencadangan rutin.</li>
            </ol>
        """)
        layout.addWidget(guide_box)

        # Form Penggantian Kata Sandi Awal
        form_title = QLabel("🔒  Keamanan: Ganti Kata Sandi Bawaan Awal")
        form_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        layout.addWidget(form_title)

        warn_lbl = QLabel(
            "Akun Administrator Anda saat ini menggunakan kata sandi bawaan awal pabrik. "
            "Sangat disarankan untuk mengubah kata sandi sekarang."
        )
        warn_lbl.setWordWrap(True)
        warn_lbl.setStyleSheet(f"font-size: 12px; color: {THEME['WARNING']}; font-weight: 500;")
        layout.addWidget(warn_lbl)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(8)

        self.old_pass_input = QLineEdit()
        self.old_pass_input.setPlaceholderText("Kata Sandi Saat Ini (Admin@SIAP2025)")
        self.old_pass_input.setEchoMode(QLineEdit.Password)
        self.old_pass_input.setFixedHeight(36)
        self.old_pass_input.setStyleSheet(self._input_style())
        form_layout.addWidget(self.old_pass_input)

        self.new_pass_input = QLineEdit()
        self.new_pass_input.setPlaceholderText("Kata Sandi Baru (Minimal 6 Karakter)")
        self.new_pass_input.setEchoMode(QLineEdit.Password)
        self.new_pass_input.setFixedHeight(36)
        self.new_pass_input.setStyleSheet(self._input_style())
        form_layout.addWidget(self.new_pass_input)

        self.confirm_pass_input = QLineEdit()
        self.confirm_pass_input.setPlaceholderText("Konfirmasi Kata Sandi Baru")
        self.confirm_pass_input.setEchoMode(QLineEdit.Password)
        self.confirm_pass_input.setFixedHeight(36)
        self.confirm_pass_input.setStyleSheet(self._input_style())
        form_layout.addWidget(self.confirm_pass_input)

        layout.addLayout(form_layout)

        # Tombol Aksi
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.skip_btn = QPushButton("Lewati (Nanti Saja)")
        self.skip_btn.setFixedHeight(38)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {THEME['TEXT_MUTED']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #f1f5f9;
                color: {THEME['TEXT_MAIN']};
            }}
        """)
        self.skip_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.skip_btn)

        btn_layout.addStretch()

        self.submit_btn = QPushButton("Simpan Kata Sandi & Lanjut")
        self.submit_btn.setFixedHeight(38)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        self.submit_btn.clicked.connect(self._on_submit)
        btn_layout.addWidget(self.submit_btn)

        layout.addLayout(btn_layout)

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
                background-color: #ffffff;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {THEME['BLUE_PRIMARY']};
            }}
        """

    def _on_submit(self):
        old_pwd = self.old_pass_input.text().strip()
        new_pwd = self.new_pass_input.text().strip()
        confirm_pwd = self.confirm_pass_input.text().strip()

        if not old_pwd or not new_pwd:
            QMessageBox.warning(self, "Validasi Gagal", "Harap isi kata sandi saat ini dan kata sandi baru.")
            return

        if len(new_pwd) < 6:
            QMessageBox.warning(self, "Validasi Gagal", "Kata sandi baru minimal harus 6 karakter.")
            return

        if new_pwd != confirm_pwd:
            QMessageBox.warning(self, "Validasi Gagal", "Konfirmasi kata sandi baru tidak cocok.")
            return

        # Proses pembaruan kata sandi
        success, message = AuthService.change_password(self.user.id, old_pwd, new_pwd)
        if success:
            QMessageBox.information(
                self,
                "Berhasil Diperbarui",
                "Kata sandi Administrator telah berhasil diubah.\nSilakan gunakan kata sandi baru untuk login berikutnya."
            )
            self.accept()
        else:
            QMessageBox.critical(self, "Gagal Mengubah Kata Sandi", message)
