# SIAP — SISTEM INFORMASI ADMINISTRASI PRESENSI
### Aplikasi Desktop Manajemen Presensi, Kalender Kerja & Rekapitulasi Potongan Karyawan
**Versi:** 1.0.0 (Final Production Release)  
**Platform Target:** Windows 10 & Windows 11 (64-bit Architecture)  
**Tahun Rilis:** 2026  
**Penyusun:** Tim Pengembang SIAP  

---

## 1. Deskripsi Aplikasi
**SIAP (Sistem Informasi Administrasi Presensi)** adalah aplikasi desktop mandiri (*offline-first*) yang dirancang khusus untuk memenuhi kebutuhan pencatatan data kehadiran pegawai, kalender kerja institusi, impor berkas log mesin *fingerprint*, pembentukan absensi harian otomatis, serta kalkulasi sanksi finansial (pemotongan honor/gaji) akibat ketidakhadiran dan pelanggaran disiplin kerja secara matematis, transparan, dan dapat diaudit secara menyeluruh.

Aplikasi dikemas dalam bentuk biner mandiri (*standalone executable*) yang tidak memerlukan instalasi Python di komputer pengguna akhir dan dilengkapi dengan paket *installer* profesional berbasis Inno Setup.

---

## 2. Fitur Utama Sistem

1. **Autentikasi & Keamanan Pengguna (RBAC)**:
   - Pembagian hak akses berjenjang: **Administrator** (wewenang penuh) dan **Operator** (operasional harian).
   - *Password hashing* aman menggunakan `bcrypt` dengan fallback PBKDF2.
   - Deteksi *First-Run Wizard* yang memandu penggantian kata sandi *default* pabrik demi proteksi institusi.
   - Perlindungan anti-bocor kredensial pada log rotasi sistem.

2. **Master Data Karyawan**:
   - Pencatatan NIP/NIK, Nama Lengkap, Nomor PIN Absensi Fingerprint, Departemen, dan Jabatan.
   - Validasi ketat terhadap duplikasi NIP dan duplikasi PIN Fingerprint.
   - Fitur Impor massal dan Ekspor seluruh data karyawan ke berkas Excel (`.xlsx`).

3. **Kalender Kerja Bulanan**:
   - Pembuatan jadwal kerja otomatis Senin s/d Jumat per bulan dan per tahun.
   - Standar jam kerja: **Senin-Kamis (08:15 - 16:30 WIB)** dan **Jumat (08:15 - 17:00 WIB)**.
   - Pengaturan hari libur nasional, cuti bersama, dan hari khusus dengan keterangan kustom.

4. **Impor Berkas Log Absensi Mesin**:
   - Pengunggahan berkas Excel mentah hasil ekspor mesin *fingerprint* (Solution, ZKTeco, Fingerspot).
   - Validasi struktur kolom, format tanggal, dan kecocokan PIN dengan master karyawan.
   - Deteksi dan pencegahan duplikasi *scan log* pada menit yang sama.
   - Dialog pratinjau interaktif (*preview*) sebelum komitmen ke database.

5. **Pembentukan Absensi Harian & Mesin Hitung Potongan**:
   - Pengelompokan cerdas: *scan* pertama sebagai Jam Masuk dan *scan* terakhir sebagai Jam Pulang.
   - Logika pemotongan presisi tinggi:
     - **Tepat Waktu (Masuk <= 08:15):** Potongan **Rp0**.
     - **Terlambat 1 s/d 60 menit (08:16 - 09:15):** Potongan **Rp7.500**.
     - **Terlambat > 60 menit (>= 09:16):** Potongan **Rp10.000**.
     - **Pulang Cepat (sebelum jam kepulangan resmi):** Potongan **Rp10.000**.
     - **Tidak Absen Masuk (hanya ada scan pulang):** Potongan **Rp10.000** (menit terlambat = 0).
     - **Tidak Absen Pulang (hanya ada scan masuk):** Potongan **Rp10.000** (menit pulang cepat = 0).
     - **Tidak Hadir / Alfa (masuk & pulang kosong):** Total potongan tepat **Rp20.000** (Rp10.000 masuk + Rp10.000 pulang).
     - **Hari Libur / Akhir Pekan:** Potongan **Rp0**.
   - **Prinsip Zero Double-Counting**: Menghilangkan risiko duplikasi denda pada hari yang sama.
   - Sifat *Idempotent Recalculation*: Penghitungan ulang tidak pernah menggandakan data di database.

