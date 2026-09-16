"""
Dialog Ringkasan Hasil Import Absensi Excel untuk Aplikasi SIAP.
Menampilkan status batch, total baris, jumlah sukses, gagal, duplikat,
serta menyediakan tombol langsung untuk mengunduh Error Log.
"""
from typing import Dict, Any, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QFileDialog,
    QMessageBox,
)
from config.settings import THEME
from services.attendance_import_service import AttendanceImportService


class ImportResultDialog(QDialog):
    """Dialog modal yang menampilkan ringkasan pasca eksekusi import."""

    def __init__(self, result_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.result = result_data
        self.setWindowTitle("Hasil Import Data Absensi")
        self.setFixedSize(520, 480)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        status = self.result.get("status", "SUCCESS")
        is_success = status == "SUCCESS"
        is_partial = status == "PARTIAL"

        # 1. Header & Icon Status
        status_color = "#10B981" if is_success else ("#F59E0B" if is_partial else "#EF4444")
        icon_str = "✅" if is_success else ("⚠️" if is_partial else "❌")
        title_text = (
            "Import Absensi Berhasil Penuh"
            if is_success
            else ("Import Absensi Sebagian Berhasil" if is_partial else "Import Absensi Gagal")
        )

        header_box = QVBoxLayout()
        header_box.setSpacing(4)
        header_box.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel(icon_str)
        icon_lbl.setStyleSheet("font-size: 40px;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        header_box.addWidget(icon_lbl)

        title_lbl = QLabel(title_text)
        title_lbl.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {status_color};")
        title_lbl.setAlignment(Qt.AlignCenter)
        header_box.addWidget(title_lbl)

        batch_id = self.result.get("batch_id", "-")
        batch_lbl = QLabel(f"Identitas Batch: {batch_id}")
        batch_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; font-family: monospace;")
        batch_lbl.setAlignment(Qt.AlignCenter)
        header_box.addWidget(batch_lbl)

        layout.addLayout(header_box)

        # 2. Ringkasan Kartu Metrik
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #F8FAFC;
                border: 1px solid {THEME['BORDER']};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        m_layout = QVBoxLayout(metrics_frame)
        m_layout.setSpacing(8)

        def make_stat_row(label: str, val: Any, color: str = THEME["TEXT_MAIN"]):
            r = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 13px; color: {THEME['TEXT_MUTED']};")
            r.addWidget(lbl)
            r.addStretch()
            v_lbl = QLabel(str(val))
            v_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {color};")
            r.addWidget(v_lbl)
            return r

        m_layout.addLayout(make_stat_row("Nama File Sumber", self.result.get("file_name", "-")))
        m_layout.addLayout(make_stat_row("Total Baris Excel", self.result.get("total_rows", 0)))
        m_layout.addLayout(make_stat_row("Transaksi Berhasil Disimpan", self.result.get("success_rows", 0), "#10B981"))
        m_layout.addLayout(make_stat_row("Data Gagal / Invalid", self.result.get("failed_rows", 0), "#EF4444"))
        m_layout.addLayout(make_stat_row("Data Dilewati (Duplikat)", self.result.get("skipped_rows", 0), "#F59E0B"))

        layout.addWidget(metrics_frame)

        # Catatan Informasi
        info_lbl = QLabel(
            "Seluruh transaksi telah disimpan ke tabel 'attendance_raw' secara utuh. "
            "Data transaksi mentah belum mengalami perhitungan alfa maupun potongan."
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("font-size: 11px; color: #64748B; line-height: 1.4;")
        layout.addWidget(info_lbl)

        # 3. Tombol Aksi Bawah
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        error_records = self.result.get("error_records", [])
        if error_records:
            self.btn_download_error = QPushButton("📥 Unduh Error Log")
            self.btn_download_error.setCursor(Qt.PointingHandCursor)
            self.btn_download_error.setFixedHeight(38)
            self.btn_download_error.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FEF2F2;
                    color: #B91C1C;
                    border: 1px solid #F87171;
                    border-radius: 6px;
                    padding: 0 16px;
                    font-weight: 700;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background-color: #FEE2E2; }}
            """)
            self.btn_download_error.clicked.connect(self._on_download_error_log)
            btn_layout.addWidget(self.btn_download_error)

        btn_layout.addStretch()

        self.btn_close = QPushButton("Tutup & Lihat Data Raw")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFixedHeight(38)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {THEME['BLUE_HOVER']}; }}
        """)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _on_download_error_log(self):
        """Mengekspor file error log import."""
        error_records = self.result.get("error_records", [])
        if not error_records:
            QMessageBox.information(self, "Informasi", "Tidak ada catatan error untuk diunduh.")
            return

        batch_id = self.result.get("batch_id", "IMPORT")
        default_filename = f"Error_Log_{batch_id}.xlsx"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan Error Log",
            default_filename,
            "Excel Files (*.xlsx);;CSV Files (*.csv)",
        )
        if save_path:
            try:
                saved_file = AttendanceImportService.export_error_log(error_records, save_path)
                QMessageBox.information(
                    self,
                    "Berhasil",
                    f"Error log berhasil disimpan ke:\n{saved_file}",
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal mengekspor error log: {e}")
