import React, { useState, useMemo } from 'react';
import {
  FileText,
  FileSpreadsheet,
  Printer,
  Search,
  Filter,
  Calendar,
  Building2,
  ChevronLeft,
  ChevronRight,
  Download,
  CheckCircle2,
  AlertTriangle,
  ArrowUpDown,
  TrendingDown,
  Layers,
  Clock,
  User
} from 'lucide-react';
import { MonthlyDeductionRecapRow, DailyDeductionReportRow } from '../types';

interface ReportsSimulatorViewProps {
  currentRole: 'ADMIN' | 'OPERATOR';
  currentUsername: string;
}

export function ReportsSimulatorView({ currentRole, currentUsername }: ReportsSimulatorViewProps) {
  const [activeTab, setActiveTab] = useState<'rekap' | 'harian'>('rekap');

  // Filter States
  const [selectedMonth, setSelectedMonth] = useState('8'); // Agustus
  const [selectedYear, setSelectedYear] = useState('2026');
  const [selectedUnit, setSelectedUnit] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [searchKeyword, setSearchKeyword] = useState('');

  // Pagination for Daily Report
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Format Currency
  const formatRp = (val: number) => `Rp ${val.toLocaleString('id-ID')}`;

  // Data Rekap Bulanan
  const rawRecapList: MonthlyDeductionRecapRow[] = [
    {
      no: 1,
      employee_id: 1,
      nik: '198501012010011001',
      no_id: '101',
      nama: 'Ahmad Fauzi, S.Kom',
      unit: 'Teknologi Informasi',
      status: 'PNS',
      terlambat: 17500,
      pulang_cepat: 10000,
      tidak_absen_masuk: 10000,
      tidak_absen_pulang: 0,
      jumlah_potongan_absensi: 37500,
    },
    {
      no: 2,
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
      jumlah_potongan_absensi: 0,
    },
    {
      no: 3,
      employee_id: 2,
      nik: '198804152012012002',
      no_id: '102',
      nama: 'Siti Rahmawati, S.E',
      unit: 'Keuangan & Akuntansi',
      status: 'PNS',
      terlambat: 7500,
      pulang_cepat: 0,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 10000,
      jumlah_potongan_absensi: 17500,
    },
    {
      no: 4,
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
      no: 5,
      employee_id: 5,
      nik: '198203252008011005',
      no_id: '105',
      nama: 'Ir. Hendra Gunawan',
      unit: 'Sekretariat Utama',
      status: 'PNS',
      terlambat: 20000,
      pulang_cepat: 20000,
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
      jumlah_potongan_absensi: 20000,
    },
  ];

  // Data Laporan Harian (17 Kolom)
  const rawDailyList: DailyDeductionReportRow[] = [
    {
      no: 1,
      unit: 'Teknologi Informasi',
      nama: 'Ahmad Fauzi, S.Kom',
      hari: 'Senin',
      tanggal: '03/08/2026',
      jam_masuk: '08:12:00',
      jam_pulang: '16:35:00',
      status_masuk: 'TEPAT WAKTU',
      status_pulang: 'TEPAT WAKTU',
      status_kehadiran: 'HADIR_LENGKAP',
      menit_terlambat: 0,
      menit_pulang_cepat: 0,
      potongan_terlambat: 0,
      potongan_pulang_cepat: 0,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 0,
      total_potongan_per_hari: 0,
    },
    {
      no: 2,
      unit: 'Teknologi Informasi',
      nama: 'Ahmad Fauzi, S.Kom',
      hari: 'Selasa',
      tanggal: '04/08/2026',
      jam_masuk: '08:40:00',
      jam_pulang: '16:30:00',
      status_masuk: 'TERLAMBAT',
      status_pulang: 'TEPAT WAKTU',
      status_kehadiran: 'HADIR_LENGKAP',
      menit_terlambat: 25,
      menit_pulang_cepat: 0,
      potongan_terlambat: 7500,
      potongan_pulang_cepat: 0,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 0,
      total_potongan_per_hari: 7500,
    },
    {
      no: 3,
      unit: 'Teknologi Informasi',
      nama: 'Ahmad Fauzi, S.Kom',
      hari: 'Selasa',
      tanggal: '11/08/2026',
      jam_masuk: '09:35:00',
      jam_pulang: '16:30:00',
      status_masuk: 'TERLAMBAT',
      status_pulang: 'TEPAT WAKTU',
      status_kehadiran: 'HADIR_LENGKAP',
      menit_terlambat: 80,
      menit_pulang_cepat: 0,
      potongan_terlambat: 10000,
      potongan_pulang_cepat: 0,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 0,
      total_potongan_per_hari: 10000,
    },
    {
      no: 4,
      unit: 'Teknologi Informasi',
      nama: 'Ahmad Fauzi, S.Kom',
      hari: 'Jumat',
      tanggal: '14/08/2026',
      jam_masuk: '08:15:00',
      jam_pulang: '16:15:00',
      status_masuk: 'TEPAT WAKTU',
      status_pulang: 'PULANG CEPAT',
      status_kehadiran: 'HADIR_LENGKAP',
      menit_terlambat: 0,
      menit_pulang_cepat: 45,
      potongan_terlambat: 0,
      potongan_pulang_cepat: 10000,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 0,
      total_potongan_per_hari: 10000,
    },
    {
      no: 5,
      unit: 'Teknologi Informasi',
      nama: 'Ahmad Fauzi, S.Kom',
      hari: 'Rabu',
      tanggal: '19/08/2026',
      jam_masuk: '-',
      jam_pulang: '16:30:00',
      status_masuk: 'TIDAK SCAN',
      status_pulang: 'TEPAT WAKTU',
      status_kehadiran: 'HANYA_ABSEN_PULANG',
      menit_terlambat: 0,
      menit_pulang_cepat: 0,
      potongan_terlambat: 0,
      potongan_pulang_cepat: 0,
      tidak_absen_masuk: 10000,
      tidak_absen_pulang: 0,
      total_potongan_per_hari: 10000,
    },
    {
      no: 6,
      unit: 'Keuangan & Akuntansi',
      nama: 'Siti Rahmawati, S.E',
      hari: 'Kamis',
      tanggal: '06/08/2026',
      jam_masuk: '08:35:00',
      jam_pulang: '16:32:00',
      status_masuk: 'TERLAMBAT',
      status_pulang: 'TEPAT WAKTU',
      status_kehadiran: 'HADIR_LENGKAP',
      menit_terlambat: 20,
      menit_pulang_cepat: 0,
      potongan_terlambat: 7500,
      potongan_pulang_cepat: 0,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 0,
      total_potongan_per_hari: 7500,
    },
    {
      no: 7,
      unit: 'Keuangan & Akuntansi',
      nama: 'Siti Rahmawati, S.E',
      hari: 'Selasa',
      tanggal: '18/08/2026',
      jam_masuk: '08:10:00',
      jam_pulang: '-',
      status_masuk: 'TEPAT WAKTU',
      status_pulang: 'TIDAK SCAN',
      status_kehadiran: 'HANYA_ABSEN_MASUK',
      menit_terlambat: 0,
      menit_pulang_cepat: 0,
      potongan_terlambat: 0,
      potongan_pulang_cepat: 0,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 10000,
      total_potongan_per_hari: 10000,
    },
    {
      no: 8,
      unit: 'Kepegawaian & Diklat',
      nama: 'Eko Prasetyo, S.E',
      hari: 'Senin',
      tanggal: '10/08/2026',
      jam_masuk: '-',
      jam_pulang: '-',
      status_masuk: 'TIDAK SCAN',
      status_pulang: 'TIDAK SCAN',
      status_kehadiran: 'TIDAK_ABSEN',
      menit_terlambat: 0,
      menit_pulang_cepat: 0,
      potongan_terlambat: 0,
      potongan_pulang_cepat: 0,
      tidak_absen_masuk: 10000,
      tidak_absen_pulang: 10000,
      total_potongan_per_hari: 20000,
    },
    {
      no: 9,
      unit: 'Sekretariat Utama',
      nama: 'Ir. Hendra Gunawan',
      hari: 'Rabu',
      tanggal: '05/08/2026',
      jam_masuk: '09:40:00',
      jam_pulang: '15:30:00',
      status_masuk: 'TERLAMBAT',
      status_pulang: 'PULANG CEPAT',
      status_kehadiran: 'HADIR_LENGKAP',
      menit_terlambat: 85,
      menit_pulang_cepat: 60,
      potongan_terlambat: 10000,
      potongan_pulang_cepat: 10000,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 0,
      total_potongan_per_hari: 20000,
    },
    {
      no: 10,
      unit: 'Teknologi Informasi',
      nama: 'Dewi Lestari, S.Tr.Kom',
      hari: 'Senin',
      tanggal: '03/08/2026',
      jam_masuk: '08:05:00',
      jam_pulang: '16:30:00',
      status_masuk: 'TEPAT WAKTU',
      status_pulang: 'TEPAT WAKTU',
      status_kehadiran: 'HADIR_LENGKAP',
      menit_terlambat: 0,
      menit_pulang_cepat: 0,
      potongan_terlambat: 0,
      potongan_pulang_cepat: 0,
      tidak_absen_masuk: 0,
      tidak_absen_pulang: 0,
      total_potongan_per_hari: 0,
    }
  ];

  // Filtered Recap
  const filteredRecap = useMemo(() => {
    return rawRecapList.filter((r) => {
      const matchUnit = selectedUnit === 'ALL' || r.unit === selectedUnit;
      const matchKw =
        searchKeyword === '' ||
        r.nama.toLowerCase().includes(searchKeyword.toLowerCase()) ||
        r.nik.includes(searchKeyword);
      return matchUnit && matchKw;
    });
  }, [rawRecapList, selectedUnit, searchKeyword]);

  // Subtotals Grouping for Recap
  const recapGroupedByUnit = useMemo(() => {
    const groups: Record<string, { rows: MonthlyDeductionRecapRow[]; subtotal: number }> = {};
    filteredRecap.forEach((r) => {
      if (!groups[r.unit]) {
        groups[r.unit] = { rows: [], subtotal: 0 };
      }
      groups[r.unit].rows.push(r);
      groups[r.unit].subtotal += r.jumlah_potongan_absensi;
    });
    return groups;
  }, [filteredRecap]);

  const recapGrandTotal = useMemo(() => {
    return filteredRecap.reduce(
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
  }, [filteredRecap]);

  // Filtered Daily
  const filteredDaily = useMemo(() => {
    return rawDailyList.filter((d) => {
      const matchUnit = selectedUnit === 'ALL' || d.unit === selectedUnit;
      const matchStatus = selectedStatus === 'ALL' || d.status_kehadiran === selectedStatus;
      const matchKw =
        searchKeyword === '' ||
        d.nama.toLowerCase().includes(searchKeyword.toLowerCase()) ||
        d.unit.toLowerCase().includes(searchKeyword.toLowerCase());
      return matchUnit && matchStatus && matchKw;
    });
  }, [rawDailyList, selectedUnit, selectedStatus, searchKeyword]);

  const totalPages = Math.max(1, Math.ceil(filteredDaily.length / pageSize));
  const paginatedDaily = filteredDaily.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const units = ['ALL', 'Teknologi Informasi', 'Keuangan & Akuntansi', 'Sekretariat Utama', 'Kepegawaian & Diklat'];

  const triggerExport = (format: 'excel' | 'pdf', type: 'rekap' | 'detail') => {
    const fileName =
      type === 'rekap'
        ? `Rekap_Potongan_Absensi_${selectedYear}_${selectedMonth}.${format === 'excel' ? 'xlsx' : 'pdf'}`
        : `Laporan_Detail_Absensi_Harian_${selectedYear}_${selectedMonth}.${format === 'excel' ? 'xlsx' : 'pdf'}`;

    alert(
      `Dokumen ${format.toUpperCase()} Berhasil Dihasilkan!\n\n` +
      `File: ${fileName}\n` +
      `Periode: Agustus ${selectedYear}\n` +
      `Format: Standar ${format === 'excel' ? 'OpenPyXL (Header Biru Navy, Formula Sum, Auto-fit)' : 'ReportLab PDF (Surat Resmi, Tabel Rapi, Header Instansi)'}\n` +
      `Lokasi Simpan: C:\\siap_presensi\\data\\reports\\`
    );
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-100 overflow-y-auto">
      {/* Top Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              Laporan & Rekapitulasi Presensi
            </h1>
            <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-700 px-2.5 py-0.5 rounded-full border border-emerald-200">
              Dokumen Resmi
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Pusat ekspor lembar rekapitulasi potongan absensi bulanan dan laporan rincian presensi harian per unit kerja.
          </p>
        </div>

        {/* Global Export Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => triggerExport('excel', activeTab === 'rekap' ? 'rekap' : 'detail')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-sm transition cursor-pointer"
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>Export Excel</span>
          </button>

          <button
            onClick={() => triggerExport('pdf', activeTab === 'rekap' ? 'rekap' : 'detail')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold shadow-sm transition cursor-pointer"
          >
            <Printer className="w-4 h-4" />
            <span>Cetak PDF</span>
          </button>
        </div>
      </div>

      {/* Main Body */}
      <div className="p-6 space-y-5">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
          <button
            onClick={() => setActiveTab('rekap')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition cursor-pointer ${
              activeTab === 'rekap'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>1. Rekap Data Potongan Bulanan</span>
          </button>

          <button
            onClick={() => setActiveTab('harian')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition cursor-pointer ${
              activeTab === 'harian'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>2. Laporan Data Absensi Harian (17 Kolom)</span>
          </button>
        </div>

        {/* Filter Controls Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <label className="text-xs font-bold text-slate-700">Bulan:</label>
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white font-medium focus:ring-2 focus:ring-blue-600 focus:outline-none"
              >
                <option value="8">Agustus 2026</option>
                <option value="9">September 2026</option>
                <option value="10">Oktober 2026</option>
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

            {activeTab === 'harian' && (
              <div className="flex items-center gap-2">
                <label className="text-xs font-bold text-slate-700">Status Kehadiran:</label>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white font-medium focus:ring-2 focus:ring-blue-600 focus:outline-none"
                >
                  <option value="ALL">Semua Status</option>
                  <option value="HADIR_LENGKAP">HADIR_LENGKAP</option>
                  <option value="HANYA_ABSEN_MASUK">HANYA_ABSEN_MASUK</option>
                  <option value="HANYA_ABSEN_PULANG">HANYA_ABSEN_PULANG</option>
                  <option value="TIDAK_ABSEN">TIDAK_ABSEN</option>
                </select>
              </div>
            )}

            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                placeholder="Cari nama / NIK..."
                className="pl-8 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-600 focus:outline-none w-44"
              />
            </div>
          </div>

          <div className="text-xs font-semibold text-slate-500">
            {activeTab === 'rekap' ? (
              <span>Daftar {filteredRecap.length} Rekap Pegawai</span>
            ) : (
              <span>Menampilkan {filteredDaily.length} Rekord Harian</span>
            )}
          </div>
        </div>

        {/* TAB 1: REKAP DATA POTONGAN BULANAN DENGAN SUBTOTAL UNIT */}
        {activeTab === 'rekap' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-extrabold text-slate-900">
                  REKAP DATA POTONGAN ABSENSI (AGUSTUS 2026)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Tersusun hierarkis berdasarkan Unit Kerja dengan baris Subtotal Unit dan Grand Total.
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-100 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider text-[11px]">
                    <th className="py-3 px-3 w-12 text-center">No</th>
                    <th className="py-3 px-3">Unit Kerja</th>
                    <th className="py-3 px-3">Nama Pegawai / NIK</th>
                    <th className="py-3 px-3 text-center">Status</th>
                    <th className="py-3 px-3 text-right">Terlambat</th>
                    <th className="py-3 px-3 text-right">Pulang Cepat</th>
                    <th className="py-3 px-3 text-right">Tdk Absen Masuk</th>
                    <th className="py-3 px-3 text-right">Tdk Absen Pulang</th>
                    <th className="py-3 px-3 text-right text-blue-700 font-extrabold">Jumlah Potongan</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(Object.entries(recapGroupedByUnit) as [string, { rows: MonthlyDeductionRecapRow[]; subtotal: number }][]).map(([unitName, groupData], unitIdx) => (
                    <React.Fragment key={unitName}>
                      {/* Unit Header Separator */}
                      <tr className="bg-slate-50/80 font-bold text-slate-800 border-t border-b border-slate-200">
                        <td colSpan={9} className="py-2 px-3 text-xs flex items-center gap-2">
                          <Building2 className="w-3.5 h-3.5 text-blue-600" />
                          <span>{unitName}</span>
                          <span className="text-[10px] text-slate-500 font-normal">
                            ({groupData.rows.length} Pegawai)
                          </span>
                        </td>
                      </tr>

                      {/* Pegawai in Unit */}
                      {groupData.rows.map((r, rIdx) => (
                        <tr key={r.employee_id} className="hover:bg-blue-50/40 transition">
                          <td className="py-2 px-3 text-center font-mono text-slate-500">{r.no}</td>
                          <td className="py-2 px-3 text-slate-600">{r.unit}</td>
                          <td className="py-2 px-3">
                            <div className="font-bold text-slate-900">{r.nama}</div>
                            <div className="text-[10px] font-mono text-slate-400">NIK: {r.nik}</div>
                          </td>
                          <td className="py-2 px-3 text-center">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                              {r.status}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-right font-mono text-slate-700">{formatRp(r.terlambat)}</td>
                          <td className="py-2 px-3 text-right font-mono text-slate-700">{formatRp(r.pulang_cepat)}</td>
                          <td className="py-2 px-3 text-right font-mono text-slate-700">{formatRp(r.tidak_absen_masuk)}</td>
                          <td className="py-2 px-3 text-right font-mono text-slate-700">{formatRp(r.tidak_absen_pulang)}</td>
                          <td className="py-2 px-3 text-right font-mono font-bold text-blue-700 bg-blue-50/30">
                            {formatRp(r.jumlah_potongan_absensi)}
                          </td>
                        </tr>
                      ))}

                      {/* Subtotal Unit Row */}
                      <tr className="bg-amber-50/40 border-b border-amber-100 font-bold text-amber-900 text-[11px]">
                        <td colSpan={4} className="py-1.5 px-3 text-right uppercase tracking-wider">
                          Subtotal Unit: {unitName}
                        </td>
                        <td colSpan={4}></td>
                        <td className="py-1.5 px-3 text-right font-mono font-black text-amber-800">
                          {formatRp(groupData.subtotal)}
                        </td>
                      </tr>
                    </React.Fragment>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-slate-900 text-white font-extrabold text-xs">
                    <td colSpan={4} className="py-3 px-4 uppercase tracking-wider">
                      GRAND TOTAL ({recapGrandTotal.karyawan_count} KARYAWAN)
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-amber-300">{formatRp(recapGrandTotal.terlambat)}</td>
                    <td className="py-3 px-3 text-right font-mono text-pink-300">{formatRp(recapGrandTotal.pulang_cepat)}</td>
                    <td className="py-3 px-3 text-right font-mono text-orange-300">{formatRp(recapGrandTotal.tidak_absen_masuk)}</td>
                    <td className="py-3 px-3 text-right font-mono text-orange-300">{formatRp(recapGrandTotal.tidak_absen_pulang)}</td>
                    <td className="py-3 px-3 text-right font-mono text-sm text-emerald-300 bg-slate-800">
                      {formatRp(recapGrandTotal.total_potongan)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}

        {/* TAB 2: LAPORAN DATA ABSENSI HARIAN (17 KOLOM LENGKAP) */}
        {activeTab === 'harian' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden flex flex-col">
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-extrabold text-slate-900">
                  LAPORAN DETAIL ABSENSI & POTONGAN HARIAN (17 KOLOM)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Rincian presensi day-by-day mencakup kalkulasi menit terlambat, menit pulang cepat, dan breakdown nominal per hari.
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-100 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider text-[10px]">
                    <th className="py-2.5 px-2 text-center w-8">No</th>
                    <th className="py-2.5 px-2">Unit</th>
                    <th className="py-2.5 px-2">Nama</th>
                    <th className="py-2.5 px-2 text-center">Hari</th>
                    <th className="py-2.5 px-2 text-center">Tanggal</th>
                    <th className="py-2.5 px-2 text-center">Masuk</th>
                    <th className="py-2.5 px-2 text-center">Pulang</th>
                    <th className="py-2.5 px-2 text-center">Status Masuk</th>
                    <th className="py-2.5 px-2 text-center">Status Pulang</th>
                    <th className="py-2.5 px-2 text-center">Status Kehadiran</th>
                    <th className="py-2.5 px-2 text-right">Menit Tlb</th>
                    <th className="py-2.5 px-2 text-right">Menit PC</th>
                    <th className="py-2.5 px-2 text-right">Pot. Tlb</th>
                    <th className="py-2.5 px-2 text-right">Pot. PC</th>
                    <th className="py-2.5 px-2 text-right">Tdk Absen Masuk</th>
                    <th className="py-2.5 px-2 text-right">Tdk Absen Pulang</th>
                    <th className="py-2.5 px-2 text-right text-blue-700 font-extrabold">Total Potongan</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {paginatedDaily.map((d, i) => (
                    <tr key={d.no} className="hover:bg-slate-50">
                      <td className="py-2 px-2 text-center font-mono text-slate-500">{(currentPage - 1) * pageSize + i + 1}</td>
                      <td className="py-2 px-2 text-slate-600 font-semibold">{d.unit}</td>
                      <td className="py-2 px-2 font-bold text-slate-900">{d.nama}</td>
                      <td className="py-2 px-2 text-center text-slate-600">{d.hari}</td>
                      <td className="py-2 px-2 text-center font-mono text-slate-600">{d.tanggal}</td>
                      <td className="py-2 px-2 text-center font-mono font-medium">{d.jam_masuk}</td>
                      <td className="py-2 px-2 text-center font-mono font-medium">{d.jam_pulang}</td>
                      <td className="py-2 px-2 text-center">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            d.status_masuk === 'TERLAMBAT'
                              ? 'bg-amber-100 text-amber-800'
                              : d.status_masuk === 'TIDAK SCAN'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {d.status_masuk}
                        </span>
                      </td>
                      <td className="py-2 px-2 text-center">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            d.status_pulang === 'PULANG CEPAT'
                              ? 'bg-pink-100 text-pink-800'
                              : d.status_pulang === 'TIDAK SCAN'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {d.status_pulang}
                        </span>
                      </td>
                      <td className="py-2 px-2 text-center">
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-100 text-slate-700">
                          {d.status_kehadiran}
                        </span>
                      </td>
                      <td className="py-2 px-2 text-right font-mono text-slate-700">{d.menit_terlambat}</td>
                      <td className="py-2 px-2 text-right font-mono text-slate-700">{d.menit_pulang_cepat}</td>
                      <td className="py-2 px-2 text-right font-mono text-slate-700">{formatRp(d.potongan_terlambat)}</td>
                      <td className="py-2 px-2 text-right font-mono text-slate-700">{formatRp(d.potongan_pulang_cepat)}</td>
                      <td className="py-2 px-2 text-right font-mono text-slate-700">{formatRp(d.tidak_absen_masuk)}</td>
                      <td className="py-2 px-2 text-right font-mono text-slate-700">{formatRp(d.tidak_absen_pulang)}</td>
                      <td className="py-2 px-2 text-right font-mono font-bold text-blue-700 bg-blue-50/40">
                        {formatRp(d.total_potongan_per_hari)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
              <div className="text-xs text-slate-500">
                Halaman <span className="font-bold text-slate-800">{currentPage}</span> dari{' '}
                <span className="font-bold text-slate-800">{totalPages}</span> (Total {filteredDaily.length} Rekord)
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold bg-white hover:bg-slate-100 disabled:opacity-40 transition cursor-pointer"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Sebelumnya</span>
                </button>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold bg-white hover:bg-slate-100 disabled:opacity-40 transition cursor-pointer"
                >
                  <span>Berikutnya</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