6. **Laporan & Ekspor**:
   - Rekapitulasi per karyawan dan per departemen.
   - Ekspor laporan komprehensif ke format **Excel (.xlsx)** dengan pewarnaan status dan formula total.
   - Cetak dokumen resmi ke format **PDF** melalui ReportLab lengkap dengan stempel waktu dan tanda tangan verifikasi.

7. **Pencadangan (Backup) & Pemulihan (Restore)**:
   - Pencadangan online *hot-backup* SQLite tanpa menghentikan aplikasi.
   - Pembuatan backup pra-migrasi otomatis sebelum pembaruan skema.
   - Pemulihan instan berkas database dengan validasi integritas checksum.

8. **Pengaturan Sistem & Diagnosa**:
   - Parameter dinamis untuk jam kerja, target hari kerja, dan nominal tarif denda.
   - Dialog "Tentang SIAP" dengan informasi direktori runtime Windows dan tombol pintas Explorer.

---

## 3. Arsitektur Teknologi

```text
+-------------------------------------------------------------+
|               ANTARMUKA PENGGUNA (GUI TIER)                 |
|             PySide6 (Qt for Python 6.6+ / 6.8+)             |
|   MainWindow | Sidebar | Dialogs | QStackedWidget | Theming |
+-------------------------------------------------------------+
                              │
+-------------------------------------------------------------+
|                 LAPISAN LOGIKA BISNIS (SERVICES)            |
|  AuthService | EmployeeService | RawAttendanceImportService |
|  CalendarService | AttendanceDailyService | ExportService   |
|  DeductionCalculationService | BackupService | Settings     |
+-------------------------------------------------------------+
                              │
+-------------------------------------------------------------+
|             PERSISTENSI & VALIDASI DATA (ORM TIER)          |
|  SQLAlchemy 2.0+ ORM Models | Alembic & MigrationRunner     |
|  DatabaseInitializer | SQLite 3 (WAL Mode, Foreign Keys ON) |
+-------------------------------------------------------------+
                              │
+-------------------------------------------------------------+
|             LINGKUNGAN SISTEM OPERASI WINDOWS               |
|  Binari: C:\Program Files\SIAP\ (Inno Setup / PyInstaller)  |
|  Data:   %LOCALAPPDATA%\SIAP\ (Database, Logs, Backups)     |
+-------------------------------------------------------------+
```

---

## 4. Struktur Direktori Final

