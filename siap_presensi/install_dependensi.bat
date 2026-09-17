@echo off
echo ==============================================================================
echo [SIAP] Menginstal Seluruh Dependensi Python untuk SIAP Presensi
echo ==============================================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak terdeteksi di sistem PATH!
    echo Silakan install Python 3.10 / 3.11 / 3.12 dari python.org
    echo Pastikan centang "Add Python to PATH" saat menginstal Python!
    echo.
    pause
    exit /b 1
)

python --version
echo Menginstal paket pip dari requirements.txt...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo ==============================================================================
echo [SELESAI] Seluruh dependensi berhasil dipasang!
echo Sekarang Anda dapat mengklik build_windows.bat untuk membuat SIAP.exe
echo ==============================================================================
pause
