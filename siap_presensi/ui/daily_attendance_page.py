"""
Halaman Absensi Harian dan Ketercukupan Scan (DailyAttendancePage) untuk SIAP.
Menampilkan data hasil pemaduan Master Karyawan x Kalender Kerja x Transaksi Mentah:
- Menampilkan status: HADIR_LENGKAP, HANYA_ABSEN_MASUK, HANYA_ABSEN_PULANG, TIDAK_ABSEN, DATA_BERMASALAH
- Menampilkan deteksi anomali scan tidak lengkap, multiple scan (earliest in / latest out)
- Filter Periode, Status, Unit, Pencarian Kata Kunci, Paginasi, dan Export Excel.
"""
from typing import Optional, Dict, Any, List
from datetime import date, datetime
import calendar as py_calendar

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
)

from config.settings import THEME
from database.models import User, AttendanceStatus, CheckScanStatus
from database.connection import get_db_session
from database.models import Employee
from services.attendance_daily_service import AttendanceDailyService
from ui.dialogs.generate_daily_dialog import GenerateDailyAttendanceDialog

MONTH_NAMES_ID = [
    (1, "Januari"),
    (2, "Februari"),
    (3, "Maret"),
    (4, "April"),
    (5, "Mei"),
    (6, "Juni"),
    (7, "Juli"),
    (8, "Agustus"),
    (9, "September"),
    (10, "Oktober"),
    (11, "November"),
    (12, "Desember"),
]


