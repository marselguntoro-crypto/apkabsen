"""
Halaman Dashboard Utama SIAP.
Menampilkan filter periode (Bulan & Tahun), 7 Kartu Statistik kehadiran & potongan,
serta ringkasan status operasional database secara transparan dan jujur.
"""
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QGridLayout,
    QFrame,
    QScrollArea,
)
from config.settings import THEME
from services.dashboard_service import DashboardService
from ui.widgets.stat_card import StatCard


class DashboardPage(QWidget):
    """Halaman Dashboard Utama untuk memantau data kehadiran dan statistik absensi."""

    MONTHS = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        # Gunakan scroll area agar responsif pada resolusi 1024x640 hingga 1366x768+
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

        # 1. Header & Filter Bar
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            background-color: {THEME['BG_CARD']};
            border: 1px solid {THEME['BORDER']};
            border-radius: 10px;
            padding: 12px;
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 10, 12, 10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        page_title = QLabel("Dashboard Ringkasan Presensi")
        page_title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        self.period_label = QLabel("Periode: Memuat...")
        self.period_label.setStyleSheet(f"font-size: 13px; color: {THEME['TEXT_MUTED']};")
        title_box.addWidget(page_title)
        title_box.addWidget(self.period_label)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Kontrol Filter Periode
        filter_box = QHBoxLayout()
        filter_box.setSpacing(10)

        lbl_bulan = QLabel("Bulan:")
        lbl_bulan.setStyleSheet(f"font-weight: 600; color: {THEME['TEXT_MAIN']};")
        filter_box.addWidget(lbl_bulan)

        self.combo_month = QComboBox()
        self.combo_month.setFixedWidth(130)
        self.combo_month.addItems(self.MONTHS)
        self.combo_month.setCurrentIndex(self.current_month - 1)
        self.combo_month.setStyleSheet(self._input_style())
        self.combo_month.currentIndexChanged.connect(self._on_filter_changed)
        filter_box.addWidget(self.combo_month)

        lbl_tahun = QLabel("Tahun:")
        lbl_tahun.setStyleSheet(f"font-weight: 600; color: {THEME['TEXT_MAIN']};")
        filter_box.addWidget(lbl_tahun)

        self.combo_year = QComboBox()
        self.combo_year.setFixedWidth(90)
        years = [str(y) for y in range(self.current_year - 3, self.current_year + 3)]
        self.combo_year.addItems(years)
        self.combo_year.setCurrentText(str(self.current_year))
        self.combo_year.setStyleSheet(self._input_style())
        self.combo_year.currentIndexChanged.connect(self._on_filter_changed)
        filter_box.addWidget(self.combo_year)

        # Tombol Refresh
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setFixedHeight(34)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                font-weight: 600;
                padding: 0 16px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        filter_box.addWidget(self.refresh_btn)

        header_layout.addLayout(filter_box)
        layout.addWidget(header_frame)

        # 2. Kartu Statistik Grid (7 Metrik Wajib Tahap 1)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)

        # Baris 1: Karyawan, Hari Kerja, Hadir, Alfa
        self.card_karyawan = StatCard("Total Karyawan", "0", "Karyawan aktif terdaftar", THEME["BLUE_PRIMARY"])
        self.card_hari_kerja = StatCard("Total Hari Kerja", "18", "Target / kalender kerja", THEME["NAVY_PRIMARY"])
        self.card_hadir = StatCard("Total Hadir", "0", "Presensi tercatat", THEME["SUCCESS"])
        self.card_alfa = StatCard("Total Alfa", "0", "Ketidakhadiran tanpa izin", THEME["DANGER"])

        grid_layout.addWidget(self.card_karyawan, 0, 0)
        grid_layout.addWidget(self.card_hari_kerja, 0, 1)
        grid_layout.addWidget(self.card_hadir, 0, 2)
        grid_layout.addWidget(self.card_alfa, 0, 3)

        # Baris 2: Terlambat, Pulang Cepat, Total Potongan
        self.card_terlambat = StatCard("Terlambat", "0", "Pelanggaran jam masuk", THEME["WARNING"])
        self.card_pulang_cepat = StatCard("Pulang Cepat", "0", "Pelanggaran jam pulang", THEME["WARNING"])
        self.card_potongan = StatCard("Total Potongan", "Rp 0", "Akumulasi potongan absensi", THEME["DANGER"])

        grid_layout.addWidget(self.card_terlambat, 1, 0)
        grid_layout.addWidget(self.card_pulang_cepat, 1, 1)
        grid_layout.addWidget(self.card_potongan, 1, 2, 1, 2)  # Span 2 kolom

        layout.addLayout(grid_layout)

        # 3. Status Transparansi Data Tahap 1
        info_card = QFrame()
        info_card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(8)

        info_header = QLabel("ℹ️  Status Fondasi Sistem (Tahap 1)")
        info_header.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        info_layout.addWidget(info_header)

        desc_text = QLabel(
            "• Database SQLite lokal aktif dan terhubung di direktori: data/database/siap_presensi.db\n"
            "• Nilai statistik saat ini menampilkan angka 0 secara jujur dan riil karena berkas absensi "
            "belum di-import ke dalam sistem.\n"
            "• Modul Import Excel (Attendance Raw), Perhitungan Presensi Harian, dan Laporan Rekapitulasi "
            "akan diintegrasikan pada Tahap 2."
        )
        desc_text.setStyleSheet(f"font-size: 13px; color: {THEME['TEXT_MUTED']}; line-height: 1.6;")
        desc_text.setWordWrap(True)
        info_layout.addWidget(desc_text)

        layout.addWidget(info_card)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _input_style(self) -> str:
        return f"""
            QComboBox {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 4px 10px;
                background-color: #ffffff;
                color: {THEME['TEXT_MAIN']};
                font-size: 13px;
            }}
            QComboBox:focus {{
                border: 1px solid {THEME['BLUE_PRIMARY']};
            }}
        """

    def _on_filter_changed(self):
        self.refresh_data()

    def refresh_data(self):
        """Mengambil data aktual dari database dan memperbarui kartu statistik."""
        month = self.combo_month.currentIndex() + 1
        try:
            year = int(self.combo_year.currentText())
        except ValueError:
            year = self.current_year

        month_name = self.MONTHS[month - 1]
        self.period_label.setText(f"Periode Aktif: {month_name} {year}")

        # Panggil Service
        stats = DashboardService.get_summary_statistics(month=month, year=year)

        # Update nilai kartu statistik
        self.card_karyawan.update_value(str(stats["total_karyawan"]))
        self.card_hari_kerja.update_value(str(stats["total_hari_kerja"]))
        self.card_hadir.update_value(str(stats["total_hadir"]))
        self.card_alfa.update_value(str(stats["total_alfa"]))
        self.card_terlambat.update_value(str(stats["total_terlambat"]))
        self.card_pulang_cepat.update_value(str(stats["total_pulang_cepat"]))
        self.card_potongan.update_value(stats["formatted_potongan"])
