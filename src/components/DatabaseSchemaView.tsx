import React from 'react';
import { Database, Table, Key, Link2, ShieldCheck } from 'lucide-react';

export default function DatabaseSchemaView() {
  const tables = [
    {
      name: 'users',
      description: 'Menyimpan kredensial login, role (ADMIN/OPERATOR), dan status akun',
      columns: [
        { name: 'id', type: 'INTEGER', isPk: true, note: 'Auto Increment' },
        { name: 'username', type: 'VARCHAR(50)', isUnique: true, note: 'Index & Unik' },
        { name: 'password_hash', type: 'VARCHAR(255)', note: 'Bcrypt Hash' },
        { name: 'full_name', type: 'VARCHAR(100)', note: 'Nama Lengkap Pengguna' },
        { name: 'role', type: 'VARCHAR(20)', note: 'ADMIN atau OPERATOR' },
        { name: 'is_active', type: 'BOOLEAN', note: 'Default TRUE' },
        { name: 'last_login', type: 'DATETIME', note: 'Waktu Login Terakhir' },
        { name: 'created_at', type: 'DATETIME', note: 'CURRENT_TIMESTAMP' },
      ],
    },
    {
      name: 'employees',
      description: 'Master data pegawai untuk pencocokan PIN/ID mesin absensi, NIP, dan NIK',
      columns: [
        { name: 'id', type: 'INTEGER', isPk: true, note: 'Auto Increment' },
        { name: 'emp_num', type: 'VARCHAR(50)', note: 'Nomor Pegawai / NIP (Unique Index)' },
        { name: 'no_id', type: 'VARCHAR(50)', note: 'No. ID / PIN Mesin Absensi (Unique Index)' },
        { name: 'nik', type: 'VARCHAR(50)', note: 'Nomor Induk Kependudukan (KTP)' },
        { name: 'nama', type: 'VARCHAR(150)', note: 'Nama Lengkap Pegawai (Wajib)' },
        { name: 'unit', type: 'VARCHAR(100)', note: 'Unit Kerja / Departemen' },
        { name: 'jabatan', type: 'VARCHAR(100)', note: 'Jabatan / Posisi Kerja' },
        { name: 'email', type: 'VARCHAR(150)', note: 'Alamat Surel Pegawai' },
        { name: 'status', type: 'VARCHAR(20)', note: 'AKTIF atau NONAKTIF (Soft Delete)' },
        { name: 'tanggal_mulai', type: 'DATE', note: 'Tanggal Mulai Bekerja' },
        { name: 'keterangan', type: 'TEXT', note: 'Catatan Tambahan HRD' },
        { name: 'created_at', type: 'DATETIME', note: 'CURRENT_TIMESTAMP' },
        { name: 'updated_at', type: 'DATETIME', note: 'Waktu Update Terakhir' },
      ],
    },
    {
      name: 'attendance_raw',
      description: 'Catatan transaksi mentah hasil import Excel mesin absensi (terisolasi tanpa kalkulasi alfa/potongan)',
      columns: [
        { name: 'id', type: 'INTEGER', isPk: true, note: 'Auto Increment' },
        { name: 'employee_id', type: 'INTEGER', isFk: true, fkRef: 'employees.id', note: 'ON DELETE SET NULL (Nullable)' },
        { name: 'emp_num', type: 'VARCHAR(50)', note: 'Emp Num dari berkas mesin' },
        { name: 'no_id', type: 'VARCHAR(50)', note: 'No. ID / PIN mesin' },
        { name: 'nik', type: 'VARCHAR(50)', note: 'NIK KTP' },
        { name: 'nama', type: 'VARCHAR(150)', note: 'Nama Karyawan dari Berkas Excel' },
        { name: 'tanggal', type: 'DATE', note: 'Tanggal Transaksi (DD/MM/YYYY diparse presisi)' },
        { name: 'scan_masuk', type: 'VARCHAR(10)', note: 'Format HH:MM:SS (Nullable jika kosong)' },
        { name: 'scan_pulang', type: 'VARCHAR(10)', note: 'Format HH:MM:SS (Nullable jika kosong)' },
        { name: 'source_file', type: 'VARCHAR(255)', note: 'Nama Berkas Excel Sumber' },
        { name: 'import_batch_id', type: 'VARCHAR(100)', note: 'Batch ID Unik (e.g. BATCH-20260801-001)' },
        { name: 'created_at', type: 'DATETIME', note: 'CURRENT_TIMESTAMP' },
      ],
    },
    {
      name: 'attendance_daily',
      description: 'Rekap absensi harian hasil pemaduan Karyawan Aktif x Kalender Hari Kerja x Transaksi Mentah',
      columns: [
        { name: 'id', type: 'INTEGER', isPk: true, note: 'Auto Increment' },
        { name: 'employee_id', type: 'INTEGER', isFk: true, fkRef: 'employees.id', note: 'Index & FK ke employees' },
        { name: 'attendance_date', type: 'DATE', note: 'Tanggal Kehadiran (Unique: employee_id + attendance_date)' },
        { name: 'scheduled_check_in', type: 'TIME', note: 'Jadwal Masuk (08:15)' },
        { name: 'scheduled_check_out', type: 'TIME', note: 'Jadwal Pulang (16:30 / 17:00)' },
        { name: 'actual_check_in', type: 'TIME', note: 'Scan Masuk Terawal (HH:MM)' },
        { name: 'actual_check_out', type: 'TIME', note: 'Scan Pulang Terakhir (HH:MM)' },
        { name: 'check_in_status', type: 'VARCHAR(20)', note: 'ADA atau TIDAK_ADA' },
        { name: 'check_out_status', type: 'VARCHAR(20)', note: 'ADA atau TIDAK_ADA' },
        { name: 'attendance_status', type: 'VARCHAR(30)', note: 'HADIR_LENGKAP, HANYA_ABSEN_MASUK, HANYA_ABSEN_PULANG, TIDAK_ABSEN' },
        { name: 'has_incomplete_scan', type: 'BOOLEAN', note: 'True jika salah satu scan tidak ada' },
        { name: 'has_conflict', type: 'BOOLEAN', note: 'True jika terdapat multi-scan' },
        { name: 'notes', type: 'TEXT', note: 'Catatan anomali absensi' },
      ],
    },
    {
      name: 'work_calendars',
      description: 'Kalender operasional hari kerja, akhir pekan, libur nasional & jadwal jam kerja dinamis',
      columns: [
        { name: 'id', type: 'INTEGER', isPk: true, note: 'Auto Increment' },
        { name: 'calendar_date', type: 'DATE', isUnique: true, note: 'Tanggal Kalender (YYYY-MM-DD)' },
        { name: 'day_name', type: 'VARCHAR(20)', note: 'Nama Hari (Senin - Minggu)' },
        { name: 'day_of_week', type: 'INTEGER', note: '0=Minggu, 1=Senin, ..., 6=Sabtu' },
        { name: 'month', type: 'INTEGER', note: 'Bulan (1-12)' },
        { name: 'year', type: 'INTEGER', note: 'Tahun (e.g. 2026)' },
        { name: 'calendar_status', type: 'VARCHAR(30)', note: 'HARI_KERJA, AKHIR_PEKAN, LIBUR_NASIONAL, CUTI_BERSAMA, HARI_KERJA_KHUSUS' },
        { name: 'is_working_day', type: 'BOOLEAN', note: 'Flag apakah hari kerja operasional wajib' },
        { name: 'scheduled_check_in', type: 'TIME', note: '08:15 untuk hari kerja' },
        { name: 'scheduled_check_out', type: 'TIME', note: '16:30 (Sen-Kam) / 17:00 (Jum)' },
        { name: 'description', type: 'VARCHAR(255)', note: 'Keterangan Hari Libur / Khusus' },
      ],
    },
    {
      name: 'settings',
      description: 'Konfigurasi target hari kerja, jam operasional, dan parameter potongan',
      columns: [
        { name: 'id', type: 'INTEGER', isPk: true, note: 'Auto Increment' },
        { name: 'setting_key', type: 'VARCHAR(100)', isUnique: true, note: 'Key Konfigurasi' },
        { name: 'setting_value', type: 'TEXT', note: 'Nilai Parameter' },
        { name: 'setting_group', type: 'VARCHAR(50)', note: 'OPERASIONAL / POTONGAN' },
        { name: 'deskripsi', type: 'VARCHAR(255)', note: 'Penjelasan Fungsi' },
      ],
    },
    {
      name: 'import_logs',
      description: 'Riwayat file Excel mesin presensi yang telah di-import',
      columns: [
        { name: 'id', type: 'INTEGER', isPk: true, note: 'Auto Increment' },
        { name: 'filename', type: 'VARCHAR(255)', note: 'Nama Berkas Excel' },
        { name: 'total_rows', type: 'INTEGER', note: 'Jumlah Baris Terbaca' },
        { name: 'imported_by', type: 'INTEGER', isFk: true, fkRef: 'users.id' },
        { name: 'created_at', type: 'DATETIME', note: 'CURRENT_TIMESTAMP' },
      ],
    },
    {
      name: 'audit_logs',
      description: 'Catatan audit jejak aktivitas sistem dan perubahan data',
      columns: [
        { name: 'id', type: 'INTEGER', isPk: true, note: 'Auto Increment' },
        { name: 'user_id', type: 'INTEGER', isFk: true, fkRef: 'users.id' },
        { name: 'action', type: 'VARCHAR(100)', note: 'LOGIN, UPDATE_SETTINGS, BACKUP' },
        { name: 'module', type: 'VARCHAR(50)', note: 'Modul Sistem' },
        { name: 'description', type: 'TEXT', note: 'Deskripsi Tindakan' },
        { name: 'created_at', type: 'DATETIME', note: 'CURRENT_TIMESTAMP' },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-600" />
            Skema Database SQLite 3 (siap_presensi.db)
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Engine SQLite lokal dengan mode <code>PRAGMA journal_mode = WAL</code> dan <code>PRAGMA foreign_keys = ON</code>.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" /> 8 Tabel Terdefinisi
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {tables.map((tbl) => (
          <div key={tbl.name} className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
            <div className="p-3.5 bg-slate-900 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Table className="w-4 h-4 text-blue-400" />
                <span className="font-mono text-sm font-bold text-blue-200">{tbl.name}</span>
              </div>
              <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
                {tbl.columns.length} Kolom
              </span>
            </div>
            <div className="px-3.5 py-2 bg-slate-50 border-b border-slate-200 text-xs text-slate-600">
              {tbl.description}
            </div>
            <div className="p-3.5 flex-1 overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="text-slate-400 text-[10px] uppercase border-b border-slate-100">
                  <tr>
                    <th className="pb-1.5 font-bold">Kolom</th>
                    <th className="pb-1.5 font-bold">Tipe</th>
                    <th className="pb-1.5 font-bold">Keterangan</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {tbl.columns.map((c, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="py-1.5 pr-2 font-semibold text-slate-800 flex items-center gap-1">
                        {c.isPk && <Key className="w-3 h-3 text-amber-500" />}
                        {c.isFk && <Link2 className="w-3 h-3 text-blue-500" />}
                        <span>{c.name}</span>
                      </td>
                      <td className="py-1.5 pr-2 text-blue-600 text-[11px]">{c.type}</td>
                      <td className="py-1.5 text-slate-500 text-[10px] font-sans">
                        {c.fkRef ? `FK -> ${c.fkRef}` : c.note}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
