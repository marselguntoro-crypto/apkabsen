import React from 'react';
import { X, Info, HardDrive, FileText, CheckCircle2, Copy, Check, ExternalLink } from 'lucide-react';

interface AboutDialogModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AboutDialogModal: React.FC<AboutDialogModalProps> = ({ isOpen, onClose }) => {
  const [copiedKey, setCopiedKey] = React.useState<string | null>(null);

  if (!isOpen) return null;

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-xl w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header Biru Navy Resmi (Sesuai PySide6 AboutDialog) */}
        <div className="bg-slate-900 text-white p-6 relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-slate-400 hover:text-white transition cursor-pointer p-1 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center font-extrabold text-2xl shadow-md text-white border border-blue-400/40">
              S
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-black tracking-wider text-white">SIAP</h2>
                <span className="text-[10px] bg-blue-500/20 text-blue-300 border border-blue-400/40 px-2 py-0.5 rounded font-mono font-bold">
                  v1.0.0
                </span>
              </div>
              <p className="text-xs text-blue-400 font-semibold mt-0.5">
                Sistem Informasi Administrasi Presensi
              </p>
              <p className="text-[11px] text-slate-400">
                Aplikasi Desktop Manajemen Presensi, Kalender Kerja & Rekapitulasi Potongan
              </p>
            </div>
          </div>
        </div>

        {/* Isi Dialog */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* Spesifikasi Rilis */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Info className="w-4 h-4 text-blue-600" />
              Spesifikasi Rilis & Runtime
            </h4>
            <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-xl border border-slate-200">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Versi Rilis</span>
                <span className="font-bold text-slate-800">1.0.0 (Final Release)</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Versi Basis Data</span>
                <span className="font-bold text-blue-700">1.0.0 (SQLite 3 WAL)</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Arsitektur Target</span>
                <span className="font-bold text-slate-800">Windows 10 / 11 (64-bit)</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">GUI Framework</span>
                <span className="font-bold text-slate-800">PySide6 (Qt 6.8+ AMD64)</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Tahun Rilis</span>
                <span className="font-bold text-slate-800">2026</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Pengembang</span>
                <span className="font-bold text-slate-800">Tim Pengembang SIAP</span>
              </div>
            </div>
          </div>

          {/* Diagnosa Lokasi Direktori Windows (%LOCALAPPDATA%\SIAP) */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-emerald-600" />
              Diagnosa Jalur Runtime Windows
            </h4>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-2.5 text-xs font-mono">
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-sans text-[10px] font-bold text-slate-500 uppercase">Folder Data Pengguna:</span>
                  <button
                    onClick={() => handleCopy('%LOCALAPPDATA%\\SIAP', 'data-dir')}
                    className="text-slate-400 hover:text-blue-600 font-sans text-[10px] flex items-center gap-1 cursor-pointer"
                  >
                    {copiedKey === 'data-dir' ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                    <span>Salin</span>
                  </button>
                </div>
                <div className="text-blue-700 bg-white p-1.5 rounded border border-slate-200 mt-1 truncate">
                  %LOCALAPPDATA%\SIAP
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <span className="font-sans text-[10px] font-bold text-slate-500 uppercase">Berkas Database Aktif:</span>
                  <button
                    onClick={() => handleCopy('%LOCALAPPDATA%\\SIAP\\database\\siap_presensi.db', 'db-file')}
                    className="text-slate-400 hover:text-blue-600 font-sans text-[10px] flex items-center gap-1 cursor-pointer"
                  >
                    {copiedKey === 'db-file' ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                    <span>Salin</span>
                  </button>
                </div>
                <div className="text-emerald-700 bg-white p-1.5 rounded border border-slate-200 mt-1 truncate">
                  %LOCALAPPDATA%\SIAP\database\siap_presensi.db
                </div>
              </div>

              <div className="pt-1 flex items-center gap-2 text-[11px] font-sans text-slate-500">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                <span>Status Izin Folder: Read/Write Terisolasi (Non-Admin Compliant)</span>
              </div>
            </div>
          </div>

          {/* Buku Panduan Resmi PDF */}
          <div className="p-3.5 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <FileText className="w-5 h-5 text-blue-700 shrink-0" />
              <div>
                <h5 className="text-xs font-bold text-blue-950">Buku Panduan Pengguna Resmi (PDF)</h5>
                <p className="text-[11px] text-blue-800">
                  Tersedia berkas panduan operasional 18 halaman di root project: <code>PANDUAN_PENGGUNA_SIAP.pdf</code>
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition cursor-pointer"
          >
            Tutup Dialog
          </button>
        </div>
      </div>
    </div>
  );
};
