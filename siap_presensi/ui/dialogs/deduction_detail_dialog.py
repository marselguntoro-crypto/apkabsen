"""
Dialog Rincian Perhitungan Potongan Absensi Harian (Tahap 5).
SIAP - Sistem Informasi Administrasi Presensi.

Menampilkan perincian transparan bagaimana angka potongan dihitung:
- Identitas Karyawan (Nama, NIK, Unit)
- Tanggal & Hari
- Jam Jadwal vs Jam Realisasi (Masuk & Pulang)
- Menit Keterlambatan beserta acuan tarif
- Menit Pulang Cepat beserta acuan tarif
- Status Absen Masuk & Pulang (scan tidak ada)
- Total Potongan Akhir
"""
from typing import Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
)
from config.settings import THEME


class DeductionDetailDialog(QDialog):
    """Dialog popup untuk melihat perincian langkah demi langkah perhitungan potongan harian."""

    def __init__(self, detail_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.data = detail_data
        self.setWindowTitle("Detail Perhitungan Potongan Absensi Harian")
        self.setFixedSize(580, 520)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header Title
        head_layout = QVBoxLayout()
        head_layout.setSpacing(2)
        title = QLabel("Rincian Logika & Komponen Potongan")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {THEME['NAVY_DARK']};")
        sub = QLabel(f"Data absensi harian {self.data.get('nama', '-')} pada tanggal {self.data.get('tanggal', '-')}")
        sub.setStyleSheet(f"font-size: 12px; color: {THEME['TEXT_MUTED']};")
        head_layout.addWidget(title)
        head_layout.addWidget(sub)
        layout.addLayout(head_layout)

        # Card Informasi Karyawan & Jadwal
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }}
        """)
        info_layout = QGridLayout(info_frame)
        info_layout.setContentsMargins(16, 12, 16, 12)
        info_layout.setSpacing(8)

        info_layout.addWidget(QLabel("<b>Nama Karyawan:</b>"), 0, 0)
        info_layout.addWidget(QLabel(str(self.data.get("nama", "-"))), 0, 1)

        info_layout.addWidget(QLabel("<b>Unit Kerja:</b>"), 0, 2)
        info_layout.addWidget(QLabel(str(self.data.get("unit", "-"))), 0, 3)

        info_layout.addWidget(QLabel("<b>Hari / Tanggal:</b>"), 1, 0)
        info_layout.addWidget(QLabel(f"{self.data.get('hari', '-')}, {self.data.get('tanggal', '-')}"), 1, 1)

        info_layout.addWidget(QLabel("<b>Status Kehadiran:</b>"), 1, 2)
        status_lbl = QLabel(str(self.data.get("status_kehadiran", "-")))
        status_lbl.setStyleSheet("font-weight: 600; color: #1e3a8a;")
        info_layout.addWidget(status_lbl, 1, 3)

        info_layout.addWidget(QLabel("<b>Jam Scan Masuk:</b>"), 2, 0)
        info_layout.addWidget(QLabel(str(self.data.get("jam_masuk", "-"))), 2, 1)

        info_layout.addWidget(QLabel("<b>Jam Scan Pulang:</b>"), 2, 2)
        info_layout.addWidget(QLabel(str(self.data.get("jam_pulang", "-"))), 2, 3)

        layout.addWidget(info_frame)

        # Card Rincian Komponen Potongan
        comp_frame = QFrame()
        comp_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }}
        """)
        comp_layout = QGridLayout(comp_frame)
        comp_layout.setContentsMargins(16, 14, 16, 14)
        comp_layout.setSpacing(10)

        # Header Komponen
        comp_layout.addWidget(QLabel("<b>Komponen Pelanggaran</b>"), 0, 0)
        comp_layout.addWidget(QLabel("<b>Keterangan / Durasi</b>"), 0, 1)
        lbl_nom = QLabel("<b>Nominal</b>")
        lbl_nom.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        comp_layout.addWidget(lbl_nom, 0, 2)

        # 1. Keterlambatan
        late_min = self.data.get("menit_terlambat", 0)
        late_nom = self.data.get("potongan_terlambat", 0)
        comp_layout.addWidget(QLabel("Keterlambatan:"), 1, 0)
        late_desc = f"{late_min} menit" if late_min > 0 else "Tepat waktu / tidak ada scan"
        if late_min > 60:
            late_desc += " (>60 mnt -> Tarif Rp10.000)"
        elif late_min > 0:
            late_desc += " (<=60 mnt -> Tarif Rp7.500)"
        comp_layout.addWidget(QLabel(late_desc), 1, 1)
        lbl_val1 = QLabel(f"Rp{late_nom:,}")
        lbl_val1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        comp_layout.addWidget(lbl_val1, 1, 2)

        # 2. Pulang Cepat
        early_min = self.data.get("menit_pulang_cepat", 0)
        early_nom = self.data.get("potongan_pulang_cepat", 0)
        comp_layout.addWidget(QLabel("Pulang Cepat:"), 2, 0)
        early_desc = f"{early_min} menit lebih awal" if early_min > 0 else "Sesuai jadwal"
        comp_layout.addWidget(QLabel(early_desc), 2, 1)
        lbl_val2 = QLabel(f"Rp{early_nom:,}")
        lbl_val2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        comp_layout.addWidget(lbl_val2, 2, 2)

        # 3. Tidak Absen Masuk
        miss_in_nom = self.data.get("tidak_absen_masuk", 0)
        comp_layout.addWidget(QLabel("Tidak Absen Masuk:"), 3, 0)
        miss_in_desc = "Scan masuk tidak ditemukan" if miss_in_nom > 0 else "Ada scan masuk"
        comp_layout.addWidget(QLabel(miss_in_desc), 3, 1)
        lbl_val3 = QLabel(f"Rp{miss_in_nom:,}")
        lbl_val3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        comp_layout.addWidget(lbl_val3, 3, 2)

        # 4. Tidak Absen Pulang
        miss_out_nom = self.data.get("tidak_absen_pulang", 0)
        comp_layout.addWidget(QLabel("Tidak Absen Pulang:"), 4, 0)
        miss_out_desc = "Scan pulang tidak ditemukan" if miss_out_nom > 0 else "Ada scan pulang"
        comp_layout.addWidget(QLabel(miss_out_desc), 4, 1)
        lbl_val4 = QLabel(f"Rp{miss_out_nom:,}")
        lbl_val4.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        comp_layout.addWidget(lbl_val4, 4, 2)

        # Garis Pembatas
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #0f172a; height: 1px;")
        comp_layout.addWidget(sep, 5, 0, 1, 3)

        # Total
        lbl_tot_text = QLabel("<b>TOTAL POTONGAN HARI INI:</b>")
        lbl_tot_text.setStyleSheet("font-size: 13px; color: #0f172a;")
        comp_layout.addWidget(lbl_tot_text, 6, 0, 1, 2)

        total_nom = self.data.get("total_potongan", 0)
        lbl_tot_val = QLabel(f"<b>Rp{total_nom:,}</b>")
        lbl_tot_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_tot_val.setStyleSheet("font-size: 15px; font-weight: 800; color: #b91c1c;")
        comp_layout.addWidget(lbl_tot_val, 6, 2)

        layout.addWidget(comp_frame)

        # Catatan audit / notes
        notes_text = self.data.get("notes") or "Perhitungan selesai tanpa konflik."
        notes_box = QLabel(f"<b>Keterangan Sistem:</b> {notes_text}")
        notes_box.setWordWrap(True)
        notes_box.setStyleSheet("font-size: 11px; color: #475569; background-color: #f1f5f9; padding: 8px; border-radius: 6px;")
        layout.addWidget(notes_box)

        # Tombol Tutup
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        close_btn = QPushButton("Tutup")
        close_btn.setFixedWidth(100)
        close_btn.setFixedHeight(34)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['BLUE_PRIMARY']};
                color: #ffffff;
                font-weight: 600;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME['BLUE_HOVER']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_bar.addWidget(close_btn)
        layout.addLayout(btn_bar)
