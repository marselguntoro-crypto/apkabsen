export type UserRole = 'ADMIN' | 'OPERATOR';

export interface UserSession {
  id: number;
  username: string;
  fullName: string;
  role: UserRole;
  isAuthenticated: boolean;
  loginTime?: string;
}

export interface SystemSettings {
  target_hari_kerja_bulanan: string;
  jam_masuk_senin_kamis: string;
  jam_pulang_senin_kamis: string;
  jam_masuk_jumat: string;
  jam_pulang_jumat: string;
  potongan_terlambat_sd_1jam: string;
  potongan_terlambat_gt_1jam: string;
  potongan_pulang_cepat: string;
  potongan_tidak_absen_masuk: string;
  potongan_tidak_absen_pulang: string;
  potongan_tidak_hadir: string;
}

export interface BackupItem {
  filename: string;
  size: string;
  timestamp: string;
  filepath: string;
}

export interface AuditLogItem {
  id: number;
  time: string;
  user: string;
  action: string;
  module: string;
  description: string;
}

export interface EmployeeItem {
  id: number;
  emp_num: string;
  no_id: string;
  nik: string;
  nama: string;
  unit: string;
  jabatan: string;
  email: string;
  keterangan: string;
  status: 'AKTIF' | 'NONAKTIF';
  tanggal_mulai: string;
  created_at: string;
  hasAttendanceHistory?: boolean;
}

export interface EmployeeStats {
  total: number;
  aktif: number;
  nonaktif: number;
  tanpaNik: number;
}

export interface ImportPreviewItem {
  rowNumber: number;
  nama: string;
  emp_num: string;
  no_id: string;
  nik: string;
  unit: string;
  jabatan: string;
  email: string;
  status: 'AKTIF' | 'NONAKTIF';
  tanggal_mulai: string;
  statusType: 'VALID' | 'DUPLIKAT' | 'INVALID';
  note: string;
  existingId?: number;
}

export interface AttendanceRawItem {
  id: number;
  no?: number;
  employee_id?: number | null;
  emp_num: string;
  no_id: string;
  nik: string;
  nama: string;
  tanggal: string; // YYYY-MM-DD
  scan_masuk: string | null;
  scan_pulang: string | null;
  source_file: string;
  import_batch_id: string;
  created_at: string;
}

export interface AttendanceRowPreview {
  no: number;
  excel_line: number;
  emp_num: string;
  no_id: string;
  nik: string;
  nama: string;
  tanggal_raw: string;
  tanggal_display: string;
  scan_masuk_raw: string;
  scan_masuk_display: string;
  scan_pulang_raw: string;
  scan_pulang_display: string;
  is_valid: boolean;
  status: 'VALID' | 'INVALID' | 'DUPLIKAT' | 'TIDAK DITEMUKAN' | 'VALID (JAM KOSONG)';
  errors: string[];
  warnings: string[];
  keterangan: string;
  employee_id?: number | null;
  is_duplicate_in_file: boolean;
  is_duplicate_in_db: boolean;
  has_empty_jam: boolean;
}

export interface ImportBatchLogItem {
  id: number;
  no?: number;
  import_batch_id: string;
  user_id?: number;
  user_name: string;
  file_name: string;
  import_type: string;
  periode: string;
  total_rows: number;
  success_rows: number;
  failed_rows: number;
  duplicate_rows: number;
  status: 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'PROCESSING';
  error_details?: string;
  created_at: string;
}

export type CalendarStatusType = 
  | 'HARI_KERJA'
  | 'AKHIR_PEKAN'
  | 'LIBUR'
  | 'HARI_KERJA_KHUSUS'
  | 'CUTI_BERSAMA'
  | 'LIBUR_NASIONAL';

export interface WorkCalendarItem {
  id: number;
  calendar_date: string; // YYYY-MM-DD
  day_name: string; // Senin, Selasa, dll
  day_of_week: number;
  month: number;
  year: number;
  calendar_status: CalendarStatusType;
  is_working_day: boolean;
  scheduled_check_in: string | null; // HH:MM
  scheduled_check_out: string | null; // HH:MM
  description: string;
}

export type AttendanceStatusType = 
  | 'HADIR_LENGKAP'
  | 'HANYA_ABSEN_MASUK'
  | 'HANYA_ABSEN_PULANG'
  | 'TIDAK_ABSEN'
  | 'DATA_BERMASALAH';

export interface DailyAttendanceItem {
  id: number;
  employee_id: number;
  emp_num: string;
  no_id: string;
  nik: string;
  nama: string;
  unit: string;
  jabatan: string;
  attendance_date: string; // YYYY-MM-DD
  day_name: string;
  scheduled_check_in: string;
  scheduled_check_out: string;
  actual_check_in: string | null;
  actual_check_out: string | null;
  check_in_status: 'ADA' | 'TIDAK_ADA';
  check_out_status: 'ADA' | 'TIDAK_ADA';
  attendance_status: AttendanceStatusType;
  has_incomplete_scan: boolean;
  has_conflict: boolean;
  notes: string;
}



