import React, { useState } from 'react';
import { FileCode, Copy, Check, Folder, Terminal, Download } from 'lucide-react';
import { PROJECT_STRUCTURE, ProjectFile } from '../data/projectFiles';

export default function CodeExplorer() {
  const [selectedFile, setSelectedFile] = useState<ProjectFile>(PROJECT_STRUCTURE[0]);
  const [copied, setCopied] = useState(false);

  // We can fetch or provide code sample for the selected file
  const handleCopy = () => {
    navigator.clipboard.writeText(`siap_presensi/${selectedFile.path}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col md:flex-row min-h-[560px]">
      {/* File Tree Sidebar */}
      <div className="w-full md:w-80 bg-slate-900 text-slate-300 p-4 border-r border-slate-800 flex flex-col">
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Folder className="w-4 h-4 text-blue-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200">siap_presensi/</span>
          </div>
          <span className="text-[11px] bg-slate-800 text-blue-300 px-2 py-0.5 rounded font-mono">
            {PROJECT_STRUCTURE.length} Files
          </span>
        </div>

        <div className="space-y-1 overflow-y-auto flex-1 pr-1">
          {PROJECT_STRUCTURE.map((file) => {
            const isSelected = selectedFile.path === file.path;
            return (
              <button
                key={file.path}
                onClick={() => setSelectedFile(file)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs flex items-center gap-2 transition cursor-pointer ${
                  isSelected
                    ? 'bg-blue-600 text-white font-semibold shadow-sm'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <FileCode className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-white' : 'text-slate-400'}`} />
                <span className="truncate font-mono">{file.filename}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Code Details & Metadata */}
      <div className="flex-1 flex flex-col bg-slate-50">
        {/* Header Bar */}
        <div className="p-4 bg-white border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 uppercase tracking-wide">
                {selectedFile.category}
              </span>
              <h3 className="font-mono text-sm font-bold text-slate-900">{selectedFile.path}</h3>
            </div>
            <p className="text-xs text-slate-500 mt-1">{selectedFile.description}</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md border border-slate-300 transition cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Path Tersalin!' : 'Salin Path'}</span>
            </button>
          </div>
        </div>

        {/* Code Content Area */}
        <div className="flex-1 p-6 font-mono text-xs overflow-auto bg-slate-950 text-slate-200">
          <div className="mb-4 pb-3 border-b border-slate-800 flex items-center justify-between text-slate-400">
            <span># Path Berkas Asli: {selectedFile.path}</span>
            <span>Bahasa: {selectedFile.language.toUpperCase()}</span>
          </div>

          <div className="text-slate-300 leading-relaxed whitespace-pre-wrap">
            {selectedFile.filename === 'main.py' && `"""
Titik Masuk Utama (Entry Point) Aplikasi Desktop SIAP.
SISTEM INFORMASI ADMINISTRASI PRESENSI
Mengatur inisialisasi database SQLite, lifecycle Qt Application,
penanganan unhandled exception hook, dan alur autentikasi login.
"""
from PySide6.QtWidgets import QApplication, QMessageBox
from database.connection import init_db
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

def main():
    init_db()  # Inisialisasi SQLite & Seed otomatis
    app = QApplication(sys.argv)
    controller = ApplicationController()
    controller.start()
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())`}

            {selectedFile.filename === 'models.py' && `class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.OPERATOR)

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    emp_num = Column(String(50), nullable=True)
    nik = Column(String(50), nullable=True)
    nama = Column(String(150), nullable=False)
    status = Column(Enum(EmployeeStatus), default=EmployeeStatus.AKTIF)

class AttendanceDaily(Base):
    __tablename__ = "attendance_daily"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    tanggal = Column(Date, nullable=False)
    total_potongan = Column(Numeric(12, 2), default=0.0)`}

            {selectedFile.filename === 'test_database.py' && `class TestSiapDatabaseTahap1(unittest.TestCase):
    def test_01_database_and_tables_creation(self):
        # Memverifikasi 8 tabel: users, employees, attendance_raw,
        # attendance_daily, calendar, settings, import_logs, audit_logs
        ...

    def test_02_seed_initial_users(self):
        # Memverifikasi akun admin & operator
        ...

    def test_03_password_hashing_and_verification(self):
        # Memverifikasi bcrypt & PBKDF2 hash
        ...`}

            {selectedFile.filename !== 'main.py' && selectedFile.filename !== 'models.py' && selectedFile.filename !== 'test_database.py' && `/* Berkas ${selectedFile.filename} tersimpan lengkap di direktori container:
   /${selectedFile.path}
   Siap dieksekusi atau di-bundle menggunakan PyInstaller untuk Windows offline. */`}
          </div>
        </div>
      </div>
    </div>
  );
}
