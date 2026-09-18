"""
Halaman Perhitungan Potongan Absensi (DeductionCalculationPage) - PySide6.
Menyediakan antarmuka untuk:
1. Menjalankan mesin perhitungan potongan absensi bulanan.
2. Opsi Hitung Ulang (Force Recalculate) untuk rekalkulasi data.
3. Menjalankan uji validasi integritas data (anti-duplikasi, anti-double counting, validasi hari libur).
4. Pratinjau hasil perhitungan dan dialog detail item komponen potongan.
5. Tombol cepat Export Excel dan PDF.
"""
from datetime import datetime
from PySide6.QtCore import Qt, QDate
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
    QMessageBox,
    QFrame,
    QDialog,
    QScrollArea,
)

from config.settings import THEME
from database.connection import get_db_session
from database.models import Employee, AttendanceDeduction, UserRole
from services.deduction_calculation_service import DeductionCalculationService
from services.export_service import ExportService
from utils.logger import get_logger

logger = get_logger("DeductionCalculationPage")


class DeductionCalculationPage(QWidget):
    """Halaman Pengoperasian Mesin Perhitungan Potongan Absensi."""

    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self._init_ui()
        self.load_preview_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # 1. Header Halaman
        header_box = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        lbl_title = QLabel("Perhitungan Potongan Absensi")
        lbl_title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {THEME['NAVY_DARK']};")
        title_box.addWidget(lbl_title)

        lbl_desc = QLabel("Mesin hitung keterlambatan, pulang cepat, dan ketidakhadiran berstandar Rupiah integer.")
        lbl_desc.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        title_box.addWidget(lbl_desc)

        header_box.addLayout(title_box)
        header_box.addStretch()

        main_layout.addLayout(header_box)

        # 2. Bar Kontrol Filter & Aksi Eksekusi
        filter_card = QFrame()
        filter_card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(12)

        # Combo Bulan
        filter_layout.addWidget(QLabel("Bulan:"))
        self.cb_month = QComboBox()
        self.cb_month.setFixedWidth(120)
        months = [
            ("Januari", 1), ("Februari", 2), ("Maret", 3), ("April", 4),
            ("Mei", 5), ("Juni", 6), ("Juli", 7), ("Agustus", 8),
            ("September", 9), ("Oktober", 10), ("November", 11), ("Desember", 12)
        ]
        for name, val in months:
            self.cb_month.addItem(name, val)
        self.cb_month.setCurrentIndex(7)  # Default Agustus (Bulan 8)
        filter_layout.addWidget(self.cb_month)

        # Combo Tahun
        filter_layout.addWidget(QLabel("Tahun:"))
        self.cb_year = QComboBox()
        self.cb_year.setFixedWidth(90)
        for y in range(2024, 2028):
            self.cb_year.addItem(str(y), y)
        self.cb_year.setCurrentText("2026")
        filter_layout.addWidget(self.cb_year)

        # Combo Unit
        filter_layout.addWidget(QLabel("Unit:"))
        self.cb_unit = QComboBox()
        self.cb_unit.setFixedWidth(180)
        self.cb_unit.addItem("Semua Unit", "ALL")
        self._load_units()
        filter_layout.addWidget(self.cb_unit)

        filter_layout.addStretch()

        # Tombol-tombol Aksi
        self.btn_calculate = QPushButton("▶ Hitung Potongan")
        self.btn_calculate.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                font-weight: 700;
                padding: 7px 14px;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: {THEME['NAVY_DARK']}; }}
        """)
        self.btn_calculate.clicked.connect(lambda: self.run_calculation(force=False))
        filter_layout.addWidget(self.btn_calculate)

        self.btn_recalculate = QPushButton("🔄 Hitung Ulang")
        self.btn_recalculate.setStyleSheet("""
            QPushButton {{
                background-color: #f59e0b;
                color: #ffffff;
                font-weight: 700;
                padding: 7px 12px;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: #d97706; }}
        """)
        self.btn_recalculate.clicked.connect(lambda: self.run_calculation(force=True))
        filter_layout.addWidget(self.btn_recalculate)

        self.btn_validate = QPushButton("🛡️ Validasi Integritas")
        self.btn_validate.setStyleSheet("""
            QPushButton {{
                background-color: #059669;
                color: #ffffff;
                font-weight: 700;
                padding: 7px 12px;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: #047857; }}
        """)
        self.btn_validate.clicked.connect(self.run_integrity_check)
        filter_layout.addWidget(self.btn_validate)

        main_layout.addWidget(filter_card)

        # 3. Kartu Ringkasan Metrik
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(12)

        self.card_total = self._create_metric_card("Total Potongan Terhitung", "Rp 0", THEME["BLUE_PRIMARY"])
        self.card_late = self._create_metric_card("Komponen Keterlambatan", "Rp 0", "#6366f1")
        self.card_early = self._create_metric_card("Komponen Pulang Cepat", "Rp 0", "#ec4899")
        self.card_missing = self._create_metric_card("Komponen Tidak Scan", "Rp 0", "#f97316")

        metrics_layout.addWidget(self.card_total)
        metrics_layout.addWidget(self.card_late)
        metrics_layout.addWidget(self.card_early)
        metrics_layout.addWidget(self.card_missing)

        main_layout.addLayout(metrics_layout)

        # 4. Tabel Pratinjau Hasil Perhitungan
        table_container = QFrame()
        table_container.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
            }}
        """)
        t_layout = QVBoxLayout(table_container)
        t_layout.setContentsMargins(12, 12, 12, 12)
        t_layout.setSpacing(10)

        t_header = QHBoxLayout()
        t_title = QLabel("Pratinjau Hasil Perhitungan Potongan Karyawan")
        t_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        t_header.addWidget(t_title)
        t_header.addStretch()

        # Tombol Export
        btn_exp_excel = QPushButton("📊 Export Excel")
        btn_exp_excel.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                color: #059669;
                font-weight: 600;
                padding: 4px 10px;
                border-radius: 5px;
            }}
            QPushButton:hover {{ background-color: #ecfdf5; }}
        """)
        btn_exp_excel.clicked.connect(self.export_excel)
        t_header.addWidget(btn_exp_excel)

        btn_exp_pdf = QPushButton("📄 Export PDF")
        btn_exp_pdf.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                color: #dc2626;
                font-weight: 600;
                padding: 4px 10px;
                border-radius: 5px;
            }}
            QPushButton:hover {{ background-color: #fef2f2; }}
        """)
        btn_exp_pdf.clicked.connect(self.export_pdf)
        t_header.addWidget(btn_exp_pdf)

        t_layout.addLayout(t_header)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "No", "Unit", "Nama Karyawan", "Terlambat", "Pulang Cepat",
            "Tdk Absen Masuk", "Tdk Absen Pulang", "Total Potongan"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.show_employee_detail_dialog)

        t_layout.addWidget(self.table)
        main_layout.addWidget(table_container)

        # Trigger filter perubahan
        self.cb_month.currentIndexChanged.connect(self.load_preview_data)
        self.cb_year.currentIndexChanged.connect(self.load_preview_data)
        self.cb_unit.currentIndexChanged.connect(self.load_preview_data)

    def _create_metric_card(self, label: str, value: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 8px;
            }}
        """)
        l = QVBoxLayout(card)
        l.setContentsMargins(14, 10, 14, 10)
        l.setSpacing(2)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {THEME['TEXT_MUTED']};")
        val = QLabel(value)
        val.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {accent_color};")
        val.setObjectName("val")

        l.addWidget(lbl)
        l.addWidget(val)
        return card

    def _load_units(self):
        try:
            with get_db_session() as session:
                units = session.query(Employee.unit).distinct().filter(Employee.unit.isnot(None)).all()
                for u in sorted([unit[0] for unit in units if unit[0]]):
                    self.cb_unit.addItem(u, u)
        except Exception as e:
            logger.error(f"Gagal memuat daftar unit: {e}")

    def run_calculation(self, force: bool = False):
        m = self.cb_month.currentData()
        y = self.cb_year.currentData()
        u = self.cb_unit.currentData()

        op_name = self.user.username if self.user else "ADMIN"

        confirm_msg = (
            f"Jalankan perhitungan ulang seluruh potongan absensi periode {m:02d}/{y}?"
            if force else
            f"Jalankan perhitungan potongan absensi periode {m:02d}/{y}?"
        )
        if QMessageBox.question(self, "Konfirmasi Perhitungan", confirm_msg, QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        res = DeductionCalculationService.calculate_period_deductions(
            year=y,
            month=m,
            unit=u if u != "ALL" else None,
            user_name=op_name,
            force_recalculate=force,
        )

        if res["success"]:
            QMessageBox.information(self, "Perhitungan Selesai", res["message"])
            self.load_preview_data()
        else:
            QMessageBox.warning(self, "Perhatian", res["message"])

    def run_integrity_check(self):
        m = self.cb_month.currentData()
        y = self.cb_year.currentData()
        u = self.cb_unit.currentData()

        val = DeductionCalculationService.validate_deductions_integrity(year=y, month=m, unit=u if u != "ALL" else None)

        if val["is_valid"]:
            QMessageBox.information(
                self,
                "Validasi Integritas Sukses",
                (
                    f"Semua data potongan periode {m:02d}/{y} valid!\n\n"
                    f"✓ Total absensi harian: {val['daily_total']}\n"
                    f"✓ Total potongan terhitung: {val['calculated_total']}\n"
                    f"✓ Tidak ada nilai negatif.\n"
                    f"✓ Tidak ada duplikasi data.\n"
                    f"✓ Tidak ada potongan di hari libur.\n"
                    f"✓ Total tidak hadir terjaga maksimal Rp20.000 (tidak ada Alfa ganda)."
                )
            )
        else:
            issues_str = "\n- ".join(val["issues"])
            QMessageBox.warning(
                self,
                "Temuan Integritas",
                f"Ditemukan beberapa catatan pada data periode {m:02d}/{y}:\n- {issues_str}"
            )

    def load_preview_data(self):
        m = self.cb_month.currentData()
        y = self.cb_year.currentData()
        u = self.cb_unit.currentData()

        recap = DeductionCalculationService.get_monthly_deduction_recap(year=y, month=m, unit=u if u != "ALL" else None)
        rows = recap["rows"]
        gt = recap["grand_total"]

        # Update Card Metrics
        self.card_total.findChild(QLabel, "val").setText(f"Rp {gt['total_potongan']:,}".replace(",", "."))
        self.card_late.findChild(QLabel, "val").setText(f"Rp {gt['terlambat']:,}".replace(",", "."))
        self.card_early.findChild(QLabel, "val").setText(f"Rp {gt['pulang_cepat']:,}".replace(",", "."))
        tot_missing = gt["tidak_absen_masuk"] + gt["tidak_absen_pulang"]
        self.card_missing.findChild(QLabel, "val").setText(f"Rp {tot_missing:,}".replace(",", "."))

        # Update Table
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r["no"])))
            self.table.setItem(i, 1, QTableWidgetItem(r["unit"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["nama"]))
            self.table.setItem(i, 3, QTableWidgetItem(f"Rp {r['terlambat']:,}".replace(",", ".")))
            self.table.setItem(i, 4, QTableWidgetItem(f"Rp {r['pulang_cepat']:,}".replace(",", ".")))
            self.table.setItem(i, 5, QTableWidgetItem(f"Rp {r['tidak_absen_masuk']:,}".replace(",", ".")))
            self.table.setItem(i, 6, QTableWidgetItem(f"Rp {r['tidak_absen_pulang']:,}".replace(",", ".")))
            self.table.setItem(i, 7, QTableWidgetItem(f"Rp {r['jumlah_potongan_absensi']:,}".replace(",", ".")))

            # Alignments
            self.table.item(i, 0).setTextAlignment(Qt.AlignCenter)
            for col in range(3, 8):
                self.table.item(i, col).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def show_employee_detail_dialog(self):
        cur_row = self.table.currentRow()
        if cur_row < 0:
            return
        emp_name = self.table.item(cur_row, 2).text()
        tot_pot = self.table.item(cur_row, 7).text()

        QMessageBox.information(
            self,
            f"Detail Potongan: {emp_name}",
            f"Karyawan: {emp_name}\nTotal Potongan Periode: {tot_pot}\n\nUntuk rincian harian selengkapnya, silakan buka menu 'Laporan & Rekap' -> 'Data Absensi Harian'."
        )

    def export_excel(self):
        m = self.cb_month.currentData()
        y = self.cb_year.currentData()
        u = self.cb_unit.currentData()
        try:
            path = ExportService.export_rekap_potongan_excel(
                year=y,
                month=m,
                unit=u if u != "ALL" else None,
                user_name=self.user.username if self.user else "ADMIN",
            )
            QMessageBox.information(self, "Export Berhasil", f"Berkas Rekap Excel berhasil disimpan ke:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Terjadi kesalahan saat mengekspor berkas: {e}")

    def export_pdf(self):
        m = self.cb_month.currentData()
        y = self.cb_year.currentData()
        u = self.cb_unit.currentData()
        try:
            path = ExportService.export_rekap_potongan_pdf(
                year=y,
                month=m,
                unit=u if u != "ALL" else None,
                user_name=self.user.username if self.user else "ADMIN",
            )
            QMessageBox.information(self, "Export Berhasil", f"Berkas Rekap PDF resmi berhasil disimpan ke:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Terjadi kesalahan saat membuat dokumen PDF: {e}")
