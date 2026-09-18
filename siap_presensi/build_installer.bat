@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM SIAP - Sistem Informasi Administrasi Presensi
REM Automated Inno Setup 6 Compiler Script for Windows 10 & 11 (64-bit)
REM Output: installer\output\SIAP_Setup_v1.0.0.exe
REM ==============================================================================

echo ==============================================================================
echo [SIAP INSTALLER BUILDER] Memulai Kompilasi Windows Setup Installer
echo Target: Windows 64-bit Inno Setup Installer
echo ==============================================================================

REM 1. Periksa berkas hasil kompilasi PyInstaller
if not exist "dist\SIAP\SIAP.exe" (
    echo [ERROR] File biner dist\SIAP\SIAP.exe belum ditemukan.
    echo Harap jalankan build_windows.bat terlebih dahulu untuk membuat executable.
    echo.
    set /p BUILD_NOW="Jalankan build_windows.bat sekarang? (Y/N): "
    if /i "!BUILD_NOW!"=="Y" (
        call build_windows.bat
        if not exist "dist\SIAP\SIAP.exe" (
            echo [ERROR FATAL] Gagal membuat executable. Proses dibatalkan.
            goto :FAIL
        )
    ) else (
        goto :FAIL
    )
)

REM 2. Cari compiler Inno Setup (ISCC.exe)
echo [1/3] Mencari Inno Setup Command-Line Compiler (ISCC.exe)...
set "ISCC_PATH="

where iscc >nul 2>&1
if not errorlevel 1 (
    set "ISCC_PATH=iscc"
    goto :FOUND_ISCC
)

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    goto :FOUND_ISCC
)

if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
    goto :FOUND_ISCC
)

if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    goto :FOUND_ISCC
)

echo [PERINGATAN] Inno Setup 6 Compiler (ISCC.exe) tidak terdeteksi di sistem PATH atau direktori default.
echo Silakan unduh dan pasang Inno Setup 6 dari: https://jrsoftware.org/isdl.php
echo Jika sudah terpasang, buka installer\SIAP_Setup.iss langsung dengan Inno Setup IDE.
goto :FAIL

:FOUND_ISCC
echo [OK] Compiler ditemukan: "%ISCC_PATH%"
echo.

REM 3. Siapkan folder output
if not exist "installer\output" (
    mkdir "installer\output"
)

REM 4. Jalankan kompilasi installer
echo [2/3] Mengompilasi script installer\SIAP_Setup.iss...
"%ISCC_PATH%" "installer\SIAP_Setup.iss"
if errorlevel 1 (
    echo [ERROR] Kompilasi Inno Setup gagal.
    goto :FAIL
)

echo.
echo [3/3] Memverifikasi output installer...
if exist "installer\output\SIAP_Setup_v1.0.0.exe" (
    echo ==============================================================================
    echo [STATUS INSTALLER: BERHASIL]
    echo SIAP_Setup_v1.0.0.exe berhasil dibuat!
    echo ==============================================================================
    echo Lokasi Installer: %CD%\installer\output\SIAP_Setup_v1.0.0.exe
    echo.
    echo Pengujian Installer:
    echo - Jalankan installer\output\SIAP_Setup_v1.0.0.exe untuk menguji instalasi
    echo - Pastikan shortcut Start Menu dan Desktop terpasang
    echo - Pastikan data tersimpan di %LOCALAPPDATA%\SIAP\
    echo ==============================================================================
    pause
    exit /b 0
) else (
    echo [ERROR] File installer\output\SIAP_Setup_v1.0.0.exe tidak ditemukan.
    goto :FAIL
)

:FAIL
echo.
echo ==============================================================================
echo [STATUS INSTALLER: GAGAL]
echo Pembuatan installer Windows belum selesai.
echo ==============================================================================
pause
exit /b 1
