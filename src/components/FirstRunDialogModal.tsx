import React, { useState } from 'react';
import { X, Shield, Lock, CheckCircle2, AlertCircle, ArrowRight } from 'lucide-react';
import { UserSession } from '../types';

interface FirstRunDialogModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserSession;
  onAddAuditLog: (action: string, module: string, description: string) => void;
}

export const FirstRunDialogModal: React.FC<FirstRunDialogModalProps> = ({
  isOpen,
  onClose,
  currentUser,
  onAddAuditLog
}) => {
  const [oldPassword, setOldPassword] = useState('Admin@SIAP2025');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!newPassword || newPassword.length < 8) {
      setStatusMsg({
        type: 'error',
        message: 'Kata sandi baru minimal harus 8 karakter.',
      });
      return;
    }

    if (newPassword !== confirmPassword) {
      setStatusMsg({
        type: 'error',
        message: 'Konfirmasi kata sandi baru tidak cocok.',
      });
      return;
    }

    if (newPassword === 'Admin@SIAP2025') {
      setStatusMsg({
        type: 'error',
        message: 'Kata sandi baru tidak boleh sama dengan kata sandi bawaan pabrik.',
      });
      return;
    }

    setStatusMsg({
      type: 'success',
      message: 'Kata sandi Administrator berhasil diperbarui! Keamanan sistem siap digunakan.',
    });

    onAddAuditLog(
      'UPDATE_PASSWORD',
      'SECURITY',
      'Administrator mengubah kata sandi bawaan pabrik melalui First-Run Setup Wizard.'
    );

    setTimeout(() => {
      onClose();
    }, 1800);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header Sesuai PySide6 FirstRunSetupDialog */}
        <div className="bg-slate-900 text-white p-5 relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-slate-400 hover:text-white transition cursor-pointer p-1 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white shadow">
              <Shield className="w-5 h-5 text-emerald-300" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Selamat Datang di SIAP</h3>
              <p className="text-xs text-blue-300">
                Konfigurasi Awal & Proteksi Keamanan Administrator
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {/* Quick Workflow Guide */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Ringkasan Alur Kerja Operasional:
            </h4>
            <ol className="text-xs text-slate-600 space-y-1.5 list-decimal pl-4">
              <li><strong>Master Karyawan:</strong> Pastikan data NIP dan PIN Fingerprint sesuai.</li>
              <li><strong>Kalender Kerja:</strong> Generate jadwal hari kerja bulanan dan tandai libur.</li>
              <li><strong>Import Absensi:</strong> Unggah berkas Excel (.xlsx) scan log mesin.</li>
              <li><strong>Hitung Potongan:</strong> Bentuk absensi harian dan nominal denda secara otomatis.</li>
              <li><strong>Laporan & Backup:</strong> Ekspor rekapitulasi ke Excel/PDF dan backup rutin.</li>
            </ol>
          </div>

          {/* Warning Banner */}
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-xs text-amber-900 leading-relaxed">
              Akun <strong>{currentUser.username}</strong> saat ini masih menggunakan kata sandi awal default (<code>Admin@SIAP2025</code>). Sangat dianjurkan untuk mengganti kata sandi sekarang demi keamanan data presensi.
            </p>
          </div>

          {statusMsg && (
            <div
              className={`p-3 rounded-xl text-xs flex items-center gap-2 border ${
                statusMsg.type === 'success'
                  ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
                  : 'bg-red-50 text-red-900 border-red-200'
              }`}
            >
              {statusMsg.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              )}
              <span>{statusMsg.message}</span>
            </div>
          )}

          {/* Form Ganti Password */}
          <form onSubmit={handleSubmit} className="space-y-3 pt-1">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Kata Sandi Bawaan Saat Ini
              </label>
              <input
                type="text"
                disabled
                value={oldPassword}
                className="w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-lg text-xs font-mono text-slate-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Kata Sandi Baru (Min. 8 Karakter)
              </label>
              <input
                type="password"
                required
                placeholder="Masukkan kata sandi baru yang kuat"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Konfirmasi Kata Sandi Baru
              </label>
              <input
                type="password"
                required
                placeholder="Ulangi kata sandi baru"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="pt-2 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition cursor-pointer"
              >
                Nanti Saja
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-xs font-bold transition flex items-center gap-1.5 shadow cursor-pointer"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>Simpan Kata Sandi Baru</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
