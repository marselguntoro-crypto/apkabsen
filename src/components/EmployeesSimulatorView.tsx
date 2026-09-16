import React, { useState, useMemo } from 'react';
import {
  Users,
  UserCheck,
  UserX,
  AlertTriangle,
  Search,
  Plus,
  Upload,
  Download,
  RotateCw,
  Edit2,
  Trash2,
  CheckCircle2,
  XCircle,
  FileSpreadsheet,
  Filter,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  Info,
} from 'lucide-react';
import { EmployeeItem, UserSession, AuditLogItem, ImportPreviewItem } from '../types';

interface EmployeesSimulatorViewProps {
  userSession: UserSession;
  onAddAuditLog: (action: string, module: string, description: string) => void;
}

// Initial realistic dataset for SIAP Phase 2
const INITIAL_EMPLOYEES: EmployeeItem[] = [
  {
    id: 1,
    emp_num: 'EMP-001',
    no_id: '101',
    nik: '3201012345678901',
    nama: 'Budi Santoso, S.Kom',
    unit: 'Teknologi Informasi',
    jabatan: 'Kepala Divisi IT',
    email: 'budi.santoso@instansi.go.id',
    keterangan: 'Administrator sistem absensi',
    status: 'AKTIF',
    tanggal_mulai: '2022-01-15',
    created_at: '2022-01-15 08:00',
    hasAttendanceHistory: true,
  },
  {
    id: 2,
    emp_num: 'EMP-002',
    no_id: '102',
    nik: '3201019988776602',
    nama: 'Siti Aminah, SE',
    unit: 'Keuangan',
    jabatan: 'Bendahara Pengeluaran',
    email: 'siti.aminah@instansi.go.id',
    keterangan: 'Verifikator potongan absensi bulanan',
    status: 'AKTIF',
    tanggal_mulai: '2022-03-01',
    created_at: '2022-03-01 08:30',
    hasAttendanceHistory: true,
  },
  {
    id: 3,
    emp_num: 'EMP-003',
    no_id: '103',
    nik: '',
    nama: 'Ahmad Fauzi',
    unit: 'Operasional',
    jabatan: 'Staff Lapangan',
    email: 'fauzi@instansi.go.id',
    keterangan: 'Berkas NIK belum diserahkan ke HRD',
    status: 'AKTIF',
    tanggal_mulai: '2023-06-10',
    created_at: '2023-06-10 09:00',
    hasAttendanceHistory: true,
  },
  {
    id: 4,
    emp_num: 'EMP-004',
    no_id: '104',
    nik: '3201014455667704',
    nama: 'Dewi Lestari, S.Psi',
    unit: 'Sumber Daya Manusia',
    jabatan: 'Spesialis Rekrutmen & Absensi',
    email: 'dewi.lestari@instansi.go.id',
    keterangan: 'Operator pengelola cuti',
    status: 'AKTIF',
    tanggal_mulai: '2023-08-01',
    created_at: '2023-08-01 08:15',
    hasAttendanceHistory: true,
  },
  {
    id: 5,
    emp_num: 'EMP-005',
    no_id: '105',
    nik: '',
    nama: 'Rian Pratama',
    unit: 'Operasional',
    jabatan: 'Teknisi Jaringan',
    email: '',
    keterangan: 'Karyawan kontrak masa percobaan',
    status: 'NONAKTIF',
    tanggal_mulai: '2024-01-02',
    created_at: '2024-01-02 08:00',
    hasAttendanceHistory: false,
  },
  {
    id: 6,
    emp_num: 'EMP-006',
    no_id: '106',
    nik: '3201017788990006',
    nama: 'Hendra Gunawan',
    unit: 'Sekretariat',
    jabatan: 'Staff Tata Usaha',
    email: 'hendra@instansi.go.id',
    keterangan: 'Pengarsipan dokumen administrasi',
    status: 'AKTIF',
    tanggal_mulai: '2024-02-15',
    created_at: '2024-02-15 08:30',
    hasAttendanceHistory: false,
  },
  {
    id: 7,
    emp_num: 'EMP-007',
    no_id: '107',
    nik: '3201011122334407',
    nama: 'Nurul Hidayati',
    unit: 'Keuangan',
    jabatan: 'Staff Akuntansi',
    email: 'nurul@instansi.go.id',
    keterangan: 'Rekonsiliasi slip gaji & potongan',
    status: 'AKTIF',
    tanggal_mulai: '2024-04-01',
    created_at: '2024-04-01 08:00',
    hasAttendanceHistory: false,
  },
];

