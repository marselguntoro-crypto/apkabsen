"""
Dialog Pratinjau & Validasi Excel (Excel Preview Dialog) SIAP.
Menampilkan tabel pratinjau seluruh baris transaksi hasil parsing:
- Filter baris: Semua, Valid, Invalid, Duplikat, Jam Kosong
- Status validasi baris: VALID, INVALID, DUPLIKAT, TIDAK DITEMUKAN
- Pengaturan resolusi duplikat & karyawan tidak ditemukan
- Tombol aksi: Validasi Ulang, Import Data (terkunci jika 0 data valid), Batal
"""
from typing import Dict, Any, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QLineEdit,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QMessageBox,
)
from config.settings import THEME


class ExcelPreviewDialog(QDialog):
    """Dialog modal pratinjau tabel transaksi absensi mentah sebelum commit."""

    revalidate_requested = Signal()

    def __init__(self, preview_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.preview_data = preview_data
        self.rows: List[Dict[str, Any]] = preview_data.get("rows", [])
        self.filtered_rows: List[Dict[str, Any]] = list(self.rows)

        self.duplicate_strategy = "SKIP"      # "SKIP" atau "INSERT"
        self.unmatched_strategy = "UNLINKED"  # "UNLINKED", "SKIP", "CREATE"
        self.is_confirmed = False

        self.setWindowTitle(f"Pratinjau Data Absensi - {preview_data.get('source_file', 'Excel')}")
        self.resize(1200, 720)
        self.setMinimumSize(960, 600)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(14)

        # 1. Header & Ringkasan Metrik
        header_box = QHBoxLayout()
        header_title = QVBoxLayout()
        header_title.setSpacing(2)

        t_lbl = QLabel(f"Pratinjau Berkas: {self.preview_data.get('source_file', 'Excel')}")
        t_lbl.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {THEME['NAVY_DARK']};")
        header_title.addWidget(t_lbl)

        sheet_info = self.preview_data.get("sheet_name", "Sheet1")
        sub_lbl = QLabel(f"Worksheet: {sheet_info} | Periksa keabsahan format sebelum menyimpan ke database.")
        sub_lbl.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        header_title.addWidget(sub_lbl)
        header_box.addLayout(header_title)

        header_box.addStretch()

        # Kartu-kartu badge ringkasan
        total_r = self.preview_data.get("total_rows", 0)
        valid_r = self.preview_data.get("valid_rows_count", 0)
        invalid_r = self.preview_data.get("invalid_rows_count", 0)
        dup_r = self.preview_data.get("duplicate_rows_count", 0)
        empty_jam_r = self.preview_data.get("empty_jam_count", 0)

        def make_metric_chip(label: str, count: int, bg: str, text_color: str):
            f = QFrame()
            f.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg};
                    border-radius: 8px;
                    padding: 4px 10px;
                }}
            """)
            fl = QVBoxLayout(f)
            fl.setContentsMargins(4, 2, 4, 2)
            fl.setSpacing(0)
            fl.setAlignment(Qt.AlignCenter)
            c_lbl = QLabel(str(count))
            c_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {text_color};")
            c_lbl.setAlignment(Qt.AlignCenter)
            l_lbl = QLabel(label)
            l_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {text_color}; text-transform: uppercase;")
            l_lbl.setAlignment(Qt.AlignCenter)
            fl.addWidget(c_lbl)
            fl.addWidget(l_lbl)
            return f

        header_box.addWidget(make_metric_chip("Total", total_r, "#F1F5F9", "#334155"))
        header_box.addWidget(make_metric_chip("Valid", valid_r, "#DCFCE7", "#15803D"))
        header_box.addWidget(make_metric_chip("Invalid", invalid_r, "#FEE2E2", "#B91C1C"))
        header_box.addWidget(make_metric_chip("Duplikat", dup_r, "#FEF3C7", "#B45309"))
        header_box.addWidget(make_metric_chip("Jam Kosong", empty_jam_r, "#E0F2FE", "#0369A1"))

        root_layout.addLayout(header_box)

        # 2. Bilah Filter & Pencarian
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari nama karyawan, Emp Num, atau NIK...")
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 10px;
                background-color: #ffffff;
                font-size: 12px;
            }}
        """)
        self.search_input.textChanged.connect(self._apply_filter)
        filter_bar.addWidget(self.search_input, stretch=3)

        self.status_filter_combo = QComboBox()
        self.status_filter_combo.setFixedHeight(36)
        self.status_filter_combo.addItems([
            "Semua Status",
            "Hanya Data Valid",
            "Hanya Data Invalid",
            "Hanya Data Duplikat",
            "Hanya Jam Kosong",
            "Karyawan Tidak Ditemukan",
        ])
        self.status_filter_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 10px;
                background-color: #ffffff;
                font-size: 12px;
            }}
        """)
        self.status_filter_combo.currentIndexChanged.connect(self._apply_filter)
        filter_bar.addWidget(self.status_filter_combo, stretch=2)

        root_layout.addLayout(filter_bar)

        # 3. Tabel Pratinjau
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "No", "Emp Num.", "No. ID.", "NIK", "Nama Karyawan",
            "Tanggal", "Scan Masuk", "Scan Pulang", "Status Validasi", "Keterangan"
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
        root_layout.addWidget(self.table)

        # 4. Panel Opsi Strategi Resolusi
        strategy_frame = QFrame()
        strategy_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #F8FAFC;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
                padding: 10px 14px;
            }}
        """)
        strat_layout = QHBoxLayout(strategy_frame)
        strat_layout.setContentsMargins(10, 6, 10, 6)
        strat_layout.setSpacing(20)

        # Opsi Duplikat
        dup_box = QHBoxLayout()
        dup_lbl = QLabel("Penanganan Duplikat:")
        dup_lbl.setStyleSheet(f"font-weight: 700; font-size: 12px; color: {THEME['NAVY_DARK']};")
        dup_box.addWidget(dup_lbl)

        self.rb_dup_skip = QRadioButton("Lewati Duplikat (Rekomendasi)")
        self.rb_dup_skip.setChecked(True)
        self.rb_dup_insert = QRadioButton("Simpan Sebagai Transaksi Baru")
        dup_group = QButtonGroup(self)
        dup_group.addButton(self.rb_dup_skip)
        dup_group.addButton(self.rb_dup_insert)
        dup_box.addWidget(self.rb_dup_skip)
        dup_box.addWidget(self.rb_dup_insert)
        strat_layout.addLayout(dup_box)

        strat_layout.addSpacing(20)

        # Opsi Karyawan Tidak Ditemukan
        unmatched_box = QHBoxLayout()
        unmatched_lbl = QLabel("Jika Karyawan Tidak Ada:")
        unmatched_lbl.setStyleSheet(f"font-weight: 700; font-size: 12px; color: {THEME['NAVY_DARK']};")
        unmatched_box.addWidget(unmatched_lbl)

        self.rb_unmatched_unlinked = QRadioButton("Simpan Tanpa Relasi")
        self.rb_unmatched_unlinked.setChecked(True)
        self.rb_unmatched_skip = QRadioButton("Lewati")
        self.rb_unmatched_create = QRadioButton("Tambahkan ke Master")
        unmatched_group = QButtonGroup(self)
        unmatched_group.addButton(self.rb_unmatched_unlinked)
        unmatched_group.addButton(self.rb_unmatched_skip)
        unmatched_group.addButton(self.rb_unmatched_create)
        unmatched_box.addWidget(self.rb_unmatched_unlinked)
        unmatched_box.addWidget(self.rb_unmatched_skip)
        unmatched_box.addWidget(self.rb_unmatched_create)
        strat_layout.addLayout(unmatched_box)

        strat_layout.addStretch()
        root_layout.addWidget(strategy_frame)

        # 5. Tombol Aksi Bawah
        btn_bar = QHBoxLayout()
        self.btn_revalidate = QPushButton("🔄 Validasi Ulang")
        self.btn_revalidate.setCursor(Qt.PointingHandCursor)
        self.btn_revalidate.setFixedHeight(38)
        self.btn_revalidate.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {THEME['TEXT_MAIN']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #f8fafc; }}
        """)
        self.btn_revalidate.clicked.connect(self._on_revalidate)
        btn_bar.addWidget(self.btn_revalidate)

        btn_bar.addStretch()

        self.btn_cancel = QPushButton("Batal")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedHeight(38)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: #f1f5f9;
                color: {THEME['TEXT_MAIN']};
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 18px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #e2e8f0; }}
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btn_bar.addWidget(self.btn_cancel)

        self.btn_import = QPushButton("💾 Simpan & Import Data")
        self.btn_import.setCursor(Qt.PointingHandCursor)
        self.btn_import.setFixedHeight(38)
        # Nonaktif jika tidak ada baris valid
        is_disabled = valid_r == 0
        self.btn_import.setEnabled(not is_disabled)
        import_bg = "#94A3B8" if is_disabled else THEME['BLUE_PRIMARY']
        self.btn_import.setStyleSheet(f"""
            QPushButton {{
                background-color: {import_bg};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 24px;
                font-weight: 700;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER'] if not is_disabled else import_bg};
            }}
        """)
        self.btn_import.clicked.connect(self._on_confirm_import)
        btn_bar.addWidget(self.btn_import)

        root_layout.addLayout(btn_bar)

        # Muat isi data tabel
        self._populate_table()

    def _populate_table(self):
        """Mengisi baris tabel pratinjau."""
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.filtered_rows))

        for row_idx, r in enumerate(self.filtered_rows):
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
            item_tgl = QTableWidgetItem(r.get("tanggal_display") or "-")
            item_tgl.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 5, item_tgl)

            # Scan Masuk
            item_in = QTableWidgetItem(r.get("scan_masuk_display") or "-")
            item_in.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 6, item_in)

            # Scan Pulang
            item_out = QTableWidgetItem(r.get("scan_pulang_display") or "-")
            item_out.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 7, item_out)

            # Status Validasi
            status_str = r.get("status", "VALID")
            item_status = QTableWidgetItem(status_str)
            item_status.setTextAlignment(Qt.AlignCenter)
            if "INVALID" in status_str:
                item_status.setForeground(Qt.red)
            elif "DUPLIKAT" in status_str:
                item_status.setForeground(Qt.darkYellow)
            elif "TIDAK DITEMUKAN" in status_str:
                item_status.setForeground(Qt.darkMagenta)
            else:
                item_status.setForeground(Qt.darkGreen)
            self.table.setItem(row_idx, 8, item_status)

            # Keterangan
            self.table.setItem(row_idx, 9, QTableWidgetItem(r.get("keterangan") or "-"))

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(4, 200)  # Kolom nama
        self.table.setColumnWidth(9, 250)  # Kolom keterangan

    def _apply_filter(self):
        """Memfilter baris yang ditampilkan berdasarkan pencarian dan status."""
        query = self.search_input.text().strip().lower()
        status_mode = self.status_filter_combo.currentText()

        results = []
        for r in self.rows:
            # Filter Kata Kunci
            match_search = True
            if query:
                searchable = f"{r.get('nama', '')} {r.get('emp_num', '')} {r.get('no_id', '')} {r.get('nik', '')}".lower()
                match_search = query in searchable

            # Filter Status
            match_status = True
            st = r.get("status", "")
            if status_mode == "Hanya Data Valid":
                match_status = r.get("is_valid", False) and not (r.get("is_duplicate_in_file") or r.get("is_duplicate_in_db"))
            elif status_mode == "Hanya Data Invalid":
                match_status = not r.get("is_valid", False)
            elif status_mode == "Hanya Data Duplikat":
                match_status = r.get("is_duplicate_in_file") or r.get("is_duplicate_in_db")
            elif status_mode == "Hanya Jam Kosong":
                match_status = r.get("has_empty_jam", False)
            elif status_mode == "Karyawan Tidak Ditemukan":
                match_status = r.get("employee_id") is None

            if match_search and match_status:
                results.append(r)

        self.filtered_rows = results
        self._populate_table()

    def _on_revalidate(self):
        self.revalidate_requested.emit()
        self.accept()

    def _on_confirm_import(self):
        # Tentukan opsi resolusi yang dipilih pengguna
        self.duplicate_strategy = "SKIP" if self.rb_dup_skip.isChecked() else "INSERT"

        if self.rb_unmatched_skip.isChecked():
            self.unmatched_strategy = "SKIP"
        elif self.rb_unmatched_create.isChecked():
            self.unmatched_strategy = "CREATE"
        else:
            self.unmatched_strategy = "UNLINKED"

        self.is_confirmed = True
        self.accept()