class DailyAttendancePage(QWidget):
    """Halaman Pengelolaan Absensi Harian Karyawan."""

    def __init__(self, parent=None, user: Optional[User] = None):
        super().__init__(parent)
        self.user = user
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.current_page = 1
        self.page_size = 50
        self.total_pages = 1
        self.units_list = []

        self._load_units()
        self._init_ui()
        self.refresh_data()

    def _load_units(self):
        """Memuat daftar unit unik dari tabel karyawan."""
        try:
            with get_db_session() as session:
                units = session.query(Employee.unit).distinct().all()
                self.units_list = sorted([u[0] for u in units if u[0] and u[0].strip()])
        except Exception:
            self.units_list = []

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # 1. Header Bar
        h_box = QHBoxLayout()
        t_box = QVBoxLayout()
        t_box.setSpacing(2)

        t_lbl = QLabel("Absensi Harian & Pembentukan Kehadiran")
        t_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {THEME['NAVY_DARK']};")
        t_box.addWidget(t_lbl)

        sub_lbl = QLabel("Hasil integrasi Master Karyawan Aktif x Kalender Kerja x Data Transaksi Mentah Absensi.")
        sub_lbl.setStyleSheet(f"font-size: 13px; color: {THEME['TEXT_MUTED']};")
        t_box.addWidget(sub_lbl)
        h_box.addLayout(t_box)

        h_box.addStretch()

        # Tombol Ekspor
        export_btn = QPushButton("  📊  Export Excel")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f8fafc;
                color: #334155;
                border: 1px solid {THEME['BORDER']};
                padding: 9px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #f1f5f9;
            }}
        """)
        export_btn.clicked.connect(self._export_to_excel)
        h_box.addWidget(export_btn)

        # Tombol Proses Pembentukan Absensi
        proc_btn = QPushButton("  ⚡  Bentuk Absensi Harian")
        proc_btn.setCursor(Qt.PointingHandCursor)
        proc_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: white;
                border: none;
                padding: 9px 18px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        proc_btn.clicked.connect(self._open_generate_dialog)
        h_box.addWidget(proc_btn)

        layout.addLayout(h_box)

        # 2. KPI Summary Bar
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(10)

        self.card_total = self._create_kpi_card("Total Catatan", "0", "Record Terbentuk", "#0f172a")
        self.card_hadir = self._create_kpi_card("Hadir Lengkap", "0", "Scan In & Out Lengkap", "#16a34a")
        self.card_masuk = self._create_kpi_card("Hanya Masuk", "0", "Tanpa Scan Pulang", "#d97706")
        self.card_pulang = self._create_kpi_card("Hanya Pulang", "0", "Tanpa Scan Masuk", "#b45309")
        self.card_tidak_absen = self._create_kpi_card("Tidak Absen", "0", "Tanpa Catatan Transaksi", THEME["DANGER"])
        self.card_conflict = self._create_kpi_card("Anomali / Multi", "0", "Multiple Scan / Konflik", "#7e22ce")

        self.kpi_layout.addWidget(self.card_total)
        self.kpi_layout.addWidget(self.card_hadir)
        self.kpi_layout.addWidget(self.card_masuk)
        self.kpi_layout.addWidget(self.card_pulang)
        self.kpi_layout.addWidget(self.card_tidak_absen)
        self.kpi_layout.addWidget(self.card_conflict)

        layout.addLayout(self.kpi_layout)

        # 3. Filter & Pencarian Bar
        filter_card = QFrame()
        filter_card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
            }}
        """)
        f_layout = QHBoxLayout(filter_card)
        f_layout.setContentsMargins(16, 12, 16, 12)
        f_layout.setSpacing(12)

        # Bulan
        f_layout.addWidget(QLabel("Periode:"))
        self.month_combo = QComboBox()
        self.month_combo.setFixedWidth(120)
        for m_num, m_name in MONTH_NAMES_ID:
            self.month_combo.addItem(m_name, m_num)
        self.month_combo.setCurrentIndex(self.current_month - 1)
        self.month_combo.currentIndexChanged.connect(self._on_filter_changed)
        f_layout.addWidget(self.month_combo)

        # Tahun
        self.year_combo = QComboBox()
        self.year_combo.setFixedWidth(90)
        for y in range(2024, 2031):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(self.current_year))
        self.year_combo.currentIndexChanged.connect(self._on_filter_changed)
        f_layout.addWidget(self.year_combo)

        # Status Filter
        f_layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.setFixedWidth(160)
        self.status_combo.addItem("Semua Status", "ALL")
        self.status_combo.addItem("Hadir Lengkap", "HADIR_LENGKAP")
        self.status_combo.addItem("Hanya Absen Masuk", "HANYA_ABSEN_MASUK")
        self.status_combo.addItem("Hanya Absen Pulang", "HANYA_ABSEN_PULANG")
        self.status_combo.addItem("Tidak Absen", "TIDAK_ABSEN")
        self.status_combo.addItem("Data Bermasalah", "DATA_BERMASALAH")
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)
        f_layout.addWidget(self.status_combo)

        # Unit Filter
        f_layout.addWidget(QLabel("Unit:"))
        self.unit_combo = QComboBox()
        self.unit_combo.setFixedWidth(140)
        self.unit_combo.addItem("Semua Unit", "ALL")
        for u in self.units_list:
            self.unit_combo.addItem(u, u)
        self.unit_combo.currentIndexChanged.connect(self._on_filter_changed)
        f_layout.addWidget(self.unit_combo)

        # Search Input
        f_layout.addWidget(QLabel("Cari:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nama, NIK, No. ID, Emp Num...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {THEME['BORDER']};
                border-radius: 6px;
                padding: 6px 10px;
                background-color: #f8fafc;
            }}
        """)
        self.search_input.textChanged.connect(self._on_filter_changed)
        f_layout.addWidget(self.search_input)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Muat Ulang")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setFixedWidth(36)
        refresh_btn.clicked.connect(self.refresh_data)
        f_layout.addWidget(refresh_btn)

        layout.addWidget(filter_card)

        # 4. Tabel Absensi Harian
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "No",
            "Tanggal",
            "Hari",
            "Emp Num",
            "No. ID",
            "Nama Karyawan",
            "Unit Kerja",
            "Jadwal In",
            "Scan In",
            "Jadwal Out",
            "Scan Out",
            "Status Kehadiran",
            "Catatan / Anomali",
        ])
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
                gridline-color: #f1f5f9;
                font-size: 13px;
            }}
            QHeaderView::section {{
                background-color: #f8fafc;
                color: #475569;
                font-weight: 700;
                padding: 9px 8px;
                border: none;
                border-bottom: 2px solid {THEME['BORDER']};
            }}
            QTableWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid #f1f5f9;
            }}
            QTableWidget::item:selected {{
                background-color: {THEME['BLUE_LIGHT']};
                color: {THEME['BLUE_PRIMARY']};
            }}
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(11, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(12, QHeaderView.Stretch)

        layout.addWidget(self.table)

        # 5. Paginasi Bar
        pag_layout = QHBoxLayout()
        self.page_info = QLabel("Halaman 1 dari 1 (Total: 0)")
        self.page_info.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        pag_layout.addWidget(self.page_info)

        pag_layout.addStretch()

        self.prev_btn = QPushButton("Sebelumnya")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(self._prev_page)
        pag_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Berikutnya")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self._next_page)
        pag_layout.addWidget(self.next_btn)

        layout.addLayout(pag_layout)

    def _create_kpi_card(self, title: str, val: str, sub: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
            }}
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(14, 10, 14, 10)
        c_layout.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {THEME['TEXT_MUTED']}; text-transform: uppercase;")
        c_layout.addWidget(t_lbl)

        v_lbl = QLabel(val)
        v_lbl.setObjectName("kpi_value")
        v_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {color};")
        c_layout.addWidget(v_lbl)

        s_lbl = QLabel(sub)
        s_lbl.setObjectName("kpi_sub")
        s_lbl.setStyleSheet(f"font-size: 10px; color: {THEME['TEXT_MUTED']};")
        c_layout.addWidget(s_lbl)

        return card

    def _update_kpi_card(self, card: QFrame, val: str, sub: str):
        v_lbl = card.findChild(QLabel, "kpi_value")
        s_lbl = card.findChild(QLabel, "kpi_sub")
        if v_lbl:
            v_lbl.setText(val)
        if s_lbl:
            s_lbl.setText(sub)

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

    def refresh_data(self):
        """Mengambil data absensi harian dan statistik dari service."""
        month = self.month_combo.currentData()
        year = int(self.year_combo.currentText())
        unit = self.unit_combo.currentData()
        status = self.status_combo.currentData()
        keyword = self.search_input.text().strip()

        # 1. Update KPI
        stats = AttendanceDailyService.get_attendance_statistics(year, month, unit)
        self._update_kpi_card(self.card_total, str(stats["total_records"]), f"{stats['unique_employees']} Karyawan Aktif")
        self._update_kpi_card(self.card_hadir, str(stats["hadir_lengkap"]), "Scan In & Out Selesai")
        self._update_kpi_card(self.card_masuk, str(stats["hanya_masuk"]), "Perlu Verifikasi")
        self._update_kpi_card(self.card_pulang, str(stats["hanya_pulang"]), "Perlu Verifikasi")
        self._update_kpi_card(self.card_tidak_absen, str(stats["tidak_absen"]), "Tanpa Presensi")
        self._update_kpi_card(self.card_conflict, str(stats["has_conflict_count"]), f"{stats['data_bermasalah']} Bermasalah")

        # 2. Update Daftar Record
        res = AttendanceDailyService.get_daily_attendance_list(
            year=year,
            month=month,
            unit=unit,
            attendance_status=status,
            keyword=keyword,
            page=self.current_page,
            page_size=self.page_size,
        )

        total_records = res.get("total_records", 0)
        self.total_pages = res.get("total_pages", 1)
        records = res.get("records", [])

        self.table.setRowCount(len(records))

        for row_idx, item in enumerate(records):
            offset = (self.current_page - 1) * self.page_size + row_idx + 1

            # No
            no_item = QTableWidgetItem(str(offset))
            no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 0, no_item)

            # Tanggal
            tgl_item = QTableWidgetItem(item.get("tanggal", ""))
            tgl_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 1, tgl_item)

            # Hari
            hari_item = QTableWidgetItem(item.get("hari", ""))
            hari_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 2, hari_item)

            # Emp Num
            self.table.setItem(row_idx, 3, QTableWidgetItem(item.get("emp_num", "-")))

            # No ID
            self.table.setItem(row_idx, 4, QTableWidgetItem(item.get("no_id", "-")))

            # Nama
            nama_item = QTableWidgetItem(item.get("nama", "-"))
            nama_item.setFont(self.font())
            self.table.setItem(row_idx, 5, nama_item)

            # Unit
            self.table.setItem(row_idx, 6, QTableWidgetItem(item.get("unit", "-")))

            # Jadwal In
            sch_in = QTableWidgetItem(item.get("scheduled_check_in", "-"))
            sch_in.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 7, sch_in)

            # Actual Scan In
            act_in = item.get("actual_check_in", "-")
            in_item = QTableWidgetItem(act_in)
            in_item.setTextAlignment(Qt.AlignCenter)
            if act_in == "-":
                in_item.setForeground(Qt.red)
            self.table.setItem(row_idx, 8, in_item)

            # Jadwal Out
            sch_out = QTableWidgetItem(item.get("scheduled_check_out", "-"))
            sch_out.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 9, sch_out)

            # Actual Scan Out
            act_out = item.get("actual_check_out", "-")
            out_item = QTableWidgetItem(act_out)
            out_item.setTextAlignment(Qt.AlignCenter)
            if act_out == "-":
                out_item.setForeground(Qt.red)
            self.table.setItem(row_idx, 10, out_item)

            # Status Kehadiran Badge
            status_val = item.get("attendance_status", "TIDAK_ABSEN")
            badge = self._create_attendance_badge(status_val)
            self.table.setCellWidget(row_idx, 11, badge)

            # Catatan / Anomali
            notes_val = item.get("notes", "")
            if item.get("has_conflict"):
                notes_val = f"⚠️ {notes_val}" if notes_val else "⚠️ Ditemukan multi-scan"
            self.table.setItem(row_idx, 12, QTableWidgetItem(notes_val or "-"))

        # Paginasi state
        self.page_info.setText(f"Halaman {self.current_page} dari {self.total_pages} (Total: {total_records} data)")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)

    def _create_attendance_badge(self, status: str) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel()
        label.setAlignment(Qt.AlignCenter)

        if status == "HADIR_LENGKAP":
            bg = "#dcfce7"
            color = "#15803d"
            text = "HADIR LENGKAP"
        elif status == "HANYA_ABSEN_MASUK":
            bg = "#fef3c7"
            color = "#b45309"
            text = "HANYA MASUK"
        elif status == "HANYA_ABSEN_PULANG":
            bg = "#ffedd5"
            color = "#c2410c"
            text = "HANYA PULANG"
        elif status == "DATA_BERMASALAH":
            bg = "#f3e8ff"
            color = "#7e22ce"
            text = "BERMASALAH"
        else:
            bg = "#fee2e2"
            color = "#b91c1c"
            text = "TIDAK ABSEN"

        label.setText(f" {text} ")
        label.setStyleSheet(f"""
            background-color: {bg};
            color: {color};
            font-size: 11px;
            font-weight: 700;
            border-radius: 4px;
            padding: 3px 8px;
        """)
        layout.addWidget(label)
        return container

    def _open_generate_dialog(self):
        """Membuka dialog untuk menjalankan pembentukan absensi harian."""
        month = self.month_combo.currentData()
        year = int(self.year_combo.currentText())
        m_name = self.month_combo.currentText()

        dlg = GenerateDailyAttendanceDialog(year, month, m_name, self.units_list, parent=self)
        if dlg.exec():
            user_name = self.user.username if self.user else "ADMIN"
            res = AttendanceDailyService.generate_daily_attendance(
                year=year,
                month=month,
                unit=dlg.selected_unit if dlg.selected_unit != "ALL" else None,
                mode=dlg.selected_mode,
                user_name=user_name,
            )

            if res.get("success"):
                QMessageBox.information(self, "Pembentukan Selesai", res.get("message", "Absensi harian berhasil dibentuk."))
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Gagal Memproses", res.get("message", "Terjadi kesalahan saat membentuk absensi harian."))

    def _export_to_excel(self):
        """Ekspor data absensi harian saat ini ke berkas Excel / CSV."""
        month = self.month_combo.currentData()
        year = int(self.year_combo.currentText())
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan Rekap Absensi Harian",
            f"Absensi_Harian_{month:02d}_{year}.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        import csv
        try:
            # Ambil seluruh data tanpa paginasi
            res = AttendanceDailyService.get_daily_attendance_list(
                year=year,
                month=month,
                page=1,
                page_size=10000,
            )
            records = res.get("records", [])

            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "No",
                    "Tanggal",
                    "Hari",
                    "Emp Num",
                    "No. ID",
                    "NIK",
                    "Nama Karyawan",
                    "Unit Kerja",
                    "Jabatan",
                    "Jadwal Masuk",
                    "Scan Masuk",
                    "Jadwal Pulang",
                    "Scan Pulang",
                    "Status Masuk",
                    "Status Pulang",
                    "Status Kehadiran",
                    "Scan Tidak Lengkap",
                    "Multi Scan / Konflik",
                    "Catatan",
                ])

                for idx, r in enumerate(records, start=1):
                    writer.writerow([
                        idx,
                        r.get("tanggal", ""),
                        r.get("hari", ""),
                        r.get("emp_num", ""),
                        r.get("no_id", ""),
                        r.get("nik", ""),
                        r.get("nama", ""),
                        r.get("unit", ""),
                        r.get("jabatan", ""),
                        r.get("scheduled_check_in", ""),
                        r.get("actual_check_in", ""),
                        r.get("scheduled_check_out", ""),
                        r.get("actual_check_out", ""),
                        r.get("check_in_status", ""),
                        r.get("check_out_status", ""),
                        r.get("attendance_status", ""),
                        "YA" if r.get("has_incomplete_scan") else "TIDAK",
                        "YA" if r.get("has_conflict") else "TIDAK",
                        r.get("notes", ""),
                    ])

            QMessageBox.information(self, "Ekspor Berhasil", f"Data absensi harian berhasil diekspor ke:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Ekspor", f"Terjadi kesalahan saat mengekspor data:\n{e}")
