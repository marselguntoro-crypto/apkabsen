import React, { useState } from 'react';
import { 
  FileSpreadsheet, 
  Search, 
  Filter, 
  Download, 
  Calendar, 
  Clock, 
  Info, 
  Layers, 
  ArrowUpDown,
  CheckCircle2
} from 'lucide-react';
import { AttendanceRawItem, ImportBatchLogItem } from '../types';

interface Props {
  rawAttendanceList: AttendanceRawItem[];
  batchLogs: ImportBatchLogItem[];
  onAddAuditLog: (action: string, module: string, description: string) => void;
}

export function RawAttendanceSimulatorView({
  rawAttendanceList,
  batchLogs,
  onAddAuditLog,
}: Props) {
  const [keyword, setKeyword] = useState<string>('');
  const [selectedMonth, setSelectedMonth] = useState<string>('8'); // Agustus
  const [selectedYear, setSelectedYear] = useState<string>('2026');
  const [selectedBatch, setSelectedBatch] = useState<string>('ALL');
  const [sortField, setSortField] = useState<'tanggal' | 'nama' | 'scan_masuk'>('tanggal');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState<number>(1);
  const pageSize = 10;

  // Filter Data
  const filteredData = rawAttendanceList.filter((item) => {
    // 1. Keyword search
    const matchKeyword =
      keyword.trim() === '' ||
      `${item.nama} ${item.emp_num} ${item.no_id} ${item.nik}`
        .toLowerCase()
        .includes(keyword.toLowerCase());

    // 2. Filter Periode
    let matchPeriod = true;
    if (selectedMonth !== 'ALL' && selectedYear !== 'ALL') {
      const parts = item.tanggal.split('-');
      if (parts.length >= 2) {
        const itemYear = parts[0];
        const itemMonth = String(parseInt(parts[1], 10));
        matchPeriod = itemYear === selectedYear && itemMonth === selectedMonth;
      }
    }

    // 3. Filter Batch
    let matchBatch = true;
    if (selectedBatch !== 'ALL') {
      matchBatch = item.import_batch_id === selectedBatch;
    }

    return matchKeyword && matchPeriod && matchBatch;
  });

  // Sorting
  const sortedData = [...filteredData].sort((a, b) => {
    let comparison = 0;
    if (sortField === 'tanggal') {
      comparison = a.tanggal.localeCompare(b.tanggal);
    } else if (sortField === 'nama') {
      comparison = a.nama.localeCompare(b.nama);
    } else if (sortField === 'scan_masuk') {
      comparison = (a.scan_masuk || '').localeCompare(b.scan_masuk || '');
    }
    return sortDirection === 'asc' ? comparison : -comparison;
  });

  // Pagination
  const totalPages = Math.max(1, Math.ceil(sortedData.length / pageSize));
  const currentPageData = sortedData.slice((page - 1) * pageSize, page * pageSize);

  // Export Data Mentah ke CSV
  const handleExportCsv = () => {
    if (sortedData.length === 0) {
      alert('Tidak ada data transaksi mentah yang sesuai untuk diekspor.');
      return;
    }

    let csvContent = 'data:text/csv;charset=utf-8,No;Emp Num;No ID;NIK;Nama;Tanggal;Scan Masuk;Scan Pulang;Berkas Sumber;Batch ID\n';
    sortedData.forEach((row, idx) => {
      csvContent += `${idx + 1};"${row.emp_num}";"${row.no_id}";"${row.nik}";"${row.nama}";${row.tanggal};${row.scan_masuk || '-'};${row.scan_pulang || '-'};"${row.source_file}";"${row.import_batch_id}"\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `SIAP_Attendance_Raw_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    onAddAuditLog(
      'EXPORT_RAW_ATTENDANCE',
      'ATTENDANCE_RAW',
      `Ekspor data mentah absensi (${sortedData.length} transaksi) ke CSV.`
    );
  };

  const toggleSort = (field: 'tanggal' | 'nama' | 'scan_masuk') => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  return (
    <div className="h-full flex flex-col p-6 space-y-5 overflow-y-auto">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600" />
            Data Transaksi Absensi Mentah (Raw Attendance)
          </h3>
          <p className="text-xs text-slate-500">
            Tabel: <code>attendance_raw</code> • Mempertahankan catatan scan asli dari mesin absensi
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCsv}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold shadow-sm transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Ekspor Data Mentah (.csv)</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center gap-4 text-xs">
        {/* Search */}
        <div className="flex-1 min-w-[240px] flex items-center gap-2 px-3 py-1.5 border border-slate-300 rounded-lg bg-slate-50">
          <Search className="w-4 h-4 text-slate-400 shrink-0" />
          <input
            type="text"
            placeholder="Cari Nama, Emp Num, No ID, atau NIK..."
            value={keyword}
            onChange={(e) => {
              setKeyword(e.target.value);
              setPage(1);
            }}
            className="w-full bg-transparent focus:outline-none"
          />
        </div>

        {/* Bulan */}
        <div className="flex items-center gap-1.5">
          <span className="font-semibold text-slate-700">Bulan:</span>
          <select
            value={selectedMonth}
            onChange={(e) => {
              setSelectedMonth(e.target.value);
              setPage(1);
            }}
            className="border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white font-medium focus:ring-1 focus:ring-blue-600"
          >
            <option value="ALL">Semua Bulan</option>
            <option value="1">Januari</option>
            <option value="2">Februari</option>
            <option value="3">Maret</option>
            <option value="4">April</option>
            <option value="5">Mei</option>
            <option value="6">Juni</option>
            <option value="7">Juli</option>
            <option value="8">Agustus</option>
            <option value="9">September</option>
            <option value="10">Oktober</option>
            <option value="11">November</option>
            <option value="12">Desember</option>
          </select>
        </div>

        {/* Tahun */}
        <div className="flex items-center gap-1.5">
          <span className="font-semibold text-slate-700">Tahun:</span>
          <select
            value={selectedYear}
            onChange={(e) => {
              setSelectedYear(e.target.value);
              setPage(1);
            }}
            className="border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white font-medium focus:ring-1 focus:ring-blue-600"
          >
            <option value="ALL">Semua Tahun</option>
            <option value="2024">2024</option>
            <option value="2025">2025</option>
            <option value="2026">2026</option>
            <option value="2027">2027</option>
          </select>
        </div>

        {/* Filter Batch ID */}
        <div className="flex items-center gap-1.5">
          <span className="font-semibold text-slate-700">Batch ID:</span>
          <select
            value={selectedBatch}
            onChange={(e) => {
              setSelectedBatch(e.target.value);
              setPage(1);
            }}
            className="border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white font-medium focus:ring-1 focus:ring-blue-600 max-w-[180px]"
          >
            <option value="ALL">Semua Batch ({batchLogs.length})</option>
            {batchLogs.map((b) => (
              <option key={b.import_batch_id} value={b.import_batch_id}>
                {b.import_batch_id} ({b.file_name})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Info Integritas Transparan Tahap 3 */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 text-xs text-amber-900 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong>Perhatian Arsitektur:</strong> Halaman ini secara murni menampilkan data transaksi mentah (Raw Log). 
          <strong> Tidak ada kalkulasi alfa, hari kerja, atau potongan absensi</strong> yang dieksekusi pada tahap ini sesuai aturan isolasi data. Modul kalkulasi kehadiran harian akan dibangun pada Tahap 4.
        </div>
      </div>

      {/* Tabel Data Mentah */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex-1 flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200 uppercase tracking-wider sticky top-0">
              <tr>
                <th className="p-3 text-center">No</th>
                <th className="p-3">Emp Num</th>
                <th className="p-3">No ID</th>
                <th className="p-3">NIK</th>
                <th 
                  onClick={() => toggleSort('nama')}
                  className="p-3 cursor-pointer hover:bg-slate-200 transition"
                >
                  <div className="flex items-center gap-1">
                    <span>Nama Karyawan</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th 
                  onClick={() => toggleSort('tanggal')}
                  className="p-3 text-center cursor-pointer hover:bg-slate-200 transition"
                >
                  <div className="flex items-center justify-center gap-1">
                    <span>Tanggal</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th 
                  onClick={() => toggleSort('scan_masuk')}
                  className="p-3 text-center cursor-pointer hover:bg-slate-200 transition"
                >
                  <div className="flex items-center justify-center gap-1">
                    <span>Scan Masuk</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="p-3 text-center">Scan Pulang</th>
                <th className="p-3">Berkas Sumber</th>
                <th className="p-3 font-mono">Batch ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {currentPageData.length === 0 ? (
                <tr>
                  <td colSpan={10} className="p-8 text-center text-slate-400 font-sans">
                    Tidak ada transaksi absensi mentah yang ditemukan.
                  </td>
                </tr>
              ) : (
                currentPageData.map((row, idx) => (
                  <tr key={row.id} className="hover:bg-slate-50 font-sans">
                    <td className="p-3 text-center text-slate-400 font-mono">
                      {(page - 1) * pageSize + idx + 1}
                    </td>
                    <td className="p-3 font-mono">{row.emp_num}</td>
                    <td className="p-3 font-mono">{row.no_id}</td>
                    <td className="p-3 font-mono">{row.nik || '-'}</td>
                    <td className="p-3 font-bold text-slate-800">{row.nama}</td>
                    <td className="p-3 text-center font-mono font-medium">{row.tanggal}</td>
                    <td className={`p-3 text-center font-mono ${!row.scan_masuk ? 'text-slate-400 italic' : 'text-slate-800'}`}>
                      {row.scan_masuk || '-'}
                    </td>
                    <td className={`p-3 text-center font-mono ${!row.scan_pulang ? 'text-slate-400 italic' : 'text-slate-800'}`}>
                      {row.scan_pulang || '-'}
                    </td>
                    <td className="p-3 text-slate-500 text-[11px] truncate max-w-[120px]">{row.source_file}</td>
                    <td className="p-3 font-mono text-[11px] text-blue-700">{row.import_batch_id}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer Paginasi */}
        <div className="p-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-600">
          <div>
            Menampilkan <strong>{currentPageData.length}</strong> dari <strong>{sortedData.length}</strong> transaksi mentah
          </div>

          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1 bg-white border border-slate-300 rounded disabled:opacity-50 hover:bg-slate-100 font-medium cursor-pointer"
            >
              Sebelumnya
            </button>
            <span className="font-semibold">
              Halaman {page} dari {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1 bg-white border border-slate-300 rounded disabled:opacity-50 hover:bg-slate-100 font-medium cursor-pointer"
            >
              Selanjutnya
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
