import React, { useState } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  Calendar, 
  Search, 
  Download, 
  Sparkles, 
  Layers, 
  ShieldAlert,
  ArrowRight,
  Filter
} from 'lucide-react';
import { 
  DailyAttendanceItem, 
  AttendanceRawItem, 
  WorkCalendarItem, 
  EmployeeItem, 
  AttendanceStatusType, 
  UserSession 
} from '../types';

interface DailyAttendanceSimulatorViewProps {
  userSession: UserSession;
  employees: EmployeeItem[];
  calendarData: WorkCalendarItem[];
  rawAttendanceList: AttendanceRawItem[];
  dailyAttendanceList: DailyAttendanceItem[];
  onUpdateDailyAttendance: (newList: DailyAttendanceItem[]) => void;
  onAddAuditLog: (action: string, module: string, description: string) => void;
}

const MONTHS_NAMES = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
];

export const DailyAttendanceSimulatorView: React.FC<DailyAttendanceSimulatorViewProps> = ({
  userSession,
  employees,
  calendarData,
  rawAttendanceList,
  dailyAttendanceList,
  onUpdateDailyAttendance,
  onAddAuditLog,
}) => {
  const [selectedMonth, setSelectedMonth] = useState<number>(8); // Default Agustus
  const [selectedYear, setSelectedYear] = useState<number>(2026);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [filterUnit, setFilterUnit] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [notice, setNotice] = useState<{ type: 'success' | 'info' | 'error'; text: string } | null>(null);

  // Unit unik
  const uniqueUnits = Array.from(new Set(employees.map(e => e.unit).filter(Boolean))).sort();

  // Filtered daily items
  const filteredItems = dailyAttendanceList.filter(item => {
    const itemDate = new Date(item.attendance_date);
    const m = itemDate.getMonth() + 1;
    const y = itemDate.getFullYear();

    if (m !== selectedMonth || y !== selectedYear) return false;
    if (filterStatus !== 'ALL' && item.attendance_status !== filterStatus) return false;
    if (filterUnit !== 'ALL' && item.unit !== filterUnit) return false;

    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      const matchName = item.nama.toLowerCase().includes(q);
      const matchNik = item.nik.toLowerCase().includes(q);
      const matchId = item.no_id.toLowerCase().includes(q);
      const matchEmp = item.emp_num.toLowerCase().includes(q);
      if (!matchName && !matchNik && !matchId && !matchEmp) return false;
    }

    return true;
  });

  // KPI Ringkasan
  const periodItems = dailyAttendanceList.filter(item => {
    const itemDate = new Date(item.attendance_date);
    return itemDate.getMonth() + 1 === selectedMonth && itemDate.getFullYear() === selectedYear;
  });

  const totalRecords = periodItems.length;
  const hadirLengkap = periodItems.filter(i => i.attendance_status === 'HADIR_LENGKAP').length;
  const hanyaMasuk = periodItems.filter(i => i.attendance_status === 'HANYA_ABSEN_MASUK').length;
  const hanyaPulang = periodItems.filter(i => i.attendance_status === 'HANYA_ABSEN_PULANG').length;
  const tidakAbsen = periodItems.filter(i => i.attendance_status === 'TIDAK_ABSEN').length;
  const multiScanConflict = periodItems.filter(i => i.has_conflict).length;

  const showNotification = (type: 'success' | 'info' | 'error', text: string) => {
    setNotice({ type, text });
    setTimeout(() => setNotice(null), 4500);
  };

  // Eksekusi Logika Pembentukan Absensi Harian (Tahap 4)
  const handleGenerateDaily = (mode: 'GENERATE_NEW' | 'REGENERATE') => {
    setIsProcessing(true);

    // 1. Dapatkan hari kerja aktif dari kalender
    const workingDays = calendarData.filter(
      d => d.month === selectedMonth && d.year === selectedYear && d.is_working_day
    );

    if (workingDays.length === 0) {
      showNotification(
        'error',
        `Kalender kerja untuk ${MONTHS_NAMES[selectedMonth - 1]} ${selectedYear} belum terbentuk atau tidak ada hari kerja aktif. Silakan generate kalender terlebih dahulu di menu Kalender Kerja.`
      );
      setIsProcessing(false);
      return;
    }

    // 2. Karyawan aktif
    const activeEmployees = employees.filter(e => e.status === 'AKTIF');
    if (activeEmployees.length === 0) {
      showNotification('error', 'Tidak ada data karyawan aktif untuk diproses.');
      setIsProcessing(false);
      return;
    }

    const generated: DailyAttendanceItem[] = [];
    let countNew = 0;
    let countUpdated = 0;

    activeEmployees.forEach(emp => {
      workingDays.forEach(cal => {
        // Cek tanggal mulai kerja karyawan
        if (emp.tanggal_mulai && cal.calendar_date < emp.tanggal_mulai) {
          return; // Belum mulai kerja
        }

        // Cari transaksi mentah yang cocok di tanggal ini
        const matchedRaws = rawAttendanceList.filter(raw => {
          if (raw.tanggal !== cal.calendar_date) return false;
          // Match identitas
          if (emp.emp_num && raw.emp_num === emp.emp_num) return true;
          if (emp.no_id && raw.no_id === emp.no_id) return true;
          if (emp.nik && raw.nik === emp.nik) return true;
          if (raw.nama.trim().toUpperCase() === emp.nama.trim().toUpperCase()) return true;
          return false;
        });

        let earliestIn: string | null = null;
        let latestOut: string | null = null;
        let hasConflict = false;
        let inCount = 0;
        let outCount = 0;

        matchedRaws.forEach(r => {
          if (r.scan_masuk) {
            inCount++;
            const cleanIn = r.scan_masuk.substring(0, 5);
            if (!earliestIn || cleanIn < earliestIn) {
              earliestIn = cleanIn;
            }
          }
          if (r.scan_pulang) {
            outCount++;
            const cleanOut = r.scan_pulang.substring(0, 5);
            if (!latestOut || cleanOut > latestOut) {
              latestOut = cleanOut;
            }
          }
        });

        if (matchedRaws.length > 1 || inCount > 1 || outCount > 1) {
          hasConflict = true;
        }

        // Tentukan status kehadiran
        let status: AttendanceStatusType = 'TIDAK_ABSEN';
        let incomplete = false;
        let notes = '';

        if (earliestIn && latestOut) {
          status = 'HADIR_LENGKAP';
        } else if (earliestIn && !latestOut) {
          status = 'HANYA_ABSEN_MASUK';
          incomplete = true;
          notes = 'Scan pulang tidak ditemukan';
        } else if (!earliestIn && latestOut) {
          status = 'HANYA_ABSEN_PULANG';
          incomplete = true;
          notes = 'Scan masuk tidak ditemukan';
        } else {
          status = 'TIDAK_ABSEN';
          incomplete = false;
          notes = 'Tidak melakukan presensi';
        }

        if (hasConflict) {
          notes = notes ? `${notes} (Multi-scan)` : 'Ditemukan lebih dari satu scan';
        }

        const recId = Number(`${emp.id}${cal.calendar_date.replace(/-/g, '')}`);
        generated.push({
          id: recId,
          employee_id: emp.id,
          emp_num: emp.emp_num,
          no_id: emp.no_id,
          nik: emp.nik,
          nama: emp.nama,
          unit: emp.unit,
          jabatan: emp.jabatan,
          attendance_date: cal.calendar_date,
          day_name: cal.day_name,
          scheduled_check_in: cal.scheduled_check_in || '08:15',
          scheduled_check_out: cal.scheduled_check_out || '16:30',
          actual_check_in: earliestIn,
          actual_check_out: latestOut,
          check_in_status: earliestIn ? 'ADA' : 'TIDAK_ADA',
          check_out_status: latestOut ? 'ADA' : 'TIDAK_ADA',
          attendance_status: status,
          has_incomplete_scan: incomplete,
          has_conflict: hasConflict,
          notes,
        });
        countNew++;
      });
    });

    // Simpan ke state
    if (mode === 'REGENERATE') {
      const otherMonths = dailyAttendanceList.filter(item => {
        const itemDate = new Date(item.attendance_date);
        return itemDate.getMonth() + 1 !== selectedMonth || itemDate.getFullYear() !== selectedYear;
      });
      onUpdateDailyAttendance([...otherMonths, ...generated]);
    } else {
      // GENERATE_NEW: hanya tambahkan yang belum ada
      const existingKeys = new Set(
        dailyAttendanceList.map(i => `${i.employee_id}_${i.attendance_date}`)
      );
      const newlyAdded = generated.filter(
        i => !existingKeys.has(`${i.employee_id}_${i.attendance_date}`)
      );
      onUpdateDailyAttendance([...dailyAttendanceList, ...newlyAdded]);
    }

    setIsProcessing(false);
    onAddAuditLog(
      'GENERATE_DAILY_ATTENDANCE',
      'ATTENDANCE_DAILY',
      `Pembentukan absensi harian ${MONTHS_NAMES[selectedMonth - 1]} ${selectedYear}: ${generated.length} record diproses.`
    );
    showNotification(
      'success',
      `Absensi Harian ${MONTHS_NAMES[selectedMonth - 1]} ${selectedYear} berhasil dibentuk! (${generated.length} record dievaluasi).`
    );
  };

  const handleExportCSV = () => {
    if (filteredItems.length === 0) {
      showNotification('error', 'Tidak ada data untuk diekspor.');
      return;
    }

    const headers = [
      'No',
      'Tanggal',
      'Hari',
      'Emp Num',
      'No. ID',
      'NIK',
      'Nama Karyawan',
      'Unit',
      'Jabatan',
      'Jadwal Masuk',
      'Scan Masuk',
      'Jadwal Pulang',
      'Scan Pulang',
      'Status Masuk',
      'Status Pulang',
      'Status Kehadiran',
      'Scan Tidak Lengkap',
      'Multi Scan',
      'Catatan',
    ];

    const rows = filteredItems.map((item, idx) => [
      idx + 1,
      item.attendance_date,
      item.day_name,
      `"${item.emp_num}"`,
      `"${item.no_id}"`,
      `"${item.nik}"`,
      `"${item.nama}"`,
      `"${item.unit}"`,
      `"${item.jabatan}"`,
      item.scheduled_check_in,
      item.actual_check_in || '-',
      item.scheduled_check_out,
      item.actual_check_out || '-',
      item.check_in_status,
      item.check_out_status,
      item.attendance_status,
      item.has_incomplete_scan ? 'YA' : 'TIDAK',
      item.has_conflict ? 'YA' : 'TIDAK',
      `"${item.notes}"`,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,\uFEFF' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `Absensi_Harian_${selectedMonth}_${selectedYear}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    onAddAuditLog(
      'EXPORT_DAILY_ATTENDANCE',
      'ATTENDANCE_DAILY',
      `Ekspor CSV Absensi Harian periode ${MONTHS_NAMES[selectedMonth - 1]} ${selectedYear} (${filteredItems.length} data).`
    );
    showNotification('success', 'Data absensi harian berhasil diunduh dalam format CSV.');
  };

  const getAttendanceBadge = (status: AttendanceStatusType) => {
    switch (status) {
      case 'HADIR_LENGKAP':
        return (
          <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-emerald-100 text-emerald-800 border border-emerald-200">
            HADIR LENGKAP
          </span>
        );
      case 'HANYA_ABSEN_MASUK':
        return (
          <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-amber-100 text-amber-800 border border-amber-200">
            HANYA MASUK
          </span>
        );
      case 'HANYA_ABSEN_PULANG':
        return (
          <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-orange-100 text-orange-800 border border-orange-200">
            HANYA PULANG
          </span>
        );
      case 'DATA_BERMASALAH':
        return (
          <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-purple-100 text-purple-800 border border-purple-200">
            BERMASALAH
          </span>
        );
      case 'TIDAK_ABSEN':
      default:
        return (
          <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-red-100 text-red-800 border border-red-200">
            TIDAK ABSEN
          </span>
        );
    }
  };

  return (
    <div className="space-y-5">
      {/* Header Bar */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-900">Absensi Harian & Ketercukupan Scan</h3>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-semibold border border-blue-200">
              Tahap 4
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Hasil pemaduan Master Karyawan Aktif x Hari Kerja Kalender x Data Mentah Absensi Mesin.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg border border-slate-300 transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={() => handleGenerateDaily('REGENERATE')}
            disabled={isProcessing}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow transition cursor-pointer disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isProcessing ? 'Memproses...' : 'Bentuk Absensi Harian'}</span>
          </button>
        </div>
      </div>

      {notice && (
        <div className={`p-3 rounded-lg text-xs font-medium flex items-center gap-2 border ${
          notice.type === 'success'
            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
            : notice.type === 'error'
            ? 'bg-red-50 text-red-800 border-red-200'
            : 'bg-blue-50 text-blue-800 border-blue-200'
        }`}>
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{notice.text}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-[10px] font-bold text-slate-400 uppercase">Total Catatan</div>
          <div className="text-xl font-extrabold text-slate-900 mt-0.5">{totalRecords}</div>
          <div className="text-[10px] text-slate-500">Record Terbentuk</div>
        </div>

        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-[10px] font-bold text-emerald-600 uppercase">Hadir Lengkap</div>
          <div className="text-xl font-extrabold text-emerald-600 mt-0.5">{hadirLengkap}</div>
          <div className="text-[10px] text-slate-500">Scan In & Out Ada</div>
        </div>

        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-[10px] font-bold text-amber-600 uppercase">Hanya Masuk</div>
          <div className="text-xl font-extrabold text-amber-600 mt-0.5">{hanyaMasuk}</div>
          <div className="text-[10px] text-slate-500">Tanpa Scan Out</div>
        </div>

        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-[10px] font-bold text-orange-600 uppercase">Hanya Pulang</div>
          <div className="text-xl font-extrabold text-orange-600 mt-0.5">{hanyaPulang}</div>
          <div className="text-[10px] text-slate-500">Tanpa Scan In</div>
        </div>

        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-[10px] font-bold text-red-600 uppercase">Tidak Absen</div>
          <div className="text-xl font-extrabold text-red-600 mt-0.5">{tidakAbsen}</div>
          <div className="text-[10px] text-slate-500">Tanpa Transaksi</div>
        </div>

        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-[10px] font-bold text-purple-600 uppercase">Multi-Scan</div>
          <div className="text-xl font-extrabold text-purple-600 mt-0.5">{multiScanConflict}</div>
          <div className="text-[10px] text-slate-500">Earliest/Latest Diambil</div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Periode Bulan */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-600">Bulan:</span>
            <select
              value={selectedMonth}
              onChange={e => setSelectedMonth(Number(e.target.value))}
              className="text-xs border border-slate-300 rounded-lg px-2 py-1.5 bg-slate-50 font-medium"
            >
              {MONTHS_NAMES.map((name, idx) => (
                <option key={idx + 1} value={idx + 1}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          {/* Tahun */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-600">Tahun:</span>
            <select
              value={selectedYear}
              onChange={e => setSelectedYear(Number(e.target.value))}
              className="text-xs border border-slate-300 rounded-lg px-2 py-1.5 bg-slate-50 font-medium"
            >
              {[2024, 2025, 2026, 2027, 2028].map(yr => (
                <option key={yr} value={yr}>
                  {yr}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-600">Status:</span>
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              className="text-xs border border-slate-300 rounded-lg px-2 py-1.5 bg-slate-50 font-medium"
            >
              <option value="ALL">Semua Status</option>
              <option value="HADIR_LENGKAP">Hadir Lengkap</option>
              <option value="HANYA_ABSEN_MASUK">Hanya Absen Masuk</option>
              <option value="HANYA_ABSEN_PULANG">Hanya Absen Pulang</option>
              <option value="TIDAK_ABSEN">Tidak Absen</option>
            </select>
          </div>

          {/* Unit Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-600">Unit:</span>
            <select
              value={filterUnit}
              onChange={e => setFilterUnit(e.target.value)}
              className="text-xs border border-slate-300 rounded-lg px-2 py-1.5 bg-slate-50 font-medium max-w-xs"
            >
              <option value="ALL">Semua Unit Kerja</option>
              {uniqueUnits.map(u => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Cari nama, NIK, ID..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="text-xs pl-8 pr-3 py-1.5 border border-slate-300 rounded-lg bg-slate-50 w-48 sm:w-56 focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
      </div>

      {/* Tabel Absensi Harian */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-3 text-center w-12">No</th>
                <th className="p-3 text-center w-24">Tanggal</th>
                <th className="p-3 text-center w-20">Hari</th>
                <th className="p-3 w-20">Emp Num</th>
                <th className="p-3 w-20">No. ID</th>
                <th className="p-3">Nama Karyawan</th>
                <th className="p-3 w-32">Unit Kerja</th>
                <th className="p-3 text-center w-20">Jadwal In</th>
                <th className="p-3 text-center w-20">Scan In</th>
                <th className="p-3 text-center w-20">Jadwal Out</th>
                <th className="p-3 text-center w-20">Scan Out</th>
                <th className="p-3 text-center w-32">Status Kehadiran</th>
                <th className="p-3">Catatan / Anomali</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={13} className="p-8 text-center text-slate-400">
                    <Clock className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                    Belum ada data absensi harian untuk periode ini.
                    <br />
                    Klik tombol <strong>"Bentuk Absensi Harian"</strong> di atas untuk memproses.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item, idx) => (
                  <tr key={item.id} className="hover:bg-slate-50/80 transition">
                    <td className="p-3 text-center text-slate-500">{idx + 1}</td>
                    <td className="p-3 text-center font-mono font-bold text-slate-800">
                      {item.attendance_date.split('-').reverse().join('/')}
                    </td>
                    <td className="p-3 text-center text-slate-600">{item.day_name}</td>
                    <td className="p-3 font-mono text-slate-700">{item.emp_num}</td>
                    <td className="p-3 font-mono text-slate-700">{item.no_id}</td>
                    <td className="p-3 font-semibold text-slate-900">{item.nama}</td>
                    <td className="p-3 text-slate-600 truncate max-w-xs">{item.unit}</td>
                    <td className="p-3 text-center font-mono text-slate-600">{item.scheduled_check_in}</td>
                    <td className="p-3 text-center font-mono font-bold">
                      {item.actual_check_in ? (
                        <span className="text-emerald-700">{item.actual_check_in}</span>
                      ) : (
                        <span className="text-red-400">-</span>
                      )}
                    </td>
                    <td className="p-3 text-center font-mono text-slate-600">{item.scheduled_check_out}</td>
                    <td className="p-3 text-center font-mono font-bold">
                      {item.actual_check_out ? (
                        <span className="text-emerald-700">{item.actual_check_out}</span>
                      ) : (
                        <span className="text-red-400">-</span>
                      )}
                    </td>
                    <td className="p-3 text-center">{getAttendanceBadge(item.attendance_status)}</td>
                    <td className="p-3 text-[11px] text-slate-500">
                      {item.has_conflict && <span className="text-purple-600 font-bold mr-1">⚠️</span>}
                      {item.notes || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
