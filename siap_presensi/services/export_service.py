"""
Modul Layanan Export Laporan SIAP (ExportService).
Mendukung:
1. Export Rekapitulasi Potongan Bulanan ke Excel (.xlsx) dan PDF (.pdf).
2. Export Laporan Detail Absensi & Potongan Harian ke Excel (.xlsx) dan PDF (.pdf).
3. Menggunakan library OpenPyXL / Pandas untuk Excel dan ReportLab untuk PDF.
4. Dilengkapi format header resmi, border sel, penomoran halaman, dan grand total.
"""
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from config.settings import EXPORTS_DIR
from services.deduction_calculation_service import DeductionCalculationService
from utils.logger import get_logger

logger = get_logger("ExportService")
EXPORT_DIR = str(EXPORTS_DIR)


class ExportService:
    """Service untuk mengekspor laporan rekapitulasi dan detail absensi."""

    @classmethod
    def export_rekap_potongan_excel(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        output_path: Optional[str] = None,
        user_name: str = "ADMIN",
    ) -> str:
        """
        Mengekspor Rekap Data Potongan Absensi ke format Excel (.xlsx).
        Kolom: No, Unit, Nama, Status, Terlambat, Pulang Cepat, Tidak Absen Masuk, Tidak Absen Pulang, Jumlah Potongan Absensi.
        """
        recap_data = DeductionCalculationService.get_monthly_deduction_recap(year, month, unit)
        rows = recap_data["rows"]
        grand_total = recap_data["grand_total"]

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unit_suffix = f"_{unit}" if unit and unit != "ALL" else ""
            filename = f"Rekap_Potongan_Absensi_{year}_{month:02d}{unit_suffix}_{timestamp}.xlsx"
            output_path = os.path.join(EXPORT_DIR, filename)

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = f"Rekap Potongan {month:02d}-{year}"
            ws.views.sheetView[0].showGridLines = True

            # Gaya Teks & Warna (Tema SIAP Navy/Blue)
            title_font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
            sub_font = Font(name="Calibri", size=10, bold=False, color="475569")
            header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
            bold_font = Font(name="Calibri", size=10, bold=True)
            regular_font = Font(name="Calibri", size=10)

            header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
            total_fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")

            thin_border = Border(
                left=Side(style="thin", color="CBD5E1"),
                right=Side(style="thin", color="CBD5E1"),
                top=Side(style="thin", color="CBD5E1"),
                bottom=Side(style="thin", color="CBD5E1"),
            )
            double_bottom = Border(
                left=Side(style="thin", color="CBD5E1"),
                right=Side(style="thin", color="CBD5E1"),
                top=Side(style="thin", color="0F172A"),
                bottom=Side(style="double", color="0F172A"),
            )

            # Judul Laporan
            ws["A1"] = "SISTEM INFORMASI ADMINISTRASI PRESENSI (SIAP)"
            ws["A1"].font = title_font
            ws["A2"] = f"REKAPITULASI POTONGAN ABSENSI KARYAWAN - PERIODE {month:02d}/{year}"
            ws["A2"].font = Font(name="Calibri", size=12, bold=True, color="0F172A")
            ws["A3"] = f"Filter Unit: {unit or 'Semua Unit'} | Tanggal Cetak: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Operator: {user_name}"
            ws["A3"].font = sub_font

            start_row = 5
            headers = [
                "No",
                "Unit Kerja",
                "Nama Karyawan",
                "Status",
                "Terlambat (Rp)",
                "Pulang Cepat (Rp)",
                "Tdk Absen Masuk (Rp)",
                "Tdk Absen Pulang (Rp)",
                "Jumlah Potongan (Rp)",
            ]

            # Tulis Header
            for col_num, h_text in enumerate(headers, 1):
                cell = ws.cell(row=start_row, column=col_num, value=h_text)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = thin_border
            ws.row_dimensions[start_row].height = 28

            current_row = start_row + 1
            for r in rows:
                ws.cell(row=current_row, column=1, value=r["no"]).alignment = Alignment(horizontal="center")
                ws.cell(row=current_row, column=2, value=r["unit"]).alignment = Alignment(horizontal="left")
                ws.cell(row=current_row, column=3, value=r["nama"]).alignment = Alignment(horizontal="left")
                ws.cell(row=current_row, column=4, value=r["status"]).alignment = Alignment(horizontal="center")
                
                # Nilai Finansial (Format Rupiah Integer)
                c5 = ws.cell(row=current_row, column=5, value=r["terlambat"])
                c6 = ws.cell(row=current_row, column=6, value=r["pulang_cepat"])
                c7 = ws.cell(row=current_row, column=7, value=r["tidak_absen_masuk"])
                c8 = ws.cell(row=current_row, column=8, value=r["tidak_absen_pulang"])
                c9 = ws.cell(row=current_row, column=9, value=r["jumlah_potongan_absensi"])

                for col_idx, c_val in [(5, c5), (6, c6), (7, c7), (8, c8), (9, c9)]:
                    c_val.number_format = '#,##0'
                    c_val.alignment = Alignment(horizontal="right")

                for c_i in range(1, 10):
                    cell = ws.cell(row=current_row, column=c_i)
                    cell.font = regular_font
                    cell.border = thin_border

                current_row += 1

            # Baris Grand Total
            ws.cell(row=current_row, column=1, value="").border = double_bottom
            ws.cell(row=current_row, column=2, value="").border = double_bottom
            ws.cell(row=current_row, column=3, value="GRAND TOTAL KESELURUHAN").alignment = Alignment(horizontal="left")
            ws.cell(row=current_row, column=4, value=f"{grand_total['karyawan_count']} Orang").alignment = Alignment(horizontal="center")

            gt_cols = [
                (5, grand_total["terlambat"]),
                (6, grand_total["pulang_cepat"]),
                (7, grand_total["tidak_absen_masuk"]),
                (8, grand_total["tidak_absen_pulang"]),
                (9, grand_total["total_potongan"]),
            ]
            for col_idx, val in gt_cols:
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal="right")

            for c_i in range(1, 10):
                cell = ws.cell(row=current_row, column=c_i)
                cell.font = bold_font
                cell.fill = total_fill
                cell.border = double_bottom

            ws.row_dimensions[current_row].height = 24

            # Atur Lebar Kolom Otomatis
            col_widths = {1: 6, 2: 24, 3: 30, 4: 12, 5: 16, 6: 18, 7: 20, 8: 20, 9: 22}
            for col_idx, w in col_widths.items():
                ws.column_dimensions[get_column_letter(col_idx)].width = w

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            wb.save(output_path)
            logger.info(f"Export rekap potongan Excel sukses: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Gagal export Excel rekap potongan: {e}", exc_info=True)
            # Fallback CSV
            import pandas as pd
            df = pd.DataFrame(rows)
            csv_path = output_path.replace(".xlsx", ".csv")
            df.to_csv(csv_path, index=False)
            return csv_path

    @classmethod
    def export_detail_absensi_excel(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        attendance_status: Optional[str] = None,
        output_path: Optional[str] = None,
        user_name: str = "ADMIN",
    ) -> str:
        """
        Mengekspor Laporan Detail Absensi & Potongan Harian ke format Excel (.xlsx).
        Kolom lengkap per hari kerja dan absensi karyawan.
        """
        report_data = DeductionCalculationService.get_daily_deduction_report(
            year=year,
            month=month,
            unit=unit,
            attendance_status=attendance_status,
            page=1,
            page_size=10000,  # Ambil seluruh data untuk export
        )
        records = report_data["records"]

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Detail_Absensi_Harian_{year}_{month:02d}_{timestamp}.xlsx"
            output_path = os.path.join(EXPORT_DIR, filename)

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = f"Detail Absensi {month:02d}-{year}"
            ws.views.sheetView[0].showGridLines = True

            title_font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
            sub_font = Font(name="Calibri", size=10, bold=False, color="475569")
            header_font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
            regular_font = Font(name="Calibri", size=9)
            header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
            thin_border = Border(
                left=Side(style="thin", color="CBD5E1"),
                right=Side(style="thin", color="CBD5E1"),
                top=Side(style="thin", color="CBD5E1"),
                bottom=Side(style="thin", color="CBD5E1"),
            )

            ws["A1"] = "SISTEM INFORMASI ADMINISTRASI PRESENSI (SIAP)"
            ws["A1"].font = title_font
            ws["A2"] = f"LAPORAN DATA ABSENSI DAN POTONGAN HARIAN - PERIODE {month:02d}/{year}"
            ws["A2"].font = Font(name="Calibri", size=12, bold=True, color="0F172A")
            ws["A3"] = f"Total Data: {len(records)} baris | Operator: {user_name} | Tanggal Cetak: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            ws["A3"].font = sub_font

            start_row = 5
            headers = [
                "No", "Unit", "Nama", "Hari", "Tanggal", "Jam Masuk", "Jam Pulang",
                "Status Masuk", "Status Pulang", "Status Kehadiran",
                "Menit Tlb", "Menit PC", "Pot. Terlambat", "Pot. Pulang Cepat",
                "Tdk Absen Masuk", "Tdk Absen Pulang", "Total Potongan"
            ]

            for col_num, h_text in enumerate(headers, 1):
                cell = ws.cell(row=start_row, column=col_num, value=h_text)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = thin_border
            ws.row_dimensions[start_row].height = 26

            current_row = start_row + 1
            for r in records:
                ws.cell(row=current_row, column=1, value=r["no"]).alignment = Alignment(horizontal="center")
                ws.cell(row=current_row, column=2, value=r["unit"]).alignment = Alignment(horizontal="left")
                ws.cell(row=current_row, column=3, value=r["nama"]).alignment = Alignment(horizontal="left")
                ws.cell(row=current_row, column=4, value=r["hari"]).alignment = Alignment(horizontal="center")
                ws.cell(row=current_row, column=5, value=r["tanggal"]).alignment = Alignment(horizontal="center")
                ws.cell(row=current_row, column=6, value=r["jam_masuk"]).alignment = Alignment(horizontal="center")
                ws.cell(row=current_row, column=7, value=r["jam_pulang"]).alignment = Alignment(horizontal="center")
                ws.cell(row=current_row, column=8, value=r["status_masuk"]).alignment = Alignment(horizontal="center")
                ws.cell(row=current_row, column=9, value=r["status_pulang"]).alignment = Alignment(horizontal="center")
                ws.cell(row=current_row, column=10, value=r["status_kehadiran"]).alignment = Alignment(horizontal="center")

                # Kolom numerik & finansial
                ws.cell(row=current_row, column=11, value=r["menit_terlambat"]).alignment = Alignment(horizontal="right")
                ws.cell(row=current_row, column=12, value=r["menit_pulang_cepat"]).alignment = Alignment(horizontal="right")

                for c_i, val in [
                    (13, r["potongan_terlambat"]),
                    (14, r["potongan_pulang_cepat"]),
                    (15, r["tidak_absen_masuk"]),
                    (16, r["tidak_absen_pulang"]),
                    (17, r["total_potongan_per_hari"]),
                ]:
                    cell = ws.cell(row=current_row, column=c_i, value=val)
                    cell.number_format = '#,##0'
                    cell.alignment = Alignment(horizontal="right")

                for c_i in range(1, 18):
                    cell = ws.cell(row=current_row, column=c_i)
                    cell.font = regular_font
                    cell.border = thin_border

                current_row += 1

            # Auto Width
            col_widths = {
                1: 5, 2: 20, 3: 26, 4: 10, 5: 12, 6: 10, 7: 10,
                8: 12, 9: 12, 10: 16, 11: 10, 12: 10,
                13: 14, 14: 14, 15: 15, 16: 15, 17: 16
            }
            for col_idx, w in col_widths.items():
                ws.column_dimensions[get_column_letter(col_idx)].width = w

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            wb.save(output_path)
            logger.info(f"Export detail absensi Excel sukses: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Gagal export Excel detail absensi: {e}", exc_info=True)
            import pandas as pd
            df = pd.DataFrame(records)
            csv_path = output_path.replace(".xlsx", ".csv")
            df.to_csv(csv_path, index=False)
            return csv_path

    @classmethod
    def export_rekap_potongan_pdf(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        output_path: Optional[str] = None,
        user_name: str = "ADMIN",
    ) -> str:
        """
        Mengekspor Rekapitulasi Potongan Bulanan ke format Dokumen PDF resmi (.pdf).
        Menggunakan ReportLab (SimpleDocTemplate, Table, TableStyle, Paragraph).
        """
        recap_data = DeductionCalculationService.get_monthly_deduction_recap(year, month, unit)
        rows = recap_data["rows"]
        grand_total = recap_data["grand_total"]

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Rekap_Potongan_Absensi_{year}_{month:02d}_{timestamp}.pdf"
            output_path = os.path.join(EXPORT_DIR, filename)

        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Orientasi Landscape untuk tabel lebar
            doc = SimpleDocTemplate(
                output_path,
                pagesize=landscape(A4),
                rightMargin=24,
                leftMargin=24,
                topMargin=24,
                bottomMargin=24,
            )

            elements = []
            styles = getSampleStyleSheet()

            # Header Dokumen Resmi
            title_style = ParagraphStyle(
                "TitleStyle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=18,
                textColor=colors.HexColor("#1E3A8A"),
                alignment=0,
            )
            sub_style = ParagraphStyle(
                "SubStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#475569"),
                alignment=0,
            )

            elements.append(Paragraph("SISTEM INFORMASI ADMINISTRASI PRESENSI (SIAP)", title_style))
            elements.append(Paragraph(f"REKAPITULASI DATA POTONGAN ABSENSI KARYAWAN - PERIODE {month:02d}/{year}", title_style))
            elements.append(Paragraph(
                f"Unit: {unit or 'Semua Unit'} | Total Karyawan: {len(rows)} orang | "
                f"Tanggal Cetak: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Dicetak oleh: {user_name}",
                sub_style
            ))
            elements.append(Spacer(1, 14))

            # Susun Tabel
            table_data = [
                [
                    "No",
                    "Unit Kerja",
                    "Nama Karyawan",
                    "Status",
                    "Terlambat",
                    "Pulang Cepat",
                    "Tdk Absen Masuk",
                    "Tdk Absen Pulang",
                    "Total Potongan",
                ]
            ]

            cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontName="Helvetica", fontSize=8, leading=10)
            bold_cell_style = ParagraphStyle("BCell", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10)

            for r in rows:
                table_data.append([
                    str(r["no"]),
                    Paragraph(r["unit"], cell_style),
                    Paragraph(r["nama"], cell_style),
                    r["status"],
                    f"Rp{r['terlambat']:,}",
                    f"Rp{r['pulang_cepat']:,}",
                    f"Rp{r['tidak_absen_masuk']:,}",
                    f"Rp{r['tidak_absen_pulang']:,}",
                    f"Rp{r['jumlah_potongan_absensi']:,}",
                ])

            # Baris Total
            table_data.append([
                "",
                "",
                Paragraph("GRAND TOTAL KESELURUHAN", bold_cell_style),
                f"{grand_total['karyawan_count']} Org",
                f"Rp{grand_total['terlambat']:,}",
                f"Rp{grand_total['pulang_cepat']:,}",
                f"Rp{grand_total['tidak_absen_masuk']:,}",
                f"Rp{grand_total['tidak_absen_pulang']:,}",
                f"Rp{grand_total['total_potongan']:,}",
            ])

            # Lebar Kolom
            col_widths = [24, 110, 150, 60, 80, 80, 90, 90, 100]

            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),      # No
                ("ALIGN", (3, 0), (3, -1), "CENTER"),      # Status
                ("ALIGN", (4, 0), (-1, -1), "RIGHT"),      # Nilai Finansial
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EFF6FF")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("LINEABOVE", (0, -1), (-1, -1), 1.2, colors.HexColor("#0F172A")),
            ]))

            elements.append(t)
            elements.append(Spacer(1, 20))

            # Tanda Tangan Pengesahan
            sign_data = [
                ["Mengetahui,", "", "Dibuat oleh,"],
                ["Kepala Sub Bagian Kepegawaian & Umum", "", "Operator Pengelola Presensi"],
                ["\n\n\n\n( ___________________________ )", "", f"\n\n\n\n( {user_name} )"],
            ]
            sign_table = Table(sign_data, colWidths=[240, 300, 240])
            sign_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]))
            elements.append(sign_table)

            doc.build(elements)
            logger.info(f"Export PDF rekap potongan sukses: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Gagal export PDF rekap potongan: {e}", exc_info=True)
            # Buat file teks informatif sebagai fallback jika reportlab terkendala
            txt_path = output_path.replace(".pdf", ".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"REKAPITULASI POTONGAN ABSENSI {month:02d}/{year}\n")
                f.write(f"Total Potongan: Rp{grand_total['total_potongan']:,}\n")
            return txt_path

    @classmethod
    def export_detail_absensi_pdf(
        cls,
        year: int,
        month: int,
        unit: Optional[str] = None,
        attendance_status: Optional[str] = None,
        output_path: Optional[str] = None,
        user_name: str = "ADMIN",
    ) -> str:
        """
        Mengekspor Laporan Detail Harian ke PDF.
        """
        report_data = DeductionCalculationService.get_daily_deduction_report(
            year=year,
            month=month,
            unit=unit,
            attendance_status=attendance_status,
            page=1,
            page_size=200,  # Batasi per lembar PDF untuk performa cetak
        )
        records = report_data["records"]

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Detail_Absensi_Harian_{year}_{month:02d}_{timestamp}.pdf"
            output_path = os.path.join(EXPORT_DIR, filename)

        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            doc = SimpleDocTemplate(
                output_path,
                pagesize=landscape(A4),
                rightMargin=20,
                leftMargin=20,
                topMargin=20,
                bottomMargin=20,
            )

            elements = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                "TitleStyle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=16,
                textColor=colors.HexColor("#1E3A8A"),
            )
            sub_style = ParagraphStyle(
                "SubStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=11,
                textColor=colors.HexColor("#475569"),
            )

            elements.append(Paragraph("SISTEM INFORMASI ADMINISTRASI PRESENSI (SIAP)", title_style))
            elements.append(Paragraph(f"LAPORAN DATA DETAIL PRESENSI DAN POTONGAN HARIAN - {month:02d}/{year}", title_style))
            elements.append(Paragraph(
                f"Data Ditampilkan: {len(records)} baris | Operator: {user_name} | Tanggal: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                sub_style
            ))
            elements.append(Spacer(1, 10))

            headers = [
                "No", "Unit", "Nama", "Hari", "Tanggal", "Masuk", "Pulang",
                "Status Kehadiran", "Tlb (m)", "PC (m)", "Pot. Tlb", "Pot. PC", "Tdk In/Out", "Total Potongan"
            ]

            table_data = [headers]
            cell_style = ParagraphStyle("C", parent=styles["Normal"], fontName="Helvetica", fontSize=7, leading=9)

            for r in records:
                tdk_in_out = r["tidak_absen_masuk"] + r["tidak_absen_pulang"]
                table_data.append([
                    str(r["no"]),
                    Paragraph(r["unit"], cell_style),
                    Paragraph(r["nama"], cell_style),
                    r["hari"],
                    r["tanggal"],
                    r["jam_masuk"],
                    r["jam_pulang"],
                    r["status_kehadiran"],
                    str(r["menit_terlambat"]),
                    str(r["menit_pulang_cepat"]),
                    f"{r['potongan_terlambat']:,}",
                    f"{r['potongan_pulang_cepat']:,}",
                    f"{tdk_in_out:,}",
                    f"{r['total_potongan_per_hari']:,}",
                ])

            col_widths = [20, 80, 110, 45, 55, 40, 40, 85, 38, 38, 55, 55, 60, 65]
            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (3, 0), (7, -1), "CENTER"),
                ("ALIGN", (8, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ]))

            elements.append(t)
            doc.build(elements)
            logger.info(f"Export PDF detail harian sukses: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Gagal export PDF detail harian: {e}", exc_info=True)
            txt_path = output_path.replace(".pdf", ".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"DETAIL PRESENSI DAN POTONGAN {month:02d}/{year}\n")
                f.write(f"Total record: {len(records)}\n")
            return txt_path