```text
siap_presensi/
│
├── main.py                     # Entry point utama bootstrap aplikasi desktop
├── SIAP.spec                   # Spesifikasi pengemasan PyInstaller (Windowed / No-Console)
├── build_windows.bat           # Script otomatis build packaging Windows (Testing + PyInstaller)
├── clean_build.bat             # Script pembersihan artefak kompilasi dan cache
├── requirements.txt            # Dependensi pustaka produksi
├── requirements-dev.txt        # Dependensi pustaka pengembangan & testing
├── PANDUAN_PENGGUNA_SIAP.pdf   # Buku panduan resmi pengguna & administrator
├── README.md                   # Dokumentasi teknis dan operasional sistem
├── .env.example                # Templat konfigurasi lingkungan
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Resolusi direktori Windows, konfigurasi tarif, tema UI
│
├── database/
│   ├── __init__.py
│   ├── base.py                 # Declarative Base SQLAlchemy
│   ├── connection.py           # Engine SQLite, session context, PRAGMA setup
│   ├── initializer.py          # DatabaseInitializer (Bootstrap, backup pra-migrasi, verifikasi)
│   ├── migration_runner.py     # Eksekutor migrasi skema idempoten (Tahap 4 & Tahap 5)
│   ├── models.py               # 8 Tabel ORM (User, Employee, Attendance, Deduction, Setting, dll)
│   └── seed.py                 # Seeding idempoten akun awal & setting pabrik
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py         # Autentikasi, hashing bcrypt, manajemen sesi aktif
│   ├── employee_service.py     # Operasi CRUD, validasi NIP/PIN, impor/ekspor Excel
│   ├── raw_attendance_service.py # Validasi berkas log mesin, deteksi duplikasi
│   ├── calendar_service.py     # Generator kalender bulanan, penandaan libur
│   ├── attendance_daily_service.py # Pembentukan kehadiran harian dari scan mentah
│   ├── deduction_calculation_service.py # Mesin hitung potongan zero-double-counting
│   ├── export_service.py       # Generator berkas laporan Excel & PDF resmi
│   ├── backup_service.py       # SQLite Online Backup API & integritas berkas
│   ├── dashboard_service.py    # Agregator metrik statistik riil
│   └── settings_service.py     # Validasi & persistensi parameter konfigurasi
│
├── ui/
│   ├── __init__.py
│   ├── login_window.py         # Form login dengan animasi status
│   ├── main_window.py          # Jendela utama (Header, Navigasi, Breadcrumb, Dialogs)
│   ├── dashboard_page.py       # Tampilan statistik kehadiran dan grafik
│   ├── employees_page.py       # Tampilan manajemen master karyawan
│   ├── import_module_page.py   # Tampilan alur impor data absensi
│   ├── attendance_hub_page.py  # Tab terpadu data mentah & absensi harian
│   ├── calendar_page.py        # Tampilan grid kalender kerja & hari libur
│   ├── deduction_page.py       # Tampilan rekapitulasi potongan & ekspor
│   ├── settings_page.py        # Tampilan konfigurasi tarif, jam operasional, direktori data
│   ├── backup_page.py          # Tampilan pencadangan & pemulihan database
│   ├── dialogs/
│   │   ├── about_dialog.py     # Dialog informasi spesifikasi rilis & tombol buka folder
│   │   ├── first_run_dialog.py # Dialog panduan awal & penggantian password default
│   │   ├── excel_preview_dialog.py # Pratinjau berkas Excel sebelum impor
│   │   ├── generate_daily_dialog.py # Parameter pemrosesan absensi harian
│   │   └── deduction_detail_dialog.py # Rincian kalkulasi per pegawai
│   └── widgets/
│       ├── sidebar.py          # Navigasi kiri adaptif sesuai peran Admin / Operator
│       └── stat_card.py        # Komponen kartu statistik
│
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Rotasi file log 5MB x 5 file dengan sensor kata sandi
│   └── validators.py           # Validasi format jam HH:MM, format tanggal, integer
│
├── assets/
│   └── icons/
│       ├── SIAP.ico            # Multi-resolution Windows icon (16x16 s/d 256x256)
│       └── SIAP.png            # Master branding icon
│
├── installer/
│   └── SIAP_Setup.iss          # Script kompilasi installer Inno Setup 64-bit
│
├── scripts/
│   └── generate_user_manual.py # Script generator buku panduan PDF (ReportLab)
│
└── tests/
    ├── __init__.py
    ├── test_database.py        # Pengujian inisialisasi DB, hashing, backup, dan migrasi
    ├── test_employees.py       # Pengujian CRUD karyawan, validasi PIN, impor Excel
    ├── test_attendance_import.py # Pengujian pemrosesan log mentah mesin
    ├── test_calendar_and_daily_attendance.py # Pengujian kalender & pembentukan absensi
    ├── test_deduction_calculation.py # 13 Kasus uji wajib perhitungan denda potongan
    └── test_phase6_deployment.py # Pengujian DatabaseInitializer, folder Windows & packaging
```

---

## 5. Lokasi Folder Data Pengguna di Windows

