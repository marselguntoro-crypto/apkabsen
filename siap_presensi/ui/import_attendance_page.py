"""
Halaman Utama Import Data Absensi Excel untuk Aplikasi Desktop SIAP.
Menyediakan antarmuka:
1. Area unggah file drag & drop atau tombol "PILIH FILE EXCEL (.xlsx)".
2. Deteksi otomatis worksheet dan pembukaan dialog pemilihan sheet jika multipage.
3. Pratinjau data dan validasi mendalam sebelum penyimpanan.
4. Indikator kemajuan proses (Progress Bar) tanpa membekukan antarmuka.
5. Dialog hasil import terintegrasi dengan opsi download Error Log.
"""
from typing import Optional, Dict, Any, List
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QFileDialog,
    QProgressBar,
    QMessageBox,
    QScrollArea,
)
from config.settings import THEME
from database.models import User
from services.attendance_import_service import AttendanceImportService
from ui.dialogs.worksheet_selection_dialog import WorksheetSelectionDialog
from ui.dialogs.excel_preview_dialog import ExcelPreviewDialog
from ui.dialogs.import_result_dialog import ImportResultDialog


class ImportWorkerThread(QThread):
    """Thread latar belakang untuk eksekusi import agar UI tetap responsif."""
    progress_updated = Signal(int, str)
    finished_with_result = Signal(dict)
    failed_with_error = Signal(str)

    def __init__(
        self,
        preview_data: Dict[str, Any],
        duplicate_strategy: str,
        unmatched_strategy: str,
        user_id: Optional[int],
        username: str,
        parent=None,
    ):
        super().__init__(parent)
        self.preview_data = preview_data
        self.duplicate_strategy = duplicate_strategy
        self.unmatched_strategy = unmatched_strategy
        self.user_id = user_id
        self.username = username

    def run(self):
        try:
            self.progress_updated.emit(25, "Memverifikasi data transaksi...")
            self.msleep(150)
            self.progress_updated.emit(50, "Menyimpan transaksi ke database...")
            result = AttendanceImportService.execute_import(
                preview_data=self.preview_data,
                duplicate_strategy=self.duplicate_strategy,
                unmatched_strategy=self.unmatched_strategy,
                user_id=self.user_id,
                username=self.username,
            )
            self.progress_updated.emit(90, "Mencatat batch log & audit trail...")
            self.msleep(100)
            self.progress_updated.emit(100, "Selesai.")
            self.finished_with_result.emit(result)
        except Exception as e:
            self.failed_with_error.emit(str(e))


