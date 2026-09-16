import React, { useState, useRef } from 'react';
import { 
  FileSpreadsheet, 
  Upload, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Clock, 
  FileDown, 
  History, 
  Search, 
  Layers, 
  RotateCcw,
  Info,
  ChevronRight,
  Eye,
  SlidersHorizontal,
  ExternalLink
} from 'lucide-react';
import { UserSession, AttendanceRawItem, ImportBatchLogItem, AttendanceRowPreview, EmployeeItem } from '../types';

interface Props {
  userSession: UserSession;
  employees: EmployeeItem[];
  rawAttendanceList: AttendanceRawItem[];
  batchLogs: ImportBatchLogItem[];
  onImportComplete: (
    newRawRecords: AttendanceRawItem[],
    newBatchLog: ImportBatchLogItem,
    newEmployees: EmployeeItem[]
  ) => void;
  onAddAuditLog: (action: string, module: string, description: string) => void;
}

// Data simulasi sampel AGUSTUS 2026.xlsx sesuai deskripsi prompt
const SAMPLE_AGUSTUS_2026_ROWS: AttendanceRowPreview[] = [
  {
    no: 1,
    excel_line: 2,
    emp_num: '1',
    no_id: '1',
    nik: '3201010001',
    nama: 'AHMAD SUJATMIKO',
    tanggal_raw: '03/08/2026',
    tanggal_display: '2026-08-03',
    scan_masuk_raw: '07:54:00',
    scan_masuk_display: '07:54:00',
    scan_pulang_raw: '16:30:00',
    scan_pulang_display: '16:30:00',
    is_valid: true,
    status: 'VALID',
    errors: [],
    warnings: [],
    keterangan: 'Data siap di-import (Terhubung: Ahmad Sujatmiko).',
    employee_id: 1,
    is_duplicate_in_file: false,
    is_duplicate_in_db: false,
    has_empty_jam: false,
  },
  {
    no: 2,
    excel_line: 3,
    emp_num: '1',
    no_id: '1',
    nik: '3201010001',
    nama: 'AHMAD SUJATMIKO',
    tanggal_raw: '04/08/2026',
    tanggal_display: '2026-08-04',
    scan_masuk_raw: '07:58:00',
    scan_masuk_display: '07:58:00',
    scan_pulang_raw: '16:35:00',
    scan_pulang_display: '16:35:00',
    is_valid: true,
    status: 'VALID',
    errors: [],
    warnings: [],
    keterangan: 'Data siap di-import.',
    employee_id: 1,
    is_duplicate_in_file: false,
    is_duplicate_in_db: false,
    has_empty_jam: false,
  },
  {
    no: 3,
    excel_line: 4,
    emp_num: '2',
    no_id: '2',
    nik: '3201010002',
    nama: 'BUDI SANTOSO',
    tanggal_raw: '03/08/2026',
    tanggal_display: '2026-08-03',
    scan_masuk_raw: '08:02:00',
    scan_masuk_display: '08:02:00',
    scan_pulang_raw: '',
    scan_pulang_display: '-',
    is_valid: true,
    status: 'VALID (JAM KOSONG)',
    errors: [],
    warnings: ['Scan pulang kosong (transaksi tetap disimpan).'],
    keterangan: 'Scan pulang kosong (transaksi mentah tetap disimpan).',
    employee_id: 2,
    is_duplicate_in_file: false,
    is_duplicate_in_db: false,
    has_empty_jam: true,
  },
  {
    no: 4,
    excel_line: 5,
    emp_num: '3',
    no_id: '3',
    nik: '3201010003',
    nama: 'CITRA LESTARI',
    tanggal_raw: '03/08/2026',
    tanggal_display: '2026-08-03',
    scan_masuk_raw: '',
    scan_masuk_display: '-',
    scan_pulang_raw: '16:45:00',
    scan_pulang_display: '16:45:00',
    is_valid: true,
    status: 'VALID (JAM KOSONG)',
    errors: [],
    warnings: ['Scan masuk kosong (transaksi tetap disimpan).'],
    keterangan: 'Scan masuk kosong (transaksi mentah tetap disimpan).',
    employee_id: 3,
    is_duplicate_in_file: false,
    is_duplicate_in_db: false,
    has_empty_jam: true,
  },
  {
    no: 5,
    excel_line: 6,
    emp_num: '4',
    no_id: '4',
    nik: '3201010004',
    nama: 'DEDDY KURNIAWAN',
    tanggal_raw: '03/08/2026',
    tanggal_display: '2026-08-03',
    scan_masuk_raw: '07:50:00',
    scan_masuk_display: '07:50:00',
    scan_pulang_raw: '16:32:00',
    scan_pulang_display: '16:32:00',
    is_valid: true,
    status: 'VALID',
    errors: [],
    warnings: [],
    keterangan: 'Data siap di-import.',
    employee_id: 4,
    is_duplicate_in_file: false,
    is_duplicate_in_db: false,
    has_empty_jam: false,
  },
  {
    no: 6,
    excel_line: 7,
    emp_num: '88',
    no_id: '88',
    nik: '3201010088',
    nama: 'EKO PRASETYO',
    tanggal_raw: '03/08/2026',
    tanggal_display: '2026-08-03',
    scan_masuk_raw: '07:55:00',
    scan_masuk_display: '07:55:00',
    scan_pulang_raw: '16:30:00',
    scan_pulang_display: '16:30:00',
    is_valid: true,
    status: 'TIDAK DITEMUKAN',
    errors: [],
    warnings: ['Karyawan tidak ditemukan di Master Data Karyawan.'],
    keterangan: 'Karyawan tidak ditemukan di Master Karyawan.',
    employee_id: null,
    is_duplicate_in_file: false,
    is_duplicate_in_db: false,
    has_empty_jam: false,
  },
  {
    no: 7,
    excel_line: 8,
    emp_num: '1',
    no_id: '1',
    nik: '3201010001',
    nama: 'AHMAD SUJATMIKO',
    tanggal_raw: '03/08/2026',
    tanggal_display: '2026-08-03',
    scan_masuk_raw: '07:54:00',
    scan_masuk_display: '07:54:00',
    scan_pulang_raw: '16:30:00',
    scan_pulang_display: '16:30:00',
    is_valid: true,
    status: 'DUPLIKAT',
    errors: [],
    warnings: ['Duplikat dengan baris 1 di dalam file yang sama.'],
    keterangan: 'Duplikat dengan baris 1 di dalam file yang sama.',
    employee_id: 1,
    is_duplicate_in_file: true,
    is_duplicate_in_db: false,
    has_empty_jam: false,
  },
  {
    no: 8,
    excel_line: 9,
    emp_num: '5',
    no_id: '5',
    nik: '3201010005',
    nama: 'FERA YULIANA',
    tanggal_raw: '32/08/2026',
    tanggal_display: '-',
    scan_masuk_raw: '07:59:00',
    scan_masuk_display: '07:59:00',
    scan_pulang_raw: '16:30:00',
    scan_pulang_display: '16:30:00',
    is_valid: false,
    status: 'INVALID',
    errors: ['Tanggal tidak valid.'],
    warnings: [],
    keterangan: 'Hari 32 tidak valid. Format tanggal harus benar.',
    employee_id: 5,
    is_duplicate_in_file: false,
    is_duplicate_in_db: false,
    has_empty_jam: false,
  },
];

