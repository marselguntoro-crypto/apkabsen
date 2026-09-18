import React, { useState } from 'react';
import {
  Package,
  Terminal,
  FileCode,
  CheckCircle2,
  Copy,
  Check,
  Download,
  FolderTree,
  Shield,
  Layers,
  FileText
} from 'lucide-react';

export function InstallerGuideView() {
  const [copiedScript, setCopiedScript] = useState<string | null>(null);

  const copyToClipboard = (key: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedScript(key);
    setTimeout(() => setCopiedScript(null), 2000);
  };

  const pyInstallerCmd =
    'pyinstaller --noconfirm --onedir --windowed \\\n' +
    '  --name "SIAP_Presensi" \\\n' +
    '  --icon "resources/icons/app_icon.ico" \\\n' +
    '  --add-data "data/templates;data/templates" \\\n' +
    '  --add-data "resources;resources" \\\n' +
    '  main.py';

  const innoCmd = '"C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe" installer/siap_installer.iss';
  const nsisCmd = 'makensis installer/siap_installer.nsi';

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Package className="w-5 h-5 text-blue-600" />
              Panduan Deployment & Pembuatan Windows Installer (.EXE)
            </h2>
            <span className="text-[11px] font-semibold bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded-full border border-blue-200">
              Inno Setup 6 & NSIS Ready
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Membungkus kode Python, PySide6 Qt runtime, SQLite engine, dan template ekspor ke dalam installer native Windows yang siap didistribusikan ke klien.
          </p>
        </div>
      </div>

      {/* Steps Pipeline */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-2 font-bold text-slate-900 text-sm mb-1">
            <span className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs">1</span>
            <span>PyInstaller Build</span>
          </div>
          <p className="text-xs text-slate-500">
            Mengompilasi script Python dan dependencies menjadi folder standalone <code className="text-blue-600">dist/SIAP_Presensi/</code>.
          </p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-2 font-bold text-slate-900 text-sm mb-1">
            <span className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs">2</span>
            <span>Installer Compiler</span>
          </div>
          <p className="text-xs text-slate-500">
            Menjalankan compiler Inno Setup (<code className="text-emerald-600">ISCC.exe</code>) atau NSIS untuk menghasilkan file setup tunggal.
          </p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-2 font-bold text-slate-900 text-sm mb-1">
            <span className="w-6 h-6 rounded-full bg-purple-600 text-white flex items-center justify-center text-xs">3</span>
            <span>Distribusi & Pasang</span>
          </div>
          <p className="text-xs text-slate-500">
            File <code className="text-purple-600">SIAP_Presensi_Setup_v1.5.0.exe</code> siap di-deploy ke komputer operator/HRD tanpa instalasi Python.
          </p>
        </div>
      </div>

      {/* Code Snippets for Commands */}
      <div className="space-y-4">
        {/* Step 1: PyInstaller */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-slate-600" />
              <span className="text-xs font-bold text-slate-800">Langkah 1: Kompilasi Executable dengan PyInstaller</span>
            </div>
            <button
              onClick={() => copyToClipboard('pyinstaller', pyInstallerCmd)}
              className="flex items-center gap-1 text-xs text-slate-600 hover:text-blue-600 font-semibold cursor-pointer"
            >
              {copiedScript === 'pyinstaller' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedScript === 'pyinstaller' ? 'Tersalin' : 'Salin Perintah'}</span>
            </button>
          </div>
          <div className="p-4 bg-slate-950 font-mono text-xs text-emerald-400 overflow-x-auto">
            <pre>{pyInstallerCmd}</pre>
          </div>
        </div>

        {/* Step 2: Inno Setup */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-bold text-slate-800">Langkah 2: Compile Installer dengan Inno Setup 6 (Rekomendasi)</span>
            </div>
            <button
              onClick={() => copyToClipboard('inno', innoCmd)}
              className="flex items-center gap-1 text-xs text-slate-600 hover:text-blue-600 font-semibold cursor-pointer"
            >
              {copiedScript === 'inno' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedScript === 'inno' ? 'Tersalin' : 'Salin Perintah'}</span>
            </button>
          </div>
          <div className="p-4 bg-slate-950 font-mono text-xs text-emerald-400 overflow-x-auto">
            <pre>{innoCmd}</pre>
          </div>
          <div className="p-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-600 flex items-center justify-between">
            <span>File konfigurasi telah dibuat di: <code className="font-mono text-blue-700">installer/siap_installer.iss</code></span>
            <span className="font-semibold text-emerald-700 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Konfigurasi Lengkap
            </span>
          </div>
        </div>

        {/* Alternative: NSIS */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 text-purple-600" />
              <span className="text-xs font-bold text-slate-800">Alternatif: Compile Installer dengan NSIS (Nullsoft)</span>
            </div>
            <button
              onClick={() => copyToClipboard('nsis', nsisCmd)}
              className="flex items-center gap-1 text-xs text-slate-600 hover:text-blue-600 font-semibold cursor-pointer"
            >
              {copiedScript === 'nsis' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedScript === 'nsis' ? 'Tersalin' : 'Salin Perintah'}</span>
            </button>
          </div>
          <div className="p-4 bg-slate-950 font-mono text-xs text-emerald-400 overflow-x-auto">
            <pre>{nsisCmd}</pre>
          </div>
          <div className="p-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-600 flex items-center justify-between">
            <span>File konfigurasi telah dibuat di: <code className="font-mono text-blue-700">installer/siap_installer.nsi</code></span>
            <span className="font-semibold text-emerald-700 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Konfigurasi Lengkap
            </span>
          </div>
        </div>
      </div>

      {/* Directory Layout Tree */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <FolderTree className="w-4 h-4 text-blue-600" />
          Struktur Target Instalasi pada Windows Komputer Klien (%LOCALAPPDATA% / Program Files)
        </h3>
        <div className="bg-slate-900 text-slate-300 p-4 rounded-lg font-mono text-xs overflow-x-auto leading-relaxed">
          <div>C:\Users\Username\AppData\Local\SIAP_Presensi\</div>
          <div className="pl-4 text-slate-400">├── SIAP_Presensi.exe &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-emerald-400">(Eksekutabel Utama PySide6)</span></div>
          <div className="pl-4 text-slate-400">├── python*.dll, Qt6*.dll &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-emerald-400">(Dynamic Link Libraries Qt & Python)</span></div>
          <div className="pl-4 text-slate-400">├── database\</div>
          <div className="pl-8 text-slate-400">└── siap_presensi.db &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-blue-400">(Database SQLite ACID)</span></div>
          <div className="pl-4 text-slate-400">├── backups\ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-amber-400">(Arsip backup .db otomatis)</span></div>
          <div className="pl-4 text-slate-400">├── reports\ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-rose-400">(Keluaran ekspor Excel & PDF)</span></div>
          <div className="pl-4 text-slate-400">├── templates\ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-slate-400">(Template import Excel absensi)</span></div>
          <div className="pl-4 text-slate-400">└── logs\ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-slate-400">(Berkas log audit & error aplikasi)</span></div>
        </div>
      </div>
    </div>
  );
}
