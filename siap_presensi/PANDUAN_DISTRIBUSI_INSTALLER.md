# PANDUAN DISTRIBUSI PENGGUNA AKHIR (END-USER RELEASE GUIDE)
# Aplikasi: SIAP (Sistem Informasi Administrasi Presensi) v1.0.0

## TARGET AKHIR
Satu-satunya file yang dikirimkan kepada pengguna akhir (klien / pegawai / admin) adalah:
```text
SIAP_Setup_v1.0.0.exe
```

---

## A. PENGALAMAN PENGGUNA AKHIR (END-USER EXPERIENCE)
Pengguna akhir **TIDAK PERLU**:
- Tidak perlu membuka Google AI Studio
- Tidak perlu membuka Command Prompt atau PowerShell
- Tidak perlu menginstal Python
- Tidak perlu menjalankan script build (`.bat`)
- Tidak perlu menginstal library / pip
- Tidak perlu konfigurasi database manual

Pengguna akhir **HANYA PERLU**:
1. Menerima file `SIAP_Setup_v1.0.0.exe` (misalnya via flashdisk, Google Drive, atau shared folder).
2. **Double-click** pada `SIAP_Setup_v1.0.0.exe`.
3. Klik **Next** -> **Install** -> **Finish**.
4. Ikon **SIAP** akan langsung muncul di **Desktop** dan **Start Menu**.
5. Klik ikon **SIAP** di Desktop, aplikasi langsung terbuka dengan GUI murni.

---

## B. CARA DEVELOPER MENGHASILKAN FILE TERSEBUT (ONE-TIME BUILD DI WINDOWS)

Karena binary Windows `.exe` memerlukan kompiler sistem Windows, Developer menjalankan langkah ini satu kali di komputer Windows:

### Prasyarat Developer (Hanya di Komputer Pembuat):
1. **Python 3.10 - 3.12 (64-bit)** terpasang (centang "Add Python to PATH").
2. **Inno Setup 6** terpasang (gratis dari [jrsoftware.org](https://jrsoftware.org/isdl.php)).

### Langkah Kompilasi:
1. Salin / download folder project `siap_presensi` ke komputer Windows Anda.
2. Buka folder `siap_presensi`.
3. **Double-click** file:
   ```cmd
   make_single_installer.bat
   ```
4. Skrip tersebut akan otomatis:
   - Menyiapkan dependensi (`PySide6`, `SQLAlchemy`, `Pandas`, `OpenPyXL`, `ReportLab`, dll).
   - Memanggil `PyInstaller` menggunakan konfigurasi `SIAP.spec` (`console=False`, mode GUI murni).
   - Memanggil compiler Inno Setup (`ISCC.exe`) menggunakan skrip `installer\SIAP_Setup.iss`.
   - Mengemas seluruh runtime Python, aset, dan panduan PDF ke dalam satu file installer.

### Hasil Output Final:
File installer mandiri akan muncul di:
```text
siap_presensi\installer\output\SIAP_Setup_v1.0.0.exe
```

File inilah yang siap didistribusikan langsung ke pengguna akhir!