const SAMPLE_IMPORT_ITEMS: ImportPreviewItem[] = [
  {
    rowNumber: 2,
    nama: 'Dian Permata, M.Kom',
    emp_num: 'EMP-008',
    no_id: '108',
    nik: '3201018899112233',
    unit: 'Teknologi Informasi',
    jabatan: 'Database Administrator',
    email: 'dian.permata@instansi.go.id',
    status: 'AKTIF',
    tanggal_mulai: '2025-01-10',
    statusType: 'VALID',
    note: 'Siap diimport',
  },
  {
    rowNumber: 3,
    nama: 'Budi Santoso, S.Kom',
    emp_num: 'EMP-001',
    no_id: '101',
    nik: '3201012345678901',
    unit: 'Teknologi Informasi',
    jabatan: 'Kepala Divisi IT & Digital',
    email: 'budi.santoso@instansi.go.id',
    status: 'AKTIF',
    tanggal_mulai: '2022-01-15',
    statusType: 'DUPLIKAT',
    note: "No. Pegawai 'EMP-001' sudah ada di database",
    existingId: 1,
  },
  {
    rowNumber: 4,
    nama: '',
    emp_num: 'EMP-009',
    no_id: '109',
    nik: '',
    unit: 'Operasional',
    jabatan: 'Staff',
    email: '',
    status: 'AKTIF',
    tanggal_mulai: '2025-02-01',
    statusType: 'INVALID',
    note: 'Nama karyawan kosong (wajib diisi)',
  },
  {
    rowNumber: 5,
    nama: 'Farhan Maulana',
    emp_num: 'EMP-010',
    no_id: '110',
    nik: '3201019900112233',
    unit: 'Sekretariat',
    jabatan: 'Resepsionis',
    email: 'farhan@instansi.go.id',
    status: 'AKTIF',
    tanggal_mulai: '2025-02-15',
    statusType: 'VALID',
    note: 'Siap diimport',
  },
];

