"""
Halaman Riwayat Import Absensi (Import History Page) SIAP.
Menampilkan tabel seluruh batch import absensi:
- Kolom: No, Batch ID, Nama File, Jenis Import, Periode, Total Baris, Berhasil, Gagal, Duplikat, Status, Tanggal Import, Pengguna
- Fitur: Pencarian kata kunci, filter status (Semua, SUCCESS, PARTIAL, FAILED), detail batch modal, dan tombol unduh Error Log.
"""
from typing import Optional, Dict, Any, List
import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QMessageBox,
    QFileDialog,
    QDialog,
    QTextEdit,
)
from config.settings import THEME
from database.models import User
from database.connection import get_db_session
from services.attendance_import_service import AttendanceImportService


class BatchDetailDialog(QDialog):
    """Dialog detail rincian satu batch import."""

    def __init__(self, batch_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.batch = batch_data
        self.setWindowTitle(f"Detail Batch - {batch_data.get('import_batch_id', '-')}")
        self.resize(680, 520)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel(f"Rincian Transaksi Batch: {self.batch.get('import_batch_id', '-')}")
        title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {THEME['NAVY_DARK']};")
        layout.addWidget(title)

        # Kartu info ringkas
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #F8FAFC;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setSpacing(6)

        def add_info_row(k: str, v: Any):
            r = QHBoxLayout()
            lbl = QLabel(k)
            lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B;")
            r.addWidget(lbl)
            r.addStretch()
            val = QLabel(str(v))
            val.setStyleSheet("font-size: 12px; font-weight: 700; color: #1E293B;")
            r.addWidget(val)
            cl.addLayout(r)

        add_info_row("Nama File Sumber:", self.batch.get("file_name", "-"))
        add_info_row("Status Batch:", self.batch.get("status", "-"))
        add_info_row("Total Baris Berkas:", self.batch.get("total_rows", 0))
        add_info_row("Transaksi Berhasil Disimpan:", self.batch.get("success_rows", 0))
        add_info_row("Data Gagal / Invalid:", self.batch.get("failed_rows", 0))
        add_info_row("Data Duplikat Terdeteksi:", self.batch.get("duplicate_rows", 0))
        add_info_row("Waktu Import:", self.batch.get("created_at", "-"))

        layout.addWidget(card)

        # Log Error / Catatan
        err_title = QLabel("Catatan Log Kendala & Peringatan:")
        err_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        layout.addWidget(err_title)

        self.txt_errors = QTextEdit()
        self.txt_errors.setReadOnly(True)
        self.txt_errors.setStyleSheet(f"""
            QTextEdit {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                font-size: 11px;
                font-family: monospace;
            }}
        """)

        errors_list = self.batch.get("errors_list", [])
        if errors_list:
            log_lines = []
            for item in errors_list:
                line_str = f"Baris {item.get('excel_line', '-')}: {item.get('nama', '-')} - {item.get('status', '-')}: {item.get('error', '-')}"
                log_lines.append(line_str)
            self.txt_errors.setText("\n".join(log_lines))
        else:
            self.txt_errors.setText("Tidak ada catatan error pada batch ini. Seluruh baris data valid.")

        layout.addWidget(self.txt_errors)

        # Tombol
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Tutup")
        btn_close.setFixedHeight(36)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-weight: 600;
            }}
        """)
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)


class ImportHistoryPage(QWidget):
    """Halaman tabel riwayat batch import presensi."""

    def __init__(self, parent=None, user: Optional[User] = None):
        super().__init__(parent)
        self.user = user
        self.current_page = 1
        self.page_size = 15
        self.total_pages = 1

        self._init_ui()
        self.refresh_history()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # 1. Header
        h_layout = QHBoxLayout()
        t_box = QVBoxLayout()
        t_box.setSpacing(2)

        t_lbl = QLabel("Riwayat Import Absensi")
        t_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {THEME['NAVY_DARK']};")
        t_box.addWidget(t_lbl)

        sub_lbl = QLabel("Daftar seluruh batch proses import berkas absensi mentah yang pernah dieksekusi.")
        sub_lbl.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        t_box.addWidget(sub_lbl)
        h_layout.addLayout(t_box)

        h_layout.addStretch()

        self.btn_refresh = QPushButton("🔄 Segarkan Data")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setFixedHeight(36)
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
        self.btn_refresh.clicked.connect(self.refresh_history)
        h_layout.addWidget(self.btn_refresh)

        layout.addLayout(h_layout)

        # 2. Filter Bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari Batch ID atau nama file Excel...")
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
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_bar.addWidget(self.search_input, stretch=3)

        self.status_combo = QComboBox()
        self.status_combo.setFixedHeight(36)
        self.status_combo.addItems(["SEMUA", "SUCCESS", "PARTIAL", "FAILED"])
        self.status_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 0 10px;
                background-color: #ffffff;
                font-size: 12px;
            }}
        """)
        self.status_combo.currentIndexChanged.connect(self.refresh_history)
        filter_bar.addWidget(self.status_combo, stretch=2)

        layout.addLayout(filter_bar)

        # 3. Tabel Riwayat
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "No", "Batch ID", "Nama File", "Jenis Import", "Periode",
            "Total", "Berhasil", "Gagal", "Duplikat", "Status", "Waktu Import", "Aksi"
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

        # 4. Paginasi Bawah
        nav_layout = QHBoxLayout()
        self.lbl_page_info = QLabel("Menampilkan 0 batch")
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
                padding: 0 10px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #f8fafc; }}
            QPushButton:disabled {{ color: #cbd5e1; }}
        """

    def _on_search_changed(self):
        self.current_page = 1
        self.refresh_history()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_history()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.refresh_history()

    def refresh_history(self):
        """Mengambil data riwayat batch dari database."""
        kw = self.search_input.text().strip()
        st = self.status_combo.currentText()

        try:
            with get_db_session() as db:
                items, total, total_pg = AttendanceImportService.get_import_history(
                    db=db,
                    keyword=kw,
                    status=st,
                    page=self.current_page,
                    page_size=self.page_size,
                )
                self.total_pages = total_pg
                self._populate_table(items, total)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat riwayat import: {e}")

    def _populate_table(self, items: List[Dict[str, Any]], total: int):
        self.table.setRowCount(0)
        self.table.setRowCount(len(items))

        self.lbl_page_info.setText(f"Total: {total} batch import tercatat")
        self.lbl_current_page.setText(f"{self.current_page} / {self.total_pages}")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)

        for row_idx, r in enumerate(items):
            # No
            item_no = QTableWidgetItem(str(r["no"]))
            item_no.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 0, item_no)

            # Batch ID
            item_b = QTableWidgetItem(r["import_batch_id"])
            item_b.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 1, item_b)

            # File Name
            self.table.setItem(row_idx, 2, QTableWidgetItem(r["file_name"]))

            # Import Type
            self.table.setItem(row_idx, 3, QTableWidgetItem(r["import_type"]))

            # Periode
            item_p = QTableWidgetItem(r.get("periode", "-"))
            item_p.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 4, item_p)

            # Total
            item_tot = QTableWidgetItem(str(r["total_rows"]))
            item_tot.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 5, item_tot)

            # Berhasil
            item_s = QTableWidgetItem(str(r["success_rows"]))
            item_s.setTextAlignment(Qt.AlignCenter)
            item_s.setForeground(Qt.darkGreen)
            self.table.setItem(row_idx, 6, item_s)

            # Gagal
            item_f = QTableWidgetItem(str(r["failed_rows"]))
            item_f.setTextAlignment(Qt.AlignCenter)
            if r["failed_rows"] > 0:
                item_f.setForeground(Qt.red)
            self.table.setItem(row_idx, 7, item_f)

            # Duplikat
            item_d = QTableWidgetItem(str(r["duplicate_rows"]))
            item_d.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 8, item_d)

            # Status
            st = r["status"]
            item_st = QTableWidgetItem(st)
            item_st.setTextAlignment(Qt.AlignCenter)
            if st == "SUCCESS":
                item_st.setForeground(Qt.darkGreen)
            elif st == "PARTIAL":
                item_st.setForeground(Qt.darkYellow)
            else:
                item_st.setForeground(Qt.red)
            self.table.setItem(row_idx, 9, item_st)

            # Created At
            item_dt = QTableWidgetItem(r["created_at"])
            item_dt.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 10, item_dt)

            # Aksi Tombol Rincian
            btn_detail = QPushButton("Detail")
            btn_detail.setCursor(Qt.PointingHandCursor)
            btn_detail.setFixedHeight(26)
            btn_detail.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME['BLUE_LIGHT']};
                    color: {THEME['BLUE_PRIMARY']};
                    border: 1px solid {THEME['BLUE_PRIMARY']}40;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 700;
                }}
                QPushButton:hover {{ background-color: #dbeafe; }}
            """)
            batch_id = r["import_batch_id"]
            btn_detail.clicked.connect(lambda _, b=batch_id: self._show_batch_detail(b))
            self.table.setCellWidget(row_idx, 11, btn_detail)

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(2, 180)  # Nama file
        self.table.setColumnWidth(11, 80)  # Aksi

    def _show_batch_detail(self, batch_id: str):
        """Menampilkan dialog modal rincian batch import."""
        try:
            with get_db_session() as db:
                batch_data = AttendanceImportService.get_batch_details(db, batch_id)
                if not batch_data:
                    QMessageBox.warning(self, "Tidak Ditemukan", f"Batch '{batch_id}' tidak ditemukan.")
                    return
                dialog = BatchDetailDialog(batch_data, self)
                dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal membuka rincian batch: {e}")