export function ImportAttendanceSimulatorView({
  userSession,
  employees,
  rawAttendanceList,
  batchLogs,
  onImportComplete,
  onAddAuditLog,
}: Props) {
  const [subTab, setSubTab] = useState<'upload' | 'history'>('upload');

  // File Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string>('');
  const [availableSheets, setAvailableSheets] = useState<string[]>(['Sheet1', 'Mesin_Finger_Utama', 'Rekap_Cadangan']);
  const [selectedSheet, setSelectedSheet] = useState<string>('Sheet1');
  const [showSheetModal, setShowSheetModal] = useState<boolean>(false);

  // Preview Dialog State
  const [showPreviewModal, setShowPreviewModal] = useState<boolean>(false);
  const [previewRows, setPreviewRows] = useState<AttendanceRowPreview[]>([]);
  const [previewFilter, setPreviewFilter] = useState<'ALL' | 'VALID' | 'INVALID' | 'DUPLICATE' | 'EMPTY_TIME' | 'NOT_FOUND'>('ALL');
  const [previewSearch, setPreviewSearch] = useState<string>('');
  const [duplicateStrategy, setDuplicateStrategy] = useState<'SKIP' | 'INSERT'>('SKIP');
  const [unmatchedStrategy, setUnmatchedStrategy] = useState<'UNLINKED' | 'SKIP' | 'CREATE'>('UNLINKED');

  // Execution & Result State
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [progressText, setProgressText] = useState<string>('');
  const [showResultModal, setShowResultModal] = useState<boolean>(false);
  const [lastResult, setLastResult] = useState<any>(null);

  // History Detail Modal
  const [selectedHistoryBatch, setSelectedHistoryBatch] = useState<ImportBatchLogItem | null>(null);
  const [historySearch, setHistorySearch] = useState<string>('');
  const [historyStatusFilter, setHistoryStatusFilter] = useState<string>('ALL');

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handler Pilih Berkas Sampel
  const handleLoadSampleFile = () => {
    setSelectedFileName('AGUSTUS 2026.xlsx');
    setAvailableSheets(['Sheet1', 'Mesin_Finger_Lt1']);
    setSelectedSheet('Sheet1');
    setShowSheetModal(true);
  };

  // Handler Upload File Nyata (atau File dialog)
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.xlsx')) {
      alert('Format berkas tidak sesuai. Hanya berkas Excel berekstensi .xlsx yang diizinkan.');
      return;
    }

    setSelectedFile(file);
    setSelectedFileName(file.name);
    setAvailableSheets(['Sheet1', 'Trans_Mesin_Presensi']);
    setSelectedSheet('Sheet1');
    setShowSheetModal(true);
  };

  // Konfirmasi Pemilihan Worksheet
  const handleConfirmSheet = () => {
    setShowSheetModal(false);
    // Persiapkan preview rows
    setPreviewRows(SAMPLE_AGUSTUS_2026_ROWS);
    setShowPreviewModal(true);
  };

  // Eksekusi Import
  const handleExecuteImport = () => {
    setShowPreviewModal(false);
    setIsProcessing(true);
    setProgressPercent(20);
    setProgressText('Memvalidasi format tanggal DD/MM/YYYY dan jam scan...');

    setTimeout(() => {
      setProgressPercent(55);
      setProgressText('Memeriksa duplikasi transaksi dan mencocokkan identitas karyawan...');

      setTimeout(() => {
        setProgressPercent(85);
        setProgressText('Menyimpan catatan transaksi ke tabel attendance_raw (ACID)...');

        setTimeout(() => {
          setProgressPercent(100);
          setProgressText('Selesai.');

          // Hitung metrik import
          const batchId = `BATCH-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${String(batchLogs.length + 1).padStart(3, '0')}`;
          
          let successCount = 0;
          let failedCount = 0;
          let duplicateCount = 0;
          let skippedCount = 0;

          const newRawRecords: AttendanceRawItem[] = [];
          const newEmployeesToAdd: EmployeeItem[] = [];

          previewRows.forEach((row, idx) => {
            if (!row.is_valid) {
              failedCount++;
              return;
            }

            if (row.is_duplicate_in_file || row.is_duplicate_in_db) {
              duplicateCount++;
              if (duplicateStrategy === 'SKIP') {
                skippedCount++;
                return;
              }
            }

            let empId = row.employee_id;
            if (!empId) {
              if (unmatchedStrategy === 'SKIP') {
                skippedCount++;
                return;
              } else if (unmatchedStrategy === 'CREATE') {
                const newEmpId = employees.length + newEmployeesToAdd.length + 1;
                newEmployeesToAdd.push({
                  id: newEmpId,
                  emp_num: row.emp_num,
                  no_id: row.no_id,
                  nik: row.nik,
                  nama: row.nama,
                  unit: 'Operasional',
                  jabatan: 'Staff',
                  email: `${row.nama.toLowerCase().replace(/\s+/g, '.')}@perusahaan.co.id`,
                  keterangan: 'Dibuat otomatis dari Import Absensi Excel',
                  status: 'AKTIF',
                  tanggal_mulai: row.tanggal_display,
                  created_at: new Date().toISOString().slice(0, 19).replace('T', ' '),
                });
                empId = newEmpId;
              }
            }

            newRawRecords.push({
              id: rawAttendanceList.length + newRawRecords.length + 1,
              no: rawAttendanceList.length + newRawRecords.length + 1,
              employee_id: empId,
              emp_num: row.emp_num,
              no_id: row.no_id,
              nik: row.nik,
              nama: row.nama,
              tanggal: row.tanggal_display,
              scan_masuk: row.scan_masuk_display !== '-' ? row.scan_masuk_display : null,
              scan_pulang: row.scan_pulang_display !== '-' ? row.scan_pulang_display : null,
              source_file: selectedFileName || 'AGUSTUS 2026.xlsx',
              import_batch_id: batchId,
              created_at: new Date().toISOString().slice(0, 19).replace('T', ' '),
            });
            successCount++;
          });

          const finalStatus: 'SUCCESS' | 'PARTIAL' | 'FAILED' = 
            failedCount === 0 && skippedCount === 0 ? 'SUCCESS' : (successCount > 0 ? 'PARTIAL' : 'FAILED');

          const newBatchLog: ImportBatchLogItem = {
            id: batchLogs.length + 1,
            no: batchLogs.length + 1,
            import_batch_id: batchId,
            user_id: userSession.id,
            user_name: userSession.fullName,
            file_name: selectedFileName || 'AGUSTUS 2026.xlsx',
            import_type: 'EXCEL_ABSENSI',
            periode: 'Agustus 2026',
            total_rows: previewRows.length,
            success_rows: successCount,
            failed_rows: failedCount + skippedCount,
            duplicate_rows: duplicateCount,
            status: finalStatus,
            created_at: new Date().toISOString().slice(0, 19).replace('T', ' '),
          };

          onImportComplete(newRawRecords, newBatchLog, newEmployeesToAdd);
          onAddAuditLog(
            'IMPORT_ATTENDANCE',
            'ATTENDANCE_RAW',
            `Import absensi file '${selectedFileName || 'AGUSTUS 2026.xlsx'}' (${batchId}). Total: ${previewRows.length}, Berhasil: ${successCount}, Dilewati/Gagal: ${failedCount + skippedCount}. Status: ${finalStatus}.`
          );

          setLastResult({
            batch_id: batchId,
            file_name: selectedFileName || 'AGUSTUS 2026.xlsx',
            total_rows: previewRows.length,
            success_rows: successCount,
            failed_rows: failedCount,
            skipped_rows: skippedCount,
            duplicate_rows: duplicateCount,
            status: finalStatus,
          });

          setIsProcessing(false);
          setShowResultModal(true);
        }, 300);
      }, 400);
    }, 400);
  };

  // Unduh Error Log
  const handleDownloadErrorLog = (batchId: string) => {
    const errorRows = previewRows.filter(r => !r.is_valid || r.is_duplicate_in_file || !r.employee_id);
    let csvContent = 'data:text/csv;charset=utf-8,No Baris Excel;Nama;Tanggal;Scan Masuk;Scan Pulang;Status;Keterangan Error\n';
    errorRows.forEach(r => {
      csvContent += `${r.excel_line};"${r.nama}";${r.tanggal_raw};${r.scan_masuk_raw};${r.scan_pulang_raw};${r.status};"${r.keterangan}"\n`;
    });
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `Error_Log_${batchId}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Filtered rows in preview
  const filteredPreviewRows = previewRows.filter(r => {
    const matchSearch = previewSearch === '' || 
      `${r.nama} ${r.emp_num} ${r.no_id} ${r.nik}`.toLowerCase().includes(previewSearch.toLowerCase());
    
    let matchStatus = true;
    if (previewFilter === 'VALID') {
      matchStatus = r.is_valid && !r.is_duplicate_in_file && !r.is_duplicate_in_db;
    } else if (previewFilter === 'INVALID') {
      matchStatus = !r.is_valid;
    } else if (previewFilter === 'DUPLICATE') {
      matchStatus = r.is_duplicate_in_file || r.is_duplicate_in_db;
    } else if (previewFilter === 'EMPTY_TIME') {
      matchStatus = r.has_empty_jam;
    } else if (previewFilter === 'NOT_FOUND') {
      matchStatus = r.employee_id === null;
    }
    return matchSearch && matchStatus;
  });

  const validRowCount = previewRows.filter(r => r.is_valid).length;
  const invalidRowCount = previewRows.filter(r => !r.is_valid).length;
  const duplicateRowCount = previewRows.filter(r => r.is_duplicate_in_file || r.is_duplicate_in_db).length;
  const emptyJamRowCount = previewRows.filter(r => r.has_empty_jam).length;

  return (
    <div className="h-full flex flex-col p-6 space-y-6 overflow-y-auto">
      {/* Sub-Tabs Navigasi */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSubTab('upload')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition cursor-pointer ${
              subTab === 'upload'
                ? 'bg-blue-600 text-white shadow'
                : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Unggah & Import Absensi</span>
          </button>

          <button
            onClick={() => setSubTab('history')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition cursor-pointer ${
              subTab === 'history'
                ? 'bg-blue-600 text-white shadow'
                : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Riwayat Batch Import ({batchLogs.length})</span>
          </button>
        </div>

        <div className="text-xs text-slate-500 flex items-center gap-1 font-medium">
          <span>Target Tabel:</span>
          <code className="bg-slate-100 text-blue-700 px-1.5 py-0.5 rounded border font-bold">attendance_raw</code>
        </div>
      </div>

      {/* TAB 1: UNGGAH & IMPORT */}
      {subTab === 'upload' && (
        <div className="space-y-6 max-w-5xl mx-auto w-full">
          {/* Hero Upload Dropzone */}
          <div className="bg-white border-2 border-dashed border-blue-200 hover:border-blue-500 rounded-2xl p-8 text-center transition bg-gradient-to-b from-blue-50/40 to-white shadow-sm">
            <div className="w-16 h-16 rounded-2xl bg-blue-100 text-blue-700 flex items-center justify-center mx-auto mb-4 shadow-inner">
              <FileSpreadsheet className="w-8 h-8" />
            </div>

            <h3 className="text-base font-extrabold text-slate-900 mb-1">
              Pilih Berkas Excel Absensi (.xlsx)
            </h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto mb-5 leading-relaxed">
              Format kolom yang didukung: <strong>Emp Num. | No. ID. | NIK | Nama | Tanggal | Scan Masuk | Scan Pulang</strong>. Sistem akan membaca format tanggal secara presisi (DD/MM/YYYY).
            </p>

            {/* Tombol Pemilihan */}
            <div className="flex flex-wrap items-center justify-center gap-3">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".xlsx"
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-2 bg-blue-700 hover:bg-blue-800 text-white px-6 py-2.5 rounded-xl text-xs font-bold shadow-md transition cursor-pointer"
              >
                <Upload className="w-4 h-4" />
                <span>PILIH FILE EXCEL (.xlsx)</span>
              </button>

              <button
                onClick={handleLoadSampleFile}
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-xl text-xs font-bold shadow-md transition cursor-pointer"
              >
                <FileSpreadsheet className="w-4 h-4" />
                <span>Gunakan Contoh Berkas "AGUSTUS 2026.xlsx"</span>
              </button>
            </div>
          </div>

          {/* Progress Bar saat memproses */}
          {isProcessing && (
            <div className="bg-white border border-blue-200 rounded-xl p-5 shadow-sm space-y-2 animate-pulse">
              <div className="flex justify-between items-center text-xs font-bold text-blue-900">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-600 animate-ping"></span>
                  {progressText}
                </span>
                <span>{progressPercent}%</span>
              </div>
              <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden border">
                <div
                  className="h-full bg-blue-600 transition-all duration-300 rounded-full"
                  style={{ width: `${progressPercent}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Panduan Tahap 3 */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
            <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <Info className="w-4 h-4 text-blue-600" />
              Ketentuan Integritas Data Mentah (Tahap 3)
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-slate-600 leading-relaxed">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <strong className="text-slate-800 block mb-1">1. Prioritas Identitas Karyawan</strong>
                Sistem memetakan karyawan berdasarkan <em>(1) Emp Num. + No. ID.</em>, lalu <em>(2) Emp Num.</em>, dan <em>(3) No. ID.</em>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <strong className="text-slate-800 block mb-1">2. Fleksibilitas Jam Scan</strong>
                Data dengan Scan Pulang atau Scan Masuk kosong tetap disimpan utuh sebagai data mentah tanpa penalti.
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <strong className="text-slate-800 block mb-1">3. Batasan Mutlak Tahap 3</strong>
                Sistem <strong>TIDAK menghitung alfa</strong>, hari kerja, keterlambatan, atau potongan pada tahap ini.
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <strong className="text-slate-800 block mb-1">4. Non-Destruktif & ACID</strong>
                Import baru tidak menghapus transaksi lama secara otomatis. Setiap batch memiliki <code>import_batch_id</code> unik.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: RIWAYAT BATCH IMPORT */}
      {subTab === 'history' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 max-w-sm w-full">
              <Search className="w-4 h-4 text-slate-400 shrink-0" />
              <input
                type="text"
                placeholder="Cari Batch ID atau nama berkas..."
                value={historySearch}
                onChange={(e) => setHistorySearch(e.target.value)}
                className="w-full text-xs bg-transparent focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Status:</span>
              <select
                value={historyStatusFilter}
                onChange={(e) => setHistoryStatusFilter(e.target.value)}
                className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white font-medium focus:ring-1 focus:ring-blue-600"
              >
                <option value="ALL">Semua Status</option>
                <option value="SUCCESS">SUCCESS</option>
                <option value="PARTIAL">PARTIAL</option>
                <option value="FAILED">FAILED</option>
              </select>
            </div>
          </div>

          {/* Tabel Riwayat */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200 uppercase tracking-wider">
                  <tr>
                    <th className="p-3 text-center">No</th>
                    <th className="p-3">Batch ID</th>
                    <th className="p-3">Nama Berkas</th>
                    <th className="p-3">Periode</th>
                    <th className="p-3 text-center">Total</th>
                    <th className="p-3 text-center">Berhasil</th>
                    <th className="p-3 text-center">Gagal/Skip</th>
                    <th className="p-3 text-center">Duplikat</th>
                    <th className="p-3 text-center">Status</th>
                    <th className="p-3">Waktu Import</th>
                    <th className="p-3 text-center">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {batchLogs
                    .filter(b => {
                      const matchSearch = historySearch === '' || 
                        `${b.import_batch_id} ${b.file_name}`.toLowerCase().includes(historySearch.toLowerCase());
                      const matchStatus = historyStatusFilter === 'ALL' || b.status === historyStatusFilter;
                      return matchSearch && matchStatus;
                    })
                    .map((batch, idx) => (
                      <tr key={batch.id} className="hover:bg-slate-50 font-sans">
                        <td className="p-3 text-center text-slate-500 font-mono">{idx + 1}</td>
                        <td className="p-3 font-bold text-blue-700 font-mono">{batch.import_batch_id}</td>
                        <td className="p-3 font-medium text-slate-800">{batch.file_name}</td>
                        <td className="p-3 text-slate-600">{batch.periode}</td>
                        <td className="p-3 text-center font-bold font-mono">{batch.total_rows}</td>
                        <td className="p-3 text-center font-bold text-emerald-600 font-mono">{batch.success_rows}</td>
                        <td className="p-3 text-center font-bold text-red-600 font-mono">{batch.failed_rows}</td>
                        <td className="p-3 text-center text-amber-600 font-mono">{batch.duplicate_rows}</td>
                        <td className="p-3 text-center">
                          <span
                            className={`inline-block text-[10px] font-extrabold px-2 py-0.5 rounded-full ${
                              batch.status === 'SUCCESS'
                                ? 'bg-emerald-100 text-emerald-800'
                                : batch.status === 'PARTIAL'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {batch.status}
                          </span>
                        </td>
                        <td className="p-3 text-slate-500 text-[11px] font-mono">{batch.created_at}</td>
                        <td className="p-3 text-center">
                          <button
                            onClick={() => setSelectedHistoryBatch(batch)}
                            className="px-2.5 py-1 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded text-[11px] font-bold border border-blue-200 transition cursor-pointer"
                          >
                            Detail
                          </button>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 1: PEMILIHAN WORKSHEET */}
      {showSheetModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-600" />
              Pilih Worksheet Excel Absensi
            </h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Berkas <code>{selectedFileName}</code> memiliki beberapa lembar kerja. Silakan pilih sheet data transaksi absensi:
            </p>

            <div className="space-y-2">
              {availableSheets.map((sh) => (
                <label
                  key={sh}
                  onClick={() => setSelectedSheet(sh)}
                  className={`flex items-center gap-3 p-3 rounded-xl border text-xs font-bold cursor-pointer transition ${
                    selectedSheet === sh
                      ? 'border-blue-600 bg-blue-50/80 text-blue-900 shadow-sm'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="sheetChoice"
                    checked={selectedSheet === sh}
                    onChange={() => setSelectedSheet(sh)}
                    className="text-blue-600"
                  />
                  <span>📄 {sh}</span>
                </label>
              ))}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowSheetModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer"
              >
                Batal
              </button>
              <button
                onClick={handleConfirmSheet}
                className="px-5 py-2 text-xs font-bold bg-blue-700 hover:bg-blue-800 text-white rounded-lg shadow cursor-pointer"
              >
                Lanjutkan ke Pratinjau
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: PRATINJAU DATA LENGKAP & VALIDASI */}
      {showPreviewModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-6xl w-full h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Header Dialog */}
            <div className="p-5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50 shrink-0">
              <div>
                <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                  <FileSpreadsheet className="w-5 h-5 text-blue-600" />
                  Pratinjau Data Transaksi: {selectedFileName}
                </h3>
                <p className="text-xs text-slate-500">
                  Worksheet: <strong>{selectedSheet}</strong> | Format tanggal diproses day-first (DD/MM/YYYY)
                </p>
              </div>

              {/* Chips Metrik Ringkasan */}
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-lg bg-slate-200 text-slate-800 text-xs font-bold">
                  Total: {previewRows.length}
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-800 text-xs font-bold">
                  Valid: {validRowCount}
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-red-100 text-red-800 text-xs font-bold">
                  Invalid: {invalidRowCount}
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-amber-100 text-amber-800 text-xs font-bold">
                  Duplikat: {duplicateRowCount}
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-blue-100 text-blue-800 text-xs font-bold">
                  Jam Kosong: {emptyJamRowCount}
                </span>
              </div>
            </div>

            {/* Filter & Search Controls */}
            <div className="p-3 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-3 shrink-0">
              <div className="flex items-center gap-2 max-w-sm w-full">
                <Search className="w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Cari nama karyawan, Emp Num, No ID..."
                  value={previewSearch}
                  onChange={(e) => setPreviewSearch(e.target.value)}
                  className="w-full text-xs bg-transparent focus:outline-none"
                />
              </div>

              <div className="flex flex-wrap items-center gap-1.5 text-xs">
                {(['ALL', 'VALID', 'INVALID', 'DUPLICATE', 'EMPTY_TIME', 'NOT_FOUND'] as const).map(f => (
                  <button
                    key={f}
                    onClick={() => setPreviewFilter(f)}
                    className={`px-3 py-1 rounded-md font-bold transition cursor-pointer ${
                      previewFilter === f
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {f === 'ALL' && 'Semua'}
                    {f === 'VALID' && 'Hanya Valid'}
                    {f === 'INVALID' && 'Hanya Invalid'}
                    {f === 'DUPLICATE' && 'Hanya Duplikat'}
                    {f === 'EMPTY_TIME' && 'Jam Kosong'}
                    {f === 'NOT_FOUND' && 'Karyawan Baru'}
                  </button>
                ))}
              </div>
            </div>

            {/* Area Tabel Pratinjau */}
            <div className="flex-1 overflow-auto p-4">
              <table className="w-full text-left text-xs border border-slate-200 rounded-lg">
                <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200 sticky top-0 uppercase tracking-wider">
                  <tr>
                    <th className="p-2.5 text-center">No</th>
                    <th className="p-2.5">Emp Num</th>
                    <th className="p-2.5">No ID</th>
                    <th className="p-2.5">NIK</th>
                    <th className="p-2.5">Nama Karyawan</th>
                    <th className="p-2.5 text-center">Tanggal</th>
                    <th className="p-2.5 text-center">Scan Masuk</th>
                    <th className="p-2.5 text-center">Scan Pulang</th>
                    <th className="p-2.5 text-center">Status Validasi</th>
                    <th className="p-2.5">Keterangan</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {filteredPreviewRows.map((r) => (
                    <tr key={r.no} className="hover:bg-slate-50 font-sans">
                      <td className="p-2.5 text-center text-slate-500 font-mono">{r.no}</td>
                      <td className="p-2.5 font-mono">{r.emp_num || '-'}</td>
                      <td className="p-2.5 font-mono">{r.no_id || '-'}</td>
                      <td className="p-2.5 font-mono">{r.nik || '-'}</td>
                      <td className="p-2.5 font-bold text-slate-800">{r.nama}</td>
                      <td className="p-2.5 text-center font-mono font-medium">{r.tanggal_display}</td>
                      <td className={`p-2.5 text-center font-mono ${r.scan_masuk_display === '-' ? 'text-slate-400 italic' : 'text-slate-800'}`}>
                        {r.scan_masuk_display}
                      </td>
                      <td className={`p-2.5 text-center font-mono ${r.scan_pulang_display === '-' ? 'text-slate-400 italic' : 'text-slate-800'}`}>
                        {r.scan_pulang_display}
                      </td>
                      <td className="p-2.5 text-center">
                        <span
                          className={`inline-block text-[10px] font-extrabold px-2 py-0.5 rounded-full ${
                            r.status === 'VALID'
                              ? 'bg-emerald-100 text-emerald-800'
                              : r.status === 'VALID (JAM KOSONG)'
                              ? 'bg-blue-100 text-blue-800'
                              : r.status === 'DUPLIKAT'
                              ? 'bg-amber-100 text-amber-800'
                              : r.status === 'TIDAK DITEMUKAN'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="p-2.5 text-slate-600 text-[11px]">{r.keterangan}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Opsi Strategi Resolusi & Footer Aksi */}
            <div className="p-4 border-t border-slate-200 bg-slate-50 flex flex-wrap items-center justify-between gap-4 shrink-0">
              {/* Strategi */}
              <div className="flex flex-wrap items-center gap-6 text-xs font-semibold">
                <div className="flex items-center gap-2">
                  <span className="text-slate-700">Duplikat:</span>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input
                      type="radio"
                      name="dupStrat"
                      checked={duplicateStrategy === 'SKIP'}
                      onChange={() => setDuplicateStrategy('SKIP')}
                    />
                    <span>Lewati (Skip)</span>
                  </label>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input
                      type="radio"
                      name="dupStrat"
                      checked={duplicateStrategy === 'INSERT'}
                      onChange={() => setDuplicateStrategy('INSERT')}
                    />
                    <span>Simpan Baru</span>
                  </label>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-slate-700">Karyawan Baru:</span>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input
                      type="radio"
                      name="unmatchedStrat"
                      checked={unmatchedStrategy === 'UNLINKED'}
                      onChange={() => setUnmatchedStrategy('UNLINKED')}
                    />
                    <span>Simpan Tanpa Relasi</span>
                  </label>
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input
                      type="radio"
                      name="unmatchedStrat"
                      checked={unmatchedStrategy === 'CREATE'}
                      onChange={() => setUnmatchedStrategy('CREATE')}
                    />
                    <span>Tambah ke Master</span>
                  </label>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowPreviewModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-200 rounded-lg cursor-pointer"
                >
                  Batal
                </button>
                <button
                  disabled={validRowCount === 0}
                  onClick={handleExecuteImport}
                  className="px-6 py-2 text-xs font-extrabold bg-blue-700 hover:bg-blue-800 disabled:bg-slate-300 text-white rounded-lg shadow transition cursor-pointer"
                >
                  Simpan & Import Transaksi
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: HASIL IMPORT */}
      {showResultModal && lastResult && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto text-3xl">
              ✅
            </div>
            <div>
              <h3 className="text-base font-extrabold text-slate-900 mb-1">
                Import Absensi Berhasil Disimpan
              </h3>
              <p className="text-xs text-slate-500 font-mono">
                Batch ID: {lastResult.batch_id}
              </p>
            </div>

            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 text-left text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">Nama Berkas:</span>
                <span className="font-bold text-slate-800">{lastResult.file_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Total Baris:</span>
                <span className="font-bold font-mono text-slate-800">{lastResult.total_rows}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Transaksi Berhasil:</span>
                <span className="font-bold font-mono text-emerald-600">{lastResult.success_rows}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Data Gagal/Invalid:</span>
                <span className="font-bold font-mono text-red-600">{lastResult.failed_rows}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Duplikat Dilewati:</span>
                <span className="font-bold font-mono text-amber-600">{lastResult.skipped_rows}</span>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3">
              {(lastResult.failed_rows > 0 || lastResult.skipped_rows > 0) && (
                <button
                  onClick={() => handleDownloadErrorLog(lastResult.batch_id)}
                  className="flex items-center gap-1.5 px-4 py-2 bg-red-50 text-red-700 hover:bg-red-100 border border-red-200 rounded-lg text-xs font-bold transition cursor-pointer"
                >
                  <FileDown className="w-3.5 h-3.5" />
                  <span>Unduh Error Log (.csv)</span>
                </button>
              )}

              <button
                onClick={() => {
                  setShowResultModal(false);
                  setSubTab('history');
                }}
                className="px-5 py-2 bg-blue-700 hover:bg-blue-800 text-white rounded-lg text-xs font-bold shadow transition cursor-pointer"
              >
                Lihat Riwayat Batch
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 4: DETAIL BATCH RIWAYAT */}
      {selectedHistoryBatch && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h4 className="text-sm font-bold text-slate-900 flex items-center justify-between">
              <span>Detail Batch: {selectedHistoryBatch.import_batch_id}</span>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-mono font-bold">
                {selectedHistoryBatch.status}
              </span>
            </h4>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">Berkas Sumber:</span>
                <span className="font-bold text-slate-800">{selectedHistoryBatch.file_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Periode:</span>
                <span className="font-bold text-slate-800">{selectedHistoryBatch.periode}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Di-import Oleh:</span>
                <span className="font-bold text-slate-800">{selectedHistoryBatch.user_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Waktu Eksekusi:</span>
                <span className="font-mono text-slate-800">{selectedHistoryBatch.created_at}</span>
              </div>
              <div className="border-t pt-2 flex justify-between">
                <span className="text-slate-500">Total / Sukses / Gagal:</span>
                <span className="font-mono font-bold">
                  {selectedHistoryBatch.total_rows} / {selectedHistoryBatch.success_rows} / {selectedHistoryBatch.failed_rows}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => handleDownloadErrorLog(selectedHistoryBatch.import_batch_id)}
                className="flex items-center gap-1.5 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold cursor-pointer"
              >
                <FileDown className="w-3.5 h-3.5" />
                <span>Unduh Log (.csv)</span>
              </button>
              <button
                onClick={() => setSelectedHistoryBatch(null)}
                className="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white rounded-lg text-xs font-bold cursor-pointer"
              >
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
