# SIAP - SISTEM INFORMASI ADMINISTRASI PRESENSI
### Sistem Pengelolaan Absensi dan Potongan Karyawan (Tahap 1 - Fondasi Desktop)

Aplikasi desktop Windows offline-first yang dirancang khusus untuk administrasi kepegawaian, pencatatan presensi, perhitungan keterlambatan, pulang cepat, ketidakhadiran (alfa), dan kalkulasi pemotongan absensi bulanan secara akurat, transparan, dan terstruktur.

---

## 1. Tujuan Tahap 1
Tahap 1 berfokus pada pembangunan fondasi arsitektur sistem yang modular, stabil, dan aman:
- **Arsitektur Modular**: Pemisahan lapisan antarmuka (PySide6), logika bisnis (Services), dan persistensi data (SQLAlchemy ORM).
- **Database Lokal Mandiri**: SQLite lokal (`data/database/siap_presensi.db`) tanpa memerlukan server terpisah atau hak akses administrator Windows.
- **Sistem Keamanan & Autentikasi**: Password hashing standar industri (bcrypt/PBKDF2), manajemen sesi aktif, pembatasan hak akses berbasis peran (*Role-Based Access Control*: `ADMIN` dan `OPERATOR`).
- **Dashboard Jujur & Transparan**: Metrik statistik berbasis data riil (menampilkan 0 sebelum berkas absensi di-import).
- **Konfigurasi Fleksibel**: Pengaturan target hari kerja, jam kerja operasional (Senin-Kamis & Jumat), serta parameter tarif potongan tersimpan di tabel `settings`.
- **Integritas & Audit**: Pencatatan aktivitas ke `audit_logs` dan berkas log rotasi di `data/logs/app.log`.
- **Pencadangan Aman**: Backup SQLite Online Backup API ke berkas `backup_siap_YYYYMMDD_HHMMSS.db`.

---

## 2. Tumpukan Teknologi
- **Bahasa**: Python 3.10+ / 3.12+
- **Antarmuka Desktop (GUI)**: PySide6 (Qt for Python)
- **Database Engine**: SQLite 3 (Lokal, mode WAL, foreign keys aktif)
- **ORM & Skema**: SQLAlchemy 2.0+
- **Migrasi Skema**: Alembic
- **Keamanan Kredensial**: bcrypt / passlib (PBKDF2-SHA256 fallback)
- **Pengolahan Berkas**: pandas & openpyxl (disiapkan untuk Tahap 2 Import Excel)
- **Laporan Dokumen**: reportlab (disiapkan untuk Tahap Laporan PDF)
- **Executable Packaging**: PyInstaller untuk kompilasi Windows EXE mandiri

---

## 3. Struktur Folder Project

```text
siap_presensi/
│
├── main.py                     # Entry point bootstrap aplikasi desktop PySide6
├── requirements.txt            # Daftar seluruh pustaka dependensi Python
├── README.md                   # Petunjuk instalasi, pengujian, dan build
├── .env.example                # Templat variabel lingkungan & konfigurasi awal
├── .gitignore                  # Berkas pengecualian Git
├── alembic.ini                 # Konfigurasi Alembic database migrations
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Konfigurasi path direktori, tema UI, dan konstanta
│
├── database/
│   ├── __init__.py
│   ├── connection.py           # Engine SQLite, session maker, dan pragma foreign keys
│   ├── base.py                 # Declarative base ORM SQLAlchemy
│   ├── models.py               # 8 Skema tabel (Users, Employees, Attendance, Settings, dll)
│   └── seed.py                 # Seeding otomatis akun bawaan & setting awal
│
├── migrations/
│   ├── env.py                  # Environment runner Alembic
│   ├── script.py.mako          # Template revisi skema
│   └── versions/               # Riwayat versi migrasi database
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py         # Login, hashing, verifikasi password, dan sesi pengguna
│   ├── settings_service.py     # Validasi dan penyimpanan parameter operasional & potongan
│   ├── dashboard_service.py    # Perhitungan analitik statistik kehadiran bulanan
│   └── backup_service.py       # SQLite Online Backup API dan validasi integritas
│
├── ui/
│   ├── __init__.py
│   ├── login_window.py         # Jendela login dengan validasi & pesan informatif
│   ├── main_window.py          # Window utama (Sidebar, Header, Stacked Navigation)
│   ├── dashboard_page.py       # Halaman dashboard dengan 7 kartu statistik & filter
│   ├── settings_page.py        # Formulir pengaturan hari kerja, jam, dan tarif potongan
│   ├── backup_page.py          # Halaman eksekusi backup dan riwayat cadangan
│   ├── placeholder_page.py     # Penampung transparan untuk modul tahap berikutnya
│   └── widgets/
│       ├── __init__.py
│       ├── sidebar.py          # Navigasi kiri dengan filter hak akses Admin/Operator
│       └── stat_card.py        # Komponen kartu statistik bernuansa modern
│
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Rotasi file log (data/logs/app.log) & sensor password
│   └── validators.py           # Validasi format jam, angka bulat, dan kredensial
│
├── data/                       # Direktori runtime lokal (dibuat otomatis saat run)
│   ├── database/               # Berkas siap_presensi.db
│   ├── backups/                # Hasil pencadangan backup_siap_*.db
│   └── logs/                   # Berkas app.log
│
├── assets/
│   └── icons/                  # Aset visual dan ikon aplikasi
│
└── tests/
    ├── __init__.py
    └── test_database.py        # Unit testing database, hashing, validasi, dan backup
```

