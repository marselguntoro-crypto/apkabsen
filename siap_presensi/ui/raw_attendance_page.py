"""
Halaman Data Absensi Mentah (Raw Attendance Page) SIAP.
Menampilkan seluruh catatan transaksi absensi yang tersimpan di tabel attendance_raw:
- Kolom: No, Emp Num., No. ID., NIK, Nama Karyawan, Tanggal, Scan Masuk, Scan Pulang, Source File, Batch ID, Waktu Import
- Fitur: Multi-parameter search, filter periode (Bulan/Tahun atau Tanggal), filter Batch ID, sorting, paginasi, dan Export Excel.
- PENTING: Hanya menampilkan data mentah, tanpa status alfa atau kalkulasi potongan.
"""
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QMessageBox,
    QFileDialog,
)
from config.settings import THEME
from database.models import User
from database.connection import get_db_session
from services.attendance_raw_service import AttendanceRawService


class RawAttendancePage(QWidget):
    """Halaman Pengelolaan dan Penelusuran Data Absensi Mentah."""

    def __init__(self, parent=None, user: Optional[User] = None):
        super().__init__(parent)
        self.user = user
        self.current_page = 1
        self.page_size = 50
        self.total_pages = 1

        self._init_ui()
        self._load_batches()
        self.refresh_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # 1. Header Judul & Tombol Ekspor
        h_box = QHBoxLayout()
        t_box = QVBoxLayout()
        t_box.setSpacing(2)

        t_lbl = QLabel("Data Transaksi Absensi Mentah (Raw Data)")
        t_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {THEME['NAVY_DARK']};")
        t_box.addWidget(t_lbl)

        sub_lbl = QLabel(
            "Tabel transaksi absensi asli hasil import mesin fingerprint. "
            "Data mentah belum dikenakan kalkulasi keterlambatan, alfa, maupun potongan."
        )
        sub_lbl.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        t_box.addWidget(sub_lbl)
        h_box.addLayout(t_box)

        h_box.addStretch()

        self.btn_export = QPushButton("📤 Ekspor ke Excel (.xlsx)")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setFixedHeight(38)
        self.btn_export.setStyleSheet(f"""
            QPushButton {{
                background-color: #059669;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #047857; }}
        """)
        self.btn_export.clicked.connect(self._on_export_excel)
        h_box.addWidget(self.btn_export)

        self.btn_refresh = QPushButton("🔄 Segarkan")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setFixedHeight(38)
        self.btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {THEME['TEXT_MAIN']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 14px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #f8fafc; }}
        """)
        self.btn_refresh.clicked.connect(self.refresh_data)
        h_box.addWidget(self.btn_refresh)

        layout.addLayout(h_box)

        # 2. Filter Bar Lengkap
        filter_card = QFrame()
        filter_card.setStyleSheet(f"""
            QFrame {{
                background-color: #F8FAFC;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
                padding: 8px 12px;
            }}
        """)
        f_layout = QHBoxLayout(filter_card)
        f_layout.setContentsMargins(4, 4, 4, 4)
        f_layout.setSpacing(10)

        # Kata Kunci
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari nama karyawan, Emp Num, No ID, NIK...")
        self.search_input.setFixedHeight(34)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 10px;
                background-color: #ffffff;
                font-size: 12px;
            }}
        """)
        self.search_input.textChanged.connect(self._on_filter_changed)
        f_layout.addWidget(self.search_input, stretch=3)

        # Filter Batch ID
        f_layout.addWidget(QLabel("Batch:"))
        self.batch_combo = QComboBox()
        self.batch_combo.setFixedHeight(34)
        self.batch_combo.addItem("SEMUA")
        self.batch_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 8px;
                background-color: #ffffff;
                font-size: 12px;
            }}
        """)
        self.batch_combo.currentIndexChanged.connect(self._on_filter_changed)
        f_layout.addWidget(self.batch_combo, stretch=2)

        # Filter Bulan
        f_layout.addWidget(QLabel("Bulan:"))
        self.month_combo = QComboBox()
        self.month_combo.setFixedHeight(34)
        self.month_combo.addItems([
            "Semua", "01 - Januari", "02 - Februari", "03 - Maret",
            "04 - April", "05 - Mei", "06 - Juni", "07 - Juli",
            "08 - Agustus", "09 - September", "10 - Oktober",
            "11 - November", "12 - Desember"
        ])
        self.month_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 8px;
                background-color: #ffffff;
                font-size: 12px;
            }}
        """)
        self.month_combo.currentIndexChanged.connect(self._on_filter_changed)
        f_layout.addWidget(self.month_combo, stretch=1)

        # Filter Tahun
        f_layout.addWidget(QLabel("Tahun:"))
        self.year_combo = QComboBox()
        self.year_combo.setFixedHeight(34)
        self.year_combo.addItems(["Semua", "2024", "2025", "2026", "2027"])
        self.year_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 8px;
                background-color: #ffffff;
                font-size: 12px;
            }}
        """)
        self.year_combo.currentIndexChanged.connect(self._on_filter_changed)
        f_layout.addWidget(self.year_combo, stretch=1)

        # Urutkan
        f_layout.addWidget(QLabel("Urutan:"))
        self.sort_combo = QComboBox()
        self.sort_combo.setFixedHeight(34)
        self.sort_combo.addItems([
            "Tanggal Terbaru",
            "Tanggal Terlama",
            "Nama A-Z",
            "Nama Z-A"
        ])
        self.sort_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 8px;
                background-color: #ffffff;
                font-size: 12px;
            }}
        """)
        self.sort_combo.currentIndexChanged.connect(self._on_filter_changed)
        f_layout.addWidget(self.sort_combo, stretch=2)

        layout.addWidget(filter_card)

        # 3. Tabel Data Raw
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "No", "Emp Num.", "No. ID.", "NIK", "Nama Karyawan",
            "Tanggal", "Scan Masuk", "Scan Pulang", "Source File", "Batch ID", "Waktu Import"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
                gridline-color: #f1f5f9;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: #f8fafc;
                color: {THEME['NAVY_DARK']};
                padding: 8px 6px;
                font-weight: 700;
                border: none;
                border-bottom: 2px solid {THEME['BORDER']};
            }}
        """)
        layout.addWidget(self.table)

        # 4. Paginasi & Bar Bawah
        nav_layout = QHBoxLayout()
        self.lbl_page_info = QLabel("Memuat data...")
        self.lbl_page_info.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        nav_layout.addWidget(self.lbl_page_info)

        nav_layout.addStretch()

        self.btn_prev = QPushButton("◀ Sebelumnya")
        self.btn_prev.setFixedHeight(32)
        self.btn_prev.setStyleSheet(self._nav_btn_style())
        self.btn_prev.clicked.connect(self._prev_page)
        nav_layout.addWidget(self.btn_prev)

        self.lbl_current_page = QLabel("1 / 1")
        self.lbl_current_page.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        nav_layout.addWidget(self.lbl_current_page)

        self.btn_next = QPushButton("Berikutnya ▶")
        self.btn_next.setFixedHeight(32)
        self.btn_next.setStyleSheet(self._nav_btn_style())
        self.btn_next.clicked.connect(self._next_page)
        nav_layout.addWidget(self.btn_next)

        layout.addLayout(nav_layout)

    def _nav_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: #ffffff;
                color: {THEME['TEXT_MAIN']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 4px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #f8fafc; }}
            QPushButton:disabled {{ color: #cbd5e1; }}
        """

    def _load_batches(self):
        """Memuat daftar batch yang ada di database ke combobox."""
        try:
            with get_db_session() as db:
                batches = AttendanceRawService.get_available_batches(db)
                self.batch_combo.clear()
                self.batch_combo.addItem("SEMUA")
                for b in batches:
                    self.batch_combo.addItem(b)
        except Exception as e:
            pass

    def _on_filter_changed(self):
        self.current_page = 1
        self.refresh_data()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_data()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.refresh_data()

    def _parse_filter_params(self):
        """Mengurai nilai filter dari widget."""
        kw = self.search_input.text().strip()
        batch = self.batch_combo.currentText()
        if batch == "SEMUA":
            batch = None

        month_idx = self.month_combo.currentIndex()
        month = month_idx if month_idx > 0 else None

        year_text = self.year_combo.currentText()
        year = int(year_text) if year_text.isdigit() else None

        sort_choice = self.sort_combo.currentText()
        if sort_choice == "Tanggal Terbaru":
            sort_by, sort_dir = "tanggal", "desc"
        elif sort_choice == "Tanggal Terlama":
            sort_by, sort_dir = "tanggal", "asc"
        elif sort_choice == "Nama A-Z":
            sort_by, sort_dir = "nama", "asc"
        else:
            sort_by, sort_dir = "nama", "desc"

        return kw, batch, month, year, sort_by, sort_dir

    def refresh_data(self):
        """Mengambil data absensi mentah dari database."""
        kw, batch, month, year, sort_by, sort_dir = self._parse_filter_params()

        try:
            with get_db_session() as db:
                records, total, total_pg = AttendanceRawService.get_raw_records(
                    db=db,
                    keyword=kw,
                    batch_id=batch,
                    month=month,
                    year=year,
                    sort_by=sort_by,
                    sort_dir=sort_dir,
                    page=self.current_page,
                    page_size=self.page_size,
                )
                self.total_pages = total_pg
                self._populate_table(records, total)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat data transaksi mentah: {e}")

    def _populate_table(self, records: List[Dict[str, Any]], total: int):
        self.table.setRowCount(0)
        self.table.setRowCount(len(records))

        self.lbl_page_info.setText(f"Total: {total:,} transaksi presensi mentah tercatat")
        self.lbl_current_page.setText(f"{self.current_page} / {self.total_pages}")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)

        for row_idx, r in enumerate(records):
            # No
            item_no = QTableWidgetItem(str(r["no"]))
            item_no.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 0, item_no)

            # Emp Num
            self.table.setItem(row_idx, 1, QTableWidgetItem(r.get("emp_num") or "-"))

            # No ID
            self.table.setItem(row_idx, 2, QTableWidgetItem(r.get("no_id") or "-"))

            # NIK
            self.table.setItem(row_idx, 3, QTableWidgetItem(r.get("nik") or "-"))

            # Nama
            self.table.setItem(row_idx, 4, QTableWidgetItem(r.get("nama") or "-"))

            # Tanggal
            item_tgl = QTableWidgetItem(r.get("tanggal") or "-")
            item_tgl.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 5, item_tgl)

            # Scan Masuk
            item_in = QTableWidgetItem(r.get("scan_masuk") or "-")
            item_in.setTextAlignment(Qt.AlignCenter)
            if not r.get("scan_masuk"):
                item_in.setForeground(Qt.gray)
            self.table.setItem(row_idx, 6, item_in)

            # Scan Pulang
            item_out = QTableWidgetItem(r.get("scan_pulang") or "-")
            item_out.setTextAlignment(Qt.AlignCenter)
            if not r.get("scan_pulang"):
                item_out.setForeground(Qt.gray)
            self.table.setItem(row_idx, 7, item_out)

            # Source File
            self.table.setItem(row_idx, 8, QTableWidgetItem(r.get("source_file") or "-"))

            # Batch ID
            item_b = QTableWidgetItem(r.get("import_batch_id") or "-")
            item_b.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 9, item_b)

            # Created At
            item_dt = QTableWidgetItem(r.get("created_at") or "-")
            item_dt.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 10, item_dt)

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(4, 200)  # Nama karyawan
        self.table.setColumnWidth(8, 160)  # Source file

    def _on_export_excel(self):
        """Mengekspor data hasil filter ke berkas Excel .xlsx."""
        kw, batch, month, year, _, _ = self._parse_filter_params()

        default_filename = f"Data_Absensi_Raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Ekspor Data Absensi Mentah",
            default_filename,
            "Excel Files (*.xlsx);;CSV Files (*.csv)",
        )
        if not save_path:
            return

        try:
            with get_db_session() as db:
                exported_file = AttendanceRawService.export_raw_to_excel(
                    db=db,
                    filepath=save_path,
                    keyword=kw,
                    batch_id=batch,
                    month=month,
                    year=year,
                )
                QMessageBox.information(
                    self,
                    "Ekspor Berhasil",
                    f"Data absensi mentah berhasil diekspor ke:\n{exported_file}",
                )
        except Exception as e:
            QMessageBox.critical(self, "Ekspor Gagal", f"Gagal mengekspor data absensi: {e}")
