"""
Halaman Pengaturan Sistem SIAP.
Mengelola parameter operasional: Target Hari Kerja, Jam Operasional (Senin-Kamis & Jumat),
serta Tarif Potongan Keterlambatan dan Ketidakhadiran.
Dilengkapi validasi real-time, tombol Simpan, Reset Form, dan Muat Pengaturan.
"""
from typing import Dict
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGridLayout,
    QFrame,
    QScrollArea,
    QMessageBox,
)
from config.settings import (
    THEME,
    APP_NAME,
    APP_FULL_NAME,
    APP_VERSION,
    DB_VERSION,
    APP_DEVELOPER,
    DATA_DIR,
    DB_PATH,
    BACKUP_DIR,
    LOGS_DIR,
    EXPORTS_DIR,
)
from services.auth_service import CurrentSession
from services.settings_service import SettingsService


class SettingsPage(QWidget):
    """Halaman Pengaturan Konfigurasi Sistem untuk hak akses Administrator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.inputs: Dict[str, QLineEdit] = {}
        self._init_ui()
        self.load_settings()

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

        # 1. Header Halaman
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        title = QLabel("Pengaturan Sistem & Parameter Operasional")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        subtitle = QLabel("Konfigurasi target hari kerja bulanan, jadwal jam operasional, dan tarif pemotongan absensi.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {THEME['TEXT_MUTED']};")
        header_box.addWidget(title)
        header_box.addWidget(subtitle)
        layout.addLayout(header_box)

        # 2. Section: Pengaturan Hari Kerja
        section_hari = self._create_card("📅  Target Hari Kerja Bulanan")
        hari_grid = QGridLayout()
        hari_grid.setSpacing(12)

        lbl_target = QLabel("Target Hari Kerja Bulanan:")
        lbl_target.setStyleSheet("font-weight: 600; font-size: 13px;")
        self.inputs["target_hari_kerja_bulanan"] = self._create_line_edit("18", "Contoh: 18 (Rentang 1-31)")
        lbl_target_note = QLabel("Catatan: Angka ini merupakan parameter acuan penghitungan dan tidak menghapus kalender kerja riil.")
        lbl_target_note.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']}; font-style: italic;")

        hari_grid.addWidget(lbl_target, 0, 0)
        hari_grid.addWidget(self.inputs["target_hari_kerja_bulanan"], 0, 1)
        hari_grid.addWidget(lbl_target_note, 1, 0, 1, 2)
        section_hari.layout().addLayout(hari_grid)
        layout.addWidget(section_hari)

        # 3. Section: Jam Operasional
        section_jam = self._create_card("⏰  Jam Operasional Kerja (Format 24 Jam: HH:MM)")
        jam_grid = QGridLayout()
        jam_grid.setSpacing(14)

        # Senin - Kamis
        lbl_sk = QLabel("Senin s/d Kamis")
        lbl_sk.setStyleSheet(f"font-weight: 700; color: {THEME['BLUE_PRIMARY']}; font-size: 14px;")
        jam_grid.addWidget(lbl_sk, 0, 0, 1, 2)

        lbl_masuk_sk = QLabel("Jam Masuk:")
        lbl_masuk_sk.setStyleSheet("font-weight: 500;")
        self.inputs["jam_masuk_senin_kamis"] = self._create_line_edit("08:15", "08:15")
        jam_grid.addWidget(lbl_masuk_sk, 1, 0)
        jam_grid.addWidget(self.inputs["jam_masuk_senin_kamis"], 1, 1)

        lbl_pulang_sk = QLabel("Jam Pulang:")
        lbl_pulang_sk.setStyleSheet("font-weight: 500;")
        self.inputs["jam_pulang_senin_kamis"] = self._create_line_edit("16:30", "16:30")
        jam_grid.addWidget(lbl_pulang_sk, 2, 0)
        jam_grid.addWidget(self.inputs["jam_pulang_senin_kamis"], 2, 1)

        # Jumat
        lbl_jum = QLabel("Hari Jumat")
        lbl_jum.setStyleSheet(f"font-weight: 700; color: {THEME['BLUE_PRIMARY']}; font-size: 14px;")
        jam_grid.addWidget(lbl_jum, 0, 2, 1, 2)

        lbl_masuk_j = QLabel("Jam Masuk:")
        lbl_masuk_j.setStyleSheet("font-weight: 500;")
        self.inputs["jam_masuk_jumat"] = self._create_line_edit("08:15", "08:15")
        jam_grid.addWidget(lbl_masuk_j, 1, 2)
        jam_grid.addWidget(self.inputs["jam_masuk_jumat"], 1, 3)

        lbl_pulang_j = QLabel("Jam Pulang:")
        lbl_pulang_j.setStyleSheet("font-weight: 500;")
        self.inputs["jam_pulang_jumat"] = self._create_line_edit("17:00", "17:00")
        jam_grid.addWidget(lbl_pulang_j, 2, 2)
        jam_grid.addWidget(self.inputs["jam_pulang_jumat"], 2, 3)

        section_jam.layout().addLayout(jam_grid)
        layout.addWidget(section_jam)

        # 4. Section: Tarif Potongan Absensi
        section_potongan = self._create_card("💰  Tarif Potongan Pelanggaran Absensi (Rupiah)")
        potongan_grid = QGridLayout()
        potongan_grid.setSpacing(14)

        potongan_fields = [
            ("potongan_terlambat_sd_1jam", "Terlambat s/d 1 Jam:", "7500", "Rp 7.500"),
            ("potongan_terlambat_gt_1jam", "Terlambat > 1 Jam:", "10000", "Rp 10.000"),
            ("potongan_pulang_cepat", "Pulang Cepat (Sebelum Waktunya):", "10000", "Rp 10.000"),
            ("potongan_tidak_absen_masuk", "Tidak Absen Masuk:", "10000", "Rp 10.000"),
            ("potongan_tidak_absen_pulang", "Tidak Absen Pulang:", "10000", "Rp 10.000"),
            ("potongan_tidak_hadir", "Tidak Hadir (Alfa per Hari):", "20000", "Rp 20.000"),
        ]

        row = 0
        col = 0
        for key, label_text, default_val, placeholder in potongan_fields:
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-weight: 500;")
            le = self._create_line_edit(default_val, placeholder)
            self.inputs[key] = le

            potongan_grid.addWidget(lbl, row, col * 2)
            potongan_grid.addWidget(le, row, col * 2 + 1)

            col += 1
            if col >= 2:
                col = 0
                row += 1

        section_potongan.layout().addLayout(potongan_grid)
        layout.addWidget(section_potongan)

        # 5. Section: Informasi Sistem & Direktori Runtime
        section_info = self._create_card("ℹ️  Informasi Sistem & Direktori Pengguna (Windows)")
        info_grid = QGridLayout()
        info_grid.setSpacing(10)

        info_items = [
            ("Aplikasi & Versi:", f"{APP_NAME} - {APP_FULL_NAME} (v{APP_VERSION}, DB v{DB_VERSION})"),
            ("Pengembang:", APP_DEVELOPER),
            ("Database Aktif:", str(DB_PATH)),
            ("Folder Cadangan (Backup):", str(BACKUP_DIR)),
            ("Folder Berkas Log:", str(LOGS_DIR)),
            ("Folder Ekspor Laporan:", str(EXPORTS_DIR)),
        ]

        for r_idx, (k, v) in enumerate(info_items):
            k_lbl = QLabel(k)
            k_lbl.setStyleSheet("font-weight: 600; font-size: 12px; color: #475569;")
            v_lbl = QLabel(v)
            v_lbl.setWordWrap(True)
            v_lbl.setStyleSheet("font-size: 12px; color: #0f172a;")
            info_grid.addWidget(k_lbl, r_idx, 0)
            info_grid.addWidget(v_lbl, r_idx, 1)

        about_btn = QPushButton("📖  Buka Dialog Tentang SIAP (Spesifikasi Lengkap)")
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.setFixedHeight(34)
        about_btn.setStyleSheet(f"""
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
        about_btn.clicked.connect(self._open_about_dialog)
        info_grid.addWidget(about_btn, len(info_items), 0, 1, 2)

        section_info.layout().addLayout(info_grid)
        layout.addWidget(section_info)

        # 6. Tombol Aksi (Simpan, Reset Form, Muat Pengaturan, Default Pabrik)
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(12)

        self.save_btn = QPushButton("💾  Simpan Pengaturan")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedHeight(40)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                padding: 0 24px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        self.save_btn.clicked.connect(self._on_save_clicked)
        btn_bar.addWidget(self.save_btn)

        self.reload_btn = QPushButton("🔄  Muat Ulang dari Database")
        self.reload_btn.setCursor(Qt.PointingHandCursor)
        self.reload_btn.setFixedHeight(40)
        self.reload_btn.setStyleSheet(self._secondary_btn_style())
        self.reload_btn.clicked.connect(self.load_settings)
        btn_bar.addWidget(self.reload_btn)

        self.reset_btn = QPushButton("↺  Reset Form")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setFixedHeight(40)
        self.reset_btn.setStyleSheet(self._secondary_btn_style())
        self.reset_btn.clicked.connect(self.load_settings)
        btn_bar.addWidget(self.reset_btn)

        btn_bar.addStretch()

        self.default_btn = QPushButton("⚙️  Kembalikan ke Default Pabrik")
        self.default_btn.setCursor(Qt.PointingHandCursor)
        self.default_btn.setFixedHeight(40)
        self.default_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #fef2f2;
                color: {THEME['DANGER']};
                border: 1px solid #fecaca;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #fee2e2;
            }}
        """)
        self.default_btn.clicked.connect(self._on_reset_default_clicked)
        btn_bar.addWidget(self.default_btn)

        layout.addLayout(btn_bar)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _create_card(self, title_text: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['BG_CARD']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)

        card_title = QLabel(title_text)
        card_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        card_layout.addWidget(card_title)
        return card

    def _create_line_edit(self, text: str, placeholder: str = "") -> QLineEdit:
        le = QLineEdit(text)
        le.setPlaceholderText(placeholder)
        le.setFixedHeight(34)
        le.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
                color: {THEME['TEXT_MAIN']};
                background-color: #ffffff;
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME['BLUE_PRIMARY']};
                background-color: #f8fafc;
            }}
        """)
        return le

    def _secondary_btn_style(self) -> str:
        return f"""
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
                border: 1px solid #cbd5e1;
            }}
        """

    def load_settings(self):
        """Membaca konfigurasi yang tersimpan di database dan mengisikannya ke form."""
        data = SettingsService.get_all()
        for key, val in data.items():
            if key in self.inputs:
                self.inputs[key].setText(str(val))

    def _on_save_clicked(self):
        """Memvalidasi dan menyimpan konfigurasi ke database."""
        current_data = {k: le.text().strip() for k, le in self.inputs.items()}
        user_id = CurrentSession.get_instance().user_id

        success, errors = SettingsService.save_settings(current_data, user_id=user_id)
        if success:
            QMessageBox.information(
                self,
                "Berhasil",
                "Pengaturan sistem berhasil disimpan ke database SQLite."
            )
            self.load_settings()
        else:
            error_list = "\n• " + "\n• ".join(errors)
            QMessageBox.warning(
                self,
                "Validasi Gagal",
                f"Terdapat kesalahan input konfigurasi:{error_list}"
            )

    def _on_reset_default_clicked(self):
        """Konfirmasi pengembalian ke pengaturan default bawaan pabrik."""
        reply = QMessageBox.question(
            self,
            "Konfirmasi Reset Default",
            "Apakah Anda yakin ingin mengembalikan seluruh pengaturan sistem ke nilai default bawaan pabrik?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            user_id = CurrentSession.get_instance().user_id
            success, errors = SettingsService.reset_to_defaults(user_id=user_id)
            if success:
                QMessageBox.information(self, "Berhasil", "Pengaturan telah berhasil di-reset ke default.")
                self.load_settings()
            else:
                QMessageBox.critical(self, "Gagal", f"Gagal me-reset pengaturan: {', '.join(errors)}")

    def _open_about_dialog(self):
        """Membuka dialog Tentang SIAP."""
        from ui.dialogs.about_dialog import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()

