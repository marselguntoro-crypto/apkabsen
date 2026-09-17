import React, { useState } from 'react';
import { Monitor, Code2, Database, Terminal, ShieldCheck, Download, Smartphone, ChevronRight } from 'lucide-react';
import DesktopSimulator from './components/DesktopSimulator';
import CodeExplorer from './components/CodeExplorer';
import DatabaseSchemaView from './components/DatabaseSchemaView';
import ExecutionGuide from './components/ExecutionGuide';
import InstallAppModal from './components/InstallAppModal';
import { usePwaInstall } from './hooks/usePwaInstall';

export default function App() {
  const [activeTab, setActiveTab] = useState<'simulator' | 'code' | 'schema' | 'guide'>('simulator');
  const [isInstallModalOpen, setIsInstallModalOpen] = useState(false);
  const { isInstallable, installApp, hasNativePrompt, isInstalled } = usePwaInstall();

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 flex flex-col font-sans">
      {/* Top Application Bar */}
      <header className="bg-slate-950 text-white border-b border-slate-800 sticky top-0 z-50 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-black text-lg shadow">
              S
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold text-base tracking-tight text-white">SIAP</h1>
                <span className="text-[10px] bg-blue-500/20 text-blue-300 border border-blue-400/30 px-2 py-0.5 rounded font-mono font-semibold">
                  Tahap 6: Finalisasi Aplikasi, Build Executable (.EXE) & Installer Windows
                </span>
              </div>
              <p className="text-xs text-slate-400">Sistem Informasi Administrasi Presensi & Potongan Karyawan</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Install APK / App Button */}
            <button
              onClick={() => setIsInstallModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg shadow-sm transition cursor-pointer"
              title="Pasang aplikasi ke HP Android atau Komputer Desktop"
            >
              <Smartphone className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Pasang APK / Aplikasi</span>
              <span className="sm:hidden">Install</span>
            </button>

            {/* Navigation Tabs */}
            <nav className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
              <button
                onClick={() => setActiveTab('simulator')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition cursor-pointer ${
                  activeTab === 'simulator'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Monitor className="w-3.5 h-3.5" />
                <span>Simulasi</span>
              </button>

              <button
                onClick={() => setActiveTab('code')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition cursor-pointer ${
                  activeTab === 'code'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>Berkas Kode</span>
              </button>

              <button
                onClick={() => setActiveTab('schema')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition cursor-pointer ${
                  activeTab === 'schema'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                <span>SQLite</span>
              </button>

              <button
                onClick={() => setActiveTab('guide')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition cursor-pointer ${
                  activeTab === 'guide'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Terminal className="w-3.5 h-3.5" />
                <span>Panduan</span>
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* PWA Quick Install Banner if available */}
        {hasNativePrompt && !isInstalled && (
          <div className="bg-emerald-900 text-white p-3.5 rounded-xl border border-emerald-700 shadow flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-500 text-white flex items-center justify-center shrink-0">
                <Smartphone className="w-4 h-4" />
              </div>
              <div className="text-xs">
                <p className="font-bold text-white">Perangkat Anda siap memasang Aplikasi SIAP!</p>
                <p className="text-emerald-200">Pasang langsung ke menu smartphone Android atau layar desktop dengan satu klik.</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => installApp()}
                className="px-3.5 py-1.5 bg-white text-emerald-950 font-bold text-xs rounded-lg shadow hover:bg-emerald-50 transition cursor-pointer flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Pasang Sekarang</span>
              </button>
            </div>
          </div>
        )}
        {/* Status Banner */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 border border-emerald-200">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900">Tahap 6: Finalisasi Aplikasi, Build Executable (.EXE) & Installer Windows</h2>
                <span className="text-[10px] bg-blue-100 text-blue-800 font-bold px-2 py-0.5 rounded">
                  PyInstaller Standalone (No Console)
                </span>
                <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded">
                  Inno Setup 64-bit Installer
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Aplikasi SIAP telah siap rilis produksi (*production-ready release*). Seluruh modul (Master Karyawan, Import Absensi Mesin, Kalender Kerja, Mesin Hitung Potongan) telah dikemas menjadi executable mandiri <code>SIAP.exe</code> dan installer setup profesional dengan proteksi basis data di <code>%LOCALAPPDATA%\SIAP\</code>.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-600 font-mono bg-slate-50 px-3 py-2 rounded-lg border border-slate-200">
            <span>Build Pipeline:</span>
            <strong className="text-blue-700">.\build_windows.bat</strong>
          </div>
        </div>

        {/* Tab Content Display */}
        {activeTab === 'simulator' && <DesktopSimulator />}
        {activeTab === 'code' && <CodeExplorer />}
        {activeTab === 'schema' && <DatabaseSchemaView />}
        {activeTab === 'guide' && <ExecutionGuide />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
          <p>
            SIAP - Sistem Informasi Administrasi Presensi &copy; {new Date().getFullYear()}. Dibangun menggunakan Python 3.12, PySide6, SQLAlchemy, dan SQLite.
          </p>
          <div className="flex items-center gap-3 font-medium">
            <span>Tahap 1: Fondasi</span>
            <span>&bull;</span>
            <span>Tahap 2: Karyawan</span>
            <span>&bull;</span>
            <span>Tahap 3: Import Excel</span>
            <span>&bull;</span>
            <span>Tahap 4: Kalender Kerja</span>
            <span>&bull;</span>
            <span>Tahap 5: Potongan</span>
            <span>&bull;</span>
            <span className="text-blue-600 font-bold">Tahap 6: Build EXE & Installer Windows</span>
          </div>
        </div>
      </footer>

      {/* Install App Modal */}
      <InstallAppModal
        isOpen={isInstallModalOpen}
        onClose={() => setIsInstallModalOpen(false)}
      />
    </div>
  );
}
