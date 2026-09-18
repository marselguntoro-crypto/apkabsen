"""
Modul Pusat Laporan & Rekapitulasi Potongan (ReportsHubPage) - PySide6.
Menyediakan 2 Tab Laporan Utama:
Tab 1: REKAP DATA POTONGAN ABSENSI (Per Karyawan, Subtotal Unit, Grand Total).
Tab 2: LAPORAN DATA ABSENSI DAN POTONGAN HARIAN (Detail day-by-day, filter kehadiran, pagination).
Dilengkapi fitur pencarian, filter unit, sorting, dan export langsung ke Excel dan PDF.
"""
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QTabWidget,
    QFrame,
    QSpinBox,
)

from config.settings import THEME
from database.connection import get_db_session
from database.models import Employee, AttendanceStatus
from services.deduction_calculation_service import DeductionCalculationService
from services.export_service import ExportService
from utils.logger import get_logger

logger = get_logger("ReportsHubPage")


class ReportsHubPage(QWidget):
    """Pusat Laporan Presensi & Potongan SIAP."""

    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.current_page = 1
        self.page_size = 50
        self._init_ui()
        self.refresh_recap()
        self.refresh_daily()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # 1. Header Halaman
        header_box = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        lbl_title = QLabel("Laporan & Rekapitulasi Presensi")
        lbl_title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {THEME['NAVY_DARK']};")
        title_box.addWidget(lbl_title)

        lbl_desc = QLabel("Cetak dan ekspor laporan potongan bulanan dan rincian kehadiran harian karyawan.")
        lbl_desc.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        title_box.addWidget(lbl_desc)

        header_box.addLayout(title_box)
        header_box.addStretch()

        main_layout.addLayout(header_box)

        # 2. Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {THEME['BORDER']};
                background: #ffffff;
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: #f1f5f9;
                color: {THEME['TEXT_MUTED']};
                font-weight: 600;
                font-size: 12px;
                padding: 8px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background: #ffffff;
                color: {THEME['BLUE_PRIMARY']};
                border: 1px solid {THEME['BORDER']};
                border-bottom: 1px solid #ffffff;
            }}
        """)

        # Tab 1: Rekap Potongan
        self.tab_recap = QWidget()
        self._init_tab_recap()
        self.tabs.addTab(self.tab_recap, "📋 Rekap Potongan Bulanan")

        # Tab 2: Detail Absensi Harian
        self.tab_daily = QWidget()
        self._init_tab_daily()
        self.tabs.addTab(self.tab_daily, "📅 Laporan Data Absensi Harian")

        main_layout.addWidget(self.tabs)

    def _init_tab_recap(self):
        layout = QVBoxLayout(self.tab_recap)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filter Bar
        fb = QHBoxLayout()
        fb.setSpacing(10)

        fb.addWidget(QLabel("Bulan:"))
        self.recap_cb_month = QComboBox()
        self.recap_cb_month.setFixedWidth(110)
        months = [
            ("Januari", 1), ("Februari", 2), ("Maret", 3), ("April", 4),
            ("Mei", 5), ("Juni", 6), ("Juli", 7), ("Agustus", 8),
            ("September", 9), ("Oktober", 10), ("November", 11), ("Desember", 12)
        ]
        for name, val in months:
            self.recap_cb_month.addItem(name, val)
        self.recap_cb_month.setCurrentIndex(7)  # Agustus
        fb.addWidget(self.recap_cb_month)

        fb.addWidget(QLabel("Tahun:"))
        self.recap_cb_year = QComboBox()
        self.recap_cb_year.setFixedWidth(80)
        for y in range(2024, 2028):
            self.recap_cb_year.addItem(str(y), y)
        self.recap_cb_year.setCurrentText("2026")
        fb.addWidget(self.recap_cb_year)

        fb.addWidget(QLabel("Unit:"))
        self.recap_cb_unit = QComboBox()
        self.recap_cb_unit.setFixedWidth(160)
        self.recap_cb_unit.addItem("Semua Unit", "ALL")
        self._load_units_into_combo(self.recap_cb_unit)
        fb.addWidget(self.recap_cb_unit)

        fb.addWidget(QLabel("Cari:"))
        self.recap_txt_search = QLineEdit()
        self.recap_txt_search.setPlaceholderText("Nama / NIK / No ID...")
        self.recap_txt_search.setFixedWidth(160)
        fb.addWidget(self.recap_txt_search)

        btn_search = QPushButton("Cari")
        btn_search.clicked.connect(self.refresh_recap)
        fb.addWidget(btn_search)

        fb.addStretch()

        # Export Buttons
        btn_exp_excel = QPushButton("📊 Export Excel")
        btn_exp_excel.setStyleSheet(f"color: #059669; font-weight: 700; border: 1px solid {THEME['BORDER']}; padding: 6px 12px; border-radius: 6px;")
        btn_exp_excel.clicked.connect(self.export_recap_excel)
        fb.addWidget(btn_exp_excel)

        btn_exp_pdf = QPushButton("📄 Export PDF")
        btn_exp_pdf.setStyleSheet("color: #dc2626; font-weight: 700; border: 1px solid #e2e8f0; padding: 6px 12px; border-radius: 6px;")
        btn_exp_pdf.clicked.connect(self.export_recap_pdf)
        fb.addWidget(btn_exp_pdf)

        layout.addLayout(fb)

        # Tabel Rekap
        self.table_recap = QTableWidget()
        self.table_recap.setColumnCount(9)
        self.table_recap.setHorizontalHeaderLabels([
            "No", "Unit", "Nama Karyawan", "Status", "Terlambat",
            "Pulang Cepat", "Tdk Absen Masuk", "Tdk Absen Pulang", "Jumlah Potongan Absensi"
        ])
        self.table_recap.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_recap.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_recap.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_recap.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_recap)

        # Footer Grand Total
        self.lbl_recap_summary = QLabel("Memuat data rekapitulasi...")
        self.lbl_recap_summary.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {THEME['NAVY_DARK']}; padding: 6px 0;")
        layout.addWidget(self.lbl_recap_summary)

        # Sinyal Filter
        self.recap_cb_month.currentIndexChanged.connect(self.refresh_recap)
        self.recap_cb_year.currentIndexChanged.connect(self.refresh_recap)
        self.recap_cb_unit.currentIndexChanged.connect(self.refresh_recap)
        self.recap_txt_search.returnPressed.connect(self.refresh_recap)

    def _init_tab_daily(self):
        layout = QVBoxLayout(self.tab_daily)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filter Bar
        fb = QHBoxLayout()
        fb.setSpacing(10)

        fb.addWidget(QLabel("Bulan:"))
        self.daily_cb_month = QComboBox()
        self.daily_cb_month.setFixedWidth(110)
        months = [
            ("Januari", 1), ("Februari", 2), ("Maret", 3), ("April", 4),
            ("Mei", 5), ("Juni", 6), ("Juli", 7), ("Agustus", 8),
            ("September", 9), ("Oktober", 10), ("November", 11), ("Desember", 12)
        ]
        for name, val in months:
            self.daily_cb_month.addItem(name, val)
        self.daily_cb_month.setCurrentIndex(7)  # Agustus
        fb.addWidget(self.daily_cb_month)

        fb.addWidget(QLabel("Tahun:"))
        self.daily_cb_year = QComboBox()
        self.daily_cb_year.setFixedWidth(80)
        for y in range(2024, 2028):
            self.daily_cb_year.addItem(str(y), y)
        self.daily_cb_year.setCurrentText("2026")
        fb.addWidget(self.daily_cb_year)

        fb.addWidget(QLabel("Unit:"))
        self.daily_cb_unit = QComboBox()
        self.daily_cb_unit.setFixedWidth(160)
        self.daily_cb_unit.addItem("Semua Unit", "ALL")
        self._load_units_into_combo(self.daily_cb_unit)
        fb.addWidget(self.daily_cb_unit)

        fb.addWidget(QLabel("Status:"))
        self.daily_cb_status = QComboBox()
        self.daily_cb_status.setFixedWidth(140)
        self.daily_cb_status.addItem("Semua Status", "ALL")
        for s in AttendanceStatus:
            self.daily_cb_status.addItem(s.value, s.value)
        fb.addWidget(self.daily_cb_status)

        fb.addWidget(QLabel("Cari:"))
        self.daily_txt_search = QLineEdit()
        self.daily_txt_search.setPlaceholderText("Nama / NIK...")
        self.daily_txt_search.setFixedWidth(140)
        fb.addWidget(self.daily_txt_search)

        btn_search = QPushButton("Cari")
        btn_search.clicked.connect(self.refresh_daily)
        fb.addWidget(btn_search)

        fb.addStretch()

        # Export Buttons
        btn_exp_excel = QPushButton("📊 Export Excel")
        btn_exp_excel.setStyleSheet("color: #059669; font-weight: 700; border: 1px solid #e2e8f0; padding: 6px 12px; border-radius: 6px;")
        btn_exp_excel.clicked.connect(self.export_daily_excel)
        fb.addWidget(btn_exp_excel)

        btn_exp_pdf = QPushButton("📄 Export PDF")
        btn_exp_pdf.setStyleSheet("color: #dc2626; font-weight: 700; border: 1px solid #e2e8f0; padding: 6px 12px; border-radius: 6px;")
        btn_exp_pdf.clicked.connect(self.export_daily_pdf)
        fb.addWidget(btn_exp_pdf)

        layout.addLayout(fb)

        # Tabel Detail Harian
        self.table_daily = QTableWidget()
        self.table_daily.setColumnCount(17)
        self.table_daily.setHorizontalHeaderLabels([
            "No", "Unit", "Nama", "Hari", "Tanggal", "Masuk", "Pulang",
            "Status Masuk", "Status Pulang", "Status Kehadiran",
            "Menit Tlb", "Menit PC", "Pot. Terlambat", "Pot. Pulang Cepat",
            "Tdk Absen Masuk", "Tdk Absen Pulang", "Total Potongan Per Hari"
        ])
        self.table_daily.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_daily.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_daily.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_daily.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_daily)

        # Pagination Bar
        pb = QHBoxLayout()
        self.btn_prev = QPushButton("◀ Sebelumnya")
        self.btn_prev.clicked.connect(self.prev_page)
        pb.addWidget(self.btn_prev)

        self.lbl_page_info = QLabel("Halaman 1 / 1")
        self.lbl_page_info.setStyleSheet("font-size: 11px; font-weight: 600; color: #475569;")
        pb.addWidget(self.lbl_page_info)

        self.btn_next = QPushButton("Berikutnya ▶")
        self.btn_next.clicked.connect(self.next_page)
        pb.addWidget(self.btn_next)

        pb.addStretch()
        self.lbl_daily_total = QLabel("Total Data: 0")
        self.lbl_daily_total.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        pb.addWidget(self.lbl_daily_total)

        layout.addLayout(pb)

        # Sinyal Filter
        self.daily_cb_month.currentIndexChanged.connect(self.refresh_daily)
        self.daily_cb_year.currentIndexChanged.connect(self.refresh_daily)
        self.daily_cb_unit.currentIndexChanged.connect(self.refresh_daily)
        self.daily_cb_status.currentIndexChanged.connect(self.refresh_daily)
        self.daily_txt_search.returnPressed.connect(self.refresh_daily)

    def _load_units_into_combo(self, combo: QComboBox):
        try:
            with get_db_session() as session:
                units = session.query(Employee.unit).distinct().filter(Employee.unit.isnot(None)).all()
                for u in sorted([unit[0] for unit in units if unit[0]]):
                    combo.addItem(u, u)
        except Exception as e:
            logger.error(f"Gagal memuat daftar unit: {e}")

    def refresh_recap(self):
        m = self.recap_cb_month.currentData()
        y = self.recap_cb_year.currentData()
        u = self.recap_cb_unit.currentData()
        kw = self.recap_txt_search.text().strip()

        recap = DeductionCalculationService.get_monthly_deduction_recap(
            year=y,
            month=m,
            unit=u if u != "ALL" else None,
            keyword=kw if kw else None,
        )
        rows = recap["rows"]
        gt = recap["grand_total"]

        self.table_recap.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table_recap.setItem(i, 0, QTableWidgetItem(str(r["no"])))
            self.table_recap.setItem(i, 1, QTableWidgetItem(r["unit"]))
            self.table_recap.setItem(i, 2, QTableWidgetItem(r["nama"]))
            self.table_recap.setItem(i, 3, QTableWidgetItem(r["status"]))
            self.table_recap.setItem(i, 4, QTableWidgetItem(f"Rp {r['terlambat']:,}".replace(",", ".")))
            self.table_recap.setItem(i, 5, QTableWidgetItem(f"Rp {r['pulang_cepat']:,}".replace(",", ".")))
            self.table_recap.setItem(i, 6, QTableWidgetItem(f"Rp {r['tidak_absen_masuk']:,}".replace(",", ".")))
            self.table_recap.setItem(i, 7, QTableWidgetItem(f"Rp {r['tidak_absen_pulang']:,}".replace(",", ".")))
            self.table_recap.setItem(i, 8, QTableWidgetItem(f"Rp {r['jumlah_potongan_absensi']:,}".replace(",", ".")))

            self.table_recap.item(i, 0).setTextAlignment(Qt.AlignCenter)
            self.table_recap.item(i, 3).setTextAlignment(Qt.AlignCenter)
            for col in range(4, 9):
                self.table_recap.item(i, col).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.lbl_recap_summary.setText(
            f"GRAND TOTAL PERIODE: {gt['karyawan_count']} Karyawan | "
            f"Terlambat: Rp {gt['terlambat']:,} | Pulang Cepat: Rp {gt['pulang_cepat']:,} | "
            f"Tdk Absen Masuk: Rp {gt['tidak_absen_masuk']:,} | Tdk Absen Pulang: Rp {gt['tidak_absen_pulang']:,} | "
            f"TOTAL POTONGAN: Rp {gt['total_potongan']:,}".replace(",", ".")
        )

    def refresh_daily(self):
        m = self.daily_cb_month.currentData()
        y = self.daily_cb_year.currentData()
        u = self.daily_cb_unit.currentData()
        s = self.daily_cb_status.currentData()
        kw = self.daily_txt_search.text().strip()

        rep = DeductionCalculationService.get_daily_deduction_report(
            year=y,
            month=m,
            unit=u if u != "ALL" else None,
            attendance_status=s if s != "ALL" else None,
            keyword=kw if kw else None,
            page=self.current_page,
            page_size=self.page_size,
        )
        records = rep["records"]

        self.table_daily.setRowCount(len(records))
        for i, r in enumerate(records):
            self.table_daily.setItem(i, 0, QTableWidgetItem(str(r["no"])))
            self.table_daily.setItem(i, 1, QTableWidgetItem(r["unit"]))
            self.table_daily.setItem(i, 2, QTableWidgetItem(r["nama"]))
            self.table_daily.setItem(i, 3, QTableWidgetItem(r["hari"]))
            self.table_daily.setItem(i, 4, QTableWidgetItem(r["tanggal"]))
            self.table_daily.setItem(i, 5, QTableWidgetItem(r["jam_masuk"]))
            self.table_daily.setItem(i, 6, QTableWidgetItem(r["jam_pulang"]))
            self.table_daily.setItem(i, 7, QTableWidgetItem(r["status_masuk"]))
            self.table_daily.setItem(i, 8, QTableWidgetItem(r["status_pulang"]))
            self.table_daily.setItem(i, 9, QTableWidgetItem(r["status_kehadiran"]))
            self.table_daily.setItem(i, 10, QTableWidgetItem(str(r["menit_terlambat"])))
            self.table_daily.setItem(i, 11, QTableWidgetItem(str(r["menit_pulang_cepat"])))
            self.table_daily.setItem(i, 12, QTableWidgetItem(f"Rp {r['potongan_terlambat']:,}".replace(",", ".")))
            self.table_daily.setItem(i, 13, QTableWidgetItem(f"Rp {r['potongan_pulang_cepat']:,}".replace(",", ".")))
            self.table_daily.setItem(i, 14, QTableWidgetItem(f"Rp {r['tidak_absen_masuk']:,}".replace(",", ".")))
            self.table_daily.setItem(i, 15, QTableWidgetItem(f"Rp {r['tidak_absen_pulang']:,}".replace(",", ".")))
            self.table_daily.setItem(i, 16, QTableWidgetItem(f"Rp {r['total_potongan_per_hari']:,}".replace(",", ".")))

            self.table_daily.item(i, 0).setTextAlignment(Qt.AlignCenter)
            for c in (3, 4, 5, 6, 7, 8, 9):
                self.table_daily.item(i, c).setTextAlignment(Qt.AlignCenter)
            for c in range(10, 17):
                self.table_daily.item(i, c).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.lbl_page_info.setText(f"Halaman {rep['current_page']} / {rep['total_pages']}")
        self.lbl_daily_total.setText(f"Total Data: {rep['total_records']}")
        self.btn_prev.setEnabled(rep["current_page"] > 1)
        self.btn_next.setEnabled(rep["current_page"] < rep["total_pages"])

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_daily()

    def next_page(self):
        self.current_page += 1
        self.refresh_daily()

    def export_recap_excel(self):
        m = self.recap_cb_month.currentData()
        y = self.recap_cb_year.currentData()
        u = self.recap_cb_unit.currentData()
        try:
            path = ExportService.export_rekap_potongan_excel(
                year=y,
                month=m,
                unit=u if u != "ALL" else None,
                user_name=self.user.username if self.user else "ADMIN",
            )
            QMessageBox.information(self, "Export Berhasil", f"Berkas Rekap Excel berhasil diekspor ke:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Terjadi kesalahan saat export Excel: {e}")

    def export_recap_pdf(self):
        m = self.recap_cb_month.currentData()
        y = self.recap_cb_year.currentData()
        u = self.recap_cb_unit.currentData()
        try:
            path = ExportService.export_rekap_potongan_pdf(
                year=y,
                month=m,
                unit=u if u != "ALL" else None,
                user_name=self.user.username if self.user else "ADMIN",
            )
            QMessageBox.information(self, "Export Berhasil", f"Dokumen Rekap PDF berhasil diekspor ke:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Terjadi kesalahan saat export PDF: {e}")

    def export_daily_excel(self):
        m = self.daily_cb_month.currentData()
        y = self.daily_cb_year.currentData()
        u = self.daily_cb_unit.currentData()
        s = self.daily_cb_status.currentData()
        try:
            path = ExportService.export_detail_absensi_excel(
                year=y,
                month=m,
                unit=u if u != "ALL" else None,
                attendance_status=s if s != "ALL" else None,
                user_name=self.user.username if self.user else "ADMIN",
            )
            QMessageBox.information(self, "Export Berhasil", f"Berkas Detail Absensi Excel berhasil disimpan ke:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Terjadi kesalahan saat export Excel: {e}")

    def export_daily_pdf(self):
        m = self.daily_cb_month.currentData()
        y = self.daily_cb_year.currentData()
        u = self.daily_cb_unit.currentData()
        s = self.daily_cb_status.currentData()
        try:
            path = ExportService.export_detail_absensi_pdf(
                year=y,
                month=m,
                unit=u if u != "ALL" else None,
                attendance_status=s if s != "ALL" else None,
                user_name=self.user.username if self.user else "ADMIN",
            )
            QMessageBox.information(self, "Export Berhasil", f"Dokumen Detail Absensi PDF berhasil disimpan ke:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Terjadi kesalahan saat export PDF: {e}")
