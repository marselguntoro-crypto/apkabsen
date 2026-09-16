"""
Halaman Kalender Hari Kerja dan Jam Operasional (CalendarPage) untuk SIAP.
Mengelola status hari kerja, akhir pekan, libur nasional, cuti bersama,
serta pengaturan jam masuk dan pulang terjadwal bulanan.
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
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QMessageBox,
    QFileDialog,
)

from config.settings import THEME
from database.models import User, CalendarStatus
from services.calendar_service import CalendarService
from ui.dialogs.edit_calendar_dialog import EditCalendarDayDialog
from utils.date_parser import format_indonesian_date

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


class CalendarPage(QWidget):
    """Halaman Pengelolaan Kalender Kerja Bulanan."""

    def __init__(self, parent=None, user: Optional[User] = None):
        super().__init__(parent)
        self.user = user
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

        self._init_ui()
        self.refresh_calendar()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # 1. Header Bar
        h_box = QHBoxLayout()
        t_box = QVBoxLayout()
        t_box.setSpacing(2)

        t_lbl = QLabel("Kalender Hari Kerja & Jam Operasional")
        t_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {THEME['NAVY_DARK']};")
        t_box.addWidget(t_lbl)

        sub_lbl = QLabel("Pengaturan status hari kerja, akhir pekan, hari libur nasional, dan jam operasional terjadwal.")
        sub_lbl.setStyleSheet(f"font-size: 13px; color: {THEME['TEXT_MUTED']};")
        t_box.addWidget(sub_lbl)
        h_box.addLayout(t_box)

        h_box.addStretch()

        # Tombol Import Excel
        import_btn = QPushButton("  📥  Import Excel Kalender")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setStyleSheet(f"""
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
                border-color: #cbd5e1;
            }}
        """)
        import_btn.clicked.connect(self._import_from_excel)
        h_box.addWidget(import_btn)

        # Tombol Generate Kalender
        self.gen_btn = QPushButton("  ⚡  Generate Kalender Otomatis")
        self.gen_btn.setCursor(Qt.PointingHandCursor)
        self.gen_btn.setStyleSheet(f"""
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
        self.gen_btn.clicked.connect(self._generate_calendar)
        h_box.addWidget(self.gen_btn)

        layout.addLayout(h_box)

        # 2. Filter Bar & Periode
        filter_card = QFrame()
        filter_card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
            }}
        """)
        f_layout = QHBoxLayout(filter_card)
        f_layout.setContentsMargins(18, 14, 18, 14)
        f_layout.setSpacing(14)

        f_layout.addWidget(QLabel("Pilih Periode Kalender:"))

        # Bulan
        self.month_combo = QComboBox()
        self.month_combo.setFixedWidth(140)
        for m_num, m_name in MONTH_NAMES_ID:
            self.month_combo.addItem(m_name, m_num)
        self.month_combo.setCurrentIndex(self.current_month - 1)
        self.month_combo.currentIndexChanged.connect(self._on_period_changed)
        f_layout.addWidget(self.month_combo)

        # Tahun
        self.year_combo = QComboBox()
        self.year_combo.setFixedWidth(100)
        for y in range(2024, 2031):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(self.current_year))
        self.year_combo.currentIndexChanged.connect(self._on_period_changed)
        f_layout.addWidget(self.year_combo)

        f_layout.addStretch()

        # Tombol Refresh
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid {THEME['BORDER']};
                padding: 6px 14px;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #e2e8f0;
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_calendar)
        f_layout.addWidget(refresh_btn)

        layout.addWidget(filter_card)

        # 3. KPI Cards Summary
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(12)

        self.card_total = self._create_kpi_card("Total Hari", "0", "Hari dalam bulan", "#0f172a")
        self.card_work = self._create_kpi_card("Hari Kerja Aktual", "0", "Target: 18 Hari", THEME["BLUE_PRIMARY"])
        self.card_weekend = self._create_kpi_card("Akhir Pekan", "0", "Sabtu & Minggu", "#64748b")
        self.card_holiday = self._create_kpi_card("Libur / Cuti", "0", "Libur Nasional & Cuti", THEME["DANGER"])

        self.kpi_layout.addWidget(self.card_total)
        self.kpi_layout.addWidget(self.card_work)
        self.kpi_layout.addWidget(self.card_weekend)
        self.kpi_layout.addWidget(self.card_holiday)

        layout.addLayout(self.kpi_layout)

        # 4. Tabel Kalender
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "No",
            "Tanggal",
            "Hari",
            "Status Kalender",
            "Jam Masuk",
            "Jam Pulang",
            "Keterangan / Catatan",
            "Aksi",
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
                padding: 10px;
                border: none;
                border-bottom: 2px solid {THEME['BORDER']};
            }}
            QTableWidget::item {{
                padding: 6px 10px;
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
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

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
        c_layout.setContentsMargins(16, 12, 16, 12)
        c_layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {THEME['TEXT_MUTED']}; text-transform: uppercase;")
        c_layout.addWidget(t_lbl)

        v_lbl = QLabel(val)
        v_lbl.setObjectName("kpi_value")
        v_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color};")
        c_layout.addWidget(v_lbl)

        s_lbl = QLabel(sub)
        s_lbl.setObjectName("kpi_sub")
        s_lbl.setStyleSheet(f"font-size: 11px; color: {THEME['TEXT_MUTED']};")
        c_layout.addWidget(s_lbl)

        return card

    def _update_kpi_card(self, card: QFrame, val: str, sub: str):
        v_lbl = card.findChild(QLabel, "kpi_value")
        s_lbl = card.findChild(QLabel, "kpi_sub")
        if v_lbl:
            v_lbl.setText(val)
        if s_lbl:
            s_lbl.setText(sub)

    def _on_period_changed(self):
        self.current_month = self.month_combo.currentData()
        self.current_year = int(self.year_combo.currentText())
        self.refresh_calendar()

    def refresh_calendar(self):
        """Memuat ulang tabel dan ringkasan kalender dari database."""
        month = self.month_combo.currentData()
        year = int(self.year_combo.currentText())

        # 1. Update KPI Summary
        summary = CalendarService.get_calendar_summary(year, month)
        self._update_kpi_card(self.card_total, str(summary["total_days"]), f"Bulan {self.month_combo.currentText()}")
        diff_text = f"Selisih: {summary['difference']:+d} Hari" if summary["working_days"] > 0 else "Belum di-generate"
        self._update_kpi_card(
            self.card_work,
            f"{summary['working_days']} Hari",
            f"Target: {summary['target_days']} Hari ({diff_text})"
        )
        self._update_kpi_card(self.card_weekend, f"{summary['weekend_days']} Hari", "Sabtu & Minggu")
        self._update_kpi_card(self.card_holiday, f"{summary['holidays']} Hari", f"Khusus: {summary['special_days']} Hari")

        # 2. Update Tabel
        items = CalendarService.get_monthly_calendar(year, month)
        self.table.setRowCount(len(items))

        for row_idx, item in enumerate(items):
            # No
            no_item = QTableWidgetItem(str(row_idx + 1))
            no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 0, no_item)

            # Tanggal
            tgl_str = item.get("tanggal", "")
            tgl_item = QTableWidgetItem(tgl_str)
            tgl_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 1, tgl_item)

            # Hari
            hari_item = QTableWidgetItem(item.get("hari", ""))
            hari_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 2, hari_item)

            # Status Badge Widget
            status_val = item.get("calendar_status", "HARI_KERJA")
            status_widget = self._create_status_badge(status_val)
            self.table.setCellWidget(row_idx, 3, status_widget)

            # Jam Masuk
            in_item = QTableWidgetItem(item.get("scheduled_check_in", "-"))
            in_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 4, in_item)

            # Jam Pulang
            out_item = QTableWidgetItem(item.get("scheduled_check_out", "-"))
            out_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 5, out_item)

            # Keterangan
            desc_item = QTableWidgetItem(item.get("description", "-"))
            self.table.setItem(row_idx, 6, desc_item)

            # Aksi: Tombol Edit
            edit_btn = QPushButton("Ubah")
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #f1f5f9;
                    color: {THEME['BLUE_PRIMARY']};
                    border: 1px solid #cbd5e1;
                    padding: 4px 10px;
                    border-radius: 4px;
                    font-weight: 600;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['BLUE_LIGHT']};
                    border-color: {THEME['BLUE_PRIMARY']};
                }}
            """)
            edit_btn.clicked.connect(lambda _, d=item: self._edit_day(d))
            self.table.setCellWidget(row_idx, 7, edit_btn)

    def _create_status_badge(self, status: str) -> QWidget:
        """Membuat badge berwarna untuk status kalender."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel()
        label.setAlignment(Qt.AlignCenter)

        if status == "HARI_KERJA":
            bg = "#eff6ff"
            color = "#1d4ed8"
            text = "HARI KERJA"
        elif status == "AKHIR_PEKAN":
            bg = "#f1f5f9"
            color = "#64748b"
            text = "AKHIR PEKAN"
        elif status == "LIBUR_NASIONAL":
            bg = "#fee2e2"
            color = "#b91c1c"
            text = "LIBUR NASIONAL"
        elif status == "CUTI_BERSAMA":
            bg = "#fef3c7"
            color = "#b45309"
            text = "CUTI BERSAMA"
        elif status == "HARI_KERJA_KHUSUS":
            bg = "#f3e8ff"
            color = "#7e22ce"
            text = "KERJA KHUSUS"
        else:
            bg = "#fee2e2"
            color = "#dc2626"
            text = "LIBUR"

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

    def _generate_calendar(self):
        """Menjalankan pembentukan kalender hari kerja otomatis."""
        month = self.month_combo.currentData()
        year = int(self.year_combo.currentText())

        # Coba generate tanpa overwrite dulu
        res = CalendarService.generate_monthly_calendar(
            year=year,
            month=month,
            overwrite=False,
            created_by=self.user.username if self.user else "ADMIN",
        )

        if not res.get("success") and res.get("already_exists"):
            reply = QMessageBox.question(
                self,
                "Kalender Sudah Ada",
                f"Kalender untuk {self.month_combo.currentText()} {year} sudah terbentuk ({res.get('total_existing')} hari).\n\n"
                f"Apakah Anda ingin menimpa (overwrite) dan memperbarui kalender ke pengaturan jam operasional default?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                res = CalendarService.generate_monthly_calendar(
                    year=year,
                    month=month,
                    overwrite=True,
                    created_by=self.user.username if self.user else "ADMIN",
                )
            else:
                return

        if res.get("success"):
            QMessageBox.information(self, "Berhasil", res.get("message", "Kalender berhasil dibuat."))
            self.refresh_calendar()
        else:
            QMessageBox.critical(self, "Gagal", res.get("message", "Gagal membuat kalender."))

    def _edit_day(self, day_data: Dict[str, Any]):
        user_name = self.user.username if self.user else "ADMIN"
        dlg = EditCalendarDayDialog(day_data, user_name=user_name, parent=self)
        if dlg.exec():
            self.refresh_calendar()

    def _import_from_excel(self):
        """Import kalender dari berkas Excel."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih Berkas Excel Kalender Kerja",
            "",
            "Excel Files (*.xlsx *.xls)",
        )
        if not file_path:
            return

        user_name = self.user.username if self.user else "ADMIN"
        res = CalendarService.import_calendar_from_excel(
            file_path=file_path,
            user_name=user_name,
        )

        if res.get("success"):
            msg = (
                f"Import Kalender Berhasil!\n\n"
                f"• Total Data: {res.get('total_rows')} baris\n"
                f"• Berhasil Disimpan: {res.get('valid_count')} tanggal\n"
                f"• Tanggal Sebelumnya: {res.get('duplicate_count')}\n"
                f"• Tidak Valid: {res.get('invalid_count')}"
            )
            QMessageBox.information(self, "Import Selesai", msg)
            self.refresh_calendar()
        else:
            QMessageBox.critical(self, "Gagal Import", res.get("message", "Gagal memproses file Excel."))
