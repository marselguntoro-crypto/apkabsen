# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification File for SIAP (Sistem Informasi Administrasi Presensi).
Target Platform: Windows 10 / Windows 11 (64-bit)
Output: dist/SIAP/SIAP.exe (Windowed GUI Application, No Console)

Catatan Penting:
1. Database aktif pengguna TIDAK disertakan di dalam bundle, melainkan di %LOCALAPPDATA%\\SIAP\\database\\
2. Asset statis (icon, styling) dipaketkan ke dalam folder internal dist/SIAP/assets/
3. Mode GUI aktif (console=False) agar tidak memunculkan jendela hitam command prompt saat dijalankan.
"""
import os
import sys
from pathlib import Path

block_cipher = None

# Direktori proyek root
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Data statis yang wajib disertakan
added_datas = [
    (os.path.join(BASE_DIR, 'assets'), 'assets'),
    (os.path.join(BASE_DIR, 'PANDUAN_PENGGUNA_SIAP.pdf'), '.'),
]

# Modul tersembunyi yang perlu di-bundle secara eksplisit
hidden_imports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtPrintSupport',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.sql.default_comparator',
    'passlib',
    'passlib.handlers',
    'passlib.handlers.bcrypt',
    'bcrypt',
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.reader.excel',
    'pandas',
    'reportlab',
    'reportlab.lib',
    'reportlab.platypus',
    'reportlab.pdfgen',
    'dotenv',
]

# Modul yang dieksklusi untuk merampingkan ukuran bundle
excluded_modules = [
    'tkinter',
    'unittest',
    'pytest',
    'IPython',
    'notebook',
    'scipy',
    'matplotlib',
    'sqlite3.test',
]

a = Analysis(
    ['main.py'],
    pathex=[BASE_DIR],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SIAP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Mode GUI murni tanpa terminal hitam
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(BASE_DIR, 'assets', 'icons', 'SIAP.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SIAP',
)
