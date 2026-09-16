"""
Dialog Import Master Karyawan dari Berkas Excel (.xlsx/.xls) dan CSV untuk SIAP (Tahap 2).
Menyediakan fitur pemilihan berkas, analisis pemetaan kolom cerdas, tabel preview data,
deteksi duplikasi, pemilihan strategi duplikasi (Lewati/Perbarui), dan eksekusi import.
"""
import os
from typing import Optional, Dict, Any, List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QRadioButton,
    QButtonGroup,
    QFrame,
    QMessageBox,
    QProgressBar,
)
from config.settings import THEME
from services.employee_import_service import EmployeeImportService


class EmployeeImportDialog(QDialog):
    """Dialog interaktif untuk import data karyawan dari file Excel."""

    def __init__(self, parent=None, user_id: Optional[int] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.selected_file_path: Optional[str] = None
        self.preview_data: Optional[Dict[str, Any]] = None

        self.setWindowTitle("Import Data Karyawan dari Excel / CSV")
        self.resize(900, 620)
        self.setMinimumSize(800, 500)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 1. Header Dialog
        header_layout = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(2)

        title_lbl = QLabel("Import Data Karyawan dari File Excel / CSV")
        title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {THEME['NAVY_PRIMARY']};")
        header_text.addWidget(title_lbl)

        desc_lbl = QLabel("Sistem akan mencocokkan kolom secara cerdas (Nama, No. ID/PIN, No. Pegawai, NIK, Unit, Jabatan).")
        desc_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
        header_text.addWidget(desc_lbl)
        header_layout.addLayout(header_text)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 2. File Selection Bar
        file_box = QFrame()
        file_box.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px dashed #cbd5e1;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        file_layout = QHBoxLayout(file_box)
        file_layout.setContentsMargins(12, 8, 12, 8)
        file_layout.setSpacing(10)

        self.lbl_file_status = QLabel("Belum ada berkas yang dipilih. Klik 'Pilih Berkas Excel...' untuk memulai.")
        self.lbl_file_status.setStyleSheet("font-size: 12px; color: #475569; font-weight: 500;")
        file_layout.addWidget(self.lbl_file_status, 1)

        self.btn_select_file = QPushButton("📁  Pilih Berkas Excel / CSV...")
        self.btn_select_file.setFixedHeight(34)
        self.btn_select_file.setCursor(Qt.PointingHandCursor)
        self.btn_select_file.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                font-size: 11px;
                font-weight: 600;
                border-radius: 6px;
                padding: 0 16px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        self.btn_select_file.clicked.connect(self._on_select_file_clicked)
        file_layout.addWidget(self.btn_select_file)

        layout.addWidget(file_box)

        # 3. Metrics Summary Banner
        self.metrics_container = QFrame()
        self.metrics_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 14px;
            }
        """)
        metrics_layout = QHBoxLayout(self.metrics_container)
        metrics_layout.setContentsMargins(10, 6, 10, 6)

        self.lbl_stat_total = QLabel("Total: 0 Baris")
        self.lbl_stat_total.setStyleSheet("font-size: 12px; font-weight: 700; color: #1e293b;")

        self.lbl_stat_valid = QLabel("✓ Valid: 0")
        self.lbl_stat_valid.setStyleSheet("font-size: 12px; font-weight: 700; color: #16a34a;")

        self.lbl_stat_dup = QLabel("⚠ Duplikat: 0")
        self.lbl_stat_dup.setStyleSheet("font-size: 12px; font-weight: 700; color: #d97706;")

        self.lbl_stat_invalid = QLabel("✕ Tidak Valid: 0")
        self.lbl_stat_invalid.setStyleSheet("font-size: 12px; font-weight: 700; color: #dc2626;")

        metrics_layout.addWidget(self.lbl_stat_total)
        metrics_layout.addSpacing(16)
        metrics_layout.addWidget(self.lbl_stat_valid)
        metrics_layout.addSpacing(16)
        metrics_layout.addWidget(self.lbl_stat_dup)
        metrics_layout.addSpacing(16)
        metrics_layout.addWidget(self.lbl_stat_invalid)
        metrics_layout.addStretch()

        self.metrics_container.setVisible(False)
        layout.addWidget(self.metrics_container)

        # 4. Preview Table
        preview_header = QLabel("Pratinjau Data (Hasil Pemeriksaan Baris):")
        preview_header.setStyleSheet("font-size: 12px; font-weight: 600; color: #334155;")
        layout.addWidget(preview_header)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Baris", "Status", "Nama Karyawan", "No. ID / PIN", "No. Pegawai", "NIK", "Unit / Bagian", "Keterangan / Error"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 11px;
                gridline-color: #f1f5f9;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #475569;
                font-weight: 600;
                font-size: 11px;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #cbd5e1;
            }
        """)
        layout.addWidget(self.table, 1)

        # 5. Duplicate Handling Strategy Options
        options_box = QFrame()
        options_box.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")
        options_layout = QHBoxLayout(options_box)
        options_layout.setContentsMargins(10, 4, 10, 4)

        opt_title = QLabel("Penanganan Data Duplikat:")
        opt_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #334155;")
        options_layout.addWidget(opt_title)

        self.btn_group_dup = QButtonGroup(self)
        self.rad_skip = QRadioButton("Lewati (Abaikan data duplikat)")
        self.rad_skip.setChecked(True)
        self.rad_skip.setStyleSheet("font-size: 11px; color: #475569;")
        self.btn_group_dup.addButton(self.rad_skip, 1)
        options_layout.addWidget(self.rad_skip)

        self.rad_update = QRadioButton("Perbarui (Timpa data karyawan lama)")
        self.rad_update.setStyleSheet("font-size: 11px; color: #475569;")
        self.btn_group_dup.addButton(self.rad_update, 2)
        options_layout.addWidget(self.rad_update)

        options_layout.addStretch()
        layout.addWidget(options_box)

        # 6. Action Buttons Footer
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)

        self.btn_cancel = QPushButton("Batal")
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_cancel)

        footer_layout.addStretch()

        self.btn_import = QPushButton("✓  Mulai Proses Import")
        self.btn_import.setFixedHeight(36)
        self.btn_import.setEnabled(False)
        self.btn_import.setCursor(Qt.PointingHandCursor)
        self.btn_import.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
            QPushButton:disabled {{
                background-color: #94a3b8;
                color: #e2e8f0;
            }}
        """)
        self.btn_import.clicked.connect(self._on_execute_import_clicked)
        footer_layout.addWidget(self.btn_import)

        layout.addLayout(footer_layout)

    def _on_select_file_clicked(self):
        """Membuka dialog file explorer untuk memilih berkas Excel atau CSV."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih Berkas Data Karyawan",
            "",
            "Berkas Data (*.xlsx *.xls *.csv);;Excel (*.xlsx *.xls);;CSV (*.csv)",
        )
        if not file_path:
            return

        self.selected_file_path = file_path
        self.lbl_file_status.setText(f"📁 {os.path.basename(file_path)} ({os.path.getsize(file_path) / 1024:.1f} KB)")

        # Jalankan preview
        result = EmployeeImportService.preview_import(file_path)
        if not result.get("success"):
            QMessageBox.critical(self, "Gagal Membaca File", result.get("error", "Terjadi kesalahan membaca file."))
            self.btn_import.setEnabled(False)
            self.metrics_container.setVisible(False)
            return

        self.preview_data = result
        self._populate_preview_table(result)
        self.btn_import.setEnabled(True)

    def _populate_preview_table(self, data: Dict[str, Any]):
        """Mengisi data hasil pratinjau ke tabel UI."""
        items = data.get("items", [])
        self.table.setRowCount(len(items))

        # Update Banner
        self.lbl_stat_total.setText(f"Total: {data.get('total_rows', 0)} Baris")
        self.lbl_stat_valid.setText(f"✓ Valid: {data.get('valid_rows', 0)}")
        self.lbl_stat_dup.setText(f"⚠ Duplikat: {data.get('duplicate_rows', 0)}")
        self.lbl_stat_invalid.setText(f"✕ Tidak Valid: {data.get('invalid_rows', 0)}")
        self.metrics_container.setVisible(True)

        for row_idx, item in enumerate(items):
            # 1. Baris
            item_row = QTableWidgetItem(str(item["row_number"]))
            item_row.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 0, item_row)

            # 2. Status Badge
            status_str = item["import_status"]
            item_status = QTableWidgetItem(status_str)
            item_status.setTextAlignment(Qt.AlignCenter)
            if status_str == "VALID":
                item_status.setForeground(Qt.darkGreen)
            elif status_str == "DUPLIKAT":
                item_status.setForeground(Qt.darkYellow)
            else:
                item_status.setForeground(Qt.red)
            self.table.setItem(row_idx, 1, item_status)

            # 3. Nama
            self.table.setItem(row_idx, 2, QTableWidgetItem(item.get("nama") or "-"))

            # 4. No ID
            item_no_id = QTableWidgetItem(item.get("no_id") or "-")
            item_no_id.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 3, item_no_id)

            # 5. No Pegawai
            item_emp_num = QTableWidgetItem(item.get("emp_num") or "-")
            item_emp_num.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 4, item_emp_num)

            # 6. NIK
            item_nik = QTableWidgetItem(item.get("nik") or "-")
            item_nik.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 5, item_nik)

            # 7. Unit
            self.table.setItem(row_idx, 6, QTableWidgetItem(item.get("unit") or "-"))

            # 8. Keterangan / Error
            detail_msg = item.get("errors") or item.get("duplicate_info") or "Siap diimport"
            item_desc = QTableWidgetItem(detail_msg)
            self.table.setItem(row_idx, 7, item_desc)

    def _on_execute_import_clicked(self):
        """Mengeksekusi import data karyawan setelah dikonfirmasi pengguna."""
        if not self.selected_file_path or not self.preview_data:
            return

        duplicate_mode = "SKIP" if self.rad_skip.isChecked() else "UPDATE"

        confirm = QMessageBox.question(
            self,
            "Konfirmasi Import Karyawan",
            (
                f"Apakah Anda yakin ingin memproses import dari berkas:\n'{os.path.basename(self.selected_file_path)}'?\n\n"
                f"Mode Duplikasi: {'Lewati Baris Duplikat' if duplicate_mode == 'SKIP' else 'Perbarui Data Karyawan Lama'}\n"
                f"Total Baris: {self.preview_data.get('total_rows', 0)}"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if confirm != QMessageBox.Yes:
            return

        # Eksekusi import
        result = EmployeeImportService.execute_import(
            file_path=self.selected_file_path,
            duplicate_mode=duplicate_mode,
            user_id=self.user_id,
        )

        if result.get("success"):
            QMessageBox.information(self, "Import Berhasil", result.get("message", "Data karyawan berhasil diimport."))
            self.accept()
        else:
            QMessageBox.critical(self, "Import Gagal", result.get("error", "Terjadi kegagalan saat import data."))