Aplikasi mematuhi standar keamanan Windows (*Non-Admin User Security*):
- **Folder Instalasi (Read-Only):** `C:\Program Files\SIAP\`
- **Folder Data Dinamis Pengguna:** `%LOCALAPPDATA%\SIAP\`

```text
%LOCALAPPDATA%\SIAP\
├── database\
│   └── siap_presensi.db       # Basis data operasional SQLite (WAL Mode)
├── backups\
│   ├── pre_migration_*.db     # Salinan otomatis sebelum pembaruan versi
│   └── backup_siap_*.db       # Salinan manual via menu pencadangan
├── logs\
│   └── app.log                # Log rotasi sistem (terproteksi dari kebocoran password)
├── exports\
│   ├── Rekap_Potongan_*.xlsx  # Berkas laporan lembar kerja Excel
│   └── Laporan_Potongan_*.pdf # Berkas dokumen cetak PDF
└── config\
```

*Keunggulan Arsitektur:*
1. Saat aplikasi diperbarui (*update*) ke versi baru, database pengguna **TIDAK PERNAH TERHAPUS** karena berada di luar direktori `Program Files`.
2. Aplikasi dapat berjalan pada akun Windows biasa (*Standar / Non-Administrator*).

---

## 6. Akun Kredensial Bawaan Awal

Saat pertama kali dijalankan, sistem otomatis membuat akun bawaan:

| Peran (Role) | Username | Password Default | Hak Akses |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@SIAP2025` | Akses penuh ke seluruh fitur dan pengaturan |
| **Operator** | `operator` | `Operator@SIAP2025` | Akses operasional presensi, impor, dan laporan |

*Keamanan:* Jika Administrator login dengan password bawaan, dialog **First-Run Setup** akan muncul otomatis meminta pembuatan kata sandi baru.

---

## 7. Cara Menjalankan dari Source Code

### Prasyarat:
- Python 3.10, 3.11, atau 3.12 (64-bit)
- Sistem Operasi: Windows 10, Windows 11, atau Linux/macOS untuk lingkungan dev

### Langkah-langkah:
```bash
# 1. Masuk ke direktori project
cd siap_presensi

# 2. Buat Python virtual environment
python -m venv .venv

# 3. Aktifkan virtual environment
# Pada Windows Command Prompt:
.venv\Scripts\activate.bat
# Pada PowerShell:
.venv\Scripts\Activate.ps1
# Pada Linux / macOS:
source .venv/bin/activate

# 4. Pasang dependensi
pip install -r requirements.txt

# 5. Jalankan aplikasi desktop
python main.py
```

---

## 8. Cara Menjalankan Pengujian (Testing Suite)

Proyek ini dilengkapi dengan 50+ pengujian unit dan integrasi otomatis yang mencakup seluruh lapisan sistem:

```bash
# Jalankan seluruh test suite
pytest tests -v

# Jalankan pengujian perhitungan denda potongan saja
pytest tests/test_deduction_calculation.py -v

# Jalankan pengujian deployment dan integritas Windows
pytest tests/test_phase6_deployment.py -v
```

---

## 9. Cara Melakukan Build Executable (PyInstaller)

Proses kompilasi ke bentuk standalone `.exe` diotomatisasi melalui script batch:

```cmd
:: Jalankan script build otomatis
build_windows.bat
```

Script batch akan secara berurutan:
1. Memeriksa keberadaan virtual environment.
2. Memverifikasi kelengkapan dependensi.
3. Membersihkan artefak build lama (`clean_build.bat`).
4. Menjalankan seluruh pengujian otomatis (`pytest`). Jika ada test yang gagal, proses build langsung dihentikan.
5. Menjalankan PyInstaller dengan berkas `SIAP.spec`.
6. Memverifikasi ketersediaan biner hasil di `dist\SIAP\SIAP.exe`.

---

## 10. Cara Membuat Installer Windows (Inno Setup)

