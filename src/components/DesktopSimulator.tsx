import React, { useState } from 'react';
import { 
  BarChart3, 
  Users, 
  FileSpreadsheet, 
  Clock, 
  Calendar, 
  FileText, 
  Settings, 
  Database, 
  LogOut, 
  RotateCw, 
  Save, 
  ShieldAlert, 
  CheckCircle2, 
  FolderDown, 
  AlertTriangle,
  Info,
  KeyRound,
  Lock,
  User as UserIcon,
  Monitor,
  PackageCheck,
  Smartphone
} from 'lucide-react';
import { 
  UserRole, 
  UserSession, 
  SystemSettings, 
  BackupItem, 
  AuditLogItem, 
  AttendanceRawItem, 
  ImportBatchLogItem, 
  EmployeeItem,
  WorkCalendarItem,
  DailyAttendanceItem,
  AttendanceDeductionItem
} from '../types';
import { EmployeesSimulatorView } from './EmployeesSimulatorView';
import { ImportAttendanceSimulatorView } from './ImportAttendanceSimulatorView';
import { RawAttendanceSimulatorView } from './RawAttendanceSimulatorView';
import { CalendarSimulatorView } from './CalendarSimulatorView';
import { DailyAttendanceSimulatorView } from './DailyAttendanceSimulatorView';
import { DeductionSimulatorView } from './DeductionSimulatorView';
import { BuildDeploymentSimulatorView } from './BuildDeploymentSimulatorView';
import { AboutDialogModal } from './AboutDialogModal';
import { FirstRunDialogModal } from './FirstRunDialogModal';
import InstallAppModal from './InstallAppModal';