export const EmployeesSimulatorView: React.FC<EmployeesSimulatorViewProps> = ({
  userSession,
  onAddAuditLog,
}) => {
  const [employees, setEmployees] = useState<EmployeeItem[]>(INITIAL_EMPLOYEES);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterUnit, setFilterUnit] = useState('ALL');
  const [filterJabatan, setFilterJabatan] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(15);

  // Dialog States
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<EmployeeItem | null>(null);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [duplicateMode, setDuplicateMode] = useState<'SKIP' | 'UPDATE'>('SKIP');
  const [feedbackNotice, setFeedbackNotice] = useState<string | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    nama: '',
    emp_num: '',
    no_id: '',
    nik: '',
    unit: 'Teknologi Informasi',
    jabatan: '',
    email: '',
    status: 'AKTIF' as 'AKTIF' | 'NONAKTIF',
    tanggal_mulai: '2025-01-01',
    keterangan: '',
  });
  const [formErrors, setFormErrors] = useState<string[]>([]);

  // Distinct units & jabatans
  const units = useMemo(() => {
    const set = new Set<string>();
    employees.forEach((e) => e.unit && set.add(e.unit));
    return Array.from(set).sort();
  }, [employees]);

  const jabatans = useMemo(() => {
    const set = new Set<string>();
    employees.forEach((e) => e.jabatan && set.add(e.jabatan));
    return Array.from(set).sort();
  }, [employees]);

  // Statistics
  const stats = useMemo(() => {
    const total = employees.length;
    const aktif = employees.filter((e) => e.status === 'AKTIF').length;
    const nonaktif = employees.filter((e) => e.status === 'NONAKTIF').length;
    const tanpaNik = employees.filter((e) => !e.nik || e.nik.trim() === '').length;
    return { total, aktif, nonaktif, tanpaNik };
  }, [employees]);

  // Filtered employees
  const filteredEmployees = useMemo(() => {
    return employees.filter((e) => {
      const matchSearch =
        searchTerm === '' ||
        e.nama.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.emp_num.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.no_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.nik.toLowerCase().includes(searchTerm.toLowerCase());

      const matchUnit = filterUnit === 'ALL' || e.unit === filterUnit;
      const matchJabatan = filterJabatan === 'ALL' || e.jabatan === filterJabatan;
      const matchStatus = filterStatus === 'ALL' || e.status === filterStatus;

      return matchSearch && matchUnit && matchJabatan && matchStatus;
    });
  }, [employees, searchTerm, filterUnit, filterJabatan, filterStatus]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredEmployees.length / perPage));
  const paginatedEmployees = useMemo(() => {
    const start = (currentPage - 1) * perPage;
    return filteredEmployees.slice(start, start + perPage);
  }, [filteredEmployees, currentPage, perPage]);

  // Reset filters
  const handleResetFilters = () => {
    setSearchTerm('');
    setFilterUnit('ALL');
    setFilterJabatan('ALL');
    setFilterStatus('ALL');
    setCurrentPage(1);
  };

  // Open Add Dialog
  const handleOpenAdd = () => {
    setEditingEmployee(null);
    setFormData({
      nama: '',
      emp_num: `EMP-${String(employees.length + 1).padStart(3, '0')}`,
      no_id: String(100 + employees.length + 1),
      nik: '',
      unit: units[0] || 'Teknologi Informasi',
      jabatan: '',
      email: '',
      status: 'AKTIF',
      tanggal_mulai: new Date().toISOString().split('T')[0],
      keterangan: '',
    });
    setFormErrors([]);
    setIsFormOpen(true);
  };

  // Open Edit Dialog
  const handleOpenEdit = (emp: EmployeeItem) => {
    setEditingEmployee(emp);
    setFormData({
      nama: emp.nama,
      emp_num: emp.emp_num,
      no_id: emp.no_id,
      nik: emp.nik,
      unit: emp.unit,
      jabatan: emp.jabatan,
      email: emp.email,
      status: emp.status,
      tanggal_mulai: emp.tanggal_mulai,
      keterangan: emp.keterangan,
    });
    setFormErrors([]);
    setIsFormOpen(true);
  };

  // Save Form (Add or Edit)
  const handleSaveForm = (e: React.FormEvent) => {
    e.preventDefault();
    const errors: string[] = [];

    if (!formData.nama.trim()) {
      errors.push('Nama karyawan wajib diisi.');
    }
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.push('Format alamat email tidak valid.');
    }

    // Check duplicate emp_num
    if (formData.emp_num) {
      const dup = employees.find(
        (emp) =>
          emp.emp_num.toLowerCase() === formData.emp_num.toLowerCase() &&
          emp.id !== editingEmployee?.id
      );
      if (dup) {
        errors.push(`No. Pegawai '${formData.emp_num}' sudah digunakan oleh '${dup.nama}'.`);
      }
    }

    // Check duplicate no_id
    if (formData.no_id) {
      const dup = employees.find(
        (emp) =>
          emp.no_id.toLowerCase() === formData.no_id.toLowerCase() &&
          emp.id !== editingEmployee?.id
      );
      if (dup) {
        errors.push(`No. ID / PIN '${formData.no_id}' sudah digunakan oleh '${dup.nama}'.`);
      }
    }

    // Check duplicate NIK if filled
    if (formData.nik) {
      const dup = employees.find(
        (emp) =>
          emp.nik &&
          emp.nik.toLowerCase() === formData.nik.toLowerCase() &&
          emp.id !== editingEmployee?.id
      );
      if (dup) {
        errors.push(`NIK '${formData.nik}' sudah terdaftar untuk '${dup.nama}'.`);
      }
    }

    if (errors.length > 0) {
      setFormErrors(errors);
      return;
    }

    if (editingEmployee) {
      // Update
      setEmployees((prev) =>
        prev.map((emp) =>
          emp.id === editingEmployee.id
            ? {
                ...emp,
                ...formData,
              }
            : emp
        )
      );
      onAddAuditLog(
        'EDIT_KARYAWAN',
        'EMPLOYEES',
        `Memperbarui profil data karyawan '${formData.nama}' (ID: ${editingEmployee.id}).`
      );
      setFeedbackNotice(`Data karyawan '${formData.nama}' berhasil diperbarui.`);
    } else {
      // Create new
      const newId = Math.max(...employees.map((e) => e.id), 0) + 1;
      const newEmp: EmployeeItem = {
        id: newId,
        ...formData,
        created_at: new Date().toISOString().replace('T', ' ').slice(0, 16),
        hasAttendanceHistory: false,
      };
      setEmployees((prev) => [newEmp, ...prev]);
      onAddAuditLog(
        'TAMBAH_KARYAWAN',
        'EMPLOYEES',
        `Menambahkan karyawan baru '${formData.nama}' (${formData.emp_num || 'ID: ' + newId}).`
      );
      setFeedbackNotice(`Karyawan baru '${formData.nama}' berhasil didaftarkan ke sistem.`);
    }

    setIsFormOpen(false);
    setTimeout(() => setFeedbackNotice(null), 4000);
  };

  // Toggle status (Soft Delete)
  const handleToggleStatus = (emp: EmployeeItem) => {
    const targetStatus = emp.status === 'AKTIF' ? 'NONAKTIF' : 'AKTIF';
    setEmployees((prev) =>
      prev.map((e) => (e.id === emp.id ? { ...e, status: targetStatus } : e))
    );
    onAddAuditLog(
      'UBAH_STATUS_KARYAWAN',
      'EMPLOYEES',
      `Mengubah status karyawan '${emp.nama}' menjadi ${targetStatus}.`
    );
    setFeedbackNotice(`Status karyawan '${emp.nama}' diubah menjadi ${targetStatus}.`);
    setTimeout(() => setFeedbackNotice(null), 3000);
  };

  // Delete employee
  const handleDeleteEmployee = (emp: EmployeeItem) => {
    if (userSession.role !== 'ADMIN') {
      alert('Akses Ditolak: Penghapusan permanen hanya dapat dilakukan oleh Administrator.');
      return;
    }

    if (emp.hasAttendanceHistory) {
      alert(
        `Penghapusan Ditolak: Karyawan '${emp.nama}' tidak dapat dihapus secara permanen karena memiliki riwayat catatan absensi.\n\nSesuai standar audit kepegawaian, silakan gunakan fitur 'Nonaktifkan' (Soft Delete) untuk menjaga integritas pembukuan presensi.`
      );
      return;
    }

    if (
      window.confirm(
        `Apakah Anda yakin ingin menghapus permanen data karyawan '${emp.nama}'?\nData yang belum berelasi dengan absensi akan dibersihkan dari database.`
      )
    ) {
      setEmployees((prev) => prev.filter((e) => e.id !== emp.id));
      onAddAuditLog(
        'HAPUS_KARYAWAN',
        'EMPLOYEES',
        `Menghapus permanen karyawan '${emp.nama}' (ID: ${emp.id}).`
      );
      setFeedbackNotice(`Karyawan '${emp.nama}' telah dihapus dari database.`);
      setTimeout(() => setFeedbackNotice(null), 3000);
    }
  };

  // Execute Excel Import Simulation
  const handleExecuteImport = () => {
    let successCount = 0;
    let dupSkipped = 0;
    let dupUpdated = 0;
    let failedCount = 0;

    setEmployees((prev) => {
      let updatedList = [...prev];

      SAMPLE_IMPORT_ITEMS.forEach((item) => {
        if (item.statusType === 'INVALID') {
          failedCount++;
          return;
        }

        if (item.statusType === 'DUPLIKAT') {
          if (duplicateMode === 'SKIP') {
            dupSkipped++;
            return;
          } else if (duplicateMode === 'UPDATE' && item.existingId) {
            updatedList = updatedList.map((emp) =>
              emp.id === item.existingId
                ? {
                    ...emp,
                    nama: item.nama,
                    jabatan: item.jabatan,
                    unit: item.unit,
                    email: item.email,
                  }
                : emp
            );
            dupUpdated++;
            successCount++;
            return;
          }
        }

        // Add new
        const newId = Math.max(...updatedList.map((e) => e.id), 0) + 1;
        updatedList.push({
          id: newId,
          emp_num: item.emp_num,
          no_id: item.no_id,
          nik: item.nik,
          nama: item.nama,
          unit: item.unit,
          jabatan: item.jabatan,
          email: item.email,
          status: item.status,
          tanggal_mulai: item.tanggal_mulai,
          keterangan: 'Diimpor dari file Excel',
          created_at: new Date().toISOString().replace('T', ' ').slice(0, 16),
          hasAttendanceHistory: false,
        });
        successCount++;
      });

      return updatedList;
    });

    onAddAuditLog(
      'IMPORT_KARYAWAN',
      'EMPLOYEES',
      `Import data karyawan dari 'Template_Karyawan.xlsx': ${successCount} berhasil, ${dupSkipped} duplikat dilewati, ${dupUpdated} diperbarui, ${failedCount} gagal.`
    );

    setIsImportOpen(false);
    setFeedbackNotice(
      `Import selesai: ${successCount} berhasil diproses (${dupSkipped} duplikat dilewati, ${failedCount} tidak valid).`
    );
    setTimeout(() => setFeedbackNotice(null), 4000);
  };

  // Export CSV
  const handleExportCSV = () => {
    const headers = [
      'No',
      'No. ID / PIN',
      'No. Pegawai',
      'NIK',
      'Nama Karyawan',
      'Unit Kerja',
      'Jabatan',
      'Email',
      'Status',
      'Tanggal Mulai',
    ];

    const rows = filteredEmployees.map((e, idx) => [
      idx + 1,
      `"${e.no_id || '-'}"`,
      `"${e.emp_num || '-'}"`,
      `"${e.nik || '-'}"`,
      `"${e.nama}"`,
      `"${e.unit || '-'}"`,
      `"${e.jabatan || '-'}"`,
      `"${e.email || '-'}"`,
      e.status,
      e.tanggal_mulai || '-',
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,\uFEFF' +
      [headers.join(';'), ...rows.map((r) => r.join(';'))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'Data_Karyawan_SIAP.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    onAddAuditLog(
      'EXPORT_KARYAWAN',
      'EMPLOYEES',
      `Export data karyawan (${filteredEmployees.length} baris) ke file CSV.`
    );
    setFeedbackNotice(
      `Berhasil mengekspor ${filteredEmployees.length} baris data karyawan ke file CSV.`
    );
    setTimeout(() => setFeedbackNotice(null), 3000);
  };

  return (
    <div className="space-y-5">
      {/* Toast Notification */}
      {feedbackNotice && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 px-4 py-3 rounded-lg text-xs font-semibold flex items-center justify-between shadow-sm animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{feedbackNotice}</span>
          </div>
          <button
            onClick={() => setFeedbackNotice(null)}
            className="text-emerald-700 hover:text-emerald-900"
          >
            ✕
          </button>
        </div>
      )}

      {/* Header Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">Master Data Karyawan</h2>
            <span className="bg-blue-100 text-blue-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
              Tahap 2
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Pengelolaan identitas pegawai, nomor mesin absensi (PIN/Barcode), unit penempatan, dan status kepegawaian.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => {
              setFeedbackNotice('Data karyawan berhasil disegarkan dari database SQLite.');
              setTimeout(() => setFeedbackNotice(null), 2500);
            }}
            className="px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 flex items-center gap-1.5 transition-colors"
          >
            <RotateCw className="w-3.5 h-3.5" />
            Segarkan
          </button>

          <button
            onClick={handleExportCSV}
            className="px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-600" />
            Export Excel/CSV
          </button>

          <button
            onClick={() => setIsImportOpen(true)}
            className="px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 flex items-center gap-1.5 transition-colors"
          >
            <Upload className="w-3.5 h-3.5 text-blue-600" />
            Import Excel
          </button>

          <button
            onClick={handleOpenAdd}
            className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center gap-1.5 shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            Tambah Karyawan
          </button>
        </div>
      </div>

      {/* 4 Summary Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="w-11 h-11 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 border border-blue-100">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-black text-slate-900">{stats.total}</div>
            <div className="text-xs text-slate-500 font-medium">Total Karyawan</div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="w-11 h-11 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 border border-emerald-100">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-black text-slate-900">{stats.aktif}</div>
            <div className="text-xs text-slate-500 font-medium">Karyawan Aktif</div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="w-11 h-11 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center shrink-0 border border-slate-200">
            <UserX className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-black text-slate-900">{stats.nonaktif}</div>
            <div className="text-xs text-slate-500 font-medium">Nonaktif / Resign</div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="w-11 h-11 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center shrink-0 border border-amber-100">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-black text-slate-900">{stats.tanpaNik}</div>
            <div className="text-xs text-slate-500 font-medium">Belum Memiliki NIK</div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row items-stretch md:items-center gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Cari nama, No. ID / PIN, No. Pegawai, atau NIK..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-900"
          />
        </div>

        {/* Filter Unit */}
        <div className="w-full md:w-48">
          <select
            value={filterUnit}
            onChange={(e) => {
              setFilterUnit(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800"
          >
            <option value="ALL">Semua Unit</option>
            {units.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
        </div>

        {/* Filter Jabatan */}
        <div className="w-full md:w-48">
          <select
            value={filterJabatan}
            onChange={(e) => {
              setFilterJabatan(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800"
          >
            <option value="ALL">Semua Jabatan</option>
            {jabatans.map((j) => (
              <option key={j} value={j}>
                {j}
              </option>
            ))}
          </select>
        </div>

        {/* Filter Status */}
        <div className="w-full md:w-36">
          <select
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800"
          >
            <option value="ALL">Semua Status</option>
            <option value="AKTIF">AKTIF</option>
            <option value="NONAKTIF">NONAKTIF</option>
          </select>
        </div>

        {/* Reset Filter Button */}
        <button
          onClick={handleResetFilters}
          className="px-3 py-2 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors shrink-0"
        >
          Reset Filter
        </button>
      </div>

      {/* Main Employee Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider text-[11px]">
                <th className="px-4 py-3 w-12 text-center">No</th>
                <th className="px-4 py-3 w-28 text-center">No. ID / PIN</th>
                <th className="px-4 py-3 w-32 text-center">No. Pegawai</th>
                <th className="px-4 py-3 w-36 text-center">NIK</th>
                <th className="px-4 py-3">Nama Karyawan</th>
                <th className="px-4 py-3">Unit / Departemen</th>
                <th className="px-4 py-3">Jabatan</th>
                <th className="px-4 py-3 w-24 text-center">Status</th>
                <th className="px-4 py-3 w-36 text-center">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-800">
              {paginatedEmployees.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <Users className="w-8 h-8 text-slate-300" />
                      <p className="font-medium text-slate-500">Tidak ada data karyawan yang cocok dengan kriteria filter.</p>
                      <button
                        onClick={handleResetFilters}
                        className="text-xs text-blue-600 hover:underline mt-1"
                      >
                        Reset Kriteria Pencarian
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (
                paginatedEmployees.map((emp, index) => {
                  const itemIndex = (currentPage - 1) * perPage + index + 1;
                  return (
                    <tr
                      key={emp.id}
                      className="hover:bg-slate-50/80 transition-colors"
                    >
                      <td className="px-4 py-3 text-center text-slate-500">{itemIndex}</td>
                      <td className="px-4 py-3 text-center font-mono font-bold text-blue-700">
                        {emp.no_id || '-'}
                      </td>
                      <td className="px-4 py-3 text-center font-mono text-slate-600">
                        {emp.emp_num || '-'}
                      </td>
                      <td className="px-4 py-3 text-center font-mono text-slate-600">
                        {emp.nik ? (
                          emp.nik
                        ) : (
                          <span className="text-amber-600 bg-amber-50 px-2 py-0.5 rounded text-[10px] font-semibold border border-amber-200">
                            Tanpa NIK
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900">{emp.nama}</div>
                        {emp.email && <div className="text-[11px] text-slate-500">{emp.email}</div>}
                      </td>
                      <td className="px-4 py-3 text-slate-700">{emp.unit || '-'}</td>
                      <td className="px-4 py-3 text-slate-700">{emp.jabatan || '-'}</td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            emp.status === 'AKTIF'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {emp.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <button
                            onClick={() => handleOpenEdit(emp)}
                            title="Edit Data Karyawan"
                            className="p-1.5 text-blue-600 hover:bg-blue-50 rounded border border-blue-200 transition-colors"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => handleToggleStatus(emp)}
                            title={
                              emp.status === 'AKTIF'
                                ? 'Nonaktifkan Karyawan (Soft Delete)'
                                : 'Aktifkan Kembali'
                            }
                            className={`px-2 py-1 text-[10px] font-bold rounded border transition-colors ${
                              emp.status === 'AKTIF'
                                ? 'text-amber-700 bg-amber-50 hover:bg-amber-100 border-amber-200'
                                : 'text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border-emerald-200'
                            }`}
                          >
                            {emp.status === 'AKTIF' ? 'Nonaktif' : 'Aktifkan'}
                          </button>

                          <button
                            onClick={() => handleDeleteEmployee(emp)}
                            title={
                              userSession.role === 'ADMIN'
                                ? 'Hapus Permanen (jika tidak ada riwayat absensi)'
                                : 'Hanya Administrator yang dapat menghapus'
                            }
                            className="p-1.5 text-rose-600 hover:bg-rose-50 rounded border border-rose-200 transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
          <div className="flex items-center gap-3">
            <span>
              Menampilkan{' '}
              <strong className="text-slate-900">
                {filteredEmployees.length === 0 ? 0 : (currentPage - 1) * perPage + 1}
              </strong>{' '}
              -{' '}
              <strong className="text-slate-900">
                {Math.min(currentPage * perPage, filteredEmployees.length)}
              </strong>{' '}
              dari <strong className="text-slate-900">{filteredEmployees.length}</strong> karyawan
            </span>

            <div className="flex items-center gap-1.5 ml-2">
              <span className="text-slate-500">Per halaman:</span>
              <select
                value={perPage}
                onChange={(e) => {
                  setPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="bg-white border border-slate-300 rounded px-2 py-1 text-xs focus:ring-1 focus:ring-blue-500"
              >
                <option value={10}>10</option>
                <option value={15}>15</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 bg-white border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 font-medium transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              Sebelumnya
            </button>
            <span className="font-semibold text-slate-700 px-2">
              Halaman {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages}
              className="px-3 py-1.5 bg-white border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 font-medium transition-colors"
            >
              Berikutnya
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Add / Edit Employee Modal Dialog */}
      {isFormOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-slate-200 animate-scale-up">
            <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">
                  {editingEmployee ? 'Edit Profil Karyawan' : 'Tambah Karyawan Baru'}
                </h3>
                <p className="text-[11px] text-slate-500">
                  Pastikan Nomor ID / PIN Mesin Absensi diisi untuk sinkronisasi rekaman sidik jari / kartu.
                </p>
              </div>
              <button
                onClick={() => setIsFormOpen(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveForm} className="p-6 space-y-4">
              {/* Errors Display */}
              {formErrors.length > 0 && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-xs space-y-1">
                  {formErrors.map((err, i) => (
                    <div key={i} className="flex items-start gap-1.5">
                      <span className="text-rose-600 font-bold">•</span>
                      <span>{err}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Nama Lengkap */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Nama Lengkap Karyawan <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="Contoh: Budi Santoso, S.Kom"
                  value={formData.nama}
                  onChange={(e) => setFormData({ ...formData, nama: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              {/* Grid ID & NIP */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    No. ID / PIN Mesin
                  </label>
                  <input
                    type="text"
                    placeholder="Contoh: 101"
                    value={formData.no_id}
                    onChange={(e) => setFormData({ ...formData, no_id: e.target.value })}
                    className="w-full px-3 py-2 text-xs font-mono border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    No. Pegawai / NIP
                  </label>
                  <input
                    type="text"
                    placeholder="Contoh: EMP-001"
                    value={formData.emp_num}
                    onChange={(e) => setFormData({ ...formData, emp_num: e.target.value })}
                    className="w-full px-3 py-2 text-xs font-mono border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Grid NIK & Unit */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    NIK KTP (16 Digit)
                  </label>
                  <input
                    type="text"
                    placeholder="Opsional (tidak wajib)"
                    value={formData.nik}
                    onChange={(e) => setFormData({ ...formData, nik: e.target.value })}
                    className="w-full px-3 py-2 text-xs font-mono border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Unit / Departemen
                  </label>
                  <input
                    type="text"
                    placeholder="Contoh: Teknologi Informasi"
                    value={formData.unit}
                    onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Grid Jabatan & Email */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Jabatan / Posisi
                  </label>
                  <input
                    type="text"
                    placeholder="Contoh: Staff Keuangan"
                    value={formData.jabatan}
                    onChange={(e) => setFormData({ ...formData, jabatan: e.target.value })}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Alamat Email
                  </label>
                  <input
                    type="email"
                    placeholder="budi@instansi.go.id"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Grid Status & Tanggal Mulai */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Status Kepegawaian
                  </label>
                  <select
                    value={formData.status}
                    onChange={(e) =>
                      setFormData({ ...formData, status: e.target.value as 'AKTIF' | 'NONAKTIF' })
                    }
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  >
                    <option value="AKTIF">AKTIF</option>
                    <option value="NONAKTIF">NONAKTIF</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Tanggal Mulai Kerja
                  </label>
                  <input
                    type="date"
                    value={formData.tanggal_mulai}
                    onChange={(e) => setFormData({ ...formData, tanggal_mulai: e.target.value })}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Keterangan */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Catatan Tambahan (Opsional)
                </label>
                <textarea
                  rows={2}
                  placeholder="Catatan khusus mengenai penugasan atau status berkas..."
                  value={formData.keterangan}
                  onChange={(e) => setFormData({ ...formData, keterangan: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              {/* Modal Buttons */}
              <div className="pt-3 border-t border-slate-200 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsFormOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors"
                >
                  {editingEmployee ? 'Simpan Perubahan' : 'Simpan Karyawan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Excel / CSV Import Modal Dialog */}
      {isImportOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full overflow-hidden border border-slate-200 animate-scale-up">
            <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <FileSpreadsheet className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">
                    Import Master Karyawan dari File Excel / CSV
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    Sistem otomatis memetakan kolom Nama, No. ID/PIN, No. Pegawai, NIK, Unit, dan Jabatan.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsImportOpen(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* File Info Card */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="w-5 h-5 text-emerald-600" />
                  <div>
                    <span className="font-semibold text-slate-800">
                      Berkas Contoh: Template_Data_Karyawan_2025.xlsx
                    </span>
                    <div className="text-[11px] text-slate-500">
                      Format terdeteksi: 4 baris data, 7 kolom header
                    </div>
                  </div>
                </div>
                <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded">
                  Siap Diproses
                </span>
              </div>

              {/* Statistics Metric Bar */}
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="p-2 bg-slate-50 border border-slate-200 rounded-lg">
                  <div className="text-slate-400 text-[10px] uppercase font-bold">Total Baris</div>
                  <div className="font-bold text-slate-800 text-sm">4</div>
                </div>
                <div className="p-2 bg-emerald-50 border border-emerald-200 rounded-lg">
                  <div className="text-emerald-700 text-[10px] uppercase font-bold">Valid</div>
                  <div className="font-bold text-emerald-700 text-sm">2 Baris</div>
                </div>
                <div className="p-2 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="text-amber-700 text-[10px] uppercase font-bold">Duplikat</div>
                  <div className="font-bold text-amber-700 text-sm">1 Baris</div>
                </div>
                <div className="p-2 bg-rose-50 border border-rose-200 rounded-lg">
                  <div className="text-rose-700 text-[10px] uppercase font-bold">Tidak Valid</div>
                  <div className="font-bold text-rose-700 text-sm">1 Baris</div>
                </div>
              </div>

              {/* Preview Table */}
              <div className="border border-slate-200 rounded-lg overflow-hidden max-h-48 overflow-y-auto">
                <table className="w-full text-left text-[11px] border-collapse">
                  <thead className="bg-slate-100 text-slate-700 font-bold sticky top-0">
                    <tr>
                      <th className="p-2 w-12 text-center">Baris</th>
                      <th className="p-2 w-20 text-center">Status</th>
                      <th className="p-2">Nama Karyawan</th>
                      <th className="p-2 text-center">No. ID</th>
                      <th className="p-2 text-center">No. Pegawai</th>
                      <th className="p-2">Unit Kerja</th>
                      <th className="p-2">Keterangan / Validasi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {SAMPLE_IMPORT_ITEMS.map((row) => (
                      <tr key={row.rowNumber} className="hover:bg-slate-50">
                        <td className="p-2 text-center text-slate-500 font-mono">#{row.rowNumber}</td>
                        <td className="p-2 text-center">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                              row.statusType === 'VALID'
                                ? 'bg-emerald-100 text-emerald-800'
                                : row.statusType === 'DUPLIKAT'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {row.statusType}
                          </span>
                        </td>
                        <td className="p-2 font-medium text-slate-900">{row.nama || '(Kosong)'}</td>
                        <td className="p-2 text-center font-mono">{row.no_id}</td>
                        <td className="p-2 text-center font-mono">{row.emp_num}</td>
                        <td className="p-2">{row.unit}</td>
                        <td className="p-2 text-slate-600">{row.note}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Duplicate Handling Strategy */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                <div className="text-xs font-bold text-slate-800">
                  Opsi Penanganan Data Duplikat:
                </div>
                <div className="flex items-center gap-6 text-xs text-slate-700">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="dupMode"
                      checked={duplicateMode === 'SKIP'}
                      onChange={() => setDuplicateMode('SKIP')}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span>
                      <strong>Lewati</strong> (Abaikan baris jika No. Pegawai / PIN sudah ada)
                    </span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="dupMode"
                      checked={duplicateMode === 'UPDATE'}
                      onChange={() => setDuplicateMode('UPDATE')}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span>
                      <strong>Perbarui</strong> (Timpa data lama dengan data file Excel)
                    </span>
                  </label>
                </div>
              </div>

              {/* Footer Buttons */}
              <div className="pt-3 border-t border-slate-200 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsImportOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  Batal
                </button>
                <button
                  type="button"
                  onClick={handleExecuteImport}
                  className="px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm flex items-center gap-1.5 transition-colors"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Mulai Proses Import
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
