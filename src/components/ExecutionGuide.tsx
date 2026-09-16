import React, { useState } from 'react';
import { Terminal, Copy, Check, Play, Shield, PackageCheck, FileText } from 'lucide-react';

export default function ExecutionGuide() {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyText = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const steps = [
    {
      id: 'step-1',
      title: '1. Buat Virtual Environment Python',
      desc: 'Buka PowerShell / Command Prompt di folder siap_presensi dan buat venv lokal terisolasi:',
      cmd: 'cd siap_presensi\npython -m venv .venv',
    },
    {
      id: 'step-2',
      title: '2. Aktifkan Virtual Environment di Windows',
      desc: 'Jalankan skrip aktivasi venv Windows:',
      cmd: '.venv\\Scripts\\activate',
    },
    {
      id: 'step-3',
      title: '3. Instal Seluruh Dependensi (requirements.txt)',
      desc: 'Menginstal PySide6, SQLAlchemy, Alembic, bcrypt, pandas, openpyxl, reportlab, dll:',
      cmd: 'pip install --upgrade pip\npip install -r requirements.txt',
    },
    {
      id: 'step-4',
      title: '4. Jalankan Aplikasi Desktop SIAP',
      desc: 'Bootstrap inisialisasi SQLite database, auto-seeding akun admin/operator, dan membuka Login Window:',
      cmd: 'python main.py',
    },
    {
      id: 'step-5',
      title: '5. Jalankan Suite Pengujian (Unit & Integrasi Tahap 1 & 2)',
      desc: 'Memverifikasi seluruh parameter database, autentikasi, dan modul Master Karyawan (CRUD, validasi, deteksi duplikat, soft delete, proteksi relasi absensi, dan import/export):',
      cmd: 'python -m unittest discover tests -v',
    },
    {
      id: 'step-6',
      title: '6. Pengujian Spesifik Modul Master Karyawan (Tahap 2)',
      desc: 'Menjalankan 10 test case khusus layanan EmployeeService dan EmployeeImportService:',
      cmd: 'python -m unittest tests/test_employees.py -v',
    },
    {
      id: 'step-7',
      title: '7. Kompilasi Menjadi File Windows Executable (.EXE)',
      desc: 'Membuat paket installer standalone tanpa perlu instalasi Python di komputer klien:',
      cmd: 'pyinstaller --noconfirm --onedir --windowed --name "SIAP_Presensi" main.py',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Terminal className="w-5 h-5 text-blue-600" />
            Panduan Eksekusi Aplikasi Desktop Windows
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Instruksi operasional langsung untuk menjalankan aplikasi SIAP secara offline di lingkungan sistem operasi Windows.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {steps.map((step) => (
          <div key={step.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div>
              <h3 className="font-bold text-slate-800 text-sm mb-1">{step.title}</h3>
              <p className="text-xs text-slate-500 mb-3">{step.desc}</p>
            </div>

            <div className="relative group bg-slate-900 rounded-lg p-3 font-mono text-xs text-slate-200 border border-slate-800">
              <pre className="overflow-x-auto whitespace-pre-wrap">{step.cmd}</pre>
              <button
                onClick={() => copyText(step.id, step.cmd)}
                className="absolute top-2 right-2 p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
                title="Salin Perintah"
              >
                {copiedId === step.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Akun Awal Banner */}
      <div className="bg-slate-900 text-slate-200 p-5 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h4 className="font-bold text-white text-sm flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-400" />
            Kredensial Akun Bawaan Sistem (Seeded Database)
          </h4>
          <p className="text-xs text-slate-400 mt-1">
            Sistem otomatis men-generate dua akun dengan password ter-hash saat pertama kali <code>python main.py</code> dijalankan:
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
          <div className="bg-slate-800 px-3 py-2 rounded border border-slate-700">
            <span className="text-blue-400 font-bold block font-sans">ADMINISTRATOR:</span>
            <span>admin</span> / <span className="text-emerald-400">Admin@SIAP2025</span>
          </div>
          <div className="bg-slate-800 px-3 py-2 rounded border border-slate-700">
            <span className="text-emerald-400 font-bold block font-sans">OPERATOR:</span>
            <span>operator</span> / <span className="text-emerald-400">Operator@SIAP2025</span>
          </div>
        </div>
      </div>
    </div>
  );
}
