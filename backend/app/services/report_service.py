import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from app.core.config import settings

class ReportService:
    @classmethod
    def export_analysis_to_excel(
        cls,
        analysis_data: dict[str, Any],
        filename_prefix: str = "Laporan_PTPN"
    ) -> Path:
        """
        Creates a professional formatted Excel workbook with:
        1. Metadata Header (Title, Generated Date, Formula Applied, Alasan, Filters)
        2. Results Table with Excel formulas
        3. Raw Dataset Sheet (if provided)
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Ringkasan Laporan"

        # Theme Colors (PTPN Green & Slate Modern Theme)
        primary_color = "1B4D3E" # PTPN Forest Green
        secondary_color = "2C6E49"
        accent_light = "E8F5E9"
        border_color = "D0D7DE"

        font_title = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        font_bold = Font(name="Calibri", size=11, bold=True)
        font_regular = Font(name="Calibri", size=11)
        font_formula = Font(name="Consolas", size=10, italic=True, color="0D47A1")

        fill_title = PatternFill(start_color=primary_color, end_color=primary_color, fill_type="solid")
        fill_header = PatternFill(start_color=secondary_color, end_color=secondary_color, fill_type="solid")
        fill_zebra = PatternFill(start_color="F9FAF8", end_color="F9FAF8", fill_type="solid")
        fill_highlight = PatternFill(start_color=accent_light, end_color=accent_light, fill_type="solid")

        thin_border = Border(
            left=Side(style="thin", color=border_color),
            right=Side(style="thin", color=border_color),
            top=Side(style="thin", color=border_color),
            bottom=Side(style="thin", color=border_color)
        )

        # 1. Main Title Banner
        ws.merge_cells("A1:G1")
        title_cell = ws["A1"]
        title_cell.value = "SISTEM PEMODELAN LAPORAN & FORMULA EXCEL OTOMATIS - PTPN"
        title_cell.font = font_title
        title_cell.fill = fill_title
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 40

        # 2. Metadata Section
        meta_items = [
            ("Analisis Permintaan:", analysis_data.get("user_query", "-")),
            ("Formula yang Dipilih:", f"{analysis_data.get('formula_id', '-')} ({analysis_data.get('formula_name', '')})"),
            ("Formula Excel yang Dihasilkan:", analysis_data.get("generated_excel_formula", "-")),
            ("Alasan Pemilihan Formula:", analysis_data.get("formula_explanation", "-")),
            ("Waktu Generate:", datetime.now().strftime("%d-%m-%Y %H:%M:%S")),
        ]

        row_idx = 3
        for label, val in meta_items:
            ws.cell(row=row_idx, column=1, value=label).font = font_bold
            ws.merge_cells(start_row=row_idx, start_column=2, end_row=row_idx, end_column=7)
            val_cell = ws.cell(row=row_idx, column=2)
            val_str = str(val or "-")
            val_cell.value = val_str
            if "Formula" in label and val_str.startswith("="):
                val_cell.data_type = "s"  # Explicitly store as text so Excel displays the formula string!
                val_cell.font = font_formula
            else:
                val_cell.font = font_formula if "Formula" in label else font_regular
            val_cell.alignment = Alignment(wrap_text=True, vertical="center")
            row_idx += 1

        row_idx += 1 # Spacing

        # 3. Table Section
        headers = analysis_data.get("table_headers", [])
        rows = analysis_data.get("table_rows", [])

        if headers and rows:
            # Table Header with 'No' as first column
            full_headers = ["No"] + headers
            for c_idx, h in enumerate(full_headers, start=1):
                cell = ws.cell(row=row_idx, column=c_idx, value=h)
                cell.font = font_header
                cell.fill = fill_header
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border
            ws.row_dimensions[row_idx].height = 25
            header_row_idx = row_idx
            row_idx += 1

            start_data_row = row_idx
            for r_idx, r in enumerate(rows, start=1):
                # Col 1: No
                cell_no = ws.cell(row=row_idx, column=1, value=r_idx)
                cell_no.border = thin_border
                cell_no.font = font_regular
                cell_no.alignment = Alignment(horizontal="center", vertical="center")
                if (row_idx - start_data_row) % 2 == 1:
                    cell_no.fill = fill_zebra

                for c_idx, h in enumerate(headers, start=2):
                    raw_val = r.get(h, "")
                    # Convert numeric strings to actual numbers for Excel formulas
                    num_val = None
                    try:
                        if isinstance(raw_val, (int, float)):
                            num_val = raw_val
                        elif isinstance(raw_val, str) and raw_val.replace("-", "", 1).replace(".", "", 1).isdigit():
                            num_val = float(raw_val) if "." in raw_val else int(raw_val)
                    except Exception:
                        num_val = None

                    cell = ws.cell(row=row_idx, column=c_idx)
                    cell.border = thin_border

                    if num_val is not None:
                        cell.value = num_val
                        cell.number_format = "#,##0.00" if isinstance(num_val, float) else "#,##0"
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                        cell.font = font_regular
                    else:
                        cell.value = str(raw_val) if raw_val is not None else "-"
                        cell.alignment = Alignment(horizontal="left", vertical="center")
                        cell.font = font_regular

                    if (row_idx - start_data_row) % 2 == 1:
                        cell.fill = fill_zebra
                row_idx += 1

            # Summary Total Row if applicable
            target_field = analysis_data.get("calculation_summary", {}).get("target_field")
            target_col_idx = None
            if target_field:
                for idx, h in enumerate(headers, start=2):
                    if h.lower() == str(target_field).lower() or str(target_field).lower() in h.lower():
                        target_col_idx = idx
                        break
            if target_col_idx is None and len(headers) >= 2:
                target_col_idx = len(headers) + 1

            grand_total = analysis_data.get("calculation_summary", {}).get("grand_total")
            if grand_total is None:
                calc_res = analysis_data.get("calculation_summary", {}).get("calculated_result")
                if isinstance(calc_res, (int, float)):
                    grand_total = calc_res

            if grand_total is not None and target_col_idx is not None:
                ws.cell(row=row_idx, column=1, value="TOTAL KESELURUHAN").font = font_bold
                col_letter = openpyxl.utils.get_column_letter(target_col_idx)
                total_cell = ws.cell(row=row_idx, column=target_col_idx)
                # Active native Excel SUM formula for the target column!
                total_cell.value = f"=SUM({col_letter}{start_data_row}:{col_letter}{row_idx-1})"
                total_cell.font = font_bold
                total_cell.number_format = "#,##0.00" if isinstance(grand_total, float) else "#,##0"
                total_cell.alignment = Alignment(horizontal="right", vertical="center")

                for c_idx in range(1, len(full_headers) + 1):
                    ws.cell(row=row_idx, column=c_idx).border = thin_border
                    ws.cell(row=row_idx, column=c_idx).fill = fill_highlight
                row_idx += 1


        # Auto-fit Column Widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

        # Save to Storage
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"{filename_prefix}_{timestamp_str}_{uuid.uuid4().hex[:6]}.xlsx"
        export_path = settings.EXPORT_DIR / export_filename
        wb.save(export_path)

        return export_path
