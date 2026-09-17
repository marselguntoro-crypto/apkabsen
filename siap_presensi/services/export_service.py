"""
Layanan Ekspor Laporan Rekapitulasi & Detail Potongan Absensi (Tahap 5).
SIAP - Sistem Informasi Administrasi Presensi.

Mendukung:
1. Ekspor Rekap Potongan Bulanan ke format Excel (.xlsx) dan PDF (.pdf)
2. Ekspor Detail Absensi & Potongan Harian ke format Excel (.xlsx) dan PDF (.pdf)
Dengan tata letak profesional, header resmi, format mata uang Rupiah, dan total otomatis.
"""
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from utils.logger import get_logger

logger = get_logger("ExportService")


class ExportService:
    """Layanan ekspor laporan absensi dan potongan ke Excel dan PDF."""

    @staticmethod
    def _ensure_directory(file_path: str):
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    # =========================================================================
    # EKSPOR REKAP POTONGAN BULANAN KE EXCEL
    # =========================================================================
    @classmethod
    def export_rekap_potongan_excel(
        cls,
        rekap_data: Dict[str, Any],
        output_path: str,
    ) -> str:
        """
        Mengekspor data rekap bulanan ke format Excel (.xlsx) menggunakan openpyxl.
        """
        cls._ensure_directory(output_path)
        year = rekap_data.get("year", datetime.now().year)
        month = rekap_data.get("month", datetime.now().month)
        unit = rekap_data.get("unit_filter", "SEMUA UNIT")
        items = rekap_data.get("items", [])
        grand_total = rekap_data.get("grand_total", {})

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            wb = Workbook()
            ws = wb.active
            ws.title = f"Rekap Potongan {month:02d}-{year}"

            # Palet Warna Korporat
            navy_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
            soft_blue_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
            gray_header_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
            
            font_title = Font(name="Calibri", size=16, bold=True, color="1E3A8A")
            font_subtitle = Font(name="Calibri", size=11, italic=True, color="475569")
            font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
            font_bold = Font(name="Calibri", size=10, bold=True)
            font_regular = Font(name="Calibri", size=10)

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

            # 1. Judul Dokumen
            ws["A1"] = "SISTEM INFORMASI ADMINISTRASI PRESENSI (SIAP)"
            ws["A1"].font = font_title
            ws["A2"] = f"LAPORAN REKAPITULASI DATA POTONGAN ABSENSI KARYAWAN"
            ws["A2"].font = Font(name="Calibri", size=12, bold=True, color="0F172A")
            ws["A3"] = f"Periode: Bulan {month:02d} Tahun {year} | Unit: {unit} | Dicetak: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            ws["A3"].font = font_subtitle

            # 2. Header Tabel (Baris 5)
            headers = [
                "No", "Unit", "No ID / NIK", "Nama Karyawan", "Status",
                "Terlambat (Rp)", "Pulang Cepat (Rp)", "Tidak Absen Masuk (Rp)",
                "Tidak Absen Pulang (Rp)", "Jumlah Potongan (Rp)"
            ]
            row_idx = 5
            for col_idx, header in enumerate(headers, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=header)
                cell.font = font_header
                cell.fill = navy_fill
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = thin_border
            ws.row_dimensions[row_idx].height = 26

            # 3. Isi Data
            currency_format = '"Rp"#,##0'
            row_idx = 6
            for item in items:
                ws.cell(row=row_idx, column=1, value=item["no"]).alignment = Alignment(horizontal="center")
                ws.cell(row=row_idx, column=2, value=item["unit"]).alignment = Alignment(horizontal="left")
                ws.cell(row=row_idx, column=3, value=item.get("no_id") or item.get("nik") or item.get("emp_num") or "-").alignment = Alignment(horizontal="center")
                ws.cell(row=row_idx, column=4, value=item["nama"]).alignment = Alignment(horizontal="left")
                ws.cell(row=row_idx, column=5, value=item["status"]).alignment = Alignment(horizontal="center")

                # Kolom Nominal
                for c_idx, val in enumerate([
                    item["terlambat"], item["pulang_cepat"],
                    item["tidak_absen_masuk"], item["tidak_absen_pulang"],
                    item["jumlah_potongan"]
                ], start=6):
                    c = ws.cell(row=row_idx, column=c_idx, value=val)
                    c.number_format = currency_format
                    c.alignment = Alignment(horizontal="right")

                for c_idx in range(1, 11):
                    ws.cell(row=row_idx, column=c_idx).font = font_regular
                    ws.cell(row=row_idx, column=c_idx).border = thin_border
                row_idx += 1

            # 4. Baris Grand Total
            ws.cell(row=row_idx, column=1, value="TOTAL KESELURUHAN")
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=5)
            ws.cell(row=row_idx, column=1).alignment = Alignment(horizontal="center")

            totals_to_write = [
                grand_total.get("total_terlambat", 0),
                grand_total.get("total_pulang_cepat", 0),
                grand_total.get("total_tidak_absen_masuk", 0),
                grand_total.get("total_tidak_absen_pulang", 0),
                grand_total.get("total_potongan_keseluruhan", 0),
            ]
            for c_idx, val in enumerate(totals_to_write, start=6):
                c = ws.cell(row=row_idx, column=c_idx, value=val)
                c.number_format = currency_format
                c.alignment = Alignment(horizontal="right")

            for c_idx in range(1, 11):
                ws.cell(row=row_idx, column=c_idx).font = font_bold
                ws.cell(row=row_idx, column=c_idx).fill = soft_blue_fill
                ws.cell(row=row_idx, column=c_idx).border = double_bottom
            ws.row_dimensions[row_idx].height = 22

            # 5. Sesuaikan Lebar Kolom
            col_widths = {
                1: 6, 2: 18, 3: 16, 4: 26, 5: 12,
                6: 18, 7: 18, 8: 24, 9: 24, 10: 24
            }
            for col_idx, width in col_widths.items():
                ws.column_dimensions[get_column_letter(col_idx)].width = width

            wb.save(output_path)
            logger.info(f"Berhasil mengekspor rekap potongan Excel ke {output_path}")
            return output_path

        except ImportError:
            logger.warning("openpyxl belum terpasang. Menggunakan fallback CSV format.")
            import csv
            with open(output_path.replace(".xlsx", ".csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["No", "Unit", "Nama", "Status", "Terlambat", "Pulang Cepat", "Tidak Absen Masuk", "Tidak Absen Pulang", "Jumlah Potongan"])
                for item in items:
                    writer.writerow([
                        item["no"], item["unit"], item["nama"], item["status"],
                        item["terlambat"], item["pulang_cepat"],
                        item["tidak_absen_masuk"], item["tidak_absen_pulang"],
                        item["jumlah_potongan"]
                    ])
            return output_path

    # =========================================================================
    # EKSPOR DETAIL ABSENSI & POTONGAN HARIAN KE EXCEL
    # =========================================================================
    @classmethod
    def export_detail_absensi_excel(
        cls,
        detail_rows: List[Dict[str, Any]],
        year: int,
        month: int,
        unit: Optional[str],
        output_path: str,
    ) -> str:
        """
        Mengekspor data rincian harian ke format Excel (.xlsx) dengan 17 kolom lengkap.
        """
        cls._ensure_directory(output_path)
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            wb = Workbook()
            ws = wb.active
            ws.title = f"Detail Harian {month:02d}-{year}"

            navy_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
            soft_blue_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
            font_title = Font(name="Calibri", size=15, bold=True, color="1E3A8A")
            font_header = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
            font_bold = Font(name="Calibri", size=9, bold=True)
            font_regular = Font(name="Calibri", size=9)

            thin_border = Border(
                left=Side(style="thin", color="CBD5E1"),
                right=Side(style="thin", color="CBD5E1"),
                top=Side(style="thin", color="CBD5E1"),
                bottom=Side(style="thin", color="CBD5E1"),
            )

            # Header Dokumen
            ws["A1"] = "DATA ABSENSI DAN RINCIAN POTONGAN HARIAN"
            ws["A1"].font = font_title
            ws["A2"] = f"Periode: Bulan {month:02d}/{year} | Unit: {unit or 'SEMUA UNIT'} | Total Record: {len(detail_rows)}"
            ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="475569")

            headers = [
                "No", "Unit", "Nama", "Hari", "Tanggal",
                "Jam Masuk", "Jam Pulang", "Status Masuk", "Status Pulang", "Status Kehadiran",
                "Menit Tlbt", "Menit PC", "Potongan Tlbt (Rp)", "Potongan PC (Rp)",
                "Tdk Absen Masuk (Rp)", "Tdk Absen Pulang (Rp)", "Total Potongan (Rp)"
            ]
            row_idx = 4
            for col_idx, header in enumerate(headers, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=header)
                cell.font = font_header
                cell.fill = navy_fill
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = thin_border
            ws.row_dimensions[row_idx].height = 28

            currency_fmt = '"Rp"#,##0'
            row_idx = 5
            total_late = 0
            total_pc = 0
            total_miss_in = 0
            total_miss_out = 0
            total_all = 0

            for r in detail_rows:
                ws.cell(row=row_idx, column=1, value=r["no"]).alignment = Alignment(horizontal="center")
                ws.cell(row=row_idx, column=2, value=r["unit"])
                ws.cell(row=row_idx, column=3, value=r["nama"])
                ws.cell(row=row_idx, column=4, value=r["hari"]).alignment = Alignment(horizontal="center")
                ws.cell(row=row_idx, column=5, value=r["tanggal"]).alignment = Alignment(horizontal="center")
                ws.cell(row=row_idx, column=6, value=r["jam_masuk"]).alignment = Alignment(horizontal="center")
                ws.cell(row=row_idx, column=7, value=r["jam_pulang"]).alignment = Alignment(horizontal="center")
                ws.cell(row=row_idx, column=8, value=r["status_masuk"]).alignment = Alignment(horizontal="center")
                ws.cell(row=row_idx, column=9, value=r["status_pulang"]).alignment = Alignment(horizontal="center")
                ws.cell(row=row_idx, column=10, value=r["status_kehadiran"]).alignment = Alignment(horizontal="center")
                ws.cell(row=row_idx, column=11, value=r["menit_terlambat"]).alignment = Alignment(horizontal="right")
                ws.cell(row=row_idx, column=12, value=r["menit_pulang_cepat"]).alignment = Alignment(horizontal="right")

                c13 = ws.cell(row=row_idx, column=13, value=r["potongan_terlambat"])
                c13.number_format = currency_fmt
                c13.alignment = Alignment(horizontal="right")

                c14 = ws.cell(row=row_idx, column=14, value=r["potongan_pulang_cepat"])
                c14.number_format = currency_fmt
                c14.alignment = Alignment(horizontal="right")

                c15 = ws.cell(row=row_idx, column=15, value=r["tidak_absen_masuk"])
                c15.number_format = currency_fmt
                c15.alignment = Alignment(horizontal="right")

                c16 = ws.cell(row=row_idx, column=16, value=r["tidak_absen_pulang"])
                c16.number_format = currency_fmt
                c16.alignment = Alignment(horizontal="right")

                c17 = ws.cell(row=row_idx, column=17, value=r["total_potongan"])
                c17.number_format = currency_fmt
                c17.alignment = Alignment(horizontal="right")

                total_late += r["potongan_terlambat"]
                total_pc += r["potongan_pulang_cepat"]
                total_miss_in += r["tidak_absen_masuk"]
                total_miss_out += r["tidak_absen_pulang"]
                total_all += r["total_potongan"]

                for c_idx in range(1, 18):
                    ws.cell(row=row_idx, column=c_idx).font = font_regular
                    ws.cell(row=row_idx, column=c_idx).border = thin_border
                row_idx += 1

            # Grand Total
            ws.cell(row=row_idx, column=1, value="TOTAL")
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=12)
            ws.cell(row=row_idx, column=1).alignment = Alignment(horizontal="center")

            for c_idx, val in enumerate([total_late, total_pc, total_miss_in, total_miss_out, total_all], start=13):
                c = ws.cell(row=row_idx, column=c_idx, value=val)
                c.number_format = currency_fmt
                c.alignment = Alignment(horizontal="right")

            for c_idx in range(1, 18):
                ws.cell(row=row_idx, column=c_idx).font = font_bold
                ws.cell(row=row_idx, column=c_idx).fill = soft_blue_fill
                ws.cell(row=row_idx, column=c_idx).border = thin_border

            # Lebar Kolom
            widths = [5, 14, 22, 10, 12, 10, 10, 14, 14, 16, 10, 10, 15, 15, 18, 18, 18]
            for c_idx, w in enumerate(widths, start=1):
                ws.column_dimensions[get_column_letter(c_idx)].width = w

            wb.save(output_path)
            logger.info(f"Berhasil mengekspor detail absensi Excel ke {output_path}")
            return output_path

        except ImportError:
            logger.warning("openpyxl belum terpasang.")
            return output_path

    # =========================================================================
    # EKSPOR KE FORMAT PDF MENGGUNAKAN REPORTLAB
    # =========================================================================
    @classmethod
    def export_rekap_potongan_pdf(
        cls,
        rekap_data: Dict[str, Any],
        user_name: str,
        output_path: str,
    ) -> str:
        """
        Mengekspor rekapitulasi bulanan ke dokumen PDF resmi berorientasi landscape.
        """
        cls._ensure_directory(output_path)
        year = rekap_data.get("year", datetime.now().year)
        month = rekap_data.get("month", datetime.now().month)
        unit = rekap_data.get("unit_filter", "SEMUA UNIT")
        items = rekap_data.get("items", [])
        grand_total = rekap_data.get("grand_total", {})

        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            doc = SimpleDocTemplate(
                output_path,
                pagesize=landscape(letter),
                rightMargin=24,
                leftMargin=24,
                topMargin=24,
                bottomMargin=24,
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "TitleStyle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=14,
                textColor=colors.HexColor("#1E3A8A"),
                spaceAfter=4,
            )
            subtitle_style = ParagraphStyle(
                "SubTitleStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                textColor=colors.HexColor("#475569"),
                spaceAfter=12,
            )
            cell_header_style = ParagraphStyle(
                "HeaderStyle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                textColor=colors.white,
                alignment=1,  # Center
            )
            cell_body_style = ParagraphStyle(
                "BodyStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                textColor=colors.HexColor("#0F172A"),
            )
            cell_right_style = ParagraphStyle(
                "RightStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                textColor=colors.HexColor("#0F172A"),
                alignment=2,  # Right
            )
            cell_bold_right_style = ParagraphStyle(
                "BoldRightStyle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                textColor=colors.HexColor("#0F172A"),
                alignment=2,  # Right
            )

            elements = []

            # 1. Judul Header
            elements.append(Paragraph("SISTEM INFORMASI ADMINISTRASI PRESENSI (SIAP)", title_style))
            elements.append(Paragraph(
                f"REKAPITULASI DATA POTONGAN ABSENSI KARYAWAN | Periode: {month:02d}/{year} | Unit: {unit} | Dicetak oleh: {user_name} ({datetime.now().strftime('%d/%m/%Y %H:%M')})",
                subtitle_style,
            ))

            # 2. Tabel Data
            table_data = [[
                Paragraph("<b>No</b>", cell_header_style),
                Paragraph("<b>Unit</b>", cell_header_style),
                Paragraph("<b>Nama</b>", cell_header_style),
                Paragraph("<b>Status</b>", cell_header_style),
                Paragraph("<b>Terlambat</b>", cell_header_style),
                Paragraph("<b>Pulang Cepat</b>", cell_header_style),
                Paragraph("<b>Tdk Absen Masuk</b>", cell_header_style),
                Paragraph("<b>Tdk Absen Pulang</b>", cell_header_style),
                Paragraph("<b>Total Potongan</b>", cell_header_style),
            ]]

            for it in items:
                table_data.append([
                    Paragraph(str(it["no"]), cell_body_style),
                    Paragraph(str(it["unit"]), cell_body_style),
                    Paragraph(str(it["nama"]), cell_body_style),
                    Paragraph(str(it["status"]), cell_body_style),
                    Paragraph(f"Rp{it['terlambat']:,}", cell_right_style),
                    Paragraph(f"Rp{it['pulang_cepat']:,}", cell_right_style),
                    Paragraph(f"Rp{it['tidak_absen_masuk']:,}", cell_right_style),
                    Paragraph(f"Rp{it['tidak_absen_pulang']:,}", cell_right_style),
                    Paragraph(f"Rp{it['jumlah_potongan']:,}", cell_bold_right_style),
                ])

            # Baris Total
            table_data.append([
                Paragraph("<b>TOTAL KESELURUHAN</b>", cell_body_style),
                "", "", "",
                Paragraph(f"Rp{grand_total.get('total_terlambat', 0):,}", cell_bold_right_style),
                Paragraph(f"Rp{grand_total.get('total_pulang_cepat', 0):,}", cell_bold_right_style),
                Paragraph(f"Rp{grand_total.get('total_tidak_absen_masuk', 0):,}", cell_bold_right_style),
                Paragraph(f"Rp{grand_total.get('total_tidak_absen_pulang', 0):,}", cell_bold_right_style),
                Paragraph(f"Rp{grand_total.get('total_potongan_keseluruhan', 0):,}", cell_bold_right_style),
            ])

            col_widths = [24, 70, 130, 60, 75, 75, 95, 95, 95]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            t_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1E3A8A")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#DBEAFE")),
                ("SPAN", (0, -1), (3, -1)),
                ("ALIGN", (0, -1), (3, -1), "CENTER"),
            ]
            # Striping rows
            for i in range(1, len(table_data) - 1):
                if i % 2 == 0:
                    t_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F8FAFC")))
            table.setStyle(TableStyle(t_style))
            elements.append(table)

            doc.build(elements)
            logger.info(f"Berhasil membuat dokumen PDF rekap potongan: {output_path}")
            return output_path

        except ImportError:
            logger.warning("reportlab belum terpasang.")
            return output_path

    @classmethod
    def export_detail_absensi_pdf(
        cls,
        detail_rows: List[Dict[str, Any]],
        year: int,
        month: int,
        unit: Optional[str],
        user_name: str,
        output_path: str,
    ) -> str:
        """
        Mengekspor laporan rincian absensi harian ke format PDF landscape.
        """
        cls._ensure_directory(output_path)
        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            doc = SimpleDocTemplate(
                output_path,
                pagesize=landscape(letter),
                rightMargin=20,
                leftMargin=20,
                topMargin=20,
                bottomMargin=20,
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "TitleStyle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=13,
                textColor=colors.HexColor("#1E3A8A"),
                spaceAfter=3,
            )
            subtitle_style = ParagraphStyle(
                "SubTitleStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                textColor=colors.HexColor("#475569"),
                spaceAfter=8,
            )
            cell_header_style = ParagraphStyle(
                "HeaderStyle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7,
                textColor=colors.white,
                alignment=1,
            )
            cell_body_style = ParagraphStyle(
                "BodyStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7,
                textColor=colors.HexColor("#0F172A"),
            )
            cell_right_style = ParagraphStyle(
                "RightStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7,
                textColor=colors.HexColor("#0F172A"),
                alignment=2,
            )

            elements = []
            elements.append(Paragraph("DATA ABSENSI DAN RINCIAN POTONGAN HARIAN (SIAP)", title_style))
            elements.append(Paragraph(
                f"Periode: Bulan {month:02d}/{year} | Unit: {unit or 'SEMUA UNIT'} | Dicetak oleh: {user_name} | {len(detail_rows)} data",
                subtitle_style,
            ))

            headers = [
                "No", "Unit", "Nama", "Tgl", "Masuk", "Pulang",
                "Status", "Tlbt", "PC", "Pot. Tlbt", "Pot. PC", "Tdk Masuk", "Tdk Pulang", "Total"
            ]
            table_data = [[Paragraph(f"<b>{h}</b>", cell_header_style) for h in headers]]

            total_pot = 0
            for r in detail_rows:
                table_data.append([
                    Paragraph(str(r["no"]), cell_body_style),
                    Paragraph(str(r["unit"]), cell_body_style),
                    Paragraph(str(r["nama"]), cell_body_style),
                    Paragraph(str(r["tanggal"])[8:], cell_body_style),
                    Paragraph(str(r["jam_masuk"]), cell_body_style),
                    Paragraph(str(r["jam_pulang"]), cell_body_style),
                    Paragraph(str(r["status_kehadiran"])[:10], cell_body_style),
                    Paragraph(f"{r['menit_terlambat']}m", cell_right_style),
                    Paragraph(f"{r['menit_pulang_cepat']}m", cell_right_style),
                    Paragraph(f"Rp{r['potongan_terlambat']:,}", cell_right_style),
                    Paragraph(f"Rp{r['potongan_pulang_cepat']:,}", cell_right_style),
                    Paragraph(f"Rp{r['tidak_absen_masuk']:,}", cell_right_style),
                    Paragraph(f"Rp{r['tidak_absen_pulang']:,}", cell_right_style),
                    Paragraph(f"<b>Rp{r['total_potongan']:,}</b>", cell_right_style),
                ])
                total_pot += r["total_potongan"]

            # Baris Total
            table_data.append([
                Paragraph("<b>TOTAL POTONGAN KESELURUHAN</b>", cell_body_style),
                "", "", "", "", "", "", "", "", "", "", "", "",
                Paragraph(f"<b>Rp{total_pot:,}</b>", cell_right_style),
            ])

            widths = [20, 55, 95, 30, 36, 36, 60, 30, 30, 50, 50, 55, 55, 60]
            t = Table(table_data, colWidths=widths, repeatRows=1)
            t_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1E3A8A")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#DBEAFE")),
                ("SPAN", (0, -1), (12, -1)),
                ("ALIGN", (0, -1), (12, -1), "CENTER"),
            ]
            for i in range(1, len(table_data) - 1):
                if i % 2 == 0:
                    t_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F8FAFC")))
            t.setStyle(TableStyle(t_style))
            elements.append(t)

            doc.build(elements)
            logger.info(f"Berhasil membuat dokumen PDF detail absensi: {output_path}")
            return output_path

        except ImportError:
            logger.warning("reportlab belum terpasang.")
            return output_path
