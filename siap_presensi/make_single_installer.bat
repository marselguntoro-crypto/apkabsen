@echo off
setlocal enabledelayedexpansion
title SIAP - Diagnosa & Builder Installer Windows v1.0.0
color 0F

echo ==============================================================================
echo       SIAP (Sistem Informasi Administrasi Presensi) - BUILD DIAGNOSTIK
echo ==============================================================================
echo.

cd /d "%~dp0"
echo [INFO] Direktori kerja saat ini:
echo        %CD%
echo.

REM ------------------------------------------------------------------------------
REM TAHAP 1: PERIKSA PYTHON
REM ------------------------------------------------------------------------------
echo [1/5] Memeriksa instalasi Python di sistem Windows...
where python >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo [GAGAL TAHAP 1] Perintah 'python' TIDAK DITEMUKAN di PATH Windows!
    echo.
    echo Penyebab:
    echo 1. Python belum terinstall di laptop/komputer Anda, ATAU
    echo 2. Saat install Python, kotak "Add python.exe to PATH" lupa dicentang.
    echo.
    echo Solusi:
    echo - Unduh Python (versi 3.10, 3.11, atau 3.12 64-bit) dari https://www.python.org/
    echo - Saat instalasi, WAJIB centang: [v] Add python.exe to PATH
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo       [OK] Ditemukan: %PY_VER%
echo.

REM ------------------------------------------------------------------------------
REM TAHAP 2: PERIKSA & INSTALL DEPENDENSI (PYSIDE6, PYINSTALLER, DLL)
REM ------------------------------------------------------------------------------
echo [2/5] Memeriksa dan menginstal dependensi (PySide6, SQLAlchemy, PyInstaller)...
echo       Proses ini membutuhkan koneksi internet (hanya saat build pertama kali)...
echo.
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [PERINGATAN] Gagal upgrade pip, melanjutkan dengan pip yang ada...
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    color 0C
    echo.
    echo [GAGAL TAHAP 2] Gagal menginstal dependensi dari requirements.txt!
    echo Periksa koneksi internet Anda atau hak akses Administrator.
    pause
    exit /b 1
)

python -m pip install pyinstaller
if errorlevel 1 (
    color 0C
    echo.
    echo [GAGAL TAHAP 2] Gagal menginstal PyInstaller!
    pause
    exit /b 1
)
echo.
echo       [OK] Seluruh pustaka Python & PyInstaller siap digunakan.
echo.

REM ------------------------------------------------------------------------------
REM TAHAP 3: PERIKSA INNO SETUP COMPILER (ISCC.EXE)
REM ------------------------------------------------------------------------------
echo [3/5] Memeriksa Inno Setup 6 Compiler (ISCC.exe)...
set "ISCC_EXE="

where iscc >nul 2>&1
if not errorlevel 1 (
    set "ISCC_EXE=iscc"
) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC_EXE=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
)

if "%ISCC_EXE%"=="" (
    color 0E
    echo.
    echo [PERINGATAN TAHAP 3] Inno Setup 6 Compiler (ISCC.exe) BELUM TERINSTALL!
    echo.
    echo Kenapa ini terjadi?
    echo File 'SIAP_Setup_v1.0.0.exe' dibuat menggunakan software Inno Setup 6.
    echo Karena Inno Setup belum terpasang di komputer Anda, sistem tidak bisa
    echo membungkus file menjadi installer tunggal.
    echo.
    echo Cara Mengatasinya (Sangat Mudah):
    echo 1. Buka browser dan download Inno Setup 6 (Gratis):
    echo    https://jrsoftware.org/isdl.php
    echo 2. Jalankan instalasi Inno Setup hingga selesai.
    echo 3. Jalankan kembali script ini!
    echo.
    pause
    exit /b 1
)

echo       [OK] Ditemukan compiler: "%ISCC_EXE%"
echo.

REM ------------------------------------------------------------------------------
REM TAHAP 4: BUILD EXECUTABLE DENGAN PYINSTALLER
REM ------------------------------------------------------------------------------
echo [4/5] Mengompilasi aplikasi ke format Windows Executable (dist\SIAP\SIAP.exe)...
echo       Proses ini memerlukan waktu sekitar 1-3 menit...
echo.

if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"

python -m PyInstaller --noconfirm --clean SIAP.spec
if errorlevel 1 (
    color 0C
    echo.
    echo [GAGAL TAHAP 4] PyInstaller mengalami error saat kompilasi!
    echo Periksa log di atas.
    pause
    exit /b 1
)

if not exist "dist\SIAP\SIAP.exe" (
    color 0C
    echo.
    echo [GAGAL TAHAP 4] Berkas dist\SIAP\SIAP.exe tidak terbentuk!
    pause
    exit /b 1
)

echo.
echo       [OK] Executable dist\SIAP\SIAP.exe berhasil dibuat!
echo.

REM ------------------------------------------------------------------------------
REM TAHAP 5: KOMPILASI INNO SETUP MENJADI SINGLE INSTALLER
REM ------------------------------------------------------------------------------
echo [5/5] Mengompilasi Setup Installer Tunggal (Inno Setup 6)...
if not exist "installer\output" mkdir "installer\output"

"%ISCC_EXE%" "installer\SIAP_Setup.iss"
if errorlevel 1 (
    color 0C
    echo.
    echo [GAGAL TAHAP 5] Inno Setup gagal mengompilasi installer!
    pause
    exit /b 1
)

echo.
if exist "installer\output\SIAP_Setup_v1.0.0.exe" (
    color 0A
    echo ==============================================================================
    echo [BERHASIL 100%%!] FILE INSTALLER TELAH SELESAI DIBUAT
    echo ==============================================================================
    echo.
    echo Letak File Installer:
    echo %CD%\installer\output\SIAP_Setup_v1.0.0.exe
    echo.
    echo Membuka folder output secara otomatis...
    explorer "%CD%\installer\output"
    echo.
    echo Silakan copy file 'SIAP_Setup_v1.0.0.exe' tersebut ke flashdisk atau bagikan
    echo ke pengguna akhir. Pengguna cukup double click file tersebut untuk install!
    echo ==============================================================================
) else (
    color 0C
    echo [ERROR] File installer\output\SIAP_Setup_v1.0.0.exe tetap tidak ditemukan.
)

pause
exit /b 0
