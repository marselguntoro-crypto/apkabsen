"""
Halaman Perhitungan Status dan Nominal Potongan Absensi (Tahap 5).
SIAP - Sistem Informasi Administrasi Presensi.

Menyediakan antarmuka terpadu:
1. Tab 1: Mesin Perhitungan Potongan (Pemilihan periode/unit/karyawan, preview, hitung potongan, hitung ulang, validasi data).
2. Tab 2: Rekap Data Potongan Absensi (Tabel 9 kolom wajib, filter unit/periode, search nama, sorting, total per karyawan/unit/keseluruhan, export Excel & PDF).
3. Tab 3: Data Absensi & Potongan Harian (Tabel 17 kolom lengkap, filter tanggal/unit/status/nama, lihat rincian dialog, export Excel & PDF).
"""
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QTabWidget,
    QMessageBox,
    QFileDialog,
    QDateEdit,
    QAbstractItemView,
)

from config.settings import THEME
from database.connection import get_db_session
from database.models import Employee, EmployeeStatus, AttendanceStatus
from services.deduction_calculation_service import DeductionCalculationService
from services.export_service import ExportService
from ui.dialogs.deduction_detail_dialog import DeductionDetailDialog
from utils.logger import get_logger

logger = get_logger("DeductionPage")


class DeductionPage(QWidget):
    """Halaman Utama Pengelolaan Perhitungan dan Rekapitulasi Potongan Absensi."""

    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.current_preview: Optional[Dict[str, Any]] = None
        self.rekap_data: Optional[Dict[str, Any]] = None
        self.daily_details_data: List[Dict[str, Any]] = []
        self._init_ui()
        self.refresh_all()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Title
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("Perhitungan Status & Potongan Absensi")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        subtitle_lbl = QLabel("Mesin kalkulasi keterlambatan, pulang cepat, scan tidak lengkap, serta rekapitulasi nominal potongan.")
        subtitle_lbl.setStyleSheet(f"font-size: 13px; color: {THEME['TEXT_MUTED']};")
        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        main_layout.addLayout(title_box)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background-color: #ffffff;
                padding: 16px;
            }}
            QTabBar::tab {{
                background-color: #f1f5f9;
                color: {THEME['NAVY_DARK']};
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #e2e8f0;
            }}
        """)

        # Inisialisasi 3 Tab
        self.tab_calc = self._create_tab_calculation()
        self.tab_rekap = self._create_tab_rekap()
        self.tab_detail = self._create_tab_detail()

        self.tabs.addTab(self.tab_calc, "⚡  Mesin Perhitungan Potongan")
        self.tabs.addTab(self.tab_rekap, "📋  Rekap Data Potongan Absensi")
        self.tabs.addTab(self.tab_detail, "🔍  Data Absensi & Potongan Harian")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs)

    # =========================================================================
    # TAB 1: MESIN PERHITUNGAN POTONGAN
    # =========================================================================
    def _create_tab_calculation(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(16)

        # 1. Filter Pemilihan Periode & Cakupan
        filter_card = QFrame()
        filter_card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;")
        filter_layout = QGridLayout(filter_card)
        filter_layout.setContentsMargins(16, 16, 16, 16)
        filter_layout.setSpacing(12)

        # Tahun
        filter_layout.addWidget(QLabel("<b>Tahun:</b>"), 0, 0)
        self.cb_calc_year = QComboBox()
        cur_year = datetime.now().year
        for y in range(cur_year - 2, cur_year + 3):
            self.cb_calc_year.addItem(str(y), y)
        self.cb_calc_year.setCurrentText(str(cur_year))
        filter_layout.addWidget(self.cb_calc_year, 0, 1)

        # Bulan
        filter_layout.addWidget(QLabel("<b>Bulan:</b>"), 0, 2)
        self.cb_calc_month = QComboBox()
        months = [
            ("01 - Januari", 1), ("02 - Februari", 2), ("03 - Maret", 3),
            ("04 - April", 4), ("05 - Mei", 5), ("06 - Juni", 6),
            ("07 - Juli", 7), ("08 - Agustus", 8), ("09 - September", 9),
            ("10 - Oktober", 10), ("11 - November", 11), ("12 - Desember", 12)
        ]
        for m_name, m_val in months:
            self.cb_calc_month.addItem(m_name, m_val)
        self.cb_calc_month.setCurrentIndex(datetime.now().month - 1)
        filter_layout.addWidget(self.cb_calc_month, 0, 3)

        # Unit Kerja
        filter_layout.addWidget(QLabel("<b>Unit Kerja:</b>"), 1, 0)
        self.cb_calc_unit = QComboBox()
        self.cb_calc_unit.addItem("SEMUA UNIT", "ALL")
        filter_layout.addWidget(self.cb_calc_unit, 1, 1)

        # Karyawan Tertentu
        filter_layout.addWidget(QLabel("<b>Karyawan:</b>"), 1, 2)
        self.cb_calc_emp = QComboBox()
        self.cb_calc_emp.addItem("Seluruh Karyawan", None)
        filter_layout.addWidget(self.cb_calc_emp, 1, 3)

        # Tombol Cek / Validasi Pra-Perhitungan
        self.btn_preview = QPushButton("🔍  Validasi & Cek Data")
        self.btn_preview.setCursor(Qt.PointingHandCursor)
        self.btn_preview.setFixedHeight(34)
        self.btn_preview.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_LIGHT']};
                color: {THEME['BLUE_PRIMARY']};
                font-weight: 600;
                border: 1px solid {THEME['BLUE_PRIMARY']};
                border-radius: 6px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: #dbeafe;
            }}
        """)
        self.btn_preview.clicked.connect(self._load_calculation_preview)
        filter_layout.addWidget(self.btn_preview, 0, 4, 2, 1)

        layout.addWidget(filter_card)

        # 2. Card Informasi Ringkasan Pra-Perhitungan
        self.preview_card = QFrame()
        self.preview_card.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px;")
        prev_layout = QVBoxLayout(self.preview_card)
        prev_layout.setContentsMargins(16, 14, 16, 14)
        prev_layout.setSpacing(10)

        prev_header = QLabel("Ringkasan Data Pra-Perhitungan")
        prev_header.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        prev_layout.addWidget(prev_header)

        # Grid Informasi
        self.lbl_prev_period = QLabel("Periode: -")
        self.lbl_prev_emp_count = QLabel("Jumlah Karyawan: -")
        self.lbl_prev_workdays = QLabel("Hari Kerja Kalender: -")
        self.lbl_prev_daily_records = QLabel("Data Absensi Harian: -")
        self.lbl_prev_problems = QLabel("Data Bermasalah: -")
        self.lbl_prev_status = QLabel("Status Kalkulasi: Belum dihitung")
        self.lbl_prev_status.setStyleSheet("font-weight: 600; color: #d97706;")

        pgrid = QGridLayout()
        pgrid.setSpacing(10)
        pgrid.addWidget(self.lbl_prev_period, 0, 0)
        pgrid.addWidget(self.lbl_prev_emp_count, 0, 1)
        pgrid.addWidget(self.lbl_prev_workdays, 0, 2)
        pgrid.addWidget(self.lbl_prev_daily_records, 1, 0)
        pgrid.addWidget(self.lbl_prev_problems, 1, 1)
        pgrid.addWidget(self.lbl_prev_status, 1, 2)
        prev_layout.addLayout(pgrid)

        layout.addWidget(self.preview_card)

        # 3. Baris Tombol Aksi Eksekusi
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(12)

        self.btn_calculate = QPushButton("⚡  Hitung Potongan")
        self.btn_calculate.setCursor(Qt.PointingHandCursor)
        self.btn_calculate.setFixedHeight(40)
        self.btn_calculate.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                border-radius: 6px;
                padding: 0 24px;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        self.btn_calculate.clicked.connect(lambda: self._execute_calculation(recalculate=False))
        btn_bar.addWidget(self.btn_calculate)

        self.btn_recalculate = QPushButton("🔄  Hitung Ulang (Recalculate)")
        self.btn_recalculate.setCursor(Qt.PointingHandCursor)
        self.btn_recalculate.setFixedHeight(40)
        self.btn_recalculate.setStyleSheet(f"""
            QPushButton {{
                background-color: #0284c7;
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                border-radius: 6px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #0369a1;
            }}
        """)
        self.btn_recalculate.clicked.connect(lambda: self._execute_calculation(recalculate=True))
        btn_bar.addWidget(self.btn_recalculate)

        self.btn_validate_integrity = QPushButton("🛡️  Validasi Integritas")
        self.btn_validate_integrity.setCursor(Qt.PointingHandCursor)
        self.btn_validate_integrity.setFixedHeight(40)
        self.btn_validate_integrity.setStyleSheet("""
            QPushButton {{
                background-color: #10b981;
                color: #ffffff;
                font-weight: 600;
                border-radius: 6px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        self.btn_validate_integrity.clicked.connect(self._validate_integrity)
        btn_bar.addWidget(self.btn_validate_integrity)

        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        # Hasil Eksekusi Banner
        self.lbl_exec_result = QLabel("")
        self.lbl_exec_result.setWordWrap(True)
        self.lbl_exec_result.setStyleSheet("padding: 12px; border-radius: 6px; font-size: 13px; font-weight: 500;")
        self.lbl_exec_result.setVisible(False)
        layout.addWidget(self.lbl_exec_result)

        layout.addStretch()
        return widget

    # =========================================================================
    # TAB 2: REKAP DATA POTONGAN ABSENSI (9 KOLOM WAJIB)
    # =========================================================================
    def _create_tab_rekap(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(14)

        # Toolbar Filter & Pencarian
        bar = QHBoxLayout()
        bar.setSpacing(10)

        bar.addWidget(QLabel("Tahun:"))
        self.cb_rekap_year = QComboBox()
        cur_year = datetime.now().year
        for y in range(cur_year - 2, cur_year + 3):
            self.cb_rekap_year.addItem(str(y), y)
        self.cb_rekap_year.setCurrentText(str(cur_year))
        self.cb_rekap_year.currentIndexChanged.connect(self._load_rekap_data)
        bar.addWidget(self.cb_rekap_year)

        bar.addWidget(QLabel("Bulan:"))
        self.cb_rekap_month = QComboBox()
        for idx in range(12):
            self.cb_rekap_month.addItem(self.cb_calc_month.itemText(idx), self.cb_calc_month.itemData(idx))
        self.cb_rekap_month.setCurrentIndex(datetime.now().month - 1)
        self.cb_rekap_month.currentIndexChanged.connect(self._load_rekap_data)
        bar.addWidget(self.cb_rekap_month)

        bar.addWidget(QLabel("Unit:"))
        self.cb_rekap_unit = QComboBox()
        self.cb_rekap_unit.addItem("SEMUA UNIT", "ALL")
        self.cb_rekap_unit.currentIndexChanged.connect(self._load_rekap_data)
        bar.addWidget(self.cb_rekap_unit)

        bar.addWidget(QLabel("Cari Nama:"))
        self.txt_rekap_search = QLineEdit()
        self.txt_rekap_search.setPlaceholderText("Ketik nama / NIK...")
        self.txt_rekap_search.textChanged.connect(self._load_rekap_data)
        bar.addWidget(self.txt_rekap_search)

        bar.addStretch()

        # Tombol Export
        self.btn_export_rekap_excel = QPushButton("📊  Export Excel")
        self.btn_export_rekap_excel.setCursor(Qt.PointingHandCursor)
        self.btn_export_rekap_excel.setStyleSheet("""
            QPushButton {
                background-color: #047857; color: white; font-weight: 600;
                padding: 6px 14px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #065f46; }
        """)
        self.btn_export_rekap_excel.clicked.connect(self._export_rekap_excel)
        bar.addWidget(self.btn_export_rekap_excel)

        self.btn_export_rekap_pdf = QPushButton("📄  Export PDF")
        self.btn_export_rekap_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_export_rekap_pdf.setStyleSheet("""
            QPushButton {
                background-color: #b91c1c; color: white; font-weight: 600;
                padding: 6px 14px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #991b1b; }
        """)
        self.btn_export_rekap_pdf.clicked.connect(self._export_rekap_pdf)
        bar.addWidget(self.btn_export_rekap_pdf)

        layout.addLayout(bar)

        # Tabel Rekap (9 Kolom Wajib)
        self.table_rekap = QTableWidget()
        self.table_rekap.setColumnCount(9)
        self.table_rekap.setHorizontalHeaderLabels([
            "No", "Unit", "Nama", "Status",
            "Terlambat", "Pulang Cepat",
            "Tidak Absen Masuk", "Tidak Absen Pulang",
            "Jumlah Potongan Absensi"
        ])
        self.table_rekap.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_rekap.horizontalHeader().setStretchLastSection(True)
        self.table_rekap.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_rekap.setAlternatingRowColors(True)
        self.table_rekap.verticalHeader().setVisible(False)
        self.table_rekap.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid #e2e8f0;
                gridline-color: #f1f5f9;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {THEME['NAVY_PRIMARY']};
                color: #ffffff;
                padding: 8px;
                font-weight: 700;
                border: none;
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
        """)
        layout.addWidget(self.table_rekap)

        # Card Ringkasan Total
        self.card_rekap_total = QFrame()
        self.card_rekap_total.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;")
        tot_layout = QHBoxLayout(self.card_rekap_total)
        tot_layout.setContentsMargins(16, 10, 16, 10)

        self.lbl_tot_karyawan = QLabel("Total Karyawan: 0")
        self.lbl_tot_tlbt = QLabel("Terlambat: Rp0")
        self.lbl_tot_pc = QLabel("Pulang Cepat: Rp0")
        self.lbl_tot_miss_in = QLabel("Tidak Absen Masuk: Rp0")
        self.lbl_tot_miss_out = QLabel("Tidak Absen Pulang: Rp0")
        self.lbl_grand_total = QLabel("Total Keseluruhan: Rp0")
        self.lbl_grand_total.setStyleSheet("font-weight: 800; color: #b91c1c; font-size: 14px;")

        tot_layout.addWidget(self.lbl_tot_karyawan)
        tot_layout.addSpacing(16)
        tot_layout.addWidget(self.lbl_tot_tlbt)
        tot_layout.addSpacing(16)
        tot_layout.addWidget(self.lbl_tot_pc)
        tot_layout.addSpacing(16)
        tot_layout.addWidget(self.lbl_tot_miss_in)
        tot_layout.addSpacing(16)
        tot_layout.addWidget(self.lbl_tot_miss_out)
        tot_layout.addStretch()
        tot_layout.addWidget(self.lbl_grand_total)

        layout.addWidget(self.card_rekap_total)
        return widget

    # =========================================================================
    # TAB 3: DATA ABSENSI DAN POTONGAN HARIAN (17 KOLOM)
    # =========================================================================
    def _create_tab_detail(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(14)

        # Filter Bar
        bar = QHBoxLayout()
        bar.setSpacing(8)

        bar.addWidget(QLabel("Tahun:"))
        self.cb_det_year = QComboBox()
        cur_year = datetime.now().year
        for y in range(cur_year - 2, cur_year + 3):
            self.cb_det_year.addItem(str(y), y)
        self.cb_det_year.setCurrentText(str(cur_year))
        self.cb_det_year.currentIndexChanged.connect(self._load_daily_details)
        bar.addWidget(self.cb_det_year)

        bar.addWidget(QLabel("Bulan:"))
        self.cb_det_month = QComboBox()
        for idx in range(12):
            self.cb_det_month.addItem(self.cb_calc_month.itemText(idx), self.cb_calc_month.itemData(idx))
        self.cb_det_month.setCurrentIndex(datetime.now().month - 1)
        self.cb_det_month.currentIndexChanged.connect(self._load_daily_details)
        bar.addWidget(self.cb_det_month)

        bar.addWidget(QLabel("Unit:"))
        self.cb_det_unit = QComboBox()
        self.cb_det_unit.addItem("SEMUA UNIT", "ALL")
        self.cb_det_unit.currentIndexChanged.connect(self._load_daily_details)
        bar.addWidget(self.cb_det_unit)

        bar.addWidget(QLabel("Status:"))
        self.cb_det_status = QComboBox()
        self.cb_det_status.addItem("Semua Status", "ALL")
        for s in [
            AttendanceStatus.HADIR_LENGKAP.value,
            AttendanceStatus.HANYA_ABSEN_MASUK.value,
            AttendanceStatus.HANYA_ABSEN_PULANG.value,
            AttendanceStatus.TIDAK_ABSEN.value,
            AttendanceStatus.LIBUR.value,
            AttendanceStatus.DATA_BERMASALAH.value,
        ]:
            self.cb_det_status.addItem(s, s)
        self.cb_det_status.currentIndexChanged.connect(self._load_daily_details)
        bar.addWidget(self.cb_det_status)

        bar.addWidget(QLabel("Nama:"))
        self.txt_det_search = QLineEdit()
        self.txt_det_search.setPlaceholderText("Filter nama...")
        self.txt_det_search.textChanged.connect(self._load_daily_details)
        bar.addWidget(self.txt_det_search)

        bar.addStretch()

        # Tombol Detail Dialog
        self.btn_view_row_detail = QPushButton("👁️  Rincian")
        self.btn_view_row_detail.setCursor(Qt.PointingHandCursor)
        self.btn_view_row_detail.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_LIGHT']}; color: {THEME['BLUE_PRIMARY']};
                font-weight: 600; padding: 6px 14px; border-radius: 6px;
                border: 1px solid {THEME['BLUE_PRIMARY']};
            }}
            QPushButton:hover {{ background-color: #dbeafe; }}
        """)
        self.btn_view_row_detail.clicked.connect(self._open_selected_detail_dialog)
        bar.addWidget(self.btn_view_row_detail)

        # Tombol Export
        self.btn_export_det_excel = QPushButton("📊  Excel")
        self.btn_export_det_excel.setCursor(Qt.PointingHandCursor)
        self.btn_export_det_excel.setStyleSheet("""
            QPushButton {
                background-color: #047857; color: white; font-weight: 600;
                padding: 6px 12px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #065f46; }
        """)
        self.btn_export_det_excel.clicked.connect(self._export_detail_excel)
        bar.addWidget(self.btn_export_det_excel)

        self.btn_export_det_pdf = QPushButton("📄  PDF")
        self.btn_export_det_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_export_det_pdf.setStyleSheet("""
            QPushButton {
                background-color: #b91c1c; color: white; font-weight: 600;
                padding: 6px 12px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #991b1b; }
        """)
        self.btn_export_det_pdf.clicked.connect(self._export_detail_pdf)
        bar.addWidget(self.btn_export_det_pdf)

        layout.addLayout(bar)

        # Tabel Detail (17 Kolom Lengkap)
        self.table_detail = QTableWidget()
        self.table_detail.setColumnCount(17)
        self.table_detail.setHorizontalHeaderLabels([
            "No", "Unit", "Nama", "Hari", "Tanggal",
            "Jam Masuk", "Jam Pulang", "Status Masuk", "Status Pulang", "Status Kehadiran",
            "Menit Tlbt", "Menit PC", "Potongan Tlbt", "Potongan PC",
            "Tdk Absen Masuk", "Tdk Absen Pulang", "Total Potongan"
        ])
        self.table_detail.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_detail.horizontalHeader().setStretchLastSection(True)
        self.table_detail.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_detail.setAlternatingRowColors(True)
        self.table_detail.verticalHeader().setVisible(False)
        self.table_detail.doubleClicked.connect(self._open_selected_detail_dialog)
        self.table_detail.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid #e2e8f0;
                gridline-color: #f1f5f9;
                font-size: 11px;
            }}
            QHeaderView::section {{
                background-color: {THEME['NAVY_PRIMARY']};
                color: #ffffff;
                padding: 6px;
                font-weight: 700;
                border: none;
            }}
        """)
        layout.addWidget(self.table_detail)

        return widget

    # =========================================================================
    # LOGIKA CONTROLLER & EVENT HANDLERS
    # =========================================================================
    def refresh_all(self):
        """Memuat master unit, karyawan, dan preview awal."""
        self._populate_unit_and_employee_combos()
        self._load_calculation_preview()

    def _on_tab_changed(self, index: int):
        if index == 1:
            self._load_rekap_data()
        elif index == 2:
            self._load_daily_details()

    def _populate_unit_and_employee_combos(self):
        """Mengisi daftar unit dan karyawan dari database."""
        with get_db_session() as session:
            # Unit unik
            units = session.query(Employee.unit).distinct().filter(Employee.unit.isnot(None)).all()
            unit_list = sorted([u[0] for u in units if u[0]])

            for cb in [self.cb_calc_unit, self.cb_rekap_unit, self.cb_det_unit]:
                cur = cb.currentData()
                cb.clear()
                cb.addItem("SEMUA UNIT", "ALL")
                for u in unit_list:
                    cb.addItem(u, u)
                if cur:
                    idx = cb.findData(cur)
                    if idx >= 0:
                        cb.setCurrentIndex(idx)

            # Karyawan aktif
            emps = session.query(Employee).filter(Employee.status == EmployeeStatus.AKTIF).order_by(Employee.nama.asc()).all()
            self.cb_calc_emp.clear()
            self.cb_calc_emp.addItem("Seluruh Karyawan", None)
            for e in emps:
                self.cb_calc_emp.addItem(f"{e.nama} ({e.unit or '-'})", e.id)

    def _load_calculation_preview(self):
        """Memuat ringkasan pra-perhitungan sebelum proses dimulai."""
        year = self.cb_calc_year.currentData()
        month = self.cb_calc_month.currentData()
        unit = self.cb_calc_unit.currentData()
        emp_id = self.cb_calc_emp.currentData()

        prev = DeductionCalculationService.get_calculation_preview(
            year=year,
            month=month,
            unit=None if unit == "ALL" else unit,
            employee_id=emp_id,
        )
        self.current_preview = prev

        self.lbl_prev_period.setText(f"<b>Periode:</b> {prev['period_label']}")
        self.lbl_prev_emp_count.setText(f"<b>Jumlah Karyawan:</b> {prev['employee_count']} orang")
        self.lbl_prev_workdays.setText(f"<b>Hari Kerja:</b> {prev['working_days_count']} hari")
        self.lbl_prev_daily_records.setText(f"<b>Data Absensi Harian:</b> {prev['total_daily_records']} catatan")
        
        prob_color = "#dc2626" if prev["problematic_count"] > 0 else "#10b981"
        self.lbl_prev_problems.setText(f"<b>Data Bermasalah:</b> <span style='color:{prob_color}'>{prev['problematic_count']}</span>")

        if prev["is_already_calculated"]:
            self.lbl_prev_status.setText(f"<b>Status:</b> Sudah pernah dihitung ({prev['existing_deduction_count']} data tersimpan). Gunakan 'Hitung Ulang' jika ada perubahan.")
            self.lbl_prev_status.setStyleSheet("color: #0284c7; font-weight: 600;")
        else:
            self.lbl_prev_status.setText("<b>Status:</b> Belum dihitung untuk periode ini.")
            self.lbl_prev_status.setStyleSheet("color: #d97706; font-weight: 600;")

    def _execute_calculation(self, recalculate: bool = False):
        """Mengeksekusi perhitungan status dan nominal potongan absensi."""
        year = self.cb_calc_year.currentData()
        month = self.cb_calc_month.currentData()
        unit = self.cb_calc_unit.currentData()
        emp_id = self.cb_calc_emp.currentData()

        # Validasi ketersediaan data harian
        if not self.current_preview or self.current_preview["total_daily_records"] == 0:
            QMessageBox.warning(
                self,
                "Data Kosong",
                f"Belum ada data Absensi Harian untuk periode {month:02d}/{year}.\n"
                "Silakan jalankan pembentukan absensi harian terlebih dahulu di menu Data Absensi.",
            )
            return

        # Peringatan data bermasalah jika ada
        if self.current_preview["problematic_count"] > 0:
            msg = (
                f"Perhatian: Terdapat {self.current_preview['problematic_count']} data absensi dengan status DATA_BERMASALAH / Konflik.\n"
                "Data bermasalah tidak akan dikenakan denda keterlambatan parsial hingga diperbaiki.\n\n"
                "Apakah Anda ingin tetap melanjutkan perhitungan?"
            )
            reply = QMessageBox.question(self, "Konfirmasi Data Bermasalah", msg, QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return

        # Konfirmasi Pengguna Sebelum Perhitungan
        action_name = "Perhitungan Ulang (Recalculate)" if recalculate else "Perhitungan Potongan"
        confirm_text = (
            f"Anda akan menjalankan {action_name} untuk:\n"
            f"- Periode: {month:02d}/{year}\n"
            f"- Unit: {unit}\n"
            f"- Karyawan: {self.cb_calc_emp.currentText()}\n"
            f"- Jumlah Record: {self.current_preview['total_daily_records']} catatan\n\n"
            "Lanjutkan proses perhitungan?"
        )
        reply = QMessageBox.question(self, "Konfirmasi Perhitungan", confirm_text, QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        # Eksekusi Service
        user_name = self.user.nama if self.user else "ADMIN"
        res = DeductionCalculationService.calculate_and_save_period(
            year=year,
            month=month,
            unit=None if unit == "ALL" else unit,
            employee_id=emp_id,
            user_name=user_name,
            recalculate=recalculate,
        )

        if res["success"]:
            self.lbl_exec_result.setText(
                f"✅ {res['message']}"
            )
            self.lbl_exec_result.setStyleSheet("background-color: #d1fae5; color: #065f46; padding: 12px; border-radius: 6px; font-weight: 600;")
            self.lbl_exec_result.setVisible(True)
            self._load_calculation_preview()
            QMessageBox.information(self, "Perhitungan Selesai", res["message"])
        else:
            self.lbl_exec_result.setText(f"❌ Gagal: {res['message']}")
            self.lbl_exec_result.setStyleSheet("background-color: #fee2e2; color: #991b1b; padding: 12px; border-radius: 6px; font-weight: 600;")
            self.lbl_exec_result.setVisible(True)
            QMessageBox.critical(self, "Error Perhitungan", res["message"])

    def _validate_integrity(self):
        """Memeriksa integritas perhitungan (anti-double counting & rumus)."""
        year = self.cb_calc_year.currentData()
        month = self.cb_calc_month.currentData()
        val = DeductionCalculationService.validate_calculation_integrity(year, month)

        if val["is_valid"]:
            QMessageBox.information(
                self,
                "Integritas Valid",
                f"Pemeriksaan integritas selesai:\n"
                f"- Total record diperiksa: {val['total_checked']}\n"
                f"- Duplikasi / Double counting: TIDAK ADA (0)\n"
                f"- Seluruh rumus komponen dan batasan plafon sesuai aturan SK.",
            )
        else:
            issues_str = "\n".join(val["issues"][:10])
            QMessageBox.warning(
                self,
                "Ditemukan Anomali Integritas",
                f"Ditemukan {val['issue_count']} isu integritas:\n\n{issues_str}",
            )

    # =========================================================================
    # TAB 2: LOAD & EXPORT REKAP
    # =========================================================================
    def _load_rekap_data(self):
        year = self.cb_rekap_year.currentData()
        month = self.cb_rekap_month.currentData()
        unit = self.cb_rekap_unit.currentData()
        search = self.txt_rekap_search.text().strip()

        data = DeductionCalculationService.get_monthly_recap(
            year=year,
            month=month,
            unit=None if unit == "ALL" else unit,
            search=search if search else None,
        )
        self.rekap_data = data

        items = data["items"]
        self.table_rekap.setRowCount(len(items))

        for row_idx, it in enumerate(items):
            # No
            item_no = QTableWidgetItem(str(it["no"]))
            item_no.setTextAlignment(Qt.AlignCenter)
            self.table_rekap.setItem(row_idx, 0, item_no)

            # Unit
            self.table_rekap.setItem(row_idx, 1, QTableWidgetItem(str(it["unit"])))

            # Nama
            item_name = QTableWidgetItem(str(it["nama"]))
            item_name.setData(Qt.UserRole, it["employee_id"])
            self.table_rekap.setItem(row_idx, 2, item_name)

            # Status Kepegawaian
            item_st = QTableWidgetItem(str(it["status"]))
            item_st.setTextAlignment(Qt.AlignCenter)
            self.table_rekap.setItem(row_idx, 3, item_st)

            # Terlambat
            item_t = QTableWidgetItem(it["terlambat_formatted"])
            item_t.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_rekap.setItem(row_idx, 4, item_t)

            # Pulang Cepat
            item_pc = QTableWidgetItem(it["pulang_cepat_formatted"])
            item_pc.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_rekap.setItem(row_idx, 5, item_pc)

            # Tidak Absen Masuk
            item_mi = QTableWidgetItem(it["tidak_absen_masuk_formatted"])
            item_mi.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_rekap.setItem(row_idx, 6, item_mi)

            # Tidak Absen Pulang
            item_mo = QTableWidgetItem(it["tidak_absen_pulang_formatted"])
            item_mo.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_rekap.setItem(row_idx, 7, item_mo)

            # Jumlah Potongan
            item_tot = QTableWidgetItem(it["jumlah_potongan_formatted"])
            item_tot.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_tot.setStyleSheet("font-weight: 700; color: #b91c1c;")
            self.table_rekap.setItem(row_idx, 8, item_tot)

        # Update Card Ringkasan Total
        gt = data["grand_total"]
        self.lbl_tot_karyawan.setText(f"<b>Karyawan:</b> {gt['total_karyawan']}")
        self.lbl_tot_tlbt.setText(f"<b>Terlambat:</b> {gt['total_terlambat_formatted']}")
        self.lbl_tot_pc.setText(f"<b>Pulang Cepat:</b> {gt['total_pulang_cepat_formatted']}")
        self.lbl_tot_miss_in.setText(f"<b>Tdk Masuk:</b> {gt['total_tidak_absen_masuk_formatted']}")
        self.lbl_tot_miss_out.setText(f"<b>Tdk Pulang:</b> {gt['total_tidak_absen_pulang_formatted']}")
        self.lbl_grand_total.setText(f"TOTAL: {gt['total_potongan_keseluruhan_formatted']}")

    def _export_rekap_excel(self):
        if not self.rekap_data or not self.rekap_data["items"]:
            QMessageBox.warning(self, "Data Kosong", "Tidak ada data rekapitulasi untuk diekspor.")
            return

        year = self.cb_rekap_year.currentData()
        month = self.cb_rekap_month.currentData()
        unit = self.cb_rekap_unit.currentData()
        default_name = f"Rekap_Potongan_Absensi_{unit}_{month:02d}_{year}.xlsx"

        path, _ = QFileDialog.getSaveFileName(self, "Simpan Laporan Excel", default_name, "Excel Files (*.xlsx)")
        if path:
            ExportService.export_rekap_potongan_excel(self.rekap_data, path)
            QMessageBox.information(self, "Ekspor Berhasil", f"Laporan rekap berhasil disimpan ke:\n{path}")

    def _export_rekap_pdf(self):
        if not self.rekap_data or not self.rekap_data["items"]:
            QMessageBox.warning(self, "Data Kosong", "Tidak ada data rekapitulasi untuk diekspor.")
            return

        year = self.cb_rekap_year.currentData()
        month = self.cb_rekap_month.currentData()
        unit = self.cb_rekap_unit.currentData()
        default_name = f"Rekap_Potongan_Absensi_{unit}_{month:02d}_{year}.pdf"

        path, _ = QFileDialog.getSaveFileName(self, "Simpan Dokumen PDF", default_name, "PDF Files (*.pdf)")
        if path:
            user_name = self.user.nama if self.user else "Administrator"
            ExportService.export_rekap_potongan_pdf(self.rekap_data, user_name, path)
            QMessageBox.information(self, "Ekspor Berhasil", f"Dokumen PDF berhasil disimpan ke:\n{path}")

    # =========================================================================
    # TAB 3: LOAD & EXPORT DETAIL
    # =========================================================================
    def _load_daily_details(self):
        year = self.cb_det_year.currentData()
        month = self.cb_det_month.currentData()
        unit = self.cb_det_unit.currentData()
        status = self.cb_det_status.currentData()
        search = self.txt_det_search.text().strip()

        rows = DeductionCalculationService.get_daily_details(
            year=year,
            month=month,
            unit=None if unit == "ALL" else unit,
            search=search if search else None,
            status_filter=None if status == "ALL" else status,
        )
        self.daily_details_data = rows

        self.table_detail.setRowCount(len(rows))
        for r_idx, r in enumerate(rows):
            # 1. No
            it_no = QTableWidgetItem(str(r["no"]))
            it_no.setTextAlignment(Qt.AlignCenter)
            it_no.setData(Qt.UserRole, r)
            self.table_detail.setItem(r_idx, 0, it_no)

            # 2. Unit
            self.table_detail.setItem(r_idx, 1, QTableWidgetItem(str(r["unit"])))

            # 3. Nama
            self.table_detail.setItem(r_idx, 2, QTableWidgetItem(str(r["nama"])))

            # 4. Hari
            it_h = QTableWidgetItem(str(r["hari"]))
            it_h.setTextAlignment(Qt.AlignCenter)
            self.table_detail.setItem(r_idx, 3, it_h)

            # 5. Tanggal
            it_d = QTableWidgetItem(str(r["tanggal"]))
            it_d.setTextAlignment(Qt.AlignCenter)
            self.table_detail.setItem(r_idx, 4, it_d)

            # 6. Jam Masuk
            it_in = QTableWidgetItem(str(r["jam_masuk"]))
            it_in.setTextAlignment(Qt.AlignCenter)
            self.table_detail.setItem(r_idx, 5, it_in)

            # 7. Jam Pulang
            it_out = QTableWidgetItem(str(r["jam_pulang"]))
            it_out.setTextAlignment(Qt.AlignCenter)
            self.table_detail.setItem(r_idx, 6, it_out)

            # 8. Status Masuk
            it_sin = QTableWidgetItem(str(r["status_masuk"] or "-"))
            it_sin.setTextAlignment(Qt.AlignCenter)
            self.table_detail.setItem(r_idx, 7, it_sin)

            # 9. Status Pulang
            it_sout = QTableWidgetItem(str(r["status_pulang"] or "-"))
            it_sout.setTextAlignment(Qt.AlignCenter)
            self.table_detail.setItem(r_idx, 8, it_sout)

            # 10. Status Kehadiran
            it_stat = QTableWidgetItem(str(r["status_kehadiran"] or "-"))
            it_stat.setTextAlignment(Qt.AlignCenter)
            self.table_detail.setItem(r_idx, 9, it_stat)

            # 11. Menit Tlbt
            it_ltm = QTableWidgetItem(str(r["menit_terlambat"]))
            it_ltm.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_detail.setItem(r_idx, 10, it_ltm)

            # 12. Menit PC
            it_pcm = QTableWidgetItem(str(r["menit_pulang_cepat"]))
            it_pcm.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_detail.setItem(r_idx, 11, it_pcm)

            # 13. Pot. Tlbt
            it_plt = QTableWidgetItem(r["potongan_terlambat_formatted"])
            it_plt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_detail.setItem(r_idx, 12, it_plt)

            # 14. Pot. PC
            it_ppc = QTableWidgetItem(r["potongan_pulang_cepat_formatted"])
            it_ppc.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_detail.setItem(r_idx, 13, it_ppc)

            # 15. Tdk Absen Masuk
            it_pmi = QTableWidgetItem(r["tidak_absen_masuk_formatted"])
            it_pmi.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_detail.setItem(r_idx, 14, it_pmi)

            # 16. Tdk Absen Pulang
            it_pmo = QTableWidgetItem(r["tidak_absen_pulang_formatted"])
            it_pmo.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_detail.setItem(r_idx, 15, it_pmo)

            # 17. Total Potongan
            it_ptot = QTableWidgetItem(r["total_potongan_formatted"])
            it_ptot.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it_ptot.setStyleSheet("font-weight: 700; color: #b91c1c;")
            self.table_detail.setItem(r_idx, 16, it_ptot)

    def _open_selected_detail_dialog(self):
        row = self.table_detail.currentRow()
        if row < 0:
            QMessageBox.information(self, "Pilih Baris", "Silakan klik salah satu baris absensi untuk melihat detail.")
            return

        item = self.table_detail.item(row, 0)
        if not item:
            return
        row_data = item.data(Qt.UserRole)
        if row_data:
            dlg = DeductionDetailDialog(row_data, self)
            dlg.exec()

    def _export_detail_excel(self):
        if not self.daily_details_data:
            QMessageBox.warning(self, "Data Kosong", "Tidak ada data detail absensi untuk diekspor.")
            return

        year = self.cb_det_year.currentData()
        month = self.cb_det_month.currentData()
        unit = self.cb_det_unit.currentData()
        default_name = f"Detail_Absensi_Potongan_{unit}_{month:02d}_{year}.xlsx"

        path, _ = QFileDialog.getSaveFileName(self, "Simpan Laporan Excel", default_name, "Excel Files (*.xlsx)")
        if path:
            ExportService.export_detail_absensi_excel(self.daily_details_data, year, month, unit, path)
            QMessageBox.information(self, "Ekspor Berhasil", f"Laporan detail berhasil disimpan ke:\n{path}")

    def _export_detail_pdf(self):
        if not self.daily_details_data:
            QMessageBox.warning(self, "Data Kosong", "Tidak ada data detail absensi untuk diekspor.")
            return

        year = self.cb_det_year.currentData()
        month = self.cb_det_month.currentData()
        unit = self.cb_det_unit.currentData()
        default_name = f"Detail_Absensi_Potongan_{unit}_{month:02d}_{year}.pdf"

        path, _ = QFileDialog.getSaveFileName(self, "Simpan Dokumen PDF", default_name, "PDF Files (*.pdf)")
        if path:
            user_name = self.user.nama if self.user else "Administrator"
            ExportService.export_detail_absensi_pdf(self.daily_details_data, year, month, unit, user_name, path)
            QMessageBox.information(self, "Ekspor Berhasil", f"Dokumen PDF detail berhasil disimpan ke:\n{path}")
