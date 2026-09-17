import React, { useState, useMemo } from 'react';
import { 
  Calculator, 
  FileText, 
  Search, 
  Download, 
  RotateCw, 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  Eye, 
  X, 
  Building2, 
  Users, 
  Clock, 
  ShieldAlert,
  Calendar as CalendarIcon,
  Printer,
  Sparkles
} from 'lucide-react';
import { 
  UserSession, 
  EmployeeItem, 
  WorkCalendarItem, 
  DailyAttendanceItem,
  SystemSettings,
  AttendanceDeductionItem,
  DeductionSummaryItem
} from '../types';

interface DeductionSimulatorViewProps {
  userSession: UserSession;
  employees: EmployeeItem[];
  calendarData: WorkCalendarItem[];
  dailyAttendanceList: DailyAttendanceItem[];
  settings: SystemSettings;
  deductionsList: AttendanceDeductionItem[];
  onUpdateDeductions: (newDeductions: AttendanceDeductionItem[]) => void;
  onAddAuditLog: (action: string, module: string, description: string) => void;
}

export const DeductionSimulatorView: React.FC<DeductionSimulatorViewProps> = ({
  userSession,
  employees,
  calendarData,
  dailyAttendanceList,
  settings,
  deductionsList,
  onUpdateDeductions,
  onAddAuditLog,
}) => {
  // Active Tab: 'calc' | 'rekap' | 'detail'
  const [activeSubTab, setActiveSubTab] = useState<'calc' | 'rekap' | 'detail'>('calc');

  // Filter Selection for Calculation (Tab 1)
  const [selectedYear, setSelectedYear] = useState('2026');
  const [selectedMonth, setSelectedMonth] = useState('8'); // Agustus
  const [selectedUnit, setSelectedUnit] = useState('ALL');
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string>('ALL');

  // Validation / Preview state
  const [isValidated, setIsValidated] = useState(false);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [calcSuccessBanner, setCalcSuccessBanner] = useState<string | null>(null);

  // Filters for Rekap (Tab 2)
  const [rekapSearch, setRekapSearch] = useState('');
  const [rekapUnitFilter, setRekapUnitFilter] = useState('ALL');

  // Filters for Harian (Tab 3)
  const [detailDateFilter, setDetailDateFilter] = useState('ALL');
  const [detailUnitFilter, setDetailUnitFilter] = useState('ALL');
  const [detailStatusFilter, setDetailStatusFilter] = useState('ALL');
  const [detailSearch, setDetailSearch] = useState('');

  // Modal Dialog for Single Day Detail
  const [selectedDetailModal, setSelectedDetailModal] = useState<AttendanceDeductionItem | null>(null);

  // Available unique units
  const uniqueUnits = useMemo(() => {
    const set = new Set(employees.map(e => e.unit).filter(Boolean));
    return Array.from(set).sort();
  }, [employees]);

  // Helper parse minutes from HH:MM
  const parseTimeToMinutes = (timeStr: string | null): number | null => {
    if (!timeStr || !timeStr.trim() || timeStr.trim() === '-') return null;
    const parts = timeStr.trim().split(':');
    if (parts.length < 2) return null;
    const h = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    if (isNaN(h) || isNaN(m)) return null;
    return h * 60 + m;
  };

  // Helper to format currency
  const formatRupiah = (amount: number) => {
    return `Rp ${amount.toLocaleString('id-ID')}`;
  };

  // 1. Calculate Deductions Core Engine
  const executeCalculation = (isRecalculate = false) => {
    setIsProcessing(true);
    setCalcSuccessBanner(null);

    setTimeout(() => {
      const lateLte60Rate = parseInt(settings.potongan_terlambat_sd_1jam, 10) || 7500;
      const lateGt60Rate = parseInt(settings.potongan_terlambat_gt_1jam, 10) || 10000;
      const earlyLeaveRate = parseInt(settings.potongan_pulang_cepat, 10) || 10000;
      const missingInRate = parseInt(settings.potongan_tidak_absen_masuk, 10) || 10000;
      const missingOutRate = parseInt(settings.potongan_tidak_absen_pulang, 10) || 10000;

      // Filter daily items by year, month, unit, employee
      const targetMonthStr = selectedMonth.padStart(2, '0');
      const targetPeriodPrefix = `${selectedYear}-${targetMonthStr}`;

      const eligibleDaily = dailyAttendanceList.filter(daily => {
        if (!daily.attendance_date.startsWith(targetPeriodPrefix)) return false;
        if (selectedUnit !== 'ALL' && daily.unit !== selectedUnit) return false;
        if (selectedEmployeeId !== 'ALL' && String(daily.employee_id) !== selectedEmployeeId) return false;
        return true;
      });

      const newDeductions: AttendanceDeductionItem[] = [];

      for (const daily of eligibleDaily) {
        // Find matching calendar day
        const cal = calendarData.find(c => c.calendar_date === daily.attendance_date);
        const isWorking = cal ? cal.is_working_day : true;
        const schedIn = daily.scheduled_check_in || '08:15';
        const schedOut = daily.scheduled_check_out || '16:30';

        let lateMinutes = 0;
        let earlyLeaveMinutes = 0;
        let dedLate = 0;
        let dedEarly = 0;
        let dedMissingIn = 0;
        let dedMissingOut = 0;
        let totalDed = 0;
        let notes = '';

        if (!isWorking) {
          notes = `Bukan hari kerja (${cal?.calendar_status || 'AKHIR_PEKAN'}). Potongan Rp0.`;
        } else {
          const hasIn = Boolean(daily.actual_check_in && daily.actual_check_in.trim() && daily.actual_check_in !== '-');
          const hasOut = Boolean(daily.actual_check_out && daily.actual_check_out.trim() && daily.actual_check_out !== '-');

          // Case A: Missing both scans -> Tidak scan masuk & pulang (Rp20.000, no double counting)
          if (!hasIn && !hasOut) {
            dedMissingIn = missingInRate;
            dedMissingOut = missingOutRate;
            totalDed = dedMissingIn + dedMissingOut;
            notes = 'Tidak scan masuk & pulang. Potongan Tidak Absen Masuk + Tidak Absen Pulang (Rp20.000).';
          } 
          // Case B: Only check in
          else if (hasIn && !hasOut) {
            const actualInM = parseTimeToMinutes(daily.actual_check_in);
            const schedInM = parseTimeToMinutes(schedIn);
            if (actualInM && schedInM && actualInM > schedInM) {
              lateMinutes = actualInM - schedInM;
              dedLate = lateMinutes <= 60 ? lateLte60Rate : lateGt60Rate;
            }
            dedMissingOut = missingOutRate;
            totalDed = dedLate + dedMissingOut;
            notes = `Hanya scan masuk (${daily.actual_check_in}). `;
            if (dedLate > 0) notes += `Terlambat ${lateMinutes} mnt (${formatRupiah(dedLate)}). `;
            notes += `Tidak scan pulang (${formatRupiah(dedMissingOut)}).`;
          }
          // Case C: Only check out
          else if (!hasIn && hasOut) {
            dedMissingIn = missingInRate;
            const actualOutM = parseTimeToMinutes(daily.actual_check_out);
            const schedOutM = parseTimeToMinutes(schedOut);
            if (actualOutM && schedOutM && actualOutM < schedOutM) {
              earlyLeaveMinutes = schedOutM - actualOutM;
              dedEarly = earlyLeaveRate;
            }
            totalDed = dedMissingIn + dedEarly;
            notes = `Hanya scan pulang (${daily.actual_check_out}). Tidak scan masuk (${formatRupiah(dedMissingIn)}). `;
            if (dedEarly > 0) notes += `Pulang cepat ${earlyLeaveMinutes} mnt (${formatRupiah(dedEarly)}).`;
          }
          // Case D: Both scans present
          else {
            const actualInM = parseTimeToMinutes(daily.actual_check_in);
            const schedInM = parseTimeToMinutes(schedIn);
            if (actualInM && schedInM && actualInM > schedInM) {
              lateMinutes = actualInM - schedInM;
              dedLate = lateMinutes <= 60 ? lateLte60Rate : lateGt60Rate;
            }

            const actualOutM = parseTimeToMinutes(daily.actual_check_out);
            const schedOutM = parseTimeToMinutes(schedOut);
            if (actualOutM && schedOutM && actualOutM < schedOutM) {
              earlyLeaveMinutes = schedOutM - actualOutM;
              dedEarly = earlyLeaveRate;
            }

            totalDed = dedLate + dedEarly;
            if (totalDed === 0) {
              notes = 'Hadir tepat waktu & pulang sesuai jadwal. Bebas potongan.';
            } else {
              const parts = [];
              if (dedLate > 0) parts.push(`Terlambat ${lateMinutes} mnt (${formatRupiah(dedLate)})`);
              if (dedEarly > 0) parts.push(`Pulang cepat ${earlyLeaveMinutes} mnt (${formatRupiah(dedEarly)})`);
              notes = parts.join(', ');
            }
          }
        }

        newDeductions.push({
          id: daily.id * 10 + 5,
          daily_attendance_id: daily.id,
          employee_id: daily.employee_id,
          emp_num: daily.emp_num,
          no_id: daily.no_id,
          nik: daily.nik,
          nama: daily.nama,
          unit: daily.unit,
          jabatan: daily.jabatan,
          attendance_date: daily.attendance_date,
          day_name: daily.day_name,
          scheduled_check_in: schedIn,
          scheduled_check_out: schedOut,
          actual_check_in: daily.actual_check_in,
          actual_check_out: daily.actual_check_out,
          attendance_status: daily.attendance_status,
          is_working_day: isWorking,
          late_minutes: lateMinutes,
          early_leave_minutes: earlyLeaveMinutes,
          deduction_late: dedLate,
          deduction_early_leave: dedEarly,
          deduction_missing_check_in: dedMissingIn,
          deduction_missing_check_out: dedMissingOut,
          total_deduction: totalDed,
          calculation_version: '5.0.0',
          calculated_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
          notes,
        });
      }

      onUpdateDeductions(newDeductions);
      setIsProcessing(false);
      setCalcSuccessBanner(
        isRecalculate
          ? `Hitung ulang berhasil! Memperbarui ${newDeductions.length} baris potongan absensi untuk periode ${selectedYear}-${targetMonthStr}.`
          : `Perhitungan selesai! Berhasil memproses ${newDeductions.length} baris potongan absensi dengan versi mesin kalkulasi 5.0.0.`
      );

      onAddAuditLog(
        isRecalculate ? 'RECALCULATE_DEDUCTIONS' : 'CALCULATE_DEDUCTIONS',
        'DEDUCTIONS',
        `Menjalankan kalkulasi potongan absensi periode ${selectedYear}-${targetMonthStr} (${newDeductions.length} data diproses).`
      );
    }, 600);
  };

  // Validation check handler
  const handleValidateData = () => {
    setIsValidated(true);
    const targetMonthStr = selectedMonth.padStart(2, '0');
    const targetPeriodPrefix = `${selectedYear}-${targetMonthStr}`;
    const matchedDaily = dailyAttendanceList.filter(d => d.attendance_date.startsWith(targetPeriodPrefix));

    if (matchedDaily.length === 0) {
      setValidationMessage('Peringatan: Belum ada data absensi harian pada periode ini. Pastikan Anda telah meng-generate absensi harian di modul Data Absensi terlebih dahulu.');
    } else {
      setValidationMessage(`Validasi Berhasil: Ditemukan ${matchedDaily.length} rekaman absensi harian dan ${employees.length} master karyawan aktif siap dihitung potongannya.`);
    }
  };

  // Compute Aggregated Summaries (Tab 2)
  const summaries: DeductionSummaryItem[] = useMemo(() => {
    const map = new Map<number, DeductionSummaryItem>();

    // Initialize map from employees
    for (const emp of employees) {
      map.set(emp.id, {
        employee_id: emp.id,
        emp_num: emp.emp_num,
        no_id: emp.no_id,
        nik: emp.nik,
        nama: emp.nama,
        unit: emp.unit,
        jabatan: emp.jabatan,
        total_hadir: 0,
        total_terlambat: 0,
        total_pulang_cepat: 0,
        total_tanpa_scan: 0,
        total_potongan_terlambat: 0,
        total_potongan_pulang_cepat: 0,
        total_potongan_tanpa_scan: 0,
        total_nominal_potongan: 0,
      });
    }

    // Accumulate from deductionsList
    for (const d of deductionsList) {
      const item = map.get(d.employee_id);
      if (item) {
        if (d.attendance_status === 'HADIR_LENGKAP' || d.actual_check_in || d.actual_check_out) {
          item.total_hadir += 1;
        }
        if (d.late_minutes > 0) {
          item.total_terlambat += 1;
          item.total_potongan_terlambat += d.deduction_late;
        }
        if (d.early_leave_minutes > 0) {
          item.total_pulang_cepat += 1;
          item.total_potongan_pulang_cepat += d.deduction_early_leave;
        }
        if (d.deduction_missing_check_in > 0 || d.deduction_missing_check_out > 0) {
          item.total_tanpa_scan += 1;
          item.total_potongan_tanpa_scan += (d.deduction_missing_check_in + d.deduction_missing_check_out);
        }
        item.total_nominal_potongan += d.total_deduction;
      }
    }

    return Array.from(map.values());
  }, [employees, deductionsList]);

  // Filtered summaries
  const filteredSummaries = useMemo(() => {
    return summaries.filter(s => {
      if (rekapUnitFilter !== 'ALL' && s.unit !== rekapUnitFilter) return false;
      if (rekapSearch.trim()) {
        const q = rekapSearch.toLowerCase();
        const matchName = s.nama.toLowerCase().includes(q);
        const matchNik = s.nik.toLowerCase().includes(q);
        const matchJabatan = s.jabatan.toLowerCase().includes(q);
        if (!matchName && !matchNik && !matchJabatan) return false;
      }
      return true;
    });
  }, [summaries, rekapUnitFilter, rekapSearch]);

  // Overall KPI totals
  const overallKpi = useMemo(() => {
    let empWithDeductions = 0;
    let totalTerlambatCount = 0;
    let totalPulangCepatCount = 0;
    let totalTanpaScanCount = 0;
    let totalRupiahDeduction = 0;

    for (const s of filteredSummaries) {
      if (s.total_nominal_potongan > 0) empWithDeductions += 1;
      totalTerlambatCount += s.total_terlambat;
      totalPulangCepatCount += s.total_pulang_cepat;
      totalTanpaScanCount += s.total_tanpa_scan;
      totalRupiahDeduction += s.total_nominal_potongan;
    }

    return {
      empWithDeductions,
      totalTerlambatCount,
      totalPulangCepatCount,
      totalTanpaScanCount,
      totalRupiahDeduction,
    };
  }, [filteredSummaries]);

  // Filtered daily deductions (Tab 3)
  const filteredDailyDeductions = useMemo(() => {
    return deductionsList.filter(d => {
      if (detailDateFilter !== 'ALL' && d.attendance_date !== detailDateFilter) return false;
      if (detailUnitFilter !== 'ALL' && d.unit !== detailUnitFilter) return false;
      if (detailStatusFilter !== 'ALL' && d.attendance_status !== detailStatusFilter) return false;
      if (detailSearch.trim()) {
        const q = detailSearch.toLowerCase();
        const matchName = d.nama.toLowerCase().includes(q);
        const matchNik = d.nik.toLowerCase().includes(q);
        if (!matchName && !matchNik) return false;
      }
      return true;
    });
  }, [deductionsList, detailDateFilter, detailUnitFilter, detailStatusFilter, detailSearch]);

  // Unique dates in deductions
  const uniqueDates = useMemo(() => {
    const set = new Set(deductionsList.map(d => d.attendance_date));
    return Array.from(set).sort();
  }, [deductionsList]);

  // Mock export handler
  const handleExport = (format: 'excel' | 'pdf', target: string) => {
    const filename = `Laporan_Potongan_SIAP_${target}_${selectedYear}${selectedMonth.padStart(2, '0')}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
    alert(`[SIAP Export Service]\nBerkas berhasil digenerate:\nNama: ${filename}\nFormat: ${format.toUpperCase()}\nStatus: Siap diunduh sesuai standar Tahap 5.`);
    onAddAuditLog('EXPORT_REPORT', 'REPORTS', `Ekspor berkas ${format.toUpperCase()} (${filename})`);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              Perhitungan Status & Potongan Absensi
            </h2>
            <span className="text-[10px] bg-blue-100 text-blue-800 border border-blue-200 px-2 py-0.5 rounded font-mono font-bold">
              Versi Mesin: 5.0.0
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Mesin kalkulasi keterlambatan bertingkat, pulang cepat, deteksi scan tidak lengkap, dan rekapitulasi nominal potongan transparan tanpa double-counting.
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1.5 rounded-lg border border-slate-200 text-xs">
          <button
            onClick={() => setActiveSubTab('calc')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-bold transition cursor-pointer ${
              activeSubTab === 'calc'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200'
            }`}
          >
            <Calculator className="w-3.5 h-3.5" />
            <span>Mesin Hitung</span>
          </button>

          <button
            onClick={() => setActiveSubTab('rekap')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-bold transition cursor-pointer ${
              activeSubTab === 'rekap'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Rekapitulasi (9 Kolom)</span>
          </button>

          <button
            onClick={() => setActiveSubTab('detail')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-bold transition cursor-pointer ${
              activeSubTab === 'detail'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            <span>Detail Harian (17 Kolom)</span>
          </button>
        </div>
      </div>

      {/* Success Notification */}
      {calcSuccessBanner && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-medium flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{calcSuccessBanner}</span>
          </div>
          <button
            onClick={() => setCalcSuccessBanner(null)}
            className="text-emerald-700 hover:text-emerald-900 cursor-pointer p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* =========================================================================
         TAB 1: MESIN PERHITUNGAN POTONGAN
         ========================================================================= */}
      {activeSubTab === 'calc' && (
        <div className="space-y-6">
          {/* Card Parameter Filter & Validasi */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-sm text-slate-800 flex items-center gap-2">
                <CalendarIcon className="w-4 h-4 text-blue-600" />
                <span>Parameter Periode & Cakupan Kalkulasi</span>
              </h3>
              <span className="text-[11px] text-slate-500 font-mono">
                Basis Data: <code>attendance_daily</code> &times; <code>work_calendar</code>
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Tahun */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Tahun Acuan</label>
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs font-medium focus:ring-2 focus:ring-blue-600 focus:outline-none"
                >
                  <option value="2024">2024</option>
                  <option value="2025">2025</option>
                  <option value="2026">2026</option>
                </select>
              </div>

              {/* Bulan */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Bulan Operasional</label>
                <select
                  value={selectedMonth}
                  onChange={(e) => setSelectedMonth(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs font-medium focus:ring-2 focus:ring-blue-600 focus:outline-none"
                >
                  <option value="1">01 - Januari</option>
                  <option value="2">02 - Februari</option>
                  <option value="3">03 - Maret</option>
                  <option value="4">04 - April</option>
                  <option value="5">05 - Mei</option>
                  <option value="6">06 - Juni</option>
                  <option value="7">07 - Juli</option>
                  <option value="8">08 - Agustus</option>
                  <option value="9">09 - September</option>
                  <option value="10">10 - Oktober</option>
                  <option value="11">11 - November</option>
                  <option value="12">12 - Desember</option>
                </select>
              </div>

              {/* Unit Kerja */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Unit Kerja</label>
                <select
                  value={selectedUnit}
                  onChange={(e) => setSelectedUnit(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs font-medium focus:ring-2 focus:ring-blue-600 focus:outline-none"
                >
                  <option value="ALL">SEMUA UNIT KERJA</option>
                  {uniqueUnits.map(unit => (
                    <option key={unit} value={unit}>{unit}</option>
                  ))}
                </select>
              </div>

              {/* Karyawan Spesifik */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Karyawan</label>
                <select
                  value={selectedEmployeeId}
                  onChange={(e) => setSelectedEmployeeId(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs font-medium focus:ring-2 focus:ring-blue-600 focus:outline-none"
                >
                  <option value="ALL">Seluruh Karyawan ({employees.length})</option>
                  {employees.map(emp => (
                    <option key={emp.id} value={String(emp.id)}>
                      {emp.nama} ({emp.nik})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <button
                type="button"
                onClick={handleValidateData}
                className="flex items-center gap-1.5 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold border border-blue-200 rounded-lg text-xs transition cursor-pointer"
              >
                <Search className="w-3.5 h-3.5" />
                <span>Validasi & Cek Data Pra-Perhitungan</span>
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => executeCalculation(false)}
                  className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg text-xs shadow-sm transition cursor-pointer disabled:opacity-50"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{isProcessing ? 'Memproses Kalkulasi...' : 'Hitung Potongan Absensi'}</span>
                </button>

                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => executeCalculation(true)}
                  className="flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold rounded-lg text-xs transition cursor-pointer disabled:opacity-50"
                  title="Menghapus record potongan lama pada periode ini dan menghitung ulang secara atomik"
                >
                  <RotateCw className={`w-3.5 h-3.5 ${isProcessing ? 'animate-spin' : ''}`} />
                  <span>Hitung Ulang (Recalculate)</span>
                </button>
              </div>
            </div>
          </div>

          {/* Validation Status Notice */}
          {isValidated && validationMessage && (
            <div className={`p-4 rounded-xl border flex items-start gap-3 text-xs leading-relaxed ${
              validationMessage.startsWith('Validasi Berhasil')
                ? 'bg-blue-50 border-blue-200 text-blue-900'
                : 'bg-amber-50 border-amber-200 text-amber-900'
            }`}>
              {validationMessage.startsWith('Validasi Berhasil') ? (
                <CheckCircle2 className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              )}
              <div>
                <strong className="font-bold block mb-0.5">Status Pemeriksaan Data:</strong>
                <span>{validationMessage}</span>
              </div>
            </div>
          )}

          {/* Grid Informasi Aturan & Tarif Aktif */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Aturan Jam Kerja */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <span>Aturan Jam Operasional & Batas Dispensasi</span>
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="font-medium text-slate-700">Senin s/d Kamis</span>
                  <span className="font-bold text-slate-900 font-mono">
                    {settings.jam_masuk_senin_kamis} &mdash; {settings.jam_pulang_senin_kamis} WIB
                  </span>
                </div>
                <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="font-medium text-slate-700">Hari Jumat</span>
                  <span className="font-bold text-slate-900 font-mono">
                    {settings.jam_masuk_jumat} &mdash; {settings.jam_pulang_jumat} WIB
                  </span>
                </div>
                <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="font-medium text-slate-700">Sabtu & Minggu / Libur</span>
                  <span className="font-bold text-emerald-700">Libur (Bebas Potongan Rp0)</span>
                </div>
              </div>
            </div>

            {/* Tarif Pelanggaran */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-red-600" />
                <span>Tarif Potongan Aktif (Tabel Settings)</span>
              </h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-slate-500 block text-[11px]">Terlambat &le; 1 Jam</span>
                  <span className="font-bold text-red-600 font-mono">
                    {formatRupiah(parseInt(settings.potongan_terlambat_sd_1jam, 10) || 7500)}
                  </span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-slate-500 block text-[11px]">Terlambat &gt; 1 Jam</span>
                  <span className="font-bold text-red-600 font-mono">
                    {formatRupiah(parseInt(settings.potongan_terlambat_gt_1jam, 10) || 10000)}
                  </span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-slate-500 block text-[11px]">Pulang Lebih Cepat</span>
                  <span className="font-bold text-amber-600 font-mono">
                    {formatRupiah(parseInt(settings.potongan_pulang_cepat, 10) || 10000)}
                  </span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-slate-500 block text-[11px]">Tidak Absen Masuk</span>
                  <span className="font-bold text-red-600 font-mono">
                    {formatRupiah(parseInt(settings.potongan_tidak_absen_masuk, 10) || 10000)}
                  </span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-slate-500 block text-[11px]">Tidak Absen Pulang</span>
                  <span className="font-bold text-red-600 font-mono">
                    {formatRupiah(parseInt(settings.potongan_tidak_absen_pulang, 10) || 10000)}
                  </span>
                </div>
                <div className="p-2 rounded bg-slate-50 border border-slate-100">
                  <span className="text-slate-500 block text-[11px]">Tidak Absen Masuk & Pulang</span>
                  <span className="font-bold text-red-700 font-mono">
                    {formatRupiah(
                      (parseInt(settings.potongan_tidak_absen_masuk, 10) || 10000) +
                      (parseInt(settings.potongan_tidak_absen_pulang, 10) || 10000)
                    )}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Banner Pencegahan Double Counting */}
          <div className="bg-slate-900 text-slate-200 p-4 rounded-xl border border-slate-800 text-xs flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h5 className="font-bold text-white">Prinsip Pencegahan Double Counting (Anti-Duplikasi Potongan)</h5>
              <p className="text-slate-400 leading-relaxed">
                Jam masuk kosong <strong>TIDAK</strong> dihitung sebagai keterlambatan, melainkan tepat diklasifikasikan sebagai <em>Tidak Absen Masuk</em>. Demikian pula jam pulang kosong <strong>TIDAK</strong> dihitung sebagai pulang cepat. Karyawan yang sama sekali tidak scan masuk dan pulang dikenakan potongan <em>Tidak Absen Masuk (Rp10.000) + Tidak Absen Pulang (Rp10.000) = Rp20.000</em> tanpa tambahan biaya fiktif ganda.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
         TAB 2: REKAP DATA POTONGAN ABSENSI (9 KOLOM WAJIB)
         ========================================================================= */}
      {activeSubTab === 'rekap' && (
        <div className="space-y-6">
          {/* KPI Mini Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                Karyawan Terkena Potongan
              </span>
              <div className="text-2xl font-black text-slate-900">
                {overallKpi.empWithDeductions} / {filteredSummaries.length}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">Memiliki nominal &gt; Rp0</p>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                Total Kejadian Terlambat
              </span>
              <div className="text-2xl font-black text-amber-600">
                {overallKpi.totalTerlambatCount}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">Scan melebihi jam masuk</p>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                Total Pulang Cepat
              </span>
              <div className="text-2xl font-black text-amber-600">
                {overallKpi.totalPulangCepatCount}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">Scan sebelum jam pulang</p>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                Total Tanpa Scan
              </span>
              <div className="text-2xl font-black text-red-600">
                {overallKpi.totalTanpaScanCount}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">Tidak masuk/pulang/alfa</p>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm lg:col-span-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                Total Akumulasi Potongan
              </span>
              <div className="text-2xl font-black text-red-600">
                {formatRupiah(overallKpi.totalRupiahDeduction)}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">Nominal rupiah bruto</p>
            </div>
          </div>

          {/* Action & Filter Bar */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3">
              {/* Search */}
              <div className="relative w-64">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={rekapSearch}
                  onChange={(e) => setRekapSearch(e.target.value)}
                  placeholder="Cari nama, NIK, jabatan..."
                  className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              {/* Unit Filter */}
              <div className="flex items-center gap-1.5 text-xs text-slate-600 font-semibold">
                <span>Unit:</span>
                <select
                  value={rekapUnitFilter}
                  onChange={(e) => setRekapUnitFilter(e.target.value)}
                  className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-blue-600"
                >
                  <option value="ALL">Semua Unit</option>
                  {uniqueUnits.map(unit => (
                    <option key={unit} value={unit}>{unit}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Export Buttons */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => handleExport('excel', 'Rekapitulasi')}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm transition cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export Excel</span>
              </button>

              <button
                type="button"
                onClick={() => handleExport('pdf', 'Rekapitulasi')}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold shadow-sm transition cursor-pointer"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Cetak Rekap PDF</span>
              </button>
            </div>
          </div>

          {/* Tabel Rekap 9 Kolom Wajib */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 bg-slate-50/70 flex items-center justify-between">
              <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider">
                Tabel Rekapitulasi Potongan Absensi Pegawai (9 Kolom Standar SIAP)
              </h4>
              <span className="text-[11px] font-mono text-slate-500">
                {filteredSummaries.length} Data Ditampilkan
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="p-3 w-12 text-center">No</th>
                    <th className="p-3">NIK</th>
                    <th className="p-3">Nama Pegawai</th>
                    <th className="p-3">Unit Kerja</th>
                    <th className="p-3">Jabatan</th>
                    <th className="p-3 text-right">Terlambat (Kali / Rp)</th>
                    <th className="p-3 text-right">Pulang Cepat (Kali / Rp)</th>
                    <th className="p-3 text-right">Tanpa Scan (Kali / Rp)</th>
                    <th className="p-3 text-right bg-red-50 text-red-900">Total Potongan (Rp)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredSummaries.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="p-8 text-center text-slate-400">
                        Tidak ada data rekapitulasi yang cocok dengan filter atau kalkulasi belum dijalankan.
                      </td>
                    </tr>
                  ) : (
                    filteredSummaries.map((s, idx) => (
                      <tr key={s.employee_id} className="hover:bg-slate-50 transition">
                        <td className="p-3 text-center text-slate-500 font-mono">{idx + 1}</td>
                        <td className="p-3 font-mono text-slate-700">{s.nik}</td>
                        <td className="p-3 font-bold text-slate-900">{s.nama}</td>
                        <td className="p-3 text-slate-600">{s.unit}</td>
                        <td className="p-3 text-slate-600">{s.jabatan}</td>
                        <td className="p-3 text-right font-mono">
                          {s.total_terlambat > 0 ? (
                            <span className="text-amber-700 font-semibold">
                              {s.total_terlambat}x ({formatRupiah(s.total_potongan_terlambat)})
                            </span>
                          ) : (
                            <span className="text-slate-400">0</span>
                          )}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {s.total_pulang_cepat > 0 ? (
                            <span className="text-amber-700 font-semibold">
                              {s.total_pulang_cepat}x ({formatRupiah(s.total_potongan_pulang_cepat)})
                            </span>
                          ) : (
                            <span className="text-slate-400">0</span>
                          )}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {s.total_tanpa_scan > 0 ? (
                            <span className="text-red-700 font-semibold">
                              {s.total_tanpa_scan}x ({formatRupiah(s.total_potongan_tanpa_scan)})
                            </span>
                          ) : (
                            <span className="text-slate-400">0</span>
                          )}
                        </td>
                        <td className="p-3 text-right font-mono font-extrabold text-red-600 bg-red-50/50">
                          {formatRupiah(s.total_nominal_potongan)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
                <tfoot className="bg-slate-100 font-bold text-slate-800 border-t border-slate-200">
                  <tr>
                    <td colSpan={5} className="p-3 text-right uppercase tracking-wider text-[11px]">
                      Total Keseluruhan:
                    </td>
                    <td className="p-3 text-right font-mono text-amber-700">
                      {overallKpi.totalTerlambatCount}x
                    </td>
                    <td className="p-3 text-right font-mono text-amber-700">
                      {overallKpi.totalPulangCepatCount}x
                    </td>
                    <td className="p-3 text-right font-mono text-red-700">
                      {overallKpi.totalTanpaScanCount}x
                    </td>
                    <td className="p-3 text-right font-mono text-red-700 bg-red-100/70 text-sm">
                      {formatRupiah(overallKpi.totalRupiahDeduction)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
         TAB 3: DATA ABSENSI & POTONGAN HARIAN (17 KOLOM LENGKAP)
         ========================================================================= */}
      {activeSubTab === 'detail' && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3">
              {/* Tanggal */}
              <div className="flex items-center gap-1.5 text-xs text-slate-600 font-semibold">
                <span>Tanggal:</span>
                <select
                  value={detailDateFilter}
                  onChange={(e) => setDetailDateFilter(e.target.value)}
                  className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-blue-600 font-mono"
                >
                  <option value="ALL">Semua Tanggal</option>
                  {uniqueDates.map(date => (
                    <option key={date} value={date}>{date}</option>
                  ))}
                </select>
              </div>

              {/* Unit */}
              <div className="flex items-center gap-1.5 text-xs text-slate-600 font-semibold">
                <span>Unit:</span>
                <select
                  value={detailUnitFilter}
                  onChange={(e) => setDetailUnitFilter(e.target.value)}
                  className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-blue-600"
                >
                  <option value="ALL">Semua Unit</option>
                  {uniqueUnits.map(u => (
                    <option key={u} value={u}>{u}</option>
                  ))}
                </select>
              </div>

              {/* Status */}
              <div className="flex items-center gap-1.5 text-xs text-slate-600 font-semibold">
                <span>Status:</span>
                <select
                  value={detailStatusFilter}
                  onChange={(e) => setDetailStatusFilter(e.target.value)}
                  className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-blue-600"
                >
                  <option value="ALL">Semua Status</option>
                  <option value="HADIR_LENGKAP">HADIR_LENGKAP</option>
                  <option value="HANYA_ABSEN_MASUK">HANYA_ABSEN_MASUK</option>
                  <option value="HANYA_ABSEN_PULANG">HANYA_ABSEN_PULANG</option>
                  <option value="TIDAK_ABSEN">TIDAK_ABSEN</option>
                </select>
              </div>

              {/* Search */}
              <div className="relative w-48">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
                <input
                  type="text"
                  value={detailSearch}
                  onChange={(e) => setDetailSearch(e.target.value)}
                  placeholder="Cari nama / NIK..."
                  className="w-full pl-8 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-600"
                />
              </div>
            </div>

            {/* Export Buttons */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => handleExport('excel', 'Harian')}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm transition cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export Excel</span>
              </button>

              <button
                type="button"
                onClick={() => handleExport('pdf', 'Harian')}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold shadow-sm transition cursor-pointer"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Cetak PDF</span>
              </button>
            </div>
          </div>

          {/* 17 Kolom Tabel Detail Harian */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 bg-slate-50/70 flex items-center justify-between">
              <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider">
                Rincian Absensi & Kalkulasi Potongan Harian (17 Kolom Terinci)
              </h4>
              <span className="text-[11px] font-mono text-slate-500">
                {filteredDailyDeductions.length} Baris Data
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200 whitespace-nowrap">
                  <tr>
                    <th className="p-3 w-10 text-center">No</th>
                    <th className="p-3">Tanggal</th>
                    <th className="p-3">Hari</th>
                    <th className="p-3">NIK</th>
                    <th className="p-3">Nama Pegawai</th>
                    <th className="p-3">Unit</th>
                    <th className="p-3">Jadwal Masuk</th>
                    <th className="p-3">Jadwal Pulang</th>
                    <th className="p-3">Scan Masuk</th>
                    <th className="p-3">Scan Pulang</th>
                    <th className="p-3">Status Kehadiran</th>
                    <th className="p-3 text-right">Terlambat (Mnt)</th>
                    <th className="p-3 text-right">Pulang Cepat (Mnt)</th>
                    <th className="p-3 text-right">Potongan Terlambat</th>
                    <th className="p-3 text-right">Potongan Pulang Cepat</th>
                    <th className="p-3 text-right">Potongan Tanpa Scan</th>
                    <th className="p-3 text-right bg-red-50 text-red-900">Total Potongan</th>
                    <th className="p-3 text-center">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 whitespace-nowrap">
                  {filteredDailyDeductions.length === 0 ? (
                    <tr>
                      <td colSpan={18} className="p-8 text-center text-slate-400">
                        Belum ada rekaman kalkulasi harian. Jalankan proses di tab Mesin Hitung terlebih dahulu.
                      </td>
                    </tr>
                  ) : (
                    filteredDailyDeductions.map((d, idx) => (
                      <tr key={d.id} className="hover:bg-slate-50 transition">
                        <td className="p-3 text-center font-mono text-slate-500">{idx + 1}</td>
                        <td className="p-3 font-mono font-medium text-slate-800">{d.attendance_date}</td>
                        <td className="p-3 text-slate-600">{d.day_name}</td>
                        <td className="p-3 font-mono text-slate-700">{d.nik}</td>
                        <td className="p-3 font-bold text-slate-900">{d.nama}</td>
                        <td className="p-3 text-slate-600">{d.unit}</td>
                        <td className="p-3 font-mono text-slate-500">{d.scheduled_check_in}</td>
                        <td className="p-3 font-mono text-slate-500">{d.scheduled_check_out}</td>
                        <td className="p-3 font-mono">
                          {d.actual_check_in ? (
                            <span className="text-slate-800 font-semibold">{d.actual_check_in}</span>
                          ) : (
                            <span className="text-red-500 font-bold">&ndash;</span>
                          )}
                        </td>
                        <td className="p-3 font-mono">
                          {d.actual_check_out ? (
                            <span className="text-slate-800 font-semibold">{d.actual_check_out}</span>
                          ) : (
                            <span className="text-red-500 font-bold">&ndash;</span>
                          )}
                        </td>
                        <td className="p-3">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                              d.attendance_status === 'HADIR_LENGKAP'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : d.attendance_status === 'TIDAK_ABSEN'
                                ? 'bg-red-50 text-red-700 border-red-200'
                                : 'bg-amber-50 text-amber-700 border-amber-200'
                            }`}
                          >
                            {d.attendance_status}
                          </span>
                        </td>
                        <td className="p-3 text-right font-mono">
                          {d.late_minutes > 0 ? (
                            <span className="text-amber-600 font-bold">+{d.late_minutes} mnt</span>
                          ) : (
                            <span className="text-slate-400">0</span>
                          )}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {d.early_leave_minutes > 0 ? (
                            <span className="text-amber-600 font-bold">-{d.early_leave_minutes} mnt</span>
                          ) : (
                            <span className="text-slate-400">0</span>
                          )}
                        </td>
                        <td className="p-3 text-right font-mono text-slate-700">
                          {formatRupiah(d.deduction_late)}
                        </td>
                        <td className="p-3 text-right font-mono text-slate-700">
                          {formatRupiah(d.deduction_early_leave)}
                        </td>
                        <td className="p-3 text-right font-mono text-slate-700">
                          {formatRupiah(d.deduction_missing_check_in + d.deduction_missing_check_out)}
                        </td>
                        <td className="p-3 text-right font-mono font-black text-red-600 bg-red-50/50">
                          {formatRupiah(d.total_deduction)}
                        </td>
                        <td className="p-3 text-center">
                          <button
                            type="button"
                            onClick={() => setSelectedDetailModal(d)}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-700 rounded text-[11px] font-semibold transition cursor-pointer border border-slate-200"
                            title="Buka rincian logika potongan langkah demi langkah"
                          >
                            <Eye className="w-3 h-3" />
                            <span>Rincian</span>
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
         MODAL DIALOG: RINCIAN PERHITUNGAN POTONGAN HARIAN (DeductionDetailDialog)
         ========================================================================= */}
      {selectedDetailModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-4 bg-slate-900 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded bg-blue-600 flex items-center justify-center font-bold text-xs">
                  5.0
                </div>
                <div>
                  <h4 className="font-bold text-sm leading-tight">Detail Perhitungan Potongan Harian</h4>
                  <p className="text-[11px] text-blue-300">PySide6 DeductionDetailDialog Simulator</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedDetailModal(null)}
                className="text-slate-400 hover:text-white p-1 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 space-y-4 max-h-[80vh] overflow-y-auto text-xs">
              {/* Pegawai Card */}
              <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500 font-semibold">Nama Pegawai:</span>
                  <span className="font-bold text-slate-900">{selectedDetailModal.nama}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-semibold">NIK / No ID:</span>
                  <span className="font-mono text-slate-800">{selectedDetailModal.nik}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-semibold">Unit & Jabatan:</span>
                  <span className="text-slate-700">{selectedDetailModal.unit} &bull; {selectedDetailModal.jabatan}</span>
                </div>
                <div className="flex justify-between border-t border-slate-200 pt-1.5">
                  <span className="text-slate-500 font-semibold">Tanggal & Hari:</span>
                  <span className="font-bold text-blue-700">
                    {selectedDetailModal.day_name}, {selectedDetailModal.attendance_date}
                  </span>
                </div>
              </div>

              {/* Komparasi Jam */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <h5 className="font-bold text-slate-700 mb-1.5 text-[11px] uppercase tracking-wide">
                    Sesi Masuk Kerja
                  </h5>
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Jadwal:</span>
                      <span className="font-mono font-semibold text-slate-800">{selectedDetailModal.scheduled_check_in}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Scan Masuk:</span>
                      <span className="font-mono font-bold text-blue-700">
                        {selectedDetailModal.actual_check_in || 'TIDAK ADA'}
                      </span>
                    </div>
                    <div className="flex justify-between border-t border-slate-200 pt-1">
                      <span className="text-slate-500">Keterlambatan:</span>
                      <span className="font-mono font-bold text-amber-700">
                        {selectedDetailModal.late_minutes} Menit
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <h5 className="font-bold text-slate-700 mb-1.5 text-[11px] uppercase tracking-wide">
                    Sesi Pulang Kerja
                  </h5>
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Jadwal:</span>
                      <span className="font-mono font-semibold text-slate-800">{selectedDetailModal.scheduled_check_out}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Scan Pulang:</span>
                      <span className="font-mono font-bold text-blue-700">
                        {selectedDetailModal.actual_check_out || 'TIDAK ADA'}
                      </span>
                    </div>
                    <div className="flex justify-between border-t border-slate-200 pt-1">
                      <span className="text-slate-500">Pulang Cepat:</span>
                      <span className="font-mono font-bold text-amber-700">
                        {selectedDetailModal.early_leave_minutes} Menit
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Rincian Komponen Potongan */}
              <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                <h5 className="font-bold text-slate-800 text-[11px] uppercase tracking-wide mb-2">
                  Rincian Komponen Potongan Nominal
                </h5>

                <div className="flex justify-between items-center py-1 border-b border-slate-200">
                  <span className="text-slate-600">
                    1. Potongan Terlambat {selectedDetailModal.late_minutes > 0 ? `(${selectedDetailModal.late_minutes} menit)` : ''}
                  </span>
                  <span className="font-mono font-bold text-slate-900">
                    {formatRupiah(selectedDetailModal.deduction_late)}
                  </span>
                </div>

                <div className="flex justify-between items-center py-1 border-b border-slate-200">
                  <span className="text-slate-600">
                    2. Potongan Pulang Cepat {selectedDetailModal.early_leave_minutes > 0 ? `(${selectedDetailModal.early_leave_minutes} menit)` : ''}
                  </span>
                  <span className="font-mono font-bold text-slate-900">
                    {formatRupiah(selectedDetailModal.deduction_early_leave)}
                  </span>
                </div>

                <div className="flex justify-between items-center py-1 border-b border-slate-200">
                  <span className="text-slate-600">3. Potongan Tidak Absen Masuk</span>
                  <span className="font-mono font-bold text-slate-900">
                    {formatRupiah(selectedDetailModal.deduction_missing_check_in)}
                  </span>
                </div>

                <div className="flex justify-between items-center py-1 border-b border-slate-200">
                  <span className="text-slate-600">4. Potongan Tidak Absen Pulang</span>
                  <span className="font-mono font-bold text-slate-900">
                    {formatRupiah(selectedDetailModal.deduction_missing_check_out)}
                  </span>
                </div>

                <div className="flex justify-between items-center pt-2 font-bold text-sm text-red-600 bg-red-50 p-2 rounded">
                  <span>Total Potongan Akhir:</span>
                  <span className="font-mono text-base">
                    {formatRupiah(selectedDetailModal.total_deduction)}
                  </span>
                </div>
              </div>

              {/* Catatan / Keterangan Sistem */}
              <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-lg text-blue-900 text-xs">
                <strong className="block font-bold mb-0.5">Penjelasan Sistem:</strong>
                <span>{selectedDetailModal.notes}</span>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-slate-100 border-t border-slate-200 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedDetailModal(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white font-semibold rounded-lg text-xs transition cursor-pointer"
              >
                Tutup Dialog
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
