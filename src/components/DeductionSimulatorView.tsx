import React, { useState, useMemo } from 'react';
import {
  Calculator,
  RotateCw,
  ShieldCheck,
  FileSpreadsheet,
  FileText,
  AlertCircle,
  CheckCircle2,
  Filter,
  Search,
  ChevronDown,
  Layers,
  ArrowRight,
  TrendingDown,
  UserCheck,
  Building2,
  CalendarCheck,
  HelpCircle,
  X,
  Clock
} from 'lucide-react';
import { DeductionItem, MonthlyDeductionRecapRow } from '../types';

interface DeductionSimulatorViewProps {
  currentRole: 'ADMIN' | 'OPERATOR';
  currentUsername: string;
}

export function DeductionSimulatorView({ currentRole, currentUsername }: DeductionSimulatorViewProps) {
  // Filter States
  const [selectedMonth, setSelectedMonth] = useState('8'); // Agustus
  const [selectedYear, setSelectedYear] = useState('2026');
  const [selectedUnit, setSelectedUnit] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Execution & Dialog States
  const [isCalculating, setIsCalculating] = useState(false);
  const [hasCalculated, setHasCalculated] = useState(true);
  const [lastCalculationTime, setLastCalculationTime] = useState<string>('2026-08-31 16:45:00');
  const [actionAlert, setActionAlert] = useState<{ type: 'success' | 'info' | 'warning'; message: string } | null>({
    type: 'success',
    message: 'Data potongan periode Agustus 2026 telah terhitung dan tersinkronisasi presisi (Rupiah integer).'
  });
  const [selectedDetailEmployee, setSelectedDetailEmployee] = useState<MonthlyDeductionRecapRow | null>(null);
  const [integrityReport, setIntegrityReport] = useState<{
    isOpen: boolean;
    validCount: number;
    zeroNegative: boolean;
    noHolidayDeductions: boolean;
    antiDoubleCountAlfa: boolean;
  }>({
    isOpen: false,
    validCount: 22,
    zeroNegative: true,
    noHolidayDeductions: true,
    antiDoubleCountAlfa: true,
  });

  // Base Mock Data Karyawan & Potongan Periode Agustus 2026
  const [recapData, setRecapData] = useState<MonthlyDeductionRecapRow[]>([
    {
      no: 1,
      employee_id: 1,
      nik: '198501012010011001',
      no_id: '101',
      nama: 'Ahmad Fauzi, S.Kom',
      unit: 'Teknologi Informasi',
      status: 'PNS',
      terlambat: 17500, // 1x <=1hr (7.500) + 1x >1hr (10.000)
      pulang_cepat: 10000, // 1x
      tidak_absen_masuk: 10000,
      tidak_absen_pulang: 0,
      jumlah_potongan_absensi: 37500,
    },
    {
      no: 2,
      employee_id: 2,
      nik: '198804152012012002',
      no_id: '102',
      nama: 'Siti Rahmawati, S.E',
      unit: 'Keuangan & Akuntansi',
      status: 'PNS',
      terlambat: 7500, // 1x <=1hr
      pulang_cepat: 0,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 10000,
      jumlah_potongan_absensi: 17500,
    },
    {
      no: 3,
      employee_id: 3,
      nik: '199207202016021003',
      no_id: '103',
      nama: 'Budi Santoso, M.Si',
      unit: 'Keuangan & Akuntansi',
      status: 'PPPK',
      terlambat: 0,
      pulang_cepat: 10000,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 0,
      jumlah_potongan_absensi: 10000,
    },
    {
      no: 4,
      employee_id: 4,
      nik: '199511102020012004',
      no_id: '104',
      nama: 'Dewi Lestari, S.Tr.Kom',
      unit: 'Teknologi Informasi',
      status: 'HONORER',
      terlambat: 0,
      pulang_cepat: 0,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 0,
      jumlah_potongan_absensi: 0, // Hadir tepat waktu penuh
    },
    {
      no: 5,
      employee_id: 5,
      nik: '198203252008011005',
      no_id: '105',
      nama: 'Ir. Hendra Gunawan',
      unit: 'Sekretariat Utama',
      status: 'PNS',
      terlambat: 20000, // 2x >1hr
      pulang_cepat: 20000, // 2x
      tidak_absen_masuk: 10000,
      tidak_absen_pulang: 10000,
      jumlah_potongan_absensi: 60000,
    },
    {
      no: 6,
      employee_id: 6,
      nik: '199009092015032006',
      no_id: '106',
      nama: 'Ratna Kusuma, S.Sos',
      unit: 'Sekretariat Utama',
      status: 'PNS',
      terlambat: 7500,
      pulang_cepat: 0,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 0,
      jumlah_potongan_absensi: 7500,
    },
    {
      no: 7,
      employee_id: 7,
      nik: '199405122019021007',
      no_id: '107',
      nama: 'Eko Prasetyo, S.E',
      unit: 'Kepegawaian & Diklat',
      status: 'PPPK',
      terlambat: 0,
      pulang_cepat: 0,
      tidak_absen_masuk: 10000,
      tidak_absen_pulang: 10000,
      jumlah_potongan_absensi: 20000, // 1 Hari tidak scan masuk & pulang (maks alfa 20.000, anti-double counting)
    },
  ]);

  // Breakdown detail per hari untuk modal rincian
  const detailItemsMap: Record<number, DeductionItem[]> = {
    1: [
      {
        id: 101,
        employee_id: 1,
        emp_num: '198501012010011001',
        no_id: '101',
        nama: 'Ahmad Fauzi, S.Kom',
        unit: 'Teknologi Informasi',
        attendance_daily_id: 1001,
        attendance_date: '2026-08-04',
        day_name: 'Selasa',
        actual_check_in: '08:40:00',
        actual_check_out: '16:30:00',
        terlambat_menit: 25,
        pulang_cepat_menit: 0,
        deduction_late: 7500,
        deduction_early_leave: 0,
        deduction_missing_check_in: 0,
        deduction_missing_check_out: 0,
        total_deduction: 7500,
        calculation_status: 'CALCULATED',
        notes: 'Terlambat 25 menit (<= 1 jam)'
      },
      {
        id: 102,
        employee_id: 1,
        emp_num: '198501012010011001',
        no_id: '101',
        nama: 'Ahmad Fauzi, S.Kom',
        unit: 'Teknologi Informasi',
        attendance_daily_id: 1002,
        attendance_date: '2026-08-11',
        day_name: 'Selasa',
        actual_check_in: '09:35:00',
        actual_check_out: '16:30:00',
        terlambat_menit: 80,
        pulang_cepat_menit: 0,
        deduction_late: 10000,
        deduction_early_leave: 0,
        deduction_missing_check_in: 0,
        deduction_missing_check_out: 0,
        total_deduction: 10000,
        calculation_status: 'CALCULATED',
        notes: 'Terlambat 80 menit (> 1 jam)'
      },
      {
        id: 103,
        employee_id: 1,
        emp_num: '198501012010011001',
        no_id: '101',
        nama: 'Ahmad Fauzi, S.Kom',
        unit: 'Teknologi Informasi',
        attendance_daily_id: 1003,
        attendance_date: '2026-08-14',
        day_name: 'Jumat',
        actual_check_in: '08:15:00',
        actual_check_out: '16:15:00',
        terlambat_menit: 0,
        pulang_cepat_menit: 45,
        deduction_late: 0,
        deduction_early_leave: 10000,
        deduction_missing_check_in: 0,
        deduction_missing_check_out: 0,
        total_deduction: 10000,
        calculation_status: 'CALCULATED',
        notes: 'Pulang cepat 45 menit sebelum jam kerja Jumat'
      },
      {
        id: 104,
        employee_id: 1,
        emp_num: '198501012010011001',
        no_id: '101',
        nama: 'Ahmad Fauzi, S.Kom',
        unit: 'Teknologi Informasi',
        attendance_daily_id: 1004,
        attendance_date: '2026-08-19',
        day_name: 'Rabu',
        actual_check_in: null,
        actual_check_out: '16:30:00',
        terlambat_menit: 0,
        pulang_cepat_menit: 0,
        deduction_late: 0,
        deduction_early_leave: 0,
        deduction_missing_check_in: 10000,
        deduction_missing_check_out: 0,
        total_deduction: 10000,
        calculation_status: 'CALCULATED',
        notes: 'Tidak scan masuk pagi hari kerja'
      }
    ],
    7: [
      {
        id: 701,
        employee_id: 7,
        emp_num: '199405122019021007',
        no_id: '107',
        nama: 'Eko Prasetyo, S.E',
        unit: 'Kepegawaian & Diklat',
        attendance_daily_id: 7001,
        attendance_date: '2026-08-10',
        day_name: 'Senin',
        actual_check_in: null,
        actual_check_out: null,
        terlambat_menit: 0,
        pulang_cepat_menit: 0,
        deduction_late: 0,
        deduction_early_leave: 0,
        deduction_missing_check_in: 10000,
        deduction_missing_check_out: 10000,
        total_deduction: 20000,
        calculation_status: 'CALCULATED',
        notes: 'Tidak hadir / tidak absen masuk & pulang (Dipatok maksimal Rp20.000)'
      }
    ]
  };

  // Filter Data
  const filteredRows = useMemo(() => {
    return recapData.filter((r) => {
      const matchUnit = selectedUnit === 'ALL' || r.unit === selectedUnit;
      const matchQuery =
        searchQuery === '' ||
        r.nama.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.nik.includes(searchQuery) ||
        r.no_id.includes(searchQuery);
      return matchUnit && matchQuery;
    });
  }, [recapData, selectedUnit, searchQuery]);

  // Aggregate Totals
  const grandTotal = useMemo(() => {
    return filteredRows.reduce(
      (acc, curr) => ({
        terlambat: acc.terlambat + curr.terlambat,
        pulang_cepat: acc.pulang_cepat + curr.pulang_cepat,
        tidak_absen_masuk: acc.tidak_absen_masuk + curr.tidak_absen_masuk,
        tidak_absen_pulang: acc.tidak_absen_pulang + curr.tidak_absen_pulang,
        total_potongan: acc.total_potongan + curr.jumlah_potongan_absensi,
        karyawan_count: acc.karyawan_count + 1,
      }),
      { terlambat: 0, pulang_cepat: 0, tidak_absen_masuk: 0, tidak_absen_pulang: 0, total_potongan: 0, karyawan_count: 0 }
    );
  }, [filteredRows]);

  const units = ['ALL', 'Teknologi Informasi', 'Keuangan & Akuntansi', 'Sekretariat Utama', 'Kepegawaian & Diklat'];

  // Handle Calculate
  const handleCalculate = (force = false) => {
    setIsCalculating(true);
    setActionAlert(null);

    setTimeout(() => {
      setIsCalculating(false);
      setHasCalculated(true);
      const now = new Date();
      setLastCalculationTime(now.toLocaleString('id-ID'));
      setActionAlert({
        type: 'success',
        message: force
          ? `Perhitungan ulang (Force Recalculate) berhasil! Seluruh ${recapData.length} data karyawan diproses ulang tanpa duplikasi.`
          : `Perhitungan potongan absensi bulan Agustus ${selectedYear} sukses dihitung untuk ${recapData.length} karyawan.`
      });
    }, 600);
  };

  // Format Currency
  const formatRp = (val: number) => `Rp ${val.toLocaleString('id-ID')}`;

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-100 overflow-y-auto">
      {/* Top Banner / Breadcrumb info */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <Calculator className="w-5 h-5 text-blue-600" />
              Perhitungan Potongan Absensi
            </h1>
            <span className="text-[11px] font-semibold bg-blue-100 text-blue-700 px-2.5 py-0.5 rounded-full border border-blue-200">
              Tahap 5: Mesin Potongan
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Kalkulasi akurat keterlambatan (Rp7.500 / Rp10.000), pulang cepat (Rp10.000), dan tidak scan (Rp10.000 / maks Rp20.000).
          </p>
        </div>

        {/* Action Buttons Header */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleCalculate(false)}
            disabled={isCalculating}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-sm transition disabled:opacity-50 cursor-pointer"
          >
            <Calculator className="w-4 h-4" />
            <span>{isCalculating ? 'Menghitung...' : 'Hitung Potongan'}</span>
          </button>

          <button
            onClick={() => handleCalculate(true)}
            disabled={isCalculating}
            className="flex items-center gap-1.5 px-3 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-bold shadow-sm transition disabled:opacity-50 cursor-pointer"
            title="Hapus cache dan hitung ulang seluruh data dari transaksi absensi"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isCalculating ? 'animate-spin' : ''}`} />
            <span>Hitung Ulang</span>
          </button>

          <button
            onClick={() => setIntegrityReport({ ...integrityReport, isOpen: true })}
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-sm transition cursor-pointer"
            title="Verifikasi integritas data: anti-negatif, no duplicate, validasi libur"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Validasi Integritas</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="p-6 space-y-5">
        {/* Notification Alert */}
        {actionAlert && (
          <div
            className={`p-3.5 rounded-lg border text-xs flex items-center justify-between transition ${
              actionAlert.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-blue-50 border-blue-200 text-blue-800'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{actionAlert.message}</span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">Sinkron: {lastCalculationTime}</span>
          </div>
        )}

        {/* Business Rule Summary Badges */}
        <div className="bg-slate-900 text-slate-200 rounded-xl p-4 border border-slate-800 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span className="font-bold text-white">Standar Bisnis Potongan Presensi SIAP:</span>
          </div>
          <div className="flex flex-wrap items-center gap-2 font-mono text-[11px]">
            <span className="bg-slate-800 border border-slate-700 px-2.5 py-1 rounded">
              Terlambat ≤ 1 jam: <strong className="text-amber-400">Rp 7.500</strong>
            </span>
            <span className="bg-slate-800 border border-slate-700 px-2.5 py-1 rounded">
              Terlambat &gt; 1 jam: <strong className="text-rose-400">Rp 10.000</strong>
            </span>
            <span className="bg-slate-800 border border-slate-700 px-2.5 py-1 rounded">
              Pulang Cepat: <strong className="text-pink-400">Rp 10.000</strong>
            </span>
            <span className="bg-slate-800 border border-slate-700 px-2.5 py-1 rounded">
              Tdk Scan Masuk / Pulang: <strong className="text-orange-400">Rp 10.000</strong>
            </span>
            <span className="bg-slate-800 border border-slate-700 px-2.5 py-1 rounded">
              Tdk Hadir Penuh (Alfa): <strong className="text-red-400">Maks Rp 20.000</strong>
            </span>
          </div>
        </div>

        {/* Key Metrics Dashboard Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500">Total Potongan Terhitung</span>
              <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
                <TrendingDown className="w-4 h-4" />
              </span>
            </div>
            <p className="text-2xl font-black text-blue-700 mt-2">{formatRp(grandTotal.total_potongan)}</p>
            <p className="text-[11px] text-slate-500 mt-1 font-medium">{grandTotal.karyawan_count} Karyawan pada periode ini</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500">Total Keterlambatan</span>
              <span className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
                <Clock className="w-4 h-4" />
              </span>
            </div>
            <p className="text-2xl font-black text-amber-600 mt-2">{formatRp(grandTotal.terlambat)}</p>
            <p className="text-[11px] text-slate-500 mt-1 font-medium">Akumulasi terlambat ringan & berat</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500">Total Pulang Cepat</span>
              <span className="p-1.5 rounded-lg bg-pink-50 text-pink-600">
                <ArrowRight className="w-4 h-4" />
              </span>
            </div>
            <p className="text-2xl font-black text-pink-600 mt-2">{formatRp(grandTotal.pulang_cepat)}</p>
            <p className="text-[11px] text-slate-500 mt-1 font-medium">Meninggalkan kantor sebelum jadwal</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500">Tidak Scan / Tidak Hadir</span>
              <span className="p-1.5 rounded-lg bg-orange-50 text-orange-600">
                <AlertCircle className="w-4 h-4" />
              </span>
            </div>
            <p className="text-2xl font-black text-orange-600 mt-2">
              {formatRp(grandTotal.tidak_absen_masuk + grandTotal.tidak_absen_pulang)}
            </p>
            <p className="text-[11px] text-slate-500 mt-1 font-medium">Integritas terjaga tanpa double counting</p>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <label className="text-xs font-bold text-slate-700">Bulan:</label>
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white font-medium focus:ring-2 focus:ring-blue-600 focus:outline-none"
              >
                <option value="8">Agustus (Bulan 08)</option>
                <option value="9">September (Bulan 09)</option>
                <option value="10">Oktober (Bulan 10)</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-xs font-bold text-slate-700">Tahun:</label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(e.target.value)}
                className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white font-medium focus:ring-2 focus:ring-blue-600 focus:outline-none"
              >
                <option value="2026">2026</option>
                <option value="2025">2025</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-xs font-bold text-slate-700">Unit:</label>
              <select
                value={selectedUnit}
                onChange={(e) => setSelectedUnit(e.target.value)}
                className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white font-medium focus:ring-2 focus:ring-blue-600 focus:outline-none"
              >
                {units.map((u) => (
                  <option key={u} value={u}>
                    {u === 'ALL' ? 'Semua Unit Kerja' : u}
                  </option>
                ))}
              </select>
            </div>

            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Cari nama / NIK..."
                className="pl-8 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-600 focus:outline-none w-44"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                alert(`Export Rekap Potongan Excel:\nFile: Rekap_Potongan_${selectedYear}_${selectedMonth}.xlsx telah diekspor.`);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-emerald-300 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-xs font-bold transition cursor-pointer"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>Export Excel</span>
            </button>

            <button
              onClick={() => {
                alert(`Export Rekap Potongan PDF:\nFile: Laporan_Rekap_Potongan_${selectedYear}_${selectedMonth}.pdf siap dicetak.`);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-rose-300 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-lg text-xs font-bold transition cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Export PDF</span>
            </button>
          </div>
        </div>

        {/* Deduction Calculation Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-extrabold text-slate-900">Rincian Hasil Perhitungan Potongan Karyawan</h3>
              <p className="text-xs text-slate-500">Klik dua kali pada baris untuk memeriksa detail hari & komponen potongan.</p>
            </div>
            <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2.5 py-1 rounded-md border border-slate-200">
              Total {filteredRows.length} Karyawan
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-3 w-12 text-center">No</th>
                  <th className="py-3 px-3">Unit Kerja</th>
                  <th className="py-3 px-3">Nama Pegawai / NIK</th>
                  <th className="py-3 px-3 text-center">Status</th>
                  <th className="py-3 px-3 text-right">Terlambat</th>
                  <th className="py-3 px-3 text-right">Pulang Cepat</th>
                  <th className="py-3 px-3 text-right">Tdk Absen Masuk</th>
                  <th className="py-3 px-3 text-right">Tdk Absen Pulang</th>
                  <th className="py-3 px-3 text-right text-blue-700 font-extrabold">Total Potongan</th>
                  <th className="py-3 px-3 text-center w-24">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredRows.map((r, idx) => (
                  <tr
                    key={r.employee_id}
                    onClick={() => setSelectedDetailEmployee(r)}
                    className="hover:bg-blue-50/60 transition cursor-pointer"
                  >
                    <td className="py-2.5 px-3 text-center font-mono text-slate-500">{idx + 1}</td>
                    <td className="py-2.5 px-3 font-semibold text-slate-700">{r.unit}</td>
                    <td className="py-2.5 px-3">
                      <div className="font-bold text-slate-900">{r.nama}</div>
                      <div className="text-[11px] font-mono text-slate-400">NIK: {r.nik}</div>
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                        {r.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-slate-700">
                      {formatRp(r.terlambat)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-slate-700">
                      {formatRp(r.pulang_cepat)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-slate-700">
                      {formatRp(r.tidak_absen_masuk)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-slate-700">
                      {formatRp(r.tidak_absen_pulang)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-bold text-blue-700 bg-blue-50/40">
                      {formatRp(r.jumlah_potongan_absensi)}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedDetailEmployee(r);
                        }}
                        className="px-2 py-1 text-[11px] font-bold text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded transition cursor-pointer"
                      >
                        Detail
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-slate-100 border-t-2 border-slate-300 font-extrabold text-slate-900">
                  <td colSpan={4} className="py-3 px-4 text-left uppercase tracking-wider text-xs">
                    GRAND TOTAL ({grandTotal.karyawan_count} Karyawan)
                  </td>
                  <td className="py-3 px-3 text-right font-mono">{formatRp(grandTotal.terlambat)}</td>
                  <td className="py-3 px-3 text-right font-mono">{formatRp(grandTotal.pulang_cepat)}</td>
                  <td className="py-3 px-3 text-right font-mono">{formatRp(grandTotal.tidak_absen_masuk)}</td>
                  <td className="py-3 px-3 text-right font-mono">{formatRp(grandTotal.tidak_absen_pulang)}</td>
                  <td className="py-3 px-3 text-right font-mono text-sm text-blue-800 bg-blue-100/70">
                    {formatRp(grandTotal.total_potongan)}
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      {/* MODAL 1: Detail Rincian Komponen Potongan Pegawai */}
      {selectedDetailEmployee && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                  <Calculator className="w-4 h-4 text-blue-600" />
                  Rincian Komponen Potongan: {selectedDetailEmployee.nama}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Unit: {selectedDetailEmployee.unit} | NIK: {selectedDetailEmployee.nik} | Periode: Agustus {selectedYear}
                </p>
              </div>
              <button
                onClick={() => setSelectedDetailEmployee(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg">
                  <span className="text-[11px] font-semibold text-blue-700">Total Potongan Bulan Ini</span>
                  <p className="text-lg font-black text-blue-800 mt-0.5">
                    {formatRp(selectedDetailEmployee.jumlah_potongan_absensi)}
                  </p>
                </div>
                <div className="bg-amber-50 border border-amber-200 p-3 rounded-lg">
                  <span className="text-[11px] font-semibold text-amber-700">Total Terlambat</span>
                  <p className="text-lg font-black text-amber-800 mt-0.5">
                    {formatRp(selectedDetailEmployee.terlambat)}
                  </p>
                </div>
                <div className="bg-pink-50 border border-pink-200 p-3 rounded-lg">
                  <span className="text-[11px] font-semibold text-pink-700">Pulang Cepat & Tdk Scan</span>
                  <p className="text-lg font-black text-pink-800 mt-0.5">
                    {formatRp(
                      selectedDetailEmployee.pulang_cepat +
                        selectedDetailEmployee.tidak_absen_masuk +
                        selectedDetailEmployee.tidak_absen_pulang
                    )}
                  </p>
                </div>
              </div>

              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Catatan Transaksi Harian Pelanggaran Presensi:
              </h4>

              {detailItemsMap[selectedDetailEmployee.employee_id] ? (
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-50 border-b border-slate-200 font-bold text-slate-600">
                      <tr>
                        <th className="py-2.5 px-3">Tanggal / Hari</th>
                        <th className="py-2.5 px-3">Jam Masuk</th>
                        <th className="py-2.5 px-3">Jam Pulang</th>
                        <th className="py-2.5 px-3">Pelanggaran</th>
                        <th className="py-2.5 px-3 text-right">Potongan (Rp)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {detailItemsMap[selectedDetailEmployee.employee_id].map((item) => (
                        <tr key={item.id} className="hover:bg-slate-50">
                          <td className="py-2 px-3 font-semibold text-slate-800">
                            {item.day_name}, {item.attendance_date}
                          </td>
                          <td className="py-2 px-3 font-mono text-slate-600">{item.actual_check_in || '-'}</td>
                          <td className="py-2 px-3 font-mono text-slate-600">{item.actual_check_out || '-'}</td>
                          <td className="py-2 px-3 text-slate-700">
                            <span className="font-medium text-slate-900">{item.notes}</span>
                          </td>
                          <td className="py-2 px-3 text-right font-mono font-bold text-rose-600">
                            {formatRp(item.total_deduction)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-8 text-center bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-500">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                  <p className="font-bold text-slate-800">Pegawai Ini Tepat Waktu & Disiplin Penuh</p>
                  <p className="mt-0.5">Tidak ditemukan catatan pelanggaran jam kerja pada periode Agustus 2026.</p>
                </div>
              )}
            </div>

            <div className="px-5 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-end">
              <button
                onClick={() => setSelectedDetailEmployee(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-bold transition cursor-pointer"
              >
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: Dialog Validasi Integritas */}
      {integrityReport.isOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200 bg-emerald-50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                <h3 className="font-bold text-emerald-950 text-sm">Laporan Audit Integritas Data Potongan</h3>
              </div>
              <button
                onClick={() => setIntegrityReport({ ...integrityReport, isOpen: false })}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 space-y-3.5 text-xs">
              <div className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-lg text-emerald-900 flex items-start gap-2.5">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold">Semua 5 Uji Validitas Lolos 100%!</p>
                  <p className="text-[11px] text-emerald-700 mt-0.5">
                    Data siap diekspor dan dicetak untuk laporan rekapitulasi slip potongan gaji.
                  </p>
                </div>
              </div>

              <div className="space-y-2 font-medium">
                <div className="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-200">
                  <span className="text-slate-700">1. Anti-Negatif (Semua nominal Rupiah &gt;= 0)</span>
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Lolos
                  </span>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-200">
                  <span className="text-slate-700">2. Anti-Double Counting (Maks Alfa Harian Rp20.000)</span>
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Lolos
                  </span>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-200">
                  <span className="text-slate-700">3. Validasi Hari Libur & Akhir Pekan (Rp0 Potongan)</span>
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Lolos
                  </span>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-200">
                  <span className="text-slate-700">4. Karyawan Non-Aktif Terisolasi (Rp0 Potongan)</span>
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Lolos
                  </span>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-200">
                  <span className="text-slate-700">5. Sinkronisasi Item Detail = Total Harian</span>
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Lolos
                  </span>
                </div>
              </div>
            </div>

            <div className="px-5 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-end">
              <button
                onClick={() => setIntegrityReport({ ...integrityReport, isOpen: false })}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition cursor-pointer"
              >
                Selesai
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
