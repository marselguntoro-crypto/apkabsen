@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM SIAP - Sistem Informasi Administrasi Presensi
REM Automated Production Build Script for Windows 10 & Windows 11 (64-bit)
REM ==============================================================================

echo ==============================================================================
echo [SIAP BUILD SYSTEM] Memulai proses kompilasi Standalone Executable
echo Target: Windows 64-bit (No Console / Pure GUI Mode)
echo ==============================================================================

REM 1. Periksa Direktori Kerja
if not exist "main.py" (
    echo [ERROR FATAL] File main.py tidak ditemukan.
    echo Pastikan script ini dijalankan dari folder root project SIAP.
    goto :BUILD_FAILED
)

REM 2. Deteksi & Aktivasi Virtual Environment
echo [LANGKAH 1/6] Mendeteksi Python Virtual Environment...
if exist ".venv\Scripts\activate.bat" (
    echo Mengaktifkan Virtual Environment di .venv...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo Mengaktifkan Virtual Environment di venv...
    call venv\Scripts\activate.bat
) else (
    echo [PERINGATAN] Folder .venv atau venv tidak ditemukan secara lokal.
    echo Menggunakan Python dari PATH sistem global...
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERROR FATAL] Python tidak ditemukan di sistem PATH.
        goto :BUILD_FAILED
    )
)

python --version
echo.

REM 3. Verifikasi Dependensi Inti
echo [LANGKAH 2/6] Memeriksa instalasi dependensi inti...
python -c "import PySide6, sqlalchemy, openpyxl, pandas, reportlab, passlib, bcrypt; print('Semua dependensi inti Python terverifikasi OK.')"
if errorlevel 1 (
    echo [ERROR] Salah satu dependensi inti belum terpasang.
    echo Silakan jalankan: pip install -r requirements.txt
    goto :BUILD_FAILED
)

where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller belum terpasang.
    echo Silakan jalankan: pip install pyinstaller
    goto :BUILD_FAILED
)
echo.

REM 4. Bersihkan Artefak Build Sebelumnya
echo [LANGKAH 3/6] Membersihkan artefak kompilasi lama...
call clean_build.bat
echo.

REM 5. Jalankan Pengujian Otomatis (QA Testing Suite)
echo [LANGKAH 4/6] Menjalankan Test Suite sebelum build packaging...
python -m pytest tests -q
if errorlevel 1 (
    echo ==============================================================================
    echo [BUILD DIBATALKAN] Pengujian otomatis mengalami kegagalan (Tests Failed).
    echo Executable TIDAK akan dibuat sebelum seluruh pengujian lulus 100%%.
    echo ==============================================================================
    goto :BUILD_FAILED
)
echo [STATUS QA] Seluruh test suite berhasil lulus dengan status hijau (100%% PASS).
echo.

REM 6. Eksekusi PyInstaller dengan SIAP.spec
echo [LANGKAH 5/6] Mengompilasi aplikasi menggunakan PyInstaller (SIAP.spec)...
pyinstaller --clean SIAP.spec
if errorlevel 1 (
    echo [ERROR] Eksekusi PyInstaller gagal.
    goto :BUILD_FAILED
)
echo.

REM 7. Verifikasi Output Binary Executable
echo [LANGKAH 6/6] Memverifikasi integritas file biner hasil kompilasi...
if exist "dist\SIAP\SIAP.exe" (
    echo.
    echo ==============================================================================
    echo [STATUS BUILD: BERHASIL]
    echo SIAP.exe berhasil dikompilasi ke folder distribusi!
    echo ==============================================================================
    echo Lokasi Executable : %CD%\dist\SIAP\SIAP.exe
    echo Folder Distribusi : %CD%\dist\SIAP\
    echo.
    echo Langkah selanjutnya:
    echo 1. Jalankan pengujian smoke test pada dist\SIAP\SIAP.exe
    echo 2. Kompilasi installer menggunakan Inno Setup: installer\SIAP_Setup.iss
    echo ==============================================================================
    exit /b 0
) else (
    echo [ERROR] File dist\SIAP\SIAP.exe tidak ditemukan setelah proses packaging.
    goto :BUILD_FAILED
)

:BUILD_FAILED
echo.
echo ==============================================================================
echo [STATUS BUILD: GAGAL]
echo Terjadi kesalahan selama proses pembuatan aplikasi Windows.
echo Periksa pesan log di atas untuk informasi detail perbaikan.
echo ==============================================================================
exit /b 1
