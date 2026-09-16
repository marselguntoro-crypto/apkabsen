import React, { useState } from 'react';
import { Monitor, Code2, Database, Terminal, ShieldCheck, Download, ChevronRight } from 'lucide-react';
import DesktopSimulator from './components/DesktopSimulator';
import CodeExplorer from './components/CodeExplorer';
import DatabaseSchemaView from './components/DatabaseSchemaView';
import ExecutionGuide from './components/ExecutionGuide';

export default function App() {
  const [activeTab, setActiveTab] = useState<'simulator' | 'code' | 'schema' | 'guide'>('simulator');

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 flex flex-col font-sans">
      {/* Top Application Bar */}
      <header className="bg-slate-950 text-white border-b border-slate-800 sticky top-0 z-50 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-black text-lg shadow">
              S
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold text-base tracking-tight text-white">SIAP</h1>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 px-2 py-0.5 rounded font-mono font-semibold">
                  Tahap 4: Kalender Kerja & Absensi Harian
                </span>
              </div>
              <p className="text-xs text-slate-400">Sistem Informasi Administrasi Presensi & Potongan Karyawan</p>
            </div>
          </div>

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
              <span>Simulasi Desktop</span>
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
              <span>Berkas Kode Python</span>
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
              <span>Skema SQLite</span>
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
              <span>Panduan Windows</span>
            </button>
          </nav>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Status Banner */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 border border-emerald-200">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900">Tahap 4: Kalender Kerja & Pembentukan Absensi Harian Aktif</h2>
                <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded">
                  Status Kehadiran Matched
                </span>
                <span className="text-[10px] bg-blue-100 text-blue-800 font-bold px-2 py-0.5 rounded">
                  Jam Kerja Dinamis (08:15 - 16:30 / 17:00)
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Modul Kalender Kerja menetapkan hari operasional wajib dan akhir pekan, sementara Modul Absensi Harian memadukan data Master Karyawan Aktif x Kalender Kerja x Transaksi Mentah menjadi record <code>attendance_daily</code> dengan status kehadiran dan deteksi scan tanpa menghitung nominal rupiah potongan (disimpan untuk Tahap 5).
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-600 font-mono bg-slate-50 px-3 py-2 rounded-lg border border-slate-200">
            <span>Entry Point:</span>
            <strong className="text-blue-700">python main.py</strong>
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
            <span>Tahap 1: Fondasi Selesai</span>
            <span>&bull;</span>
            <span className="text-emerald-600 font-semibold">Tahap 2: Master Karyawan Selesai</span>
            <span>&bull;</span>
            <span className="text-blue-600">Tahap 3: Mesin Absensi & Potongan</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