---

## 4. Cara Instalasi dan Menjalankan di Windows

### Langkah 1: Buat Virtual Environment
Buka terminal PowerShell atau Command Prompt pada folder `siap_presensi`:
```bash
python -m venv .venv
```

### Langkah 2: Aktifkan Virtual Environment
Di Windows:
```bash
.venv\Scripts\activate
```

*(Pada Linux/macOS jika digunakan untuk development:* `source .venv/bin/activate`*)*

### Langkah 3: Instalasi Dependensi
Pastikan pip sudah dalam versi terbaru, lalu jalankan:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Langkah 4: Jalankan Aplikasi
```bash
python main.py
```

Saat pertama kali dijalankan, sistem secara otomatis akan:
1. Membuat folder `data/database/`, `data/backups/`, dan `data/logs/`.
2. Membuat database SQLite `siap_presensi.db` beserta 8 tabel.
3. Melakukan seeding akun awal:
   - **Administrator**: username `admin` | password `Admin@SIAP2025`
   - **Operator**: username `operator` | password `Operator@SIAP2025`
4. Mengisi pengaturan bawaan (Target hari kerja 18 hari, jam masuk 08:15, tarif potongan).

---

## 5. Menjalankan Pengujian (Testing)

Pengujian dapat dijalankan menggunakan runner `unittest` bawaan Python atau `pytest`:

Menggunakan runner standar:
```bash
python -m unittest tests/test_database.py -v
```

Atau menggunakan pytest:
```bash
pytest tests/ -v
```

Pengujian memverifikasi 8 parameter kritis:
1. Pembuatan berkas database SQLite
2. Pembuatan 8 tabel model SQLAlchemy
3. Seeding akun bawaan `admin` dan `operator`
4. Verifikasi kecocokan password hash
5. Penolakan terhadap password yang salah
6. Penyimpanan konfigurasi sistem ke database
7. Pembacaan dan validasi rentang nilai pengaturan
8. Eksekusi pencadangan database dan verifikasi integritas file SQLite

---

## 6. Cara Membangun Berkas Windows Executable (.EXE)

Untuk mendistribusikan aplikasi kepada staf administrasi Windows tanpa memerlukan instalasi Python secara manual:

```bash
pyinstaller --noconfirm --onedir --windowed \
  --name "SIAP_Presensi" \
  --add-data "data;data" \
  --add-data "config;config" \
  main.py
```

File `.exe` mandiri yang dihasilkan akan berada di dalam folder `dist/SIAP_Presensi/SIAP_Presensi.exe`.
Folder data dan log akan tersimpan secara otomatis di samping file executable tanpa memerlukan hak administrator.

---

## 7. Rencana Pengembangan Bertahap
- **Tahap 1 (Saat Ini)**: Fondasi arsitektur desktop, database SQLite, sistem autentikasi, otorisasi peran, dashboard statistik kosong yang jujur, konfigurasi sistem lengkap, dan backup database.
- **Tahap 2 (Berikutnya)**: Modul Import Berkas Excel Absensi Mesin (Fingerprint/Face Scan), sinkronisasi data master karyawan, pengolahan presensi harian, dan kalkulasi otomatis potongan.
- **Tahap 3**: Modul Kalender Hari Kerja & Libur Nasional, Cetak Laporan PDF & Rekapitulasi Potongan Gaji Karyawan.
