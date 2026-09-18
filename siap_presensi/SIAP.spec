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

# Direktori proyek root (SPECPATH disediakan otomatis oleh PyInstaller saat membaca .spec)
BASE_DIR = os.path.abspath(SPECPATH if 'SPECPATH' in globals() else os.getcwd())

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
    # Internal services modules
    'services',
    'services.attendance_daily_service',
    'services.attendance_raw_service',
    'services.attendance_import_service',
    'services.employee_service',
    'services.employee_import_service',
    'services.calendar_service',
    'services.deduction_calculation_service',
    'services.export_service',
    'services.import_validation_service',
    'services.auth_service',
    'services.settings_service',
    'services.dashboard_service',
    'services.backup_service',
    # Internal UI modules and dialogs
    'ui',
    'ui.main_window',
    'ui.login_window',
    'ui.dashboard_page',
    'ui.attendance_hub_page',
    'ui.raw_attendance_page',
    'ui.daily_attendance_page',
    'ui.employees_page',
    'ui.calendar_page',
    'ui.deduction_calculation_page',
    'ui.deduction_page',
    'ui.reports_hub_page',
    'ui.settings_page',
    'ui.backup_page',
    'ui.import_attendance_page',
    'ui.import_history_page',
    'ui.import_module_page',
    'ui.dialogs',
    'ui.dialogs.generate_daily_dialog',
    'ui.dialogs.import_result_dialog',
    'ui.dialogs.excel_preview_dialog',
    'ui.dialogs.edit_calendar_dialog',
    'ui.dialogs.worksheet_selection_dialog',
    'ui.dialogs.first_run_dialog',
    'ui.dialogs.about_dialog',
    'ui.dialogs.deduction_detail_dialog',
    'ui.widgets',
    'ui.widgets.sidebar',
    'ui.widgets.stat_card',
    'ui.widgets.employee_import_dialog',
    'ui.widgets.employee_form_dialog',
    # Internal utils and database
    'utils',
    'utils.date_parser',
    'utils.time_parser',
    'utils.logger',
    'utils.validators',
    'utils.excel_reader',
    'utils.duplicate_detector',
    'database',
    'database.models',
    'database.connection',
    'database.base',
    'database.initializer',
    'database.seed',
    'config',
    'config.settings',
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
