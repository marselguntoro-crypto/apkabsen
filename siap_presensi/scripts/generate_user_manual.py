"""
Script Generator Buku Panduan Pengguna Resmi SIAP.
Output: PANDUAN_PENGGUNA_SIAP.pdf
Menggunakan library ReportLab dengan layout dokumen profesional:
- Cover page elegan dengan branding SIAP.
- Daftar isi dan ringkasan eksekutif.
- Panduan operasional langkah-demi-langkah seluruh modul.
- Tabel tarif perhitungan potongan dan parameter operasional.
- FAQ, penanganan kendala (troubleshooting), dan panduan instalasi.
"""
import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PDF = BASE_DIR / "PANDUAN_PENGGUNA_SIAP.pdf"


class NumberedCanvas(canvas.Canvas):
    """Canvas kustom untuk menambahkan footer nomor halaman dan running header."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Jangan gambar header/footer pada halaman cover (halaman 1)
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header
        self.drawString(2 * cm, 28.5 * cm, "SIAP - Sistem Informasi Administrasi Presensi | Panduan Pengguna v1.0.0")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(2 * cm, 28.3 * cm, 19 * cm, 28.3 * cm)

        # Running Footer
        page_text = f"Halaman {self._pageNumber} dari {page_count}"
        self.drawRightString(19 * cm, 1.2 * cm, page_text)
        self.drawString(2 * cm, 1.2 * cm, "Dokumen Resmi Tim Pengembang SIAP (2026)")
        self.line(2 * cm, 1.5 * cm, 19 * cm, 1.5 * cm)

        self.restoreState()


def build_manual_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    styles = getSampleStyleSheet()

    # Kustom Style
    navy_dark = colors.HexColor("#0f172a")
    blue_primary = colors.HexColor("#1d4ed8")
    text_muted = colors.HexColor("#475569")

    style_cover_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=30,
        leading=36,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
    )

    style_cover_sub = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=15,
        leading=22,
        textColor=colors.HexColor("#1d4ed8"),
        alignment=1,
    )

    style_h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=24,
        textColor=navy_dark,
        spaceAfter=10,
        keepWithNext=True,
    )

    style_h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=18,
        textColor=blue_primary,
        spaceBefore=8,
        spaceAfter=6,
        keepWithNext=True,
    )

    style_body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=8,
    )

    style_bullet = ParagraphStyle(
        "Bullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    style_note = ParagraphStyle(
        "Note",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0369a1"),
        spaceAfter=6,
    )

    story = []

    # =========================================================================
    # 1. HALAMAN SAMPUL (COVER)
    # =========================================================================
    story.append(Spacer(1, 3.5 * cm))

    # Badge Judul
    badge_data = [[Paragraph("<b>SISTEM INFORMASI ADMINISTRASI PRESENSI</b>", ParagraphStyle(
        "B", fontName="Helvetica-Bold", fontSize=11, textColor=colors.white, alignment=1
    ))]]
    badge_table = Table(badge_data, colWidths=[17 * cm])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), navy_dark),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 1.2 * cm))

    story.append(Paragraph("SIAP", style_cover_title))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("BUKU PANDUAN PENGGUNA & ADMINISTRATOR", style_cover_sub))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Aplikasi Desktop Manajemen Presensi & Kalkulasi Potongan Finansial", ParagraphStyle(
        "CDesc", fontName="Helvetica", fontSize=11, leading=16, textColor=text_muted, alignment=1
    )))

    story.append(Spacer(1, 4 * cm))

    # Informasi Metadata Sampul
    meta_data = [
        [Paragraph("<b>Versi Aplikasi:</b>", style_body), Paragraph("1.0.0 (Production Release)", style_body)],
        [Paragraph("<b>Target Sistem Operasi:</b>", style_body), Paragraph("Windows 10 & Windows 11 (64-bit Architecture)", style_body)],
        [Paragraph("<b>Teknologi:</b>", style_body), Paragraph("Python 3.10+, PySide6 (Qt6), SQLite (WAL Mode)", style_body)],
        [Paragraph("<b>Penyusun:</b>", style_body), Paragraph("Tim Pengembang SIAP", style_body)],
        [Paragraph("<b>Tahun Terbit:</b>", style_body), Paragraph("2026", style_body)],
    ]
    meta_table = Table(meta_data, colWidths=[5 * cm, 12 * cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(meta_table)

    story.append(PageBreak())

    # =========================================================================
    # 2. DAFTAR ISI & PENGENALAN
    # =========================================================================
    story.append(Paragraph("Daftar Isi Buku Panduan", style_h1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=blue_primary, spaceAfter=14))

    toc_items = [
        ("Bab 1: Ikhtisar & Arsitektur SIAP", "Mengenal aplikasi, penyimpanan data Windows, dan keamanan."),
        ("Bab 2: Panduan Login & Hak Akses", "Kredensial bawaan, peran Administrator vs Operator, First-Run Wizard."),
        ("Bab 3: Master Data Karyawan", "Pengelolaan pegawai, validasi PIN scan, serta import/export Excel."),
        ("Bab 4: Kalender Kerja Bulanan", "Penjadwalan hari kerja Senin-Jumat, jam kerja operasional, hari libur."),
        ("Bab 5: Import Berkas Log Mesin Absensi", "Pengunggahan Excel mentah scan mesin, validasi tanggal dan PIN."),
        ("Bab 6: Pembentukan Absensi & Hitung Potongan", "Aturan 08:15, tarif keterlambatan, zero double-counting, alur eksekusi."),
        ("Bab 7: Laporan & Ekspor Rekapitulasi", "Mencetak laporan rincian dan rekapitulasi ke format Excel dan PDF."),
        ("Bab 8: Pengaturan Sistem & Pencadangan", "Parameter dinamis, backup hot SQLite otomatis, dan pemulihan data."),
        ("Bab 9: Instalasi & Pembaruan (Inno Setup)", "Panduan setup executable di Program Files dan proteksi database."),
        ("Bab 10: FAQ & Solusi Kendala Teknis", "Daftar tanya jawab praktis dan pemecahan kendala umum di Windows."),
    ]
    for title, desc in toc_items:
        story.append(Paragraph(f"• <b>{title}</b> — {desc}", style_bullet))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Bab 1: Ikhtisar & Arsitektur Sistem", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    story.append(Paragraph(
        "<b>SIAP (Sistem Informasi Administrasi Presensi)</b> adalah aplikasi desktop berbasis Windows "
        "yang dirancang untuk mencatat, mengolah, dan mengaudit data kehadiran karyawan secara akurat, "
        "sekaligus menghitung nominal sanksi finansial (potongan) atas pelanggaran kedisiplinan kerja harian.",
        style_body
    ))

    story.append(Paragraph(
        "<b>Penyimpanan Data Pengguna Windows:</b><br/>"
        "Sesuai standar arsitektur Windows Modern, SIAP memisahkan file instalasi aplikasi (Program Files) "
        "dengan folder data kerja pengguna. Seluruh database SQLite, rekaman backup, file log rotasi, dan hasil ekspor "
        "disimpan secara terisolasi pada direktori pengguna di:",
        style_body
    ))

    path_box = [[Paragraph("<b>Lokasi Data Pengguna:</b> %LOCALAPPDATA%\\SIAP\\<br/>"
                           "├── database\\siap_presensi.db (Database utama SQLite mode WAL)<br/>"
                           "├── backups\\ (Arsip pencadangan berkala .db otomatis)<br/>"
                           "├── logs\\app.log (Catatan aktivitas bersanitasi & berotasi)<br/>"
                           "└── exports\\ (Hasil ekspor laporan Excel dan PDF)", ParagraphStyle(
        "PB", fontName="Courier", fontSize=8.5, leading=12, textColor=navy_dark
    ))]]
    ptbl = Table(path_box, colWidths=[17 * cm])
    ptbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(ptbl)
    story.append(Spacer(1, 12))

    story.append(PageBreak())

    # =========================================================================
    # 3. BAB 2 & 3: LOGIN & MASTER KARYAWAN
    # =========================================================================
    story.append(Paragraph("Bab 2: Panduan Login & Hak Akses Pengguna", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    story.append(Paragraph(
        "Aplikasi SIAP memiliki 2 (dua) tingkat peran pengguna (Role-Based Access Control):", style_body
    ))
    story.append(Paragraph("1. <b>Administrator:</b> Memiliki wewenang penuh mencakup seluruh modul operasional, Master Karyawan, Pengaturan Parameter Sistem, dan Backup/Restore database.", style_bullet))
    story.append(Paragraph("2. <b>Operator:</b> Memiliki akses operasional harian (Import Berkas, Pembentukan Absensi, Rekapitulasi Potongan, dan Ekspor Laporan) tanpa akses ke pengaturan kritis.", style_bullet))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Akun Bawaan Default Awal:</b>", style_h2))

    creds_data = [
        [Paragraph("<b>Peran (Role)</b>", style_body), Paragraph("<b>Username Default</b>", style_body), Paragraph("<b>Password Default</b>", style_body), Paragraph("<b>Keterangan</b>", style_body)],
        [Paragraph("Administrator", style_body), Paragraph("admin", style_body), Paragraph("Admin@SIAP2025", style_body), Paragraph("Akses penuh ke semua modul", style_body)],
        [Paragraph("Operator Presensi", style_body), Paragraph("operator", style_body), Paragraph("Operator@SIAP2025", style_body), Paragraph("Akses operasional presensi", style_body)],
    ]
    ctbl = Table(creds_data, colWidths=[4 * cm, 3.5 * cm, 4.5 * cm, 5 * cm])
    ctbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(ctbl)
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<i>Catatan Keamanan:</i> Saat Administrator pertama kali login menggunakan kata sandi awal pabrik, "
        "sistem akan memunculkan dialog <b>Setup Awal (First-Run Wizard)</b> yang mewajibkan/merekomendasikan "
        "penggantian kata sandi baru demi menjaga kerahasiaan institusi.",
        style_note
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Bab 3: Master Data Karyawan", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
    story.append(Paragraph(
        "Modul <b>Data Karyawan</b> digunakan untuk mendata seluruh pegawai yang wajib melakukan absensi. "
        "Kolom <b>Nomor ID / PIN Absensi</b> wajib diisi sesuai dengan nomor pendaftaran fingerprint pada mesin.",
        style_body
    ))
    story.append(Paragraph("• <b>Tambah Karyawan:</b> Klik tombol <i>Tambah Karyawan</i>, masukkan NIP/NIK, Nama Lengkap, Nomor PIN Fingerprint, Departemen, dan Jabatan.", style_bullet))
    story.append(Paragraph("• <b>Import dari Excel:</b> Unggah berkas Excel berformat .xlsx yang memuat data master seluruh pegawai secara massal.", style_bullet))
    story.append(Paragraph("• <b>Export ke Excel:</b> Unduh seluruh data master karyawan ke file Excel untuk arsip kepegawaian.", style_bullet))

    story.append(PageBreak())

    # =========================================================================
    # 4. BAB 4 & 5: KALENDER & IMPORT ABSENSI MENTAH
    # =========================================================================
    story.append(Paragraph("Bab 4: Kalender Kerja & Jadwal Operasional", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
    story.append(Paragraph(
        "Sebelum membentuk data absensi bulanan, Anda wajib memastikan <b>Kalender Kerja</b> pada bulan yang bersangkutan telah di-generate. "
        "SIAP menerapkan standar jadwal jam kerja institusi sebagai berikut:",
        style_body
    ))

    cal_data = [
        [Paragraph("<b>Hari Kerja</b>", style_body), Paragraph("<b>Jam Masuk</b>", style_body), Paragraph("<b>Jam Pulang</b>", style_body), Paragraph("<b>Toleransi Bebas Potongan</b>", style_body)],
        [Paragraph("Senin s/d Kamis", style_body), Paragraph("08:15 WIB", style_body), Paragraph("16:30 WIB", style_body), Paragraph("Scan Masuk &lt;= 08:15 (Denda Rp0)", style_body)],
        [Paragraph("Jumat", style_body), Paragraph("08:15 WIB", style_body), Paragraph("17:00 WIB", style_body), Paragraph("Scan Masuk &lt;= 08:15 (Denda Rp0)", style_body)],
        [Paragraph("Sabtu & Minggu", style_body), Paragraph("LIBUR AKHIR PEKAN", style_body), Paragraph("-", style_body), Paragraph("Tidak ada kewajiban presensi", style_body)],
    ]
    cal_table = Table(cal_data, colWidths=[4 * cm, 3 * cm, 3 * cm, 7 * cm])
    cal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(cal_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph("• <b>Generate Kalender:</b> Pilih Bulan dan Tahun, lalu klik <i>Generate Kalender Kerja</i>.", style_bullet))
    story.append(Paragraph("• <b>Ubah Hari Libur Nasional:</b> Klik ganda pada tanggal yang bersangkutan, ubah status menjadi <i>LIBUR_NASIONAL</i> atau <i>CUTI_BERSAMA</i> dan beri keterangan.", style_bullet))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Bab 5: Import Berkas Log Mesin Absensi", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
    story.append(Paragraph(
        "Modul <b>Import Absensi</b> memproses berkas raw log yang diekspor langsung dari mesin fingerprint (Solution / ZKTeco / Fingerspot). "
        "Fitur utama modul ini mencakup:",
        style_body
    ))
    story.append(Paragraph("• <b>Pencegahan Duplikasi:</b> Setiap log scan diverifikasi berdasarkan kombinasi PIN, Tanggal, dan Jam. Scan ganda dalam menit yang sama secara otomatis diabaikan.", style_bullet))
    story.append(Paragraph("• <b>Pratinjau Data (Preview):</b> Dialog interaktif menampilkan data awal sebelum masuk ke database, memberikan estimasi baris valid dan baris bermasalah.", style_bullet))
    story.append(Paragraph("• <b>Riwayat Import:</b> Seluruh proses import dicatat ke tabel riwayat bersama stempel waktu dan identitas user pelaksana.", style_bullet))

    story.append(PageBreak())

    # =========================================================================
    # 5. BAB 6: MESIN PERHITUNGAN POTONGAN
    # =========================================================================
    story.append(Paragraph("Bab 6: Pembentukan Absensi & Hitung Potongan", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
    story.append(Paragraph(
        "Setelah berkas log mentah berhasil diimport, klik tombol <b>Bentuk Absensi Harian & Hitung Potongan</b>. "
        "Sistem secara otomatis mengelompokkan scan pertama sebagai Jam Masuk dan scan terakhir sebagai Jam Pulang, "
        "kemudian menghitung sanksi pemotongan berdasarkan regulasi resmi berikut:",
        style_body
    ))

    rate_data = [
        [Paragraph("<b>Jenis Pelanggaran Presensi</b>", style_body), Paragraph("<b>Kriteria Waktu</b>", style_body), Paragraph("<b>Tarif Potongan (Rp)</b>", style_body), Paragraph("<b>Kaidah Perhitungan</b>", style_body)],
        [Paragraph("Tepat Waktu", style_body), Paragraph("Scan Masuk &lt;= 08:15", style_body), Paragraph("Rp0", style_body), Paragraph("Bebas denda keterlambatan", style_body)],
        [Paragraph("Terlambat Tingkat I", style_body), Paragraph("1 s/d 60 menit (08:16 - 09:15)", style_body), Paragraph("Rp7.500", style_body), Paragraph("Denda flat keterlambatan sedang", style_body)],
        [Paragraph("Terlambat Tingkat II", style_body), Paragraph("&gt; 60 menit (&gt;= 09:16)", style_body), Paragraph("Rp10.000", style_body), Paragraph("Denda flat keterlambatan berat", style_body)],
        [Paragraph("Pulang Cepat", style_body), Paragraph("Sebelum jam pulang resmi", style_body), Paragraph("Rp10.000", style_body), Paragraph("Denda flat pulang awal", style_body)],
        [Paragraph("Tidak Scan Masuk", style_body), Paragraph("Hanya ada scan pulang", style_body), Paragraph("Rp10.000", style_body), Paragraph("Keterlambatan dihitung Rp0", style_body)],
        [Paragraph("Tidak Scan Pulang", style_body), Paragraph("Hanya ada scan masuk", style_body), Paragraph("Rp10.000", style_body), Paragraph("Pulang cepat dihitung Rp0", style_body)],
        [Paragraph("Tidak Hadir (Alfa)", style_body), Paragraph("Scan Masuk &amp; Pulang kosong", style_body), Paragraph("Rp20.000", style_body), Paragraph("Tidak Absen Masuk (10rb) + Pulang (10rb)", style_body)],
        [Paragraph("Hari Libur / Akhir Pekan", style_body), Paragraph("Sabtu, Minggu, Hari Libur", style_body), Paragraph("Rp0", style_body), Paragraph("Bebas potongan sepenuhnya", style_body)],
    ]
    rtbl = Table(rate_data, colWidths=[4 * cm, 4.5 * cm, 3.5 * cm, 5 * cm])
    rtbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(rtbl)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Prinsip Zero Double-Counting (Anti Duplikasi Denda):</b><br/>"
        "1. Jika seorang pegawai tidak melakukan scan masuk sama sekali, sistem mengenakan denda <i>Tidak Absen Masuk (Rp10.000)</i>, "
        "dan menit keterlambatannya <b>TIDAK</b> boleh dihitung lagi.<br/>"
        "2. Jika pegawai tidak hadir (alfa), total potongan tepat <b>Rp20.000</b> (Rp10.000 + Rp10.000) dan tidak boleh berlipat menjadi Rp40.000.<br/>"
        "3. Perhitungan ulang (recalculate) bersifat idempoten: tidak akan pernah menggandakan data di database.",
        style_body
    ))

    story.append(PageBreak())

    # =========================================================================
    # 6. BAB 7, 8, 9, 10: LAPORAN, BACKUP, INSTALLER & FAQ
    # =========================================================================
    story.append(Paragraph("Bab 7: Laporan & Ekspor Rekapitulasi", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
    story.append(Paragraph(
        "Modul <b>Laporan & Rekap</b> menyediakan penyajian ringkas per departemen dan per karyawan. "
        "Pengguna dapat mengekspor rekap bulanan ke berkas <b>Excel (.xlsx)</b> atau dokumen cetak <b>PDF Resmi</b> "
        "yang memuat stempel waktu cetak, tanda tangan verifikasi, dan total potongan yang sinkron 100% dengan database.",
        style_body
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Bab 8: Pengaturan Sistem & Pencadangan (Backup)", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
    story.append(Paragraph(
        "• <b>Pengaturan Tarif & Jam:</b> Administrator dapat mengubah jam masuk/pulang dan besaran denda secara fleksibel. Nilai baru otomatis digunakan pada kalkulasi berikutnya.<br/>"
        "• <b>Pencadangan (Backup Database):</b> SIAP menggunakan SQLite Online Backup API. Anda dapat membuat salinan cadangan kapan saja tanpa perlu menutup aplikasi. Berkas disimpan di <code>%LOCALAPPDATA%\\SIAP\\backups\\</code>.<br/>"
        "• <b>Pemulihan (Restore):</b> Memungkinkan restore data dari arsip cadangan dengan verifikasi integritas checksum.",
        style_body
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Bab 9: Panduan Instalasi & Pembaruan Aplikasi", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
    story.append(Paragraph(
        "Aplikasi SIAP didistribusikan dalam bentuk installer terkompilasi <b>SIAP_Setup_v1.0.0.exe</b> (Inno Setup 64-bit):<br/>"
        "1. Jalankan installer dengan hak akses Administrator (Run as administrator).<br/>"
        "2. Ikuti instruksi wizard. Default lokasi instalasi adalah <code>C:\\Program Files\\SIAP\\</code>.<br/>"
        "3. Shortcut aplikasi akan otomatis dibuat di Desktop dan Start Menu.<br/>"
        "<b>Pembaruan Versi (Update):</b> Saat menginstal versi baru di kemudian hari, Anda cukup menjalankan installer versi baru. "
        "Installer hanya memperbarui program di Program Files dan <b>TIDAK AKAN</b> menimpa database transaksi Anda di %LOCALAPPDATA%\\SIAP\\.",
        style_body
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Bab 10: FAQ & Solusi Kendala Teknis (Troubleshooting)", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    faqs = [
        ("Q: Aplikasi tidak terbuka saat diklik?",
         "A: Pastikan sistem operasi Windows 10/11 64-bit. Periksa berkas log di %LOCALAPPDATA%\\SIAP\\logs\\app.log untuk detail kendala teknis."),
        ("Q: Lupa kata sandi Administrator?",
         "A: Hubungi penanggung jawab IT institusi untuk mereset akun admin melalui konsol pemulihan atau memulihkan file database dari backup terakhir."),
        ("Q: Mengapa hasil import Excel menampilkan baris tidak valid?",
         "A: Pastikan kolom berkas Excel memuat nomor PIN karyawan yang sudah terdaftar di Master Karyawan dan format tanggal valid (YYYY-MM-DD atau DD/MM/YYYY)."),
        ("Q: Bagaimana cara memindahkan data SIAP ke komputer baru?",
         "A: Cukup salin folder %LOCALAPPDATA%\\SIAP\\ dari komputer lama ke lokasi yang sama di komputer baru setelah menginstal aplikasi SIAP."),
    ]
    for q, a in faqs:
        story.append(Paragraph(f"<b>{q}</b>", style_body))
        story.append(Paragraph(a, style_bullet))
        story.append(Spacer(1, 4))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUKSES] Buku panduan pengguna berhasil dibuat di: {OUTPUT_PDF}")


if __name__ == "__main__":
    build_manual_pdf()