1. Unduh dan pasang **Inno Setup 6** (https://jrsoftware.org/isdl.php).
2. Pastikan proses build PyInstaller telah selesai dan menghasilkan folder `dist\SIAP\`.
3. Buka berkas `installer\SIAP_Setup.iss` menggunakan Inno Setup Compiler.
4. Klik menu **Build -> Compile** (atau tekan `Ctrl + F9`).
5. File installer siap distribusi akan dibuat di:
   `installer\output\SIAP_Setup_v1.0.0.exe`

---

## 11. Alur Operasional Pengguna (Step-by-Step)

```text
[1. Master Karyawan] ──> [2. Kalender Kerja] ──> [3. Import Log Mesin]
                                                         │
                                                         ▼
[6. Ekspor Laporan]  <── [5. Hitung Potongan] <── [4. Bentuk Absensi]
```

1. **Langkah 1 (Master Karyawan):** Daftarkan karyawan beserta Nomor ID / PIN Fingerprint yang identik dengan mesin presensi.
2. **Langkah 2 (Kalender Kerja):** Generate hari kerja bulanan dan tentukan hari libur nasional atau cuti bersama.
3. **Langkah 3 (Import Absensi):** Masukkan file Excel hasil unduh mesin *fingerprint*. Periksa hasil validasi pada dialog pratinjau.
4. **Langkah 4 & 5 (Pembentukan Absensi & Hitung Potongan):** Buka menu Data Absensi, klik tombol *Bentuk Absensi Harian & Hitung Potongan*. Sistem secara otomatis memetakan scan dan menghitung denda.
5. **Langkah 6 (Laporan & Rekap):** Buka menu Laporan & Rekap untuk melihat total denda per divisi dan mencetak ke Excel/PDF.

---

## 12. Regulasi Perhitungan Potongan Presensi

| Kondisi Presensi | Kriteria Waktu | Nominal Potongan | Keterangan |
| :--- | :--- | :--- | :--- |
| **Tepat Waktu** | Jam Masuk <= 08:15 | **Rp 0** | Bebas denda |
| **Terlambat Tingkat I** | 1 s/d 60 menit (08:16 - 09:15) | **Rp 7.500** | Denda flat sedang |
| **Terlambat Tingkat II** | > 60 menit (>= 09:16) | **Rp 10.000** | Denda flat berat |
| **Pulang Cepat** | Pulang sebelum waktu operasional | **Rp 10.000** | Denda flat pulang awal |
| **Tidak Absen Masuk** | Jam Masuk kosong, Jam Pulang ada | **Rp 10.000** | Menit telat dihitung 0 |
| **Tidak Absen Pulang** | Jam Masuk ada, Jam Pulang kosong | **Rp 10.000** | Menit pulang cepat dihitung 0 |
| **Tidak Hadir (Alfa)** | Jam Masuk & Pulang kosong | **Rp 20.000** | Gabungan tidak masuk + pulang |
| **Hari Libur / Weekend** | Sabtu, Minggu, Libur Nasional | **Rp 0** | Bebas denda sepenuhnya |

*Aturan Tambahan:* Terlambat dan pulang cepat pada hari yang sama diakumulasikan secara aditif (contoh: terlambat 15 menit [Rp7.500] + pulang cepat [Rp10.000] = Rp17.500).

---

## 13. Manajemen Pencadangan & Pemulihan (Backup & Restore)

- **Pencadangan Rutin:** Buka menu *Backup Database*, klik *Buat Cadangan Sekarang*. File cadangan disimpan dengan format nama stempel waktu `backup_siap_YYYYMMDD_HHMMSS.db`.
- **Backup Pra-Migrasi Otomatis:** Setiap kali aplikasi versi baru dijalankan, `DatabaseInitializer` secara otomatis mencadangkan file database lama ke folder `backups/pre_migration_backup_*.db` sebelum mengeksekusi skrip migrasi skema baru.
- **Pemulihan Data:** Jika terjadi kerusakan berkas, klik tombol *Pulihkan dari Backup* pada halaman Backup dan pilih berkas `.db` yang valid.

---

## 14. Lisensi & Hak Cipta
Hak Cipta (C) 2026 Tim Pengembang SIAP. Seluruh hak dilindungi undang-undang.
Aplikasi ini dikembangkan untuk keperluan administrasi institusional kepegawaian dan disebarluaskan di bawah lisensi *Proprietary Institutional License*.