export default function DesktopSimulator() {
  // Authentication State
  const [session, setSession] = useState<UserSession | null>(null);
  const [loginUsername, setLoginUsername] = useState('admin');
  const [loginPassword, setLoginPassword] = useState('Admin@SIAP2025');
  const [loginError, setLoginError] = useState('');

  // Modals Tahap 6 & PWA
  const [showAboutDialog, setShowAboutDialog] = useState<boolean>(false);
  const [showFirstRunDialog, setShowFirstRunDialog] = useState<boolean>(false);
  const [showInstallModal, setShowInstallModal] = useState<boolean>(false);

  // Navigation State
  const [activeMenu, setActiveMenu] = useState<string>('dashboard');

  // Dashboard Filters
  const [selectedMonth, setSelectedMonth] = useState('9'); // September
  const [selectedYear, setSelectedYear] = useState('2025');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Settings State
  const [settings, setSettings] = useState<SystemSettings>({
    target_hari_kerja_bulanan: '18',
    jam_masuk_senin_kamis: '08:15',
    jam_pulang_senin_kamis: '16:30',
    jam_masuk_jumat: '08:15',
    jam_pulang_jumat: '17:00',
    potongan_terlambat_sd_1jam: '7500',
    potongan_terlambat_gt_1jam: '10000',
    potongan_pulang_cepat: '10000',
    potongan_tidak_absen_masuk: '10000',
    potongan_tidak_absen_pulang: '10000',
    potongan_tidak_hadir: '20000',
  });
  const [settingsStatus, setSettingsStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Backups State
  const [backups, setBackups] = useState<BackupItem[]>([
    {
      filename: 'backup_siap_20250915_083012.db',
      size: '24.5 KB',
      timestamp: '2025-09-15 08:30:12',
      filepath: 'C:\\siap_presensi\\data\\backups\\backup_siap_20250915_083012.db',
    },
  ]);
  const [backupNotice, setBackupNotice] = useState<string | null>(null);

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([
    { id: 1, time: '2025-09-15 08:00:00', user: 'SYSTEM', action: 'INITIAL_SEED', module: 'DATABASE', description: 'Inisialisasi database SQLite dan akun admin/operator bawaan.' },
  ]);

  // Phase 3: Raw Attendance & Import Batch Logs
  const [rawAttendanceList, setRawAttendanceList] = useState<AttendanceRawItem[]>([
    {
      id: 1,
      emp_num: '1',
      no_id: '1',
      nik: '3201010001',
      nama: 'AHMAD SUJATMIKO',
      tanggal: '2026-08-03',
      scan_masuk: '07:54:00',
      scan_pulang: '16:30:00',
      source_file: 'AGUSTUS 2026.xlsx',
      import_batch_id: 'BATCH-20260801-001',
      created_at: '2026-08-04 09:12:00',
    },
    {
      id: 2,
      emp_num: '2',
      no_id: '2',
      nik: '3201010002',
      nama: 'BUDI SANTOSO',
      tanggal: '2026-08-03',
      scan_masuk: '08:02:00',
      scan_pulang: null,
      source_file: 'AGUSTUS 2026.xlsx',
      import_batch_id: 'BATCH-20260801-001',
      created_at: '2026-08-04 09:12:00',
    },
    {
      id: 3,
      emp_num: '3',
      no_id: '3',
      nik: '3201010003',
      nama: 'CITRA LESTARI',
      tanggal: '2026-08-03',
      scan_masuk: null,
      scan_pulang: '16:45:00',
      source_file: 'AGUSTUS 2026.xlsx',
      import_batch_id: 'BATCH-20260801-001',
      created_at: '2026-08-04 09:12:00',
    },
    {
      id: 4,
      emp_num: '4',
      no_id: '4',
      nik: '3201010004',
      nama: 'DEDDY KURNIAWAN',
      tanggal: '2026-08-03',
      scan_masuk: '07:50:00',
      scan_pulang: '16:32:00',
      source_file: 'AGUSTUS 2026.xlsx',
      import_batch_id: 'BATCH-20260801-001',
      created_at: '2026-08-04 09:12:00',
    },
  ]);

  const [batchLogs, setBatchLogs] = useState<ImportBatchLogItem[]>([
    {
      id: 1,
      import_batch_id: 'BATCH-20260801-001',
      user_id: 1,
      user_name: 'Administrator Utama',
      file_name: 'AGUSTUS 2026.xlsx',
      import_type: 'EXCEL_ABSENSI',
      periode: 'Agustus 2026',
      total_rows: 4,
      success_rows: 4,
      failed_rows: 0,
      duplicate_rows: 0,
      status: 'SUCCESS',
      created_at: '2026-08-04 09:12:00',
    },
  ]);

  const [simulatedEmployees, setSimulatedEmployees] = useState<EmployeeItem[]>([
    {
      id: 1,
      emp_num: '1',
      no_id: '1',
      nik: '3201010001',
      nama: 'AHMAD SUJATMIKO',
      unit: 'Teknologi Informasi',
      jabatan: 'Software Engineer',
      email: 'ahmad.sujatmiko@perusahaan.co.id',
      keterangan: 'Karyawan tetap',
      status: 'AKTIF',
      tanggal_mulai: '2022-01-10',
      created_at: '2022-01-10 08:00',
    },
    {
      id: 2,
      emp_num: '2',
      no_id: '2',
      nik: '3201010002',
      nama: 'BUDI SANTOSO',
      unit: 'Keuangan & Akuntansi',
      jabatan: 'Staff Pajak',
      email: 'budi.santoso@perusahaan.co.id',
      keterangan: 'Karyawan tetap',
      status: 'AKTIF',
      tanggal_mulai: '2022-03-01',
      created_at: '2022-03-01 08:30',
    },
    {
      id: 3,
      emp_num: '3',
      no_id: '3',
      nik: '3201010003',
      nama: 'CITRA LESTARI',
      unit: 'Sumber Daya Manusia',
      jabatan: 'HR Officer',
      email: 'citra.lestari@perusahaan.co.id',
      keterangan: 'Karyawan tetap',
      status: 'AKTIF',
      tanggal_mulai: '2023-02-01',
      created_at: '2023-02-01 09:00',
    },
    {
      id: 4,
      emp_num: '4',
      no_id: '4',
      nik: '3201010004',
      nama: 'DEDDY KURNIAWAN',
      unit: 'Operasional',
      jabatan: 'Koordinator Lapangan',
      email: 'deddy.kurniawan@perusahaan.co.id',
      keterangan: 'Karyawan tetap',
      status: 'AKTIF',
      tanggal_mulai: '2021-06-15',
      created_at: '2021-06-15 08:00',
    },
  ]);

  // Phase 4: Attendance Tab Switcher ('daily' | 'raw')
  const [attendanceSubTab, setAttendanceSubTab] = useState<'daily' | 'raw'>('daily');

  // Phase 4: Initial Work Calendar Data (Agustus 2026)
  const [calendarData, setCalendarData] = useState<WorkCalendarItem[]>(() => {
    const days: WorkCalendarItem[] = [];
    const dayNames = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
    for (let d = 1; d <= 31; d++) {
      const padD = String(d).padStart(2, '0');
      const dateStr = `2026-08-${padD}`;
      const dt = new Date(2026, 7, d);
      const dow = dt.getDay();
      let st: any = 'HARI_KERJA';
      let isW = true;
      let inTime: string | null = '08:15';
      let outTime: string | null = dow === 5 ? '17:00' : '16:30';
      let desc = '';

      if (dow === 0 || dow === 6) {
        st = 'AKHIR_PEKAN';
        isW = false;
        inTime = null;
        outTime = null;
      }
      if (d === 17) {
        st = 'LIBUR_NASIONAL';
        isW = false;
        inTime = null;
        outTime = null;
        desc = 'Hari Kemerdekaan Republik Indonesia ke-81';
      }

      days.push({
        id: 20260800 + d,
        calendar_date: dateStr,
        day_name: dayNames[dow],
        day_of_week: dow,
        month: 8,
        year: 2026,
        calendar_status: st,
        is_working_day: isW,
        scheduled_check_in: inTime,
        scheduled_check_out: outTime,
        description: desc,
      });
    }
    return days;
  });

  // Phase 4: Initial Daily Attendance Records (Dipadukan dari Karyawan x Kalender x Raw)
  const [dailyAttendanceList, setDailyAttendanceList] = useState<DailyAttendanceItem[]>([
    {
      id: 120260803,
      employee_id: 1,
      emp_num: '1',
      no_id: '1',
      nik: '3201010001',
      nama: 'AHMAD SUJATMIKO',
      unit: 'Teknologi Informasi',
      jabatan: 'Software Engineer',
      attendance_date: '2026-08-03',
      day_name: 'Senin',
      scheduled_check_in: '08:15',
      scheduled_check_out: '16:30',
      actual_check_in: '07:54',
      actual_check_out: '16:30',
      check_in_status: 'ADA',
      check_out_status: 'ADA',
      attendance_status: 'HADIR_LENGKAP',
      has_incomplete_scan: false,
      has_conflict: false,
      notes: '',
    },
    {
      id: 220260803,
      employee_id: 2,
      emp_num: '2',
      no_id: '2',
      nik: '3201010002',
      nama: 'BUDI SANTOSO',
      unit: 'Keuangan',
      jabatan: 'Staff Akuntansi',
      attendance_date: '2026-08-03',
      day_name: 'Senin',
      scheduled_check_in: '08:15',
      scheduled_check_out: '16:30',
      actual_check_in: '08:02',
      actual_check_out: null,
      check_in_status: 'ADA',
      check_out_status: 'TIDAK_ADA',
      attendance_status: 'HANYA_ABSEN_MASUK',
      has_incomplete_scan: true,
      has_conflict: false,
      notes: 'Scan pulang tidak ditemukan',
    },
    {
      id: 320260803,
      employee_id: 3,
      emp_num: '3',
      no_id: '3',
      nik: '3201010003',
      nama: 'CITRA LESTARI',
      unit: 'Kepegawaian (SDM)',
      jabatan: 'HR Officer',
      attendance_date: '2026-08-03',
      day_name: 'Senin',
      scheduled_check_in: '08:15',
      scheduled_check_out: '16:30',
      actual_check_in: null,
      actual_check_out: '16:45',
      check_in_status: 'TIDAK_ADA',
      check_out_status: 'ADA',
      attendance_status: 'HANYA_ABSEN_PULANG',
      has_incomplete_scan: true,
      has_conflict: false,
      notes: 'Scan masuk tidak ditemukan',
    },
    {
      id: 420260803,
      employee_id: 4,
      emp_num: '4',
      no_id: '4',
      nik: '3201010004',
      nama: 'DEDDY KURNIAWAN',
      unit: 'Operasional',
      jabatan: 'Koordinator Lapangan',
      attendance_date: '2026-08-03',
      day_name: 'Senin',
      scheduled_check_in: '08:15',
      scheduled_check_out: '16:30',
      actual_check_in: '07:50',
      actual_check_out: '16:32',
      check_in_status: 'ADA',
      check_out_status: 'ADA',
      attendance_status: 'HADIR_LENGKAP',
      has_incomplete_scan: false,
      has_conflict: false,
      notes: '',
    },
  ]);

  // Deductions State (Tahap 5)
  const [deductionsList, setDeductionsList] = useState<AttendanceDeductionItem[]>([
    {
      id: 1,
      daily_attendance_id: 120260803,
      employee_id: 1,
      emp_num: '1',
      no_id: '1',
      nik: '3201010001',
      nama: 'AHMAD FAUZI',
      unit: 'Teknologi Informasi (TI)',
      jabatan: 'Senior Software Engineer',
      attendance_date: '2026-08-03',
      day_name: 'Senin',
      scheduled_check_in: '08:15',
      scheduled_check_out: '16:30',
      actual_check_in: '08:35',
      actual_check_out: '16:30',
      attendance_status: 'HADIR_LENGKAP',
      is_working_day: true,
      late_minutes: 20,
      early_leave_minutes: 0,
      deduction_late: 7500,
      deduction_early_leave: 0,
      deduction_missing_check_in: 0,
      deduction_missing_check_out: 0,
      total_deduction: 7500,
      calculation_version: '5.0.0',
      calculated_at: '2026-08-03 17:00:00',
      notes: 'Terlambat 20 mnt (Rp7.500). Pulang tepat waktu.',
    },
    {
      id: 2,
      daily_attendance_id: 220260803,
      employee_id: 2,
      emp_num: '2',
      no_id: '2',
      nik: '3201010002',
      nama: 'BUDI SANTOSO',
      unit: 'Keuangan',
      jabatan: 'Staff Akuntansi',
      attendance_date: '2026-08-03',
      day_name: 'Senin',
      scheduled_check_in: '08:15',
      scheduled_check_out: '16:30',
      actual_check_in: '08:02',
      actual_check_out: null,
      attendance_status: 'HANYA_ABSEN_MASUK',
      is_working_day: true,
      late_minutes: 0,
      early_leave_minutes: 0,
      deduction_late: 0,
      deduction_early_leave: 0,
      deduction_missing_check_in: 0,
      deduction_missing_check_out: 10000,
      total_deduction: 10000,
      calculation_version: '5.0.0',
      calculated_at: '2026-08-03 17:00:00',
      notes: 'Hanya scan masuk (08:02). Tidak scan pulang (Rp10.000).',
    },
    {
      id: 3,
      daily_attendance_id: 320260803,
      employee_id: 3,
      emp_num: '3',
      no_id: '3',
      nik: '3201010003',
      nama: 'CITRA LESTARI',
      unit: 'Kepegawaian (SDM)',
      jabatan: 'HR Officer',
      attendance_date: '2026-08-03',
      day_name: 'Senin',
      scheduled_check_in: '08:15',
      scheduled_check_out: '16:30',
      actual_check_in: null,
      actual_check_out: '16:45',
      attendance_status: 'HANYA_ABSEN_PULANG',
      is_working_day: true,
      late_minutes: 0,
      early_leave_minutes: 0,
      deduction_late: 0,
      deduction_early_leave: 0,
      deduction_missing_check_in: 10000,
      deduction_missing_check_out: 0,
      total_deduction: 10000,
      calculation_version: '5.0.0',
      calculated_at: '2026-08-03 17:00:00',
      notes: 'Hanya scan pulang (16:45). Tidak scan masuk (Rp10.000).',
    },
    {
      id: 4,
      daily_attendance_id: 420260803,
      employee_id: 4,
      emp_num: '4',
      no_id: '4',
      nik: '3201010004',
      nama: 'DEDDY KURNIAWAN',
      unit: 'Operasional',
      jabatan: 'Koordinator Lapangan',
      attendance_date: '2026-08-03',
      day_name: 'Senin',
      scheduled_check_in: '08:15',
      scheduled_check_out: '16:30',
      actual_check_in: '07:50',
      actual_check_out: '16:32',
      attendance_status: 'HADIR_LENGKAP',
      is_working_day: true,
      late_minutes: 0,
      early_leave_minutes: 0,
      deduction_late: 0,
      deduction_early_leave: 0,
      deduction_missing_check_in: 0,
      deduction_missing_check_out: 0,
      total_deduction: 0,
      calculation_version: '5.0.0',
      calculated_at: '2026-08-03 17:00:00',
      notes: 'Hadir tepat waktu & pulang sesuai jadwal. Bebas potongan.',
    },
  ]);

  // Login Handler
  const handleLogin = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoginError('');

    const u = loginUsername.trim();
    const p = loginPassword;

    if (u === 'admin' && p === 'Admin@SIAP2025') {
      const newSession: UserSession = {
        id: 1,
        username: 'admin',
        fullName: 'Administrator Utama',
        role: 'ADMIN',
        isAuthenticated: true,
        loginTime: new Date().toLocaleTimeString(),
      };
      setSession(newSession);
      setActiveMenu('dashboard');
      addAuditLog('admin', 'LOGIN_SUCCESS', 'AUTH', 'Login berhasil sebagai Administrator.');
      setShowFirstRunDialog(true);
    } else if (u === 'operator' && p === 'Operator@SIAP2025') {
      const newSession: UserSession = {
        id: 2,
        username: 'operator',
        fullName: 'Petugas Presensi',
        role: 'OPERATOR',
        isAuthenticated: true,
        loginTime: new Date().toLocaleTimeString(),
      };
      setSession(newSession);
      setActiveMenu('dashboard');
      addAuditLog('operator', 'LOGIN_SUCCESS', 'AUTH', 'Login berhasil sebagai Petugas Operator.');
    } else {
      setLoginError('Username atau password yang dimasukkan salah.');
    }
  };

  const handleLogout = () => {
    if (window.confirm('Apakah Anda yakin ingin keluar dari sistem SIAP?')) {
      if (session) {
        addAuditLog(session.username, 'LOGOUT', 'AUTH', 'Pengguna logout dari sistem.');
      }
      setSession(null);
      setLoginPassword('');
      setLoginError('');
      setActiveMenu('dashboard');
    }
  };

  const addAuditLog = (user: string, action: string, module: string, description: string) => {
    const newLog: AuditLogItem = {
      id: Date.now(),
      time: new Date().toISOString().replace('T', ' ').substring(0, 19),
      user,
      action,
      module,
      description,
    };
    setAuditLogs(prev => [newLog, ...prev]);
  };

  // Settings Handlers
  const handleSaveSettings = () => {
    // Validasi Jam Format HH:MM
    const timeRegex = /^([01]\d|2[0-3]):([0-5]\d)$/;
    if (
      !timeRegex.test(settings.jam_masuk_senin_kamis) ||
      !timeRegex.test(settings.jam_pulang_senin_kamis) ||
      !timeRegex.test(settings.jam_masuk_jumat) ||
      !timeRegex.test(settings.jam_pulang_jumat)
    ) {
      setSettingsStatus({
        type: 'error',
        message: 'Format jam operasional harus HH:MM (contoh: 08:15 atau 16:30).',
      });
      return;
    }

    const targetDays = parseInt(settings.target_hari_kerja_bulanan, 10);
    if (isNaN(targetDays) || targetDays < 1 || targetDays > 31) {
      setSettingsStatus({
        type: 'error',
        message: 'Target hari kerja bulanan harus bernilai antara 1 sampai 31 hari.',
      });
      return;
    }

    setSettingsStatus({
      type: 'success',
      message: 'Pengaturan sistem berhasil disimpan ke tabel database SQLite (settings).',
    });
    addAuditLog(session?.username || 'admin', 'UPDATE_SETTINGS', 'SETTINGS', 'Pengaturan jam & tarif potongan berhasil diperbarui.');
    setTimeout(() => setSettingsStatus(null), 4000);
  };

  const handleResetSettings = () => {
    setSettings({
      target_hari_kerja_bulanan: '18',
      jam_masuk_senin_kamis: '08:15',
      jam_pulang_senin_kamis: '16:30',
      jam_masuk_jumat: '08:15',
      jam_pulang_jumat: '17:00',
      potongan_terlambat_sd_1jam: '7500',
      potongan_terlambat_gt_1jam: '10000',
      potongan_pulang_cepat: '10000',
      potongan_tidak_absen_masuk: '10000',
      potongan_tidak_absen_pulang: '10000',
      potongan_tidak_hadir: '20000',
    });
    setSettingsStatus({
      type: 'success',
      message: 'Nilai form dikembalikan ke pengaturan default pabrik.',
    });
    setTimeout(() => setSettingsStatus(null), 3000);
  };

  // Backup Handler
  const handleCreateBackup = () => {
    const now = new Date();
    const pad = (n: number) => String(n).padStart(2, '0');
    const ts = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
    const filename = `backup_siap_${ts}.db`;
    const newBackup: BackupItem = {
      filename,
      size: '24.8 KB',
      timestamp: now.toISOString().replace('T', ' ').substring(0, 19),
      filepath: `C:\\siap_presensi\\data\\backups\\${filename}`,
    };
    setBackups(prev => [newBackup, ...prev]);
    setBackupNotice(`Cadangan SQLite baru berhasil dibuat: ${filename} (Integritas OK)`);
    addAuditLog(session?.username || 'admin', 'BACKUP_DATABASE', 'DATABASE', `Backup database SQLite ke ${filename}`);
    setTimeout(() => setBackupNotice(null), 4500);
  };

  const monthsList = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
  ];

  return (
    <div className="w-full bg-slate-900/90 p-2 sm:p-4 rounded-xl border border-slate-800 shadow-2xl">
      {/* OS Window Frame Header */}
      <div className="bg-slate-950 text-slate-300 px-4 py-2.5 rounded-t-lg border-b border-slate-800 flex items-center justify-between select-none">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-500/80 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-yellow-500/80 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-green-500/80 inline-block"></span>
          </div>
          <span className="text-xs font-mono text-slate-400 ml-2">PySide6 Desktop Application Runner (Windows 1366x768 Window Frame)</span>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1 bg-slate-800 px-2 py-0.5 rounded text-[11px] text-emerald-400">
            <Monitor className="w-3 h-3" /> SQLite: siap_presensi.db
          </span>
          <span className="font-semibold text-slate-300">SIAP v1.0.0 (Tahap 1)</span>
        </div>
      </div>

      {/* OS Window Inner Content */}
      <div className="bg-slate-100 min-h-[640px] rounded-b-lg overflow-hidden flex flex-col font-sans text-slate-900 shadow-inner">
        {!session ? (
          /* ========================================================
             LOGIN WINDOW VIEW
             ======================================================== */
          <div className="flex-1 flex items-center justify-center p-6 bg-slate-100">
            <div className="w-full max-w-md bg-white rounded-xl shadow-lg border border-slate-200 p-8">
              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-700 text-white font-black text-2xl mb-3 shadow-md">
                  SIAP
                </div>
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">SISTEM INFORMASI ADMINISTRASI PRESENSI</h1>
                <p className="text-xs text-blue-600 font-semibold mt-0.5">Sistem Pengelolaan Absensi dan Potongan Karyawan</p>
                <p className="text-xs text-slate-500 mt-1">Silakan masuk dengan kredensial terdaftar untuk mengakses sistem.</p>
              </div>

              {loginError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2 text-xs text-red-700">
                  <ShieldAlert className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                  <span>{loginError}</span>
                </div>
              )}

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Username</label>
                  <div className="relative">
                    <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      value={loginUsername}
                      onChange={(e) => setLoginUsername(e.target.value)}
                      placeholder="admin / operator"
                      className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="password"
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      placeholder="Password"
                      className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full py-2.5 px-4 bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold rounded-lg shadow transition cursor-pointer flex items-center justify-center gap-2 mt-2"
                >
                  <KeyRound className="w-4 h-4" /> Masuk ke Sistem (PySide6 Auth)
                </button>
              </form>

              {/* Quick Fill Helpers for Testing */}
              <div className="mt-6 pt-4 border-t border-slate-100">
                <p className="text-[11px] font-semibold text-slate-500 mb-2 uppercase tracking-wide">Kredensial Seed Database Awal:</p>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => { setLoginUsername('admin'); setLoginPassword('Admin@SIAP2025'); }}
                    className="text-left p-2 rounded bg-slate-50 hover:bg-blue-50 border border-slate-200 text-xs transition cursor-pointer"
                  >
                    <span className="font-bold text-blue-700 block">Akun Admin</span>
                    <span className="text-[10px] text-slate-500">admin / Admin@SIAP2025</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { setLoginUsername('operator'); setLoginPassword('Operator@SIAP2025'); }}
                    className="text-left p-2 rounded bg-slate-50 hover:bg-emerald-50 border border-slate-200 text-xs transition cursor-pointer"
                  >
                    <span className="font-bold text-emerald-700 block">Akun Operator</span>
                    <span className="text-[10px] text-slate-500">operator / Operator@SIAP2025</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* ========================================================
             MAIN WINDOW VIEW (SIDEBAR + HEADER + STACKED CONTENT)
             ======================================================== */
          <div className="flex-1 flex flex-row overflow-hidden">
            {/* Sidebar Kiri */}
            <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 border-r border-slate-800 select-none">
              {/* Brand Header */}
              <div className="p-4 border-b border-slate-800">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-extrabold text-lg shadow">
                    S
                  </div>
                  <div>
                    <h2 className="font-bold text-white text-base leading-none">SIAP</h2>
                    <p className="text-[11px] text-blue-400 font-medium mt-0.5">Presensi & Potongan</p>
                  </div>
                </div>
              </div>

              {/* Menu Navigation */}
              <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
                <button
                  onClick={() => setActiveMenu('dashboard')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold text-left transition cursor-pointer ${
                    activeMenu === 'dashboard' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <BarChart3 className="w-4 h-4 shrink-0" />
                  <span>Dashboard Utama</span>
                </button>

                <button
                  onClick={() => setActiveMenu('karyawan')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold text-left transition cursor-pointer ${
                    activeMenu === 'karyawan' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <Users className="w-4 h-4 shrink-0" />
                  <span>Data Karyawan</span>
                </button>

                <button
                  onClick={() => setActiveMenu('import')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold text-left transition cursor-pointer ${
                    activeMenu === 'import' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <FileSpreadsheet className="w-4 h-4 shrink-0" />
                  <span>Import Absensi</span>
                </button>

                <button
                  onClick={() => setActiveMenu('absensi')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold text-left transition cursor-pointer ${
                    activeMenu === 'absensi' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <Clock className="w-4 h-4 shrink-0" />
                  <span>Data Absensi</span>
                </button>

                <button
                  onClick={() => setActiveMenu('kalender')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold text-left transition cursor-pointer ${
                    activeMenu === 'kalender' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <Calendar className="w-4 h-4 shrink-0" />
                  <span>Kalender Kerja</span>
                </button>

                <button
                  onClick={() => setActiveMenu('laporan')}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold text-left transition cursor-pointer ${
                    activeMenu === 'laporan' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <FileText className="w-4 h-4 shrink-0" />
                  <span>Laporan & Rekap</span>
                </button>

                {/* Khusus ADMIN Menu (Sesuai Aturan RBAC Tahap 1) */}
                {session.role === 'ADMIN' && (
                  <>
                    <div className="pt-2 pb-1 px-3 text-[10px] font-bold tracking-wider text-slate-500 uppercase">
                      Administrator
                    </div>

                    <button
                      onClick={() => setActiveMenu('pengaturan')}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold text-left transition cursor-pointer ${
                        activeMenu === 'pengaturan' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <Settings className="w-4 h-4 shrink-0" />
                      <span>Pengaturan Sistem</span>
                    </button>

                    <button
                      onClick={() => setActiveMenu('backup')}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold text-left transition cursor-pointer ${
                        activeMenu === 'backup' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <Database className="w-4 h-4 shrink-0" />
                      <span>Backup Database</span>
                    </button>

                    <button
                      onClick={() => setActiveMenu('build')}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold text-left transition cursor-pointer ${
                        activeMenu === 'build' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <PackageCheck className="w-4 h-4 shrink-0 text-emerald-400" />
                      <span>Build & Rilis Windows</span>
                    </button>
                  </>
                )}
              </nav>

              {/* Sidebar Footer */}
              <div className="p-3 border-t border-slate-800 space-y-2">
                <button
                  onClick={() => setShowInstallModal(true)}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold bg-emerald-700 hover:bg-emerald-600 text-white transition cursor-pointer shadow-xs"
                >
                  <Smartphone className="w-3.5 h-3.5 text-emerald-200" />
                  <span>Pasang APK / Aplikasi</span>
                </button>

                <button
                  onClick={() => setShowAboutDialog(true)}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
                >
                  <Info className="w-3.5 h-3.5 text-blue-400" />
                  <span>Tentang Aplikasi SIAP</span>
                </button>

                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold text-red-400 hover:bg-red-950/50 hover:text-red-300 transition cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Keluar (Logout)</span>
                </button>
                <div className="text-[10px] text-slate-500 text-center">
                  Versi 1.0.0 (Tahap 6: Rilis Windows)
                </div>
              </div>
            </aside>

            {/* Area Konten Utama */}
            <div className="flex-1 flex flex-col overflow-hidden bg-slate-50">
              {/* Header Atas */}
              <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0">
                <div className="flex items-center gap-3">
                  <h3 className="font-bold text-slate-800 text-sm capitalize">
                    {activeMenu === 'dashboard' && 'Dashboard Utama'}
                    {activeMenu === 'karyawan' && 'Master Data Karyawan'}
                    {activeMenu === 'import' && 'Import Berkas Absensi Mesin'}
                    {activeMenu === 'absensi' && 'Data Absensi Harian'}
                    {activeMenu === 'kalender' && 'Kalender Kerja & Hari Libur'}
                    {activeMenu === 'laporan' && 'Laporan Rekapitulasi & Potongan'}
                    {activeMenu === 'pengaturan' && 'Pengaturan Sistem & Parameter'}
                    {activeMenu === 'backup' && 'Pencadangan Database SQLite'}
                    {activeMenu === 'build' && 'Finalisasi Aplikasi, Build Executable (.EXE) & Installer Windows'}
                  </h3>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowInstallModal(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-300 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-semibold shadow-2xs transition cursor-pointer"
                    title="Pasang aplikasi ke Android atau Desktop"
                  >
                    <Smartphone className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="hidden sm:inline">Pasang APK / Aplikasi</span>
                  </button>

                  <button
                    onClick={() => setShowAboutDialog(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition cursor-pointer"
                  >
                    <Info className="w-3.5 h-3.5 text-blue-600" />
                    <span className="hidden sm:inline">Tentang SIAP</span>
                  </button>

                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-extrabold px-2 py-0.5 rounded uppercase tracking-wider ${
                        session.role === 'ADMIN'
                          ? 'bg-blue-100 text-blue-800 border border-blue-200'
                          : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      }`}
                    >
                      {session.role}
                    </span>
                    <span className="text-xs font-semibold text-slate-700">{session.fullName}</span>
                  </div>
                </div>
              </header>

              {/* Isi Halaman Sesuai Navigasi */}
              <main className="flex-1 p-6 overflow-y-auto">
                {/* 1. DASHBOARD PAGE */}
                {activeMenu === 'dashboard' && (
                  <div className="space-y-6 max-w-6xl mx-auto">
                    {/* Filter Periode & Refresh Bar */}
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <h2 className="text-base font-bold text-slate-900">Ringkasan Presensi Pegawai</h2>
                        <p className="text-xs text-slate-500">
                          Periode Aktif: <strong className="text-slate-800">{monthsList[parseInt(selectedMonth) - 1]} {selectedYear}</strong>
                        </p>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600">
                          <span>Bulan:</span>
                          <select
                            value={selectedMonth}
                            onChange={(e) => setSelectedMonth(e.target.value)}
                            className="bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs font-medium focus:ring-1 focus:ring-blue-600 focus:outline-none"
                          >
                            {monthsList.map((m, idx) => (
                              <option key={idx + 1} value={String(idx + 1)}>{m}</option>
                            ))}
                          </select>
                        </div>

                        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600">
                          <span>Tahun:</span>
                          <select
                            value={selectedYear}
                            onChange={(e) => setSelectedYear(e.target.value)}
                            className="bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs font-medium focus:ring-1 focus:ring-blue-600 focus:outline-none"
                          >
                            <option value="2024">2024</option>
                            <option value="2025">2025</option>
                            <option value="2026">2026</option>
                          </select>
                        </div>

                        <button
                          onClick={() => {
                            setIsRefreshing(true);
                            setTimeout(() => setIsRefreshing(false), 400);
                          }}
                          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition cursor-pointer"
                        >
                          <RotateCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                          <span>Refresh</span>
                        </button>
                      </div>
                    </div>

                    {/* 7 Kartu Statistik Tahap 5 */}
                    {(() => {
                      const totalHadirCount = dailyAttendanceList.filter(d => d.attendance_status === 'HADIR_LENGKAP' || d.actual_check_in || d.actual_check_out).length;
                      const totalAlfaCount = dailyAttendanceList.filter(d => d.attendance_status === 'TIDAK_ABSEN').length;
                      const totalTerlambatCount = deductionsList.filter(d => d.late_minutes > 0).length;
                      const totalPulangCepatCount = deductionsList.filter(d => d.early_leave_minutes > 0).length;
                      const totalPotonganRupiah = deductionsList.reduce((acc, d) => acc + d.total_deduction, 0);

                      return (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                          {/* 1. Total Karyawan */}
                          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-blue-400 transition">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Karyawan</span>
                              <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
                            </div>
                            <div className="text-3xl font-extrabold text-slate-900">{simulatedEmployees.length}</div>
                            <p className="text-[11px] text-slate-500 mt-1">Karyawan aktif terdaftar</p>
                          </div>

                          {/* 2. Total Hari Kerja */}
                          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-slate-400 transition">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Hari Kerja</span>
                              <span className="w-2.5 h-2.5 rounded-full bg-slate-700"></span>
                            </div>
                            <div className="text-3xl font-extrabold text-slate-900">{settings.target_hari_kerja_bulanan}</div>
                            <p className="text-[11px] text-slate-500 mt-1">Target acuan hari kerja</p>
                          </div>

                          {/* 3. Total Hadir */}
                          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-emerald-400 transition">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Hadir</span>
                              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                            </div>
                            <div className="text-3xl font-extrabold text-emerald-700">{totalHadirCount}</div>
                            <p className="text-[11px] text-slate-500 mt-1">Presensi berhasil tercatat</p>
                          </div>

                          {/* 4. Total Alfa */}
                          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-red-400 transition">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Alfa</span>
                              <span className="w-2.5 h-2.5 rounded-full bg-red-600"></span>
                            </div>
                            <div className="text-3xl font-extrabold text-red-600">{totalAlfaCount}</div>
                            <p className="text-[11px] text-slate-500 mt-1">Ketidakhadiran tanpa izin</p>
                          </div>

                          {/* 5. Terlambat */}
                          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-amber-400 transition">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Terlambat</span>
                              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                            </div>
                            <div className="text-3xl font-extrabold text-amber-600">{totalTerlambatCount}</div>
                            <p className="text-[11px] text-slate-500 mt-1">Pelanggaran jam masuk</p>
                          </div>

                          {/* 6. Pulang Cepat */}
                          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-amber-400 transition">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Pulang Cepat</span>
                              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                            </div>
                            <div className="text-3xl font-extrabold text-amber-600">{totalPulangCepatCount}</div>
                            <p className="text-[11px] text-slate-500 mt-1">Pelanggaran jam pulang</p>
                          </div>

                          {/* 7. Total Potongan (Span 2 cols on lg) */}
                          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-red-400 transition lg:col-span-2">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Potongan Absensi</span>
                              <span className="w-2.5 h-2.5 rounded-full bg-red-600"></span>
                            </div>
                            <div className="text-3xl font-extrabold text-red-600">
                              Rp {totalPotonganRupiah.toLocaleString('id-ID')}
                            </div>
                            <p className="text-[11px] text-slate-500 mt-1">Akumulasi tarif potongan absensi periode aktif</p>
                          </div>
                        </div>
                      );
                    })()}

                    {/* Banner Transparansi Kondisi Tahap 5 */}
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-xs text-blue-900 flex items-start gap-3">
                      <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-bold text-blue-950 mb-0.5">Kondisi Database Tahap 5: Mesin Perhitungan Potongan & Rekapitulasi Aktif</h4>
                        <p className="text-blue-800 leading-relaxed">
                          Sistem membaca langsung dari database SQLite lokal <code>siap_presensi.db</code>. Seluruh modul Master Karyawan, Import Absensi Excel, Transaksi Raw, Kalender Kerja, Absensi Harian, dan Mesin Kalkulasi Potongan Absensi telah aktif dan terintegrasi penuh. Anda dapat melakukan simulasi hitung potongan, rekapitulasi pegawai, serta peninjauan 17 kolom kalkulasi harian di menu <strong>Laporan & Rekap</strong>.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. PENGATURAN SISTEM PAGE */}
                {activeMenu === 'pengaturan' && (
                  <div className="space-y-6 max-w-5xl mx-auto">
                    {/* Status Alert */}
                    {settingsStatus && (
                      <div className={`p-4 rounded-xl border flex items-center gap-3 text-xs font-medium ${
                        settingsStatus.type === 'success' 
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-800' 
                          : 'bg-red-50 border-red-200 text-red-800'
                      }`}>
                        {settingsStatus.type === 'success' ? (
                          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                        ) : (
                          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0" />
                        )}
                        <span>{settingsStatus.message}</span>
                      </div>
                    )}

                    {/* Section 1: Target Hari Kerja */}
                    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                      <h3 className="font-bold text-slate-800 text-sm mb-3 flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-blue-600" />
                        Pengaturan Hari Kerja
                      </h3>
                      <div className="max-w-xs">
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Target Hari Kerja Bulanan</label>
                        <input
                          type="number"
                          value={settings.target_hari_kerja_bulanan}
                          onChange={(e) => setSettings({ ...settings, target_hari_kerja_bulanan: e.target.value })}
                          className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
                        />
                        <p className="text-[11px] text-slate-500 mt-1">
                          Nilai parameter acuan (default: 18). Kalender kerja riil tetap menjadi dasar kalkulasi pada tahap berikutnya.
                        </p>
                      </div>
                    </div>

                    {/* Section 2: Jam Operasional */}
                    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                      <h3 className="font-bold text-slate-800 text-sm mb-4 flex items-center gap-2">
                        <Clock className="w-4 h-4 text-blue-600" />
                        Jam Operasional Kerja (Format 24-Jam: HH:MM)
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Senin - Kamis */}
                        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
                          <h4 className="text-xs font-bold text-blue-700 uppercase tracking-wide">Senin s/d Kamis</h4>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs text-slate-600 mb-1">Jam Masuk</label>
                              <input
                                type="text"
                                value={settings.jam_masuk_senin_kamis}
                                onChange={(e) => setSettings({ ...settings, jam_masuk_senin_kamis: e.target.value })}
                                className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded bg-white font-mono"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-slate-600 mb-1">Jam Pulang</label>
                              <input
                                type="text"
                                value={settings.jam_pulang_senin_kamis}
                                onChange={(e) => setSettings({ ...settings, jam_pulang_senin_kamis: e.target.value })}
                                className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded bg-white font-mono"
                              />
                            </div>
                          </div>
                        </div>

                        {/* Jumat */}
                        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
                          <h4 className="text-xs font-bold text-blue-700 uppercase tracking-wide">Hari Jumat</h4>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs text-slate-600 mb-1">Jam Masuk</label>
                              <input
                                type="text"
                                value={settings.jam_masuk_jumat}
                                onChange={(e) => setSettings({ ...settings, jam_masuk_jumat: e.target.value })}
                                className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded bg-white font-mono"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-slate-600 mb-1">Jam Pulang</label>
                              <input
                                type="text"
                                value={settings.jam_pulang_jumat}
                                onChange={(e) => setSettings({ ...settings, jam_pulang_jumat: e.target.value })}
                                className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded bg-white font-mono"
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Section 3: Tarif Potongan */}
                    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                      <h3 className="font-bold text-slate-800 text-sm mb-4 flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4 text-blue-600" />
                        Tarif Potongan Pelanggaran (Rupiah)
                      </h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-xs font-medium text-slate-700 mb-1">Terlambat &le; 1 Jam</label>
                          <div className="relative">
                            <span className="absolute left-2.5 top-2 text-xs font-semibold text-slate-400">Rp</span>
                            <input
                              type="number"
                              value={settings.potongan_terlambat_sd_1jam}
                              onChange={(e) => setSettings({ ...settings, potongan_terlambat_sd_1jam: e.target.value })}
                              className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-300 rounded"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-slate-700 mb-1">Terlambat &gt; 1 Jam</label>
                          <div className="relative">
                            <span className="absolute left-2.5 top-2 text-xs font-semibold text-slate-400">Rp</span>
                            <input
                              type="number"
                              value={settings.potongan_terlambat_gt_1jam}
                              onChange={(e) => setSettings({ ...settings, potongan_terlambat_gt_1jam: e.target.value })}
                              className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-300 rounded"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-slate-700 mb-1">Pulang Cepat</label>
                          <div className="relative">
                            <span className="absolute left-2.5 top-2 text-xs font-semibold text-slate-400">Rp</span>
                            <input
                              type="number"
                              value={settings.potongan_pulang_cepat}
                              onChange={(e) => setSettings({ ...settings, potongan_pulang_cepat: e.target.value })}
                              className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-300 rounded"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-slate-700 mb-1">Tidak Scan Masuk</label>
                          <div className="relative">
                            <span className="absolute left-2.5 top-2 text-xs font-semibold text-slate-400">Rp</span>
                            <input
                              type="number"
                              value={settings.potongan_tidak_absen_masuk}
                              onChange={(e) => setSettings({ ...settings, potongan_tidak_absen_masuk: e.target.value })}
                              className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-300 rounded"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-slate-700 mb-1">Tidak Scan Pulang</label>
                          <div className="relative">
                            <span className="absolute left-2.5 top-2 text-xs font-semibold text-slate-400">Rp</span>
                            <input
                              type="number"
                              value={settings.potongan_tidak_absen_pulang}
                              onChange={(e) => setSettings({ ...settings, potongan_tidak_absen_pulang: e.target.value })}
                              className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-300 rounded"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-slate-700 mb-1">Tidak Hadir (Alfa)</label>
                          <div className="relative">
                            <span className="absolute left-2.5 top-2 text-xs font-semibold text-slate-400">Rp</span>
                            <input
                              type="number"
                              value={settings.potongan_tidak_hadir}
                              onChange={(e) => setSettings({ ...settings, potongan_tidak_hadir: e.target.value })}
                              className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-300 rounded"
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons Bar */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={handleSaveSettings}
                          className="flex items-center gap-2 bg-blue-700 hover:bg-blue-800 text-white px-5 py-2.5 rounded-lg text-xs font-bold shadow transition cursor-pointer"
                        >
                          <Save className="w-4 h-4" />
                          <span>Simpan Pengaturan</span>
                        </button>
                        <button
                          onClick={handleResetSettings}
                          className="px-4 py-2.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold transition cursor-pointer"
                        >
                          Reset Form
                        </button>
                      </div>

                      <button
                        onClick={handleResetSettings}
                        className="text-xs text-red-600 hover:text-red-800 font-semibold px-3 py-2 rounded transition cursor-pointer"
                      >
                        Kembalikan ke Default Pabrik
                      </button>
                    </div>
                  </div>
                )}

                {/* 3. BACKUP DATABASE PAGE */}
                {activeMenu === 'backup' && (
                  <div className="space-y-6 max-w-5xl mx-auto">
                    {backupNotice && (
                      <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                        <span>{backupNotice}</span>
                      </div>
                    )}

                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                      <h3 className="font-bold text-slate-800 text-base mb-1 flex items-center gap-2">
                        <Database className="w-5 h-5 text-blue-600" />
                        Pencadangan Database SQLite (Online Backup API)
                      </h3>
                      <p className="text-xs text-slate-500 mb-4">
                        Database sumber: <code>data/database/siap_presensi.db</code>. Pencadangan menggunakan SQLite Online Backup API yang aman dari kerusakan berkas walau sistem sedang aktif.
                      </p>

                      <div className="flex flex-wrap items-center gap-3">
                        <button
                          onClick={handleCreateBackup}
                          className="flex items-center gap-2 bg-blue-700 hover:bg-blue-800 text-white px-5 py-2.5 rounded-lg text-xs font-bold shadow transition cursor-pointer"
                        >
                          <FolderDown className="w-4 h-4" />
                          <span>Buat Backup Database Sekarang</span>
                        </button>

                        <button
                          onClick={() => alert('Fitur Restore Database secara penuh dengan verifikasi skema akan diaktifkan pada Tahap berikutnya.')}
                          className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-500 border border-dashed border-slate-300 rounded-lg text-xs font-medium cursor-pointer"
                        >
                          Restore Database (Placeholder Tahap 2)
                        </button>
                      </div>
                    </div>

                    {/* Riwayat Backup */}
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                      <div className="p-4 border-b border-slate-200 bg-slate-50/70">
                        <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider">
                          Daftar Berkas Cadangan Tersimpan (data/backups/)
                        </h4>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
                            <tr>
                              <th className="p-3">Nama Berkas</th>
                              <th className="p-3">Ukuran</th>
                              <th className="p-3">Waktu Pembuatan</th>
                              <th className="p-3">Lokasi Penyimpanan</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {backups.map((b, idx) => (
                              <tr key={idx} className="hover:bg-slate-50 font-mono">
                                <td className="p-3 font-semibold text-slate-800">{b.filename}</td>
                                <td className="p-3 text-slate-600">{b.size}</td>
                                <td className="p-3 text-slate-600">{b.timestamp}</td>
                                <td className="p-3 text-slate-400 text-[11px] truncate max-w-xs">{b.filepath}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}

                {/* 4. MODUL MASTER DATA KARYAWAN (TAHAP 2) */}
                {activeMenu === 'karyawan' && session && (
                  <EmployeesSimulatorView
                    userSession={session}
                    onAddAuditLog={(action, module, description) =>
                      addAuditLog(session.username, action, module, description)
                    }
                  />
                )}

                {/* 5. MODUL IMPORT ABSENSI EXCEL (TAHAP 3) */}
                {activeMenu === 'import' && session && (
                  <ImportAttendanceSimulatorView
                    userSession={session}
                    employees={simulatedEmployees}
                    rawAttendanceList={rawAttendanceList}
                    batchLogs={batchLogs}
                    onImportComplete={(newRaw, newBatch, newEmps) => {
                      setRawAttendanceList([...rawAttendanceList, ...newRaw]);
                      setBatchLogs([newBatch, ...batchLogs]);
                      if (newEmps.length > 0) {
                        setSimulatedEmployees([...simulatedEmployees, ...newEmps]);
                      }
                    }}
                    onAddAuditLog={(action, module, description) =>
                      addAuditLog(session.username, action, module, description)
                    }
                  />
                )}

                {/* 6. MODUL DATA ABSENSI (TAB GANDA: ABSENSI HARIAN TAHAP 4 & RAW DATA TAHAP 3) */}
                {activeMenu === 'absensi' && session && (
                  <div className="space-y-4">
                    {/* Tab Bar Navigasi Absensi */}
                    <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
                      <button
                        onClick={() => setAttendanceSubTab('daily')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition cursor-pointer ${
                          attendanceSubTab === 'daily'
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        <span>📋</span>
                        <span>Absensi Harian & Kehadiran (Tahap 4)</span>
                      </button>

                      <button
                        onClick={() => setAttendanceSubTab('raw')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition cursor-pointer ${
                          attendanceSubTab === 'raw'
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        <span>🕒</span>
                        <span>Data Absensi Mentah / Raw (Tahap 3)</span>
                      </button>
                    </div>

                    {/* Konten Tab Terpilih */}
                    {attendanceSubTab === 'daily' ? (
                      <DailyAttendanceSimulatorView
                        userSession={session}
                        employees={simulatedEmployees}
                        calendarData={calendarData}
                        rawAttendanceList={rawAttendanceList}
                        dailyAttendanceList={dailyAttendanceList}
                        onUpdateDailyAttendance={newList => setDailyAttendanceList(newList)}
                        onAddAuditLog={(action, module, description) =>
                          addAuditLog(session.username, action, module, description)
                        }
                      />
                    ) : (
                      <RawAttendanceSimulatorView
                        rawAttendanceList={rawAttendanceList}
                        batchLogs={batchLogs}
                        onAddAuditLog={(action, module, description) =>
                          addAuditLog(session.username, action, module, description)
                        }
                      />
                    )}
                  </div>
                )}

                {/* 7. MODUL KALENDER KERJA (TAHAP 4) */}
                {activeMenu === 'kalender' && session && (
                  <CalendarSimulatorView
                    userSession={session}
                    calendarData={calendarData}
                    onUpdateCalendar={updated => setCalendarData(updated)}
                    onAddAuditLog={(action, module, description) =>
                      addAuditLog(session.username, action, module, description)
                    }
                  />
                )}

                {/* 8. MODUL TAHAP 5: PERHITUNGAN POTONGAN & REKAP LAPORAN */}
                {activeMenu === 'laporan' && session && (
                  <DeductionSimulatorView
                    userSession={session}
                    employees={simulatedEmployees}
                    calendarData={calendarData}
                    dailyAttendanceList={dailyAttendanceList}
                    settings={settings}
                    deductionsList={deductionsList}
                    onUpdateDeductions={(newList) => setDeductionsList(newList)}
                    onAddAuditLog={(action, module, description) =>
                      addAuditLog(session.username, action, module, description)
                    }
                  />
                )}

                {/* 9. MODUL TAHAP 6: BUILD EXECUTABLE (.EXE) & INSTALLER WINDOWS */}
                {activeMenu === 'build' && session && (
                  <BuildDeploymentSimulatorView
                    userSession={session}
                    onAddAuditLog={(action, module, description) =>
                      addAuditLog(session.username, action, module, description)
                    }
                    onOpenAboutDialog={() => setShowAboutDialog(true)}
                    onOpenFirstRunDialog={() => setShowFirstRunDialog(true)}
                  />
                )}
              </main>
            </div>
          </div>
        )}

        {/* Modal Dialog Tentang Aplikasi (Tahap 6) */}
        <AboutDialogModal
          isOpen={showAboutDialog}
          onClose={() => setShowAboutDialog(false)}
        />

        {/* Modal Dialog First-Run Setup / Keamanan (Tahap 6) */}
        {session && (
          <FirstRunDialogModal
            isOpen={showFirstRunDialog}
            onClose={() => setShowFirstRunDialog(false)}
            currentUser={session}
            onAddAuditLog={(action, module, description) =>
              addAuditLog(session.username, action, module, description)
            }
          />
        )}

        {/* Modal Pasang APK / PWA */}
        <InstallAppModal
          isOpen={showInstallModal}
          onClose={() => setShowInstallModal(false)}
        />
      </div>
    </div>
  );
}
