import React, { useState } from 'react';
import { 
  Calendar as CalendarIcon, 
  Sparkles, 
  UploadCloud, 
  RotateCw, 
  Edit3, 
  CheckCircle2, 
  AlertTriangle,
  Info,
  Clock,
  Check,
  X
} from 'lucide-react';
import { WorkCalendarItem, CalendarStatusType, UserSession } from '../types';

interface CalendarSimulatorViewProps {
  userSession: UserSession;
  calendarData: WorkCalendarItem[];
  onUpdateCalendar: (updated: WorkCalendarItem[]) => void;
  onAddAuditLog: (action: string, module: string, description: string) => void;
}

const INDONESIAN_DAYS = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
const MONTHS_NAMES = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
];

export const CalendarSimulatorView: React.FC<CalendarSimulatorViewProps> = ({
  userSession,
  calendarData,
  onUpdateCalendar,
  onAddAuditLog,
}) => {
  const [selectedMonth, setSelectedMonth] = useState<number>(8); // Default Agustus
  const [selectedYear, setSelectedYear] = useState<number>(2026);
  const [editingDay, setEditingDay] = useState<WorkCalendarItem | null>(null);
  const [editStatus, setEditStatus] = useState<CalendarStatusType>('HARI_KERJA');
  const [editIn, setEditIn] = useState<string>('08:15');
  const [editOut, setEditOut] = useState<string>('16:30');
  const [editDesc, setEditDesc] = useState<string>('');
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'info' | 'error'; text: string } | null>(null);

  // Filter current view
  const currentMonthDays = calendarData.filter(
    d => d.month === selectedMonth && d.year === selectedYear
  ).sort((a, b) => a.calendar_date.localeCompare(b.calendar_date));

  // Metrik KPI
  const totalDays = currentMonthDays.length;
  const workingDays = currentMonthDays.filter(d => d.is_working_day).length;
  const weekendDays = currentMonthDays.filter(d => d.calendar_status === 'AKHIR_PEKAN').length;
  const holidayDays = currentMonthDays.filter(
    d => d.calendar_status === 'LIBUR_NASIONAL' || d.calendar_status === 'CUTI_BERSAMA' || d.calendar_status === 'LIBUR'
  ).length;
  const specialDays = currentMonthDays.filter(d => d.calendar_status === 'HARI_KERJA_KHUSUS').length;
  const targetDays = 18;
  const difference = workingDays - targetDays;

  const showNotification = (type: 'success' | 'info' | 'error', text: string) => {
    setFeedbackMsg({ type, text });
    setTimeout(() => setFeedbackMsg(null), 4000);
  };

  // Generate kalender otomatis sesuai aturan jam kerja SIAP
  const handleGenerateCalendar = (forceOverwrite = false) => {
    if (currentMonthDays.length > 0 && !forceOverwrite) {
      const confirm = window.confirm(
        `Kalender untuk ${MONTHS_NAMES[selectedMonth - 1]} ${selectedYear} sudah ada (${currentMonthDays.length} hari).\nApakah Anda ingin memperbarui dan menimpa dengan jam kerja standar?`
      );
      if (!confirm) return;
    }

    const daysInMonth = new Date(selectedYear, selectedMonth, 0).getDate();
    const newItems: WorkCalendarItem[] = [];

    for (let day = 1; day <= daysInMonth; day++) {
      const padDay = String(day).padStart(2, '0');
      const padMonth = String(selectedMonth).padStart(2, '0');
      const dateStr = `${selectedYear}-${padMonth}-${padDay}`;
      const dObj = new Date(selectedYear, selectedMonth - 1, day);
      const dayOfWeek = dObj.getDay(); // 0 = Minggu, 1 = Senin, ... 6 = Sabtu
      const dayName = INDONESIAN_DAYS[dayOfWeek];

      let status: CalendarStatusType = 'HARI_KERJA';
      let isWork = true;
      let checkIn: string | null = '08:15';
      let checkOut: string | null = '16:30';
      let desc = '';

      if (dayOfWeek === 0 || dayOfWeek === 6) {
        status = 'AKHIR_PEKAN';
        isWork = false;
        checkIn = null;
        checkOut = null;
      } else if (dayOfWeek === 5) {
        // Jumat pulang 17:00
        checkOut = '17:00';
      }

      // Contoh default libur nasional: 17 Agustus
      if (selectedMonth === 8 && day === 17) {
        status = 'LIBUR_NASIONAL';
        isWork = false;
        checkIn = null;
        checkOut = null;
        desc = 'Hari Kemerdekaan Republik Indonesia ke-81';
      }

      newItems.push({
        id: selectedYear * 10000 + selectedMonth * 100 + day,
        calendar_date: dateStr,
        day_name: dayName,
        day_of_week: dayOfWeek,
        month: selectedMonth,
        year: selectedYear,
        calendar_status: status,
        is_working_day: isWork,
        scheduled_check_in: checkIn,
        scheduled_check_out: checkOut,
        description: desc,
      });
    }

    // Merge dengan data bulan lain
    const filteredOthers = calendarData.filter(
      d => !(d.month === selectedMonth && d.year === selectedYear)
    );
    onUpdateCalendar([...filteredOthers, ...newItems]);
    onAddAuditLog('GENERATE_CALENDAR', 'CALENDAR', `Generate kalender otomatis ${MONTHS_NAMES[selectedMonth - 1]} ${selectedYear} (${daysInMonth} hari).`);
    showNotification('success', `Kalender ${MONTHS_NAMES[selectedMonth - 1]} ${selectedYear} berhasil di-generate (${newItems.length} hari).`);
  };

  const handleOpenEdit = (item: WorkCalendarItem) => {
    setEditingDay(item);
    setEditStatus(item.calendar_status);
    setEditIn(item.scheduled_check_in || (item.day_of_week === 5 ? '08:15' : '08:15'));
    setEditOut(item.scheduled_check_out || (item.day_of_week === 5 ? '17:00' : '16:30'));
    setEditDesc(item.description || '');
  };

  const handleSaveEdit = () => {
    if (!editingDay) return;

    const isWork = editStatus === 'HARI_KERJA' || editStatus === 'HARI_KERJA_KHUSUS';
    const updatedList = calendarData.map(item => {
      if (item.id === editingDay.id) {
        return {
          ...item,
          calendar_status: editStatus,
          is_working_day: isWork,
          scheduled_check_in: isWork ? editIn : null,
          scheduled_check_out: isWork ? editOut : null,
          description: editDesc,
        };
      }
      return item;
    });

    onUpdateCalendar(updatedList);
    onAddAuditLog(
      'UPDATE_CALENDAR_DAY',
      'CALENDAR',
      `Penyesuaian tanggal ${editingDay.calendar_date} (${editingDay.day_name}) status=${editStatus}, in=${isWork ? editIn : '-'}, out=${isWork ? editOut : '-'}`
    );
    showNotification('success', `Tanggal ${editingDay.calendar_date} berhasil diperbarui.`);
    setEditingDay(null);
  };

  const getStatusBadge = (status: CalendarStatusType) => {
    switch (status) {
      case 'HARI_KERJA':
        return <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-blue-100 text-blue-800 border border-blue-200">HARI KERJA</span>;
      case 'AKHIR_PEKAN':
        return <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-slate-100 text-slate-600 border border-slate-200">AKHIR PEKAN</span>;
      case 'LIBUR_NASIONAL':
        return <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-red-100 text-red-800 border border-red-200">LIBUR NASIONAL</span>;
      case 'CUTI_BERSAMA':
        return <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-amber-100 text-amber-800 border border-amber-200">CUTI BERSAMA</span>;
      case 'HARI_KERJA_KHUSUS':
        return <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-purple-100 text-purple-800 border border-purple-200">KERJA KHUSUS</span>;
      default:
        return <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-red-50 text-red-700 border border-red-200">LIBUR</span>;
    }
  };

  return (
    <div className="space-y-5">
      {/* Header Bar */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-900">Kalender Hari Kerja & Jam Operasional</h3>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-semibold border border-blue-200">
              Tahap 4
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Menetapkan hari operasional wajib, akhir pekan, libur nasional, dan jam kerja masuk/pulang terjadwal.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => handleGenerateCalendar(false)}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow transition cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Generate Kalender Otomatis</span>
          </button>
        </div>
      </div>

      {feedbackMsg && (
        <div className={`p-3 rounded-lg text-xs font-medium flex items-center gap-2 border ${
          feedbackMsg.type === 'success'
            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
            : 'bg-blue-50 text-blue-800 border-blue-200'
        }`}>
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{feedbackMsg.text}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Total Hari Kalender</div>
          <div className="text-2xl font-extrabold text-slate-900 mt-1">{totalDays}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">{MONTHS_NAMES[selectedMonth - 1]} {selectedYear}</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-[11px] font-bold text-blue-600 uppercase tracking-wider">Hari Kerja Aktual</div>
          <div className="text-2xl font-extrabold text-blue-600 mt-1">{workingDays} Hari</div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            Target: {targetDays} Hari ({difference >= 0 ? `+${difference}` : difference} hari)
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Akhir Pekan</div>
          <div className="text-2xl font-extrabold text-slate-700 mt-1">{weekendDays} Hari</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Sabtu & Minggu Off</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-[11px] font-bold text-red-600 uppercase tracking-wider">Libur & Cuti</div>
          <div className="text-2xl font-extrabold text-red-600 mt-1">{holidayDays} Hari</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Kerja Khusus: {specialDays} Hari</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-600">Pilih Bulan:</span>
            <select
              value={selectedMonth}
              onChange={e => setSelectedMonth(Number(e.target.value))}
              className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-slate-50 font-medium focus:ring-2 focus:ring-blue-500 outline-none"
            >
              {MONTHS_NAMES.map((name, idx) => (
                <option key={idx + 1} value={idx + 1}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-600">Tahun:</span>
            <select
              value={selectedYear}
              onChange={e => setSelectedYear(Number(e.target.value))}
              className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-slate-50 font-medium focus:ring-2 focus:ring-blue-500 outline-none"
            >
              {[2024, 2025, 2026, 2027, 2028].map(yr => (
                <option key={yr} value={yr}>
                  {yr}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-xs text-slate-500 flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>Kebijakan Operasional: Senin-Kamis 08:15-16:30, Jumat 08:15-17:00</span>
        </div>
      </div>

      {/* Tabel Kalender */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-3 text-center w-12">No</th>
                <th className="p-3 text-center w-28">Tanggal</th>
                <th className="p-3 text-center w-24">Hari</th>
                <th className="p-3 text-center w-36">Status Kalender</th>
                <th className="p-3 text-center w-28">Jadwal Masuk</th>
                <th className="p-3 text-center w-28">Jadwal Pulang</th>
                <th className="p-3">Keterangan / Alasan</th>
                <th className="p-3 text-center w-24">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {currentMonthDays.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-slate-400">
                    <CalendarIcon className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                    Belum ada data kalender untuk {MONTHS_NAMES[selectedMonth - 1]} {selectedYear}.
                    <br />
                    Klik tombol <strong>"Generate Kalender Otomatis"</strong> di atas.
                  </td>
                </tr>
              ) : (
                currentMonthDays.map((item, idx) => (
                  <tr 
                    key={item.id} 
                    className={`hover:bg-slate-50/80 transition ${
                      !item.is_working_day ? 'bg-slate-50/40' : ''
                    }`}
                  >
                    <td className="p-3 text-center text-slate-500">{idx + 1}</td>
                    <td className="p-3 text-center font-mono font-bold text-slate-800">
                      {item.calendar_date.split('-').reverse().join('/')}
                    </td>
                    <td className="p-3 text-center text-slate-700 font-semibold">{item.day_name}</td>
                    <td className="p-3 text-center">{getStatusBadge(item.calendar_status)}</td>
                    <td className="p-3 text-center font-mono text-slate-700">
                      {item.scheduled_check_in || <span className="text-slate-300">-</span>}
                    </td>
                    <td className="p-3 text-center font-mono text-slate-700">
                      {item.scheduled_check_out || <span className="text-slate-300">-</span>}
                    </td>
                    <td className="p-3 text-slate-600 text-[11px]">
                      {item.description || <span className="text-slate-300 italic">-</span>}
                    </td>
                    <td className="p-3 text-center">
                      <button
                        onClick={() => handleOpenEdit(item)}
                        className="px-2.5 py-1 text-[11px] font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 rounded border border-blue-200 transition cursor-pointer"
                      >
                        Ubah
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Edit Hari Kalender */}
      {editingDay && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h4 className="font-bold text-slate-900 text-sm">
                  Penyesuaian Hari: {editingDay.day_name}, {editingDay.calendar_date}
                </h4>
                <p className="text-xs text-slate-500">Ubah status hari atau jadwal operasional kerja khusus.</p>
              </div>
              <button 
                onClick={() => setEditingDay(null)}
                className="text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Status Kalender:</label>
                <select
                  value={editStatus}
                  onChange={e => setEditStatus(e.target.value as CalendarStatusType)}
                  className="w-full border border-slate-300 rounded-lg p-2 bg-slate-50 font-medium"
                >
                  <option value="HARI_KERJA">HARI_KERJA (Wajib Hadir)</option>
                  <option value="AKHIR_PEKAN">AKHIR_PEKAN (Sabtu / Minggu)</option>
                  <option value="LIBUR_NASIONAL">LIBUR_NASIONAL (Hari Libur Resmi)</option>
                  <option value="CUTI_BERSAMA">CUTI_BERSAMA (Cuti Pemerintah)</option>
                  <option value="HARI_KERJA_KHUSUS">HARI_KERJA_KHUSUS (Jam Kerja Berbeda)</option>
                  <option value="LIBUR">LIBUR (Lainnya)</option>
                </select>
              </div>

              {(editStatus === 'HARI_KERJA' || editStatus === 'HARI_KERJA_KHUSUS') && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Jam Masuk (HH:MM):</label>
                    <input
                      type="text"
                      value={editIn}
                      onChange={e => setEditIn(e.target.value)}
                      placeholder="08:15"
                      className="w-full border border-slate-300 rounded-lg p-2 font-mono"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Jam Pulang (HH:MM):</label>
                    <input
                      type="text"
                      value={editOut}
                      onChange={e => setEditOut(e.target.value)}
                      placeholder="16:30"
                      className="w-full border border-slate-300 rounded-lg p-2 font-mono"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Keterangan / Alasan:</label>
                <textarea
                  value={editDesc}
                  onChange={e => setEditDesc(e.target.value)}
                  placeholder="Misal: Hari Kemerdekaan RI ke-81, Cuti Bersama Idul Fitri..."
                  className="w-full border border-slate-300 rounded-lg p-2 h-20 resize-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setEditingDay(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg cursor-pointer"
              >
                Batal
              </button>
              <button
                onClick={handleSaveEdit}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow cursor-pointer"
              >
                Simpan Perubahan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