class ImportAttendancePage(QWidget):
    """Halaman Pengunggahan dan Import Data Transaksi Absensi."""

    def __init__(self, parent=None, user: Optional[User] = None):
        super().__init__(parent)
        self.user = user
        self.current_filepath: Optional[str] = None
        self.current_sheet_name: Optional[str] = None
        self.preview_data: Optional[Dict[str, Any]] = None
        self.worker_thread: Optional[ImportWorkerThread] = None

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(20)

        # 1. Header Judul
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        t_lbl = QLabel("Import Data Absensi Excel")
        t_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {THEME['NAVY_DARK']};")
        title_box.addWidget(t_lbl)

        sub_lbl = QLabel(
            "Unggah berkas presensi mentah (.xlsx) dari mesin fingerprint / RFID. "
            "Sistem akan memvalidasi tanggal, jam scan, dan mencocokkan karyawan sebelum disimpan."
        )
        sub_lbl.setStyleSheet(f"font-size: 13px; color: {THEME['TEXT_MUTED']};")
        title_box.addWidget(sub_lbl)
        main_layout.addLayout(title_box)

        # 2. Area Unggah / Drag & Drop
        self.upload_card = QFrame()
        self.upload_card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 2px dashed #93C5FD;
                border-radius: 12px;
                padding: 32px;
            }}
            QFrame:hover {{
                border-color: {THEME['BLUE_PRIMARY']};
                background-color: #F8FAFC;
            }}
        """)
        upload_layout = QVBoxLayout(self.upload_card)
        upload_layout.setAlignment(Qt.AlignCenter)
        upload_layout.setSpacing(12)

        icon_lbl = QLabel("📁")
        icon_lbl.setStyleSheet("font-size: 48px;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        upload_layout.addWidget(icon_lbl)

        prompt_lbl = QLabel("Pilih Berkas Excel Absensi (.xlsx)")
        prompt_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        prompt_lbl.setAlignment(Qt.AlignCenter)
        upload_layout.addWidget(prompt_lbl)

        format_info = QLabel(
            "Format kolom standar: Emp Num. | No. ID. | NIK | Nama | Tanggal | Scan Masuk | Scan Pulang\n"
            "(Contoh file sumber: AGUSTUS 2026.xlsx)"
        )
        format_info.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        format_info.setAlignment(Qt.AlignCenter)
        upload_layout.addWidget(format_info)

        # Tombol Pilih File
        self.btn_select_file = QPushButton("  📂  PILIH FILE EXCEL  ")
        self.btn_select_file.setCursor(Qt.PointingHandCursor)
        self.btn_select_file.setFixedHeight(44)
        self.btn_select_file.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 0 28px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {THEME['BLUE_HOVER']}; }}
        """)
        self.btn_select_file.clicked.connect(self._on_select_file)
        upload_layout.addWidget(self.btn_select_file, alignment=Qt.AlignCenter)

        main_layout.addWidget(self.upload_card)

        # 3. Kartu Status File Terpilih & Quick Action
        self.file_info_card = QFrame()
        self.file_info_card.setVisible(False)
        self.file_info_card.setStyleSheet(f"""
            QFrame {{
                background-color: #F8FAFC;
                border: 1px solid {THEME['BORDER']};
                border-radius: 10px;
                padding: 16px 20px;
            }}
        """)
        fi_layout = QHBoxLayout(self.file_info_card)
        fi_layout.setSpacing(16)

        fi_icon = QLabel("📊")
        fi_icon.setStyleSheet("font-size: 28px;")
        fi_layout.addWidget(fi_icon)

        fi_text_layout = QVBoxLayout()
        fi_text_layout.setSpacing(2)
        self.lbl_selected_filename = QLabel("AGUSTUS 2026.xlsx")
        self.lbl_selected_filename.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        fi_text_layout.addWidget(self.lbl_selected_filename)

        self.lbl_file_stats = QLabel("Menyiapkan validasi...")
        self.lbl_file_stats.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        fi_text_layout.addWidget(self.lbl_file_stats)
        fi_layout.addLayout(fi_text_layout)

        fi_layout.addStretch()

        self.btn_open_preview = QPushButton("🔍 Buka Pratinjau & Import")
        self.btn_open_preview.setCursor(Qt.PointingHandCursor)
        self.btn_open_preview.setFixedHeight(38)
        self.btn_open_preview.setStyleSheet(f"""
            QPushButton {{
                background-color: #059669;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 18px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: #047857; }}
        """)
        self.btn_open_preview.clicked.connect(self._on_open_preview)
        fi_layout.addWidget(self.btn_open_preview)

        main_layout.addWidget(self.file_info_card)

        # 4. Progress Bar saat proses import berlangsung
        self.progress_container = QWidget()
        self.progress_container.setVisible(False)
        p_layout = QVBoxLayout(self.progress_container)
        p_layout.setContentsMargins(0, 8, 0, 0)
        p_layout.setSpacing(6)

        self.lbl_progress_status = QLabel("Memproses import data...")
        self.lbl_progress_status.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {THEME['BLUE_PRIMARY']};")
        p_layout.addWidget(self.lbl_progress_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #E2E8F0;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME['BLUE_PRIMARY']};
                border-radius: 4px;
            }}
        """)
        p_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.progress_container)

        # 5. Informasi Panduan & Larangan Tahap 3
        info_card = QFrame()
        info_card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {THEME['BORDER']};
                border-radius: 10px;
                padding: 20px;
            }}
        """)
        ic_layout = QVBoxLayout(info_card)
        ic_layout.setSpacing(10)

        ic_title = QLabel("ℹ️  Ketentuan & Prinsip Integritas Data Mentah (Tahap 3)")
        ic_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        ic_layout.addWidget(ic_title)

        bullet_points = [
            "1. Validasi Kolom: Kolom 'Nama' dan 'Tanggal' wajib tersedia. Kolom 'Emp Num.' atau 'No. ID.' diperlukan untuk identifikasi.",
            "2. Fleksibilitas Data: Scan Pulang dan Scan Masuk yang kosong tetap disimpan sebagai data mentah tanpa penalti alfa.",
            "3. Non-Destruktif: Data absensi lama tidak akan terhapus secara otomatis saat import baru dijalankan.",
            "4. Batas Tahap 3: Modul ini HANYA menyimpan data mentah ke tabel 'attendance_raw'. Perhitungan hari kerja, alfa, keterlambatan, dan potongan dilakukan pada Tahap 4 & 5.",
        ]
        for pt in bullet_points:
            lbl = QLabel(pt)
            lbl.setStyleSheet("font-size: 12px; color: #475569; line-height: 1.5;")
            ic_layout.addWidget(lbl)

        main_layout.addWidget(info_card)
        main_layout.addStretch()

    def _on_select_file(self):
        """Membuka dialog pemilihan file Excel .xlsx."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih Berkas Excel Absensi (.xlsx)",
            "",
            "Excel Files (*.xlsx);;All Files (*.*)",
        )
        if not filepath:
            return

        path = Path(filepath)
        if not path.suffix.lower() == ".xlsx":
            QMessageBox.critical(self, "Format Tidak Sesuai", "Hanya berkas dengan ekstensi .xlsx yang diizinkan.")
            return

        self.current_filepath = filepath
        self._process_selected_file()

    def _process_selected_file(self):
        """Mendeteksi worksheet dan menyiapkan preview data."""
        try:
            sheet_names = AttendanceImportService.get_worksheets(self.current_filepath)
            if not sheet_names:
                raise ValueError("Tidak ada worksheet yang ditemukan pada berkas Excel.")

            # Jika memiliki lebih dari 1 sheet, tampilkan dialog pemilihan
            if len(sheet_names) > 1:
                dialog = WorksheetSelectionDialog(sheet_names, self)
                if dialog.exec() == WorksheetSelectionDialog.Accepted:
                    self.current_sheet_name = dialog.selected_sheet
                else:
                    return  # Batal
            else:
                self.current_sheet_name = sheet_names[0]

            # Lakukan parsing dan validasi awal
            self.preview_data = AttendanceImportService.preview_excel_file(
                self.current_filepath,
                sheet_name=self.current_sheet_name
            )

            # Tampilkan info card
            self.lbl_selected_filename.setText(Path(self.current_filepath).name)
            t_rows = self.preview_data.get("total_rows", 0)
            v_rows = self.preview_data.get("valid_rows_count", 0)
            inv_rows = self.preview_data.get("invalid_rows_count", 0)
            dup_rows = self.preview_data.get("duplicate_rows_count", 0)

            self.lbl_file_stats.setText(
                f"Worksheet: {self.current_sheet_name} | Total: {t_rows} baris | "
                f"Valid: {v_rows} | Invalid: {inv_rows} | Duplikat: {dup_rows}"
            )
            self.file_info_card.setVisible(True)

            # Buka dialog preview secara otomatis
            self._on_open_preview()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Membaca File",
                f"Terjadi kesalahan saat membaca file Excel:\n\n{str(e)}"
            )

    def _on_open_preview(self):
        """Membuka dialog pratinjau tabel validasi Excel."""
        if not self.preview_data:
            return

        preview_dialog = ExcelPreviewDialog(self.preview_data, self)
        preview_dialog.revalidate_requested.connect(self._process_selected_file)

        if preview_dialog.exec() == ExcelPreviewDialog.Accepted and preview_dialog.is_confirmed:
            # Pengguna menekan tombol "Simpan & Import Data"
            self._execute_import_thread(
                dup_strat=preview_dialog.duplicate_strategy,
                unmatched_strat=preview_dialog.unmatched_strategy
            )

    def _execute_import_thread(self, dup_strat: str, unmatched_strat: str):
        """Menjalankan import pada QThread agar UI tetap lancar."""
        self.progress_container.setVisible(True)
        self.progress_bar.setValue(10)
        self.btn_select_file.setEnabled(False)
        self.btn_open_preview.setEnabled(False)

        user_id = self.user.id if self.user else None
        username = self.user.username if self.user else "SYSTEM"

        self.worker_thread = ImportWorkerThread(
            preview_data=self.preview_data,
            duplicate_strategy=dup_strat,
            unmatched_strategy=unmatched_strat,
            user_id=user_id,
            username=username,
            parent=self,
        )
        self.worker_thread.progress_updated.connect(self._on_progress_update)
        self.worker_thread.finished_with_result.connect(self._on_import_success)
        self.worker_thread.failed_with_error.connect(self._on_import_failed)
        self.worker_thread.start()

    def _on_progress_update(self, val: int, msg: str):
        self.progress_bar.setValue(val)
        self.lbl_progress_status.setText(msg)

    def _on_import_success(self, result: Dict[str, Any]):
        self.progress_container.setVisible(False)
        self.btn_select_file.setEnabled(True)
        self.btn_open_preview.setEnabled(True)

        # Tampilkan dialog hasil import
        res_dialog = ImportResultDialog(result, self)
        res_dialog.exec()

        # Reset info card
        self.file_info_card.setVisible(False)
        self.current_filepath = None
        self.preview_data = None

    def _on_import_failed(self, err_msg: str):
        self.progress_container.setVisible(False)
        self.btn_select_file.setEnabled(True)
        self.btn_open_preview.setEnabled(True)
        QMessageBox.critical(
            self,
            "Import Gagal",
            f"Proses import dibatalkan karena kegagalan teknis:\n\n{err_msg}"
        )
