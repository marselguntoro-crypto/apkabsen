@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM Script Pembersihan Artefak Build SIAP
REM Tidak menghapus database, backups, log, atau data pengguna.
REM ==============================================================================

echo [SIAP CLEAN BUILD] Membersihkan artefak build sementara...

REM 1. Hapus folder build PyInstaller
if exist "build" (
    echo Menghapus folder build/...
    rmdir /s /q "build"
)

REM 2. Hapus folder dist PyInstaller
if exist "dist" (
    echo Menghapus folder dist/...
    rmdir /s /q "dist"
)

REM 3. Hapus cache pytest
if exist ".pytest_cache" (
    echo Menghapus .pytest_cache/...
    rmdir /s /q ".pytest_cache"
)

REM 4. Hapus seluruh __pycache__ secara rekursif
echo Membersihkan Python __pycache__...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM 5. Hapus file *.pyc dan *.pyo
del /s /q *.pyc >nul 2>&1
del /s /q *.pyo >nul 2>&1

echo [SELESAI] Pembersihan artefak build selesai. Data pengguna tetap aman.
exit /b 0
