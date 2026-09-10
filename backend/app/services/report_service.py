import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import pandas as pd
from app.core.config import settings
from app.services.formula_planner import FormulaPlanner

class ReportService:
    @classmethod
    def export_analysis_to_excel(
        cls,
        analysis_data: dict[str, Any],
        filename_prefix: str = "Laporan_PTPN"
    ) -> Path:
        """
        Creates a professional formatted Excel workbook with:
        1. Single Source of Truth: if table_rows is provided, export 100% faithful to displayed table!
        2. Tiered grouped report (if grouping active and raw_df provided without table_rows)
        3. Raw Dataset Sheet (preserving 100% source of truth)
        """
        table_rows = analysis_data.get("table_rows") or []
        table_headers = analysis_data.get("table_headers") or []

        # Single Source of Truth (Rules 1, 2, 8, 11, 13):
        # If web table rows are provided, export must 100% match the displayed table rows and columns!
        is_multi_task_summary = bool(
            analysis_data.get("tasks")
            and len(analysis_data.get("tasks")) > 1
            and not analysis_data.get("formula_plan")
        )

        if not is_multi_task_summary and table_rows and len(table_rows) > 0 and table_headers and len(table_headers) > 0:
            return cls._export_displayed_table(
                analysis_data=analysis_data,
                filename_prefix=filename_prefix,
                table_headers=table_headers,
                table_rows=table_rows,
                raw_df=analysis_data.get("raw_df")
            )

        # Check if full raw DataFrame or table rows are available
        df = analysis_data.get("raw_df")
        if df is None and table_rows:
            try:
                df = pd.DataFrame(table_rows)
            except Exception:
                df = None

        # Detect grouping dimension from formula_plan, group_by, or query
        formula_plan = analysis_data.get("formula_plan")
        grouping_col = None
        if formula_plan and formula_plan.get("grouping"):
            grouping_col = formula_plan["grouping"]
        elif analysis_data.get("group_by") and len(analysis_data["group_by"]) > 0:
            grouping_col = analysis_data["group_by"][0]
        elif df is not None and not df.empty:
            plan = FormulaPlanner.plan_formula(analysis_data.get("user_query", ""), sample_df=df)
            if plan.get("groups") and len(plan["groups"]) > 1:
                grouping_col = plan.get("grouping")
                formula_plan = plan

        # If grouping column is detected and exists in DataFrame, generate tiered report!
        if grouping_col and df is not None and not df.empty:
            # Resolve exact column name in df
            actual_group_col = None
            for c in df.columns:
                if c.lower() == str(grouping_col).lower() or c.lower().replace("_", " ") == str(grouping_col).lower():
                    actual_group_col = c
                    break
            if actual_group_col:
                return cls._export_tiered_report(
                    analysis_data=analysis_data,
                    filename_prefix=filename_prefix,
                    df=df,
                    grouping_col=actual_group_col,
                    formula_plan=formula_plan
                )

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

        # 2b. Multi-Task Execution Summary Table (If multiple tasks generated)
        tasks = analysis_data.get("tasks") or []
        if isinstance(tasks, list) and len(tasks) > 1:
            row_idx += 1
            ws.cell(row=row_idx, column=1, value="DAFTAR MULTI-TASK & FORMULA TERVERIFIKASI:").font = font_bold
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=7)
            row_idx += 1

            task_headers = ["No", "Task ID", "Tipe", "Operasi", "Target", "Formula Excel", "Hasil Eksekusi"]
            for c_idx, th in enumerate(task_headers, start=1):
                c = ws.cell(row=row_idx, column=c_idx, value=th)
                c.font = font_header
                c.fill = fill_header
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.border = thin_border
            row_idx += 1

            for t_num, t in enumerate(tasks, start=1):
                t_id = t.get("task_id", f"task_{t_num}")
                t_type = t.get("task_type") or ("retrieval" if t.get("operation") in ["FILTER", "RETRIEVAL"] else "calculation")
                t_op = t.get("operation", "-")
                t_tgt = t.get("target") or t.get("target_term") or "-"
                t_formula = t.get("formula") or t.get("generated_formula") or "-"
                t_res = t.get("result")
                if t_res is None and isinstance(t.get("execution"), dict):
                    t_res = t.get("execution", {}).get("result")

                vals = [t_num, t_id, t_type, t_op, t_tgt, t_formula, str(t_res) if t_res is not None else "-"]
                for c_idx, val in enumerate(vals, start=1):
                    c = ws.cell(row=row_idx, column=c_idx, value=val)
                    c.border = thin_border
                    if c_idx == 1:
                        c.alignment = Alignment(horizontal="center", vertical="center")
                    elif c_idx == 6:
                        c.font = font_formula
                        c.data_type = "s"
                        c.alignment = Alignment(horizontal="left", vertical="center")
                    elif c_idx == 7 and isinstance(t_res, (int, float)):
                        c.alignment = Alignment(horizontal="right", vertical="center")
                        c.number_format = "#,##0.00" if isinstance(t_res, float) else "#,##0"
                    else:
                        c.alignment = Alignment(horizontal="left", vertical="center")

                    if t_num % 2 == 1:
                        c.fill = fill_zebra
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

            # Summary Total Row: calculate totals for all targeted and amount/metric columns (Harga, DP, Netto, dll.)
            tasks = analysis_data.get("tasks") or []
            task_targets = set()
            for t in tasks:
                if isinstance(t, dict):
                    op = str(t.get("operation") or t.get("formula_name") or "").upper()
                    if any(s in op for s in ["SUM", "TOTAL", "FILTER", "RETRIEVAL"]):
                        tgt = t.get("target") or t.get("target_term")
                        if not tgt and isinstance(t.get("columns"), dict):
                            t_col = t.get("columns", {}).get("target")
                            if isinstance(t_col, dict):
                                tgt = t_col.get("matched_column")
                        if tgt:
                            task_targets.add(str(tgt).lower().replace("_", " ").strip())

            calc_tgt = analysis_data.get("calculation_summary", {}).get("target_field")
            if calc_tgt:
                task_targets.add(str(calc_tgt).lower().replace("_", " ").strip())

            summable_col_indices = set()
            for idx, h in enumerate(headers, start=2):
                h_clean = str(h).lower().replace("_", " ").strip()
                # Check if column matches any task target
                is_task_target = any(tt == h_clean or tt in h_clean or h_clean in tt for tt in task_targets)

                # Check if column is a financial/amount/metric column (Harga, DP, Netto, Diskon, Biaya, Cicilan, dll.)
                is_excluded = any(ex in h_clean for ex in ["id", "tahun", "year", "persen", "percent", "%", "tenor", "kode", "code", "tanggal", "date", "cc", "usia"])
                is_metric = any(inc in h_clean for inc in ["harga", "dp", "netto", "diskon", "nominal", "biaya", "cicilan", "asuransi", "total", "produksi", "tbs", "cpo", "jumlah", "nilai", "volume"])

                # Verify column actually contains numeric data in rows
                has_numeric_data = any(
                    isinstance(r.get(h), (int, float)) or 
                    (isinstance(r.get(h), str) and r.get(h).replace("-", "", 1).replace(".", "", 1).isdigit())
                    for r in rows[:15]
                )

                if (is_task_target or (is_metric and not is_excluded)) and has_numeric_data:
                    summable_col_indices.add(idx)

            if summable_col_indices:
                ws.cell(row=row_idx, column=1, value="TOTAL KESELURUHAN").font = font_bold
                ws.cell(row=row_idx, column=1).alignment = Alignment(horizontal="center", vertical="center")
                ws.cell(row=row_idx, column=1).border = thin_border
                ws.cell(row=row_idx, column=1).fill = fill_highlight

                for c_idx in range(2, len(full_headers) + 1):
                    h = headers[c_idx - 2]
                    cell = ws.cell(row=row_idx, column=c_idx)
                    cell.border = thin_border
                    cell.fill = fill_highlight
                    if c_idx in summable_col_indices:
                        col_letter = openpyxl.utils.get_column_letter(c_idx)
                        cell.value = f"=SUM({col_letter}{start_data_row}:{col_letter}{row_idx-1})"
                        cell.font = font_bold
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                        # Format as currency/decimal
                        sample_val = next((r.get(h) for r in rows if r.get(h) is not None), 0)
                        is_float = isinstance(sample_val, float) or ("." in str(sample_val) if isinstance(sample_val, str) else False)
                        cell.number_format = "#,##0.00" if is_float else "#,##0"
                    else:
                        cell.value = "-"
                        cell.font = font_regular
                        cell.alignment = Alignment(horizontal="center", vertical="center")

                ws.row_dimensions[row_idx].height = 24
                row_idx += 1

            # Check if any tasks requested AVERAGE
            avg_targets = set()
            for t in tasks:
                if isinstance(t, dict):
                    op = str(t.get("operation") or t.get("formula_name") or "").upper()
                    if "AVERAGE" in op:
                        tgt = t.get("target") or t.get("target_term")
                        if not tgt and isinstance(t.get("columns"), dict):
                            t_col = t.get("columns", {}).get("target")
                            if isinstance(t_col, dict):
                                tgt = t_col.get("matched_column")
                        if tgt:
                            avg_targets.add(str(tgt).lower().replace("_", " ").strip())

            avg_col_indices = set()
            if avg_targets:
                for idx, h in enumerate(headers, start=2):
                    h_clean = str(h).lower().replace("_", " ").strip()
                    if any(tt == h_clean or tt in h_clean or h_clean in tt for tt in avg_targets):
                        avg_col_indices.add(idx)

            if avg_col_indices:
                ws.cell(row=row_idx, column=1, value="RATA-RATA").font = font_bold
                ws.cell(row=row_idx, column=1).alignment = Alignment(horizontal="center", vertical="center")
                ws.cell(row=row_idx, column=1).border = thin_border
                ws.cell(row=row_idx, column=1).fill = fill_highlight

                for c_idx in range(2, len(full_headers) + 1):
                    cell = ws.cell(row=row_idx, column=c_idx)
                    cell.border = thin_border
                    cell.fill = fill_highlight
                    if c_idx in avg_col_indices:
                        col_letter = openpyxl.utils.get_column_letter(c_idx)
                        cell.value = f"=AVERAGE({col_letter}{start_data_row}:{col_letter}{row_idx-2})"
                        cell.font = font_bold
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                        cell.number_format = "#,##0.00"
                    else:
                        cell.value = "-"
                        cell.font = font_regular
                        cell.alignment = Alignment(horizontal="center", vertical="center")

                ws.row_dimensions[row_idx].height = 24
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

    @classmethod
    def _export_displayed_table(
        cls,
        analysis_data: dict[str, Any],
        filename_prefix: str,
        table_headers: List[str],
        table_rows: List[dict],
        raw_df: Optional[pd.DataFrame] = None
    ) -> Path:
        """
        Exports the exact processed/displayed data from the web data table (Single Source of Truth).
        Strictly preserves:
        1. Exact row order as shown on the web table (e.g. TRX0175, TRX0057, TRX0668, TRX0655, TRX0925...)
        2. Exact column order (No + table_headers)
        3. Formatted headers in PTPN / SAP Corporate colors (#A9D08E and #9BC2E6)
        4. Bottom TOTAL row with active =SUM(...) formulas in #C6EFCE
        5. AutoFilter on headers
        6. Optional Sheet 2: Data Mentah if raw_df is present
        """
        wb = openpyxl.Workbook()
        ws_rep = wb.active
        ws_rep.title = "Rekap Penjualan"

        # Corporate PTPN / SAP Color Palette
        c_ptpn_light_green = "A9D08E" # PTPN Corporate Green Header
        c_subtotal_green = "C6EFCE"   # Soft Mint Subtotal / Total Fill
        c_accent_blue = "9BC2E6"      # Soft Blue for Netto / DP / Output columns
        c_black = "000000"

        font_brand = Font(name="Arial", size=16, bold=True, color="1F4E79")
        font_title = Font(name="Arial", size=13, bold=True, color="000000")
        font_subtitle = Font(name="Arial", size=10, bold=True, color="333333")
        font_header = Font(name="Arial", size=9, bold=True, color="000000")
        font_detail = Font(name="Arial", size=9)
        font_bold = Font(name="Arial", size=9, bold=True)
        font_total = Font(name="Arial", size=10, bold=True, color="000000")

        fill_header_green = PatternFill(start_color=c_ptpn_light_green, end_color=c_ptpn_light_green, fill_type="solid")
        fill_header_blue = PatternFill(start_color=c_accent_blue, end_color=c_accent_blue, fill_type="solid")
        fill_total = PatternFill(start_color=c_subtotal_green, end_color=c_subtotal_green, fill_type="solid")

        thin_side = Side(style="thin", color=c_black)
        double_side = Side(style="double", color=c_black)

        thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
        total_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=double_side)

        num_fmt = '#,##0;(#,##0);"-"'

        # -------------------------------------------------------------
        # 1. Sheet 1: Header / Branding Section (Rows 1-3)
        # -------------------------------------------------------------
        full_headers = ["No"] + table_headers
        total_cols = len(full_headers)
        last_col_letter = openpyxl.utils.get_column_letter(total_cols)

        user_query = analysis_data.get("user_query", "Rekap Penjualan Mobil")
        is_car = any(w in user_query.lower() for w in ["mobil", "toyota", "avanza", "honda", "sales", "tipe", "panam", "cabang"]) or "mobil" in filename_prefix.lower()

        # Row 1: Left SAP Logo
        ws_rep["A1"] = "SAP"
        ws_rep["A1"].font = font_brand
        ws_rep["A1"].alignment = Alignment(horizontal="left", vertical="center")

        # Row 1-2: Right Aligned Title & Subtitle (PTPN Standard)
        title_text = "LAPORAN REKAPITULASI PENJUALAN MOBIL" if is_car else "LAPORAN DATA TRANSAKSI - SMARTEXCEL"
        subtitle_text = "DI PKS PT. PERKEBUNAN NUSANTARA - IV REGIONAL - III"

        mid_col = max(3, total_cols // 2)
        ws_rep.merge_cells(start_row=1, start_column=mid_col, end_row=1, end_column=total_cols)
        ws_rep.cell(row=1, column=mid_col, value=title_text).font = font_title
        ws_rep.cell(row=1, column=mid_col).alignment = Alignment(horizontal="right", vertical="center")

        ws_rep.merge_cells(start_row=2, start_column=mid_col, end_row=2, end_column=total_cols)
        ws_rep.cell(row=2, column=mid_col, value=subtitle_text).font = font_subtitle
        ws_rep.cell(row=2, column=mid_col).alignment = Alignment(horizontal="right", vertical="center")

        ws_rep.row_dimensions[1].height = 24
        ws_rep.row_dimensions[2].height = 18

        # Row 3: Date row
        ws_rep["A3"] = "TANGGAL :"
        ws_rep["A3"].font = font_bold
        ws_rep["A3"].alignment = Alignment(horizontal="left", vertical="center")

        ws_rep["B3"] = datetime.now().strftime("%d-%b-%y")
        ws_rep["B3"].font = font_bold
        ws_rep["B3"].alignment = Alignment(horizontal="left", vertical="center")
        ws_rep.row_dimensions[3].height = 20

        # -------------------------------------------------------------
        # 2. Sheet 1: Master Table Header (Row 4)
        # -------------------------------------------------------------
        header_row = 4
        for c_idx, h in enumerate(full_headers, start=1):
            cell = ws_rep.cell(row=header_row, column=c_idx, value=h.replace("_", " ").upper())
            cell.font = font_header
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            # Columns like Netto, DP, CPO styled with soft blue
            if any(k in h.lower() for k in ["netto", "dp", "cpo", "sisa"]):
                cell.fill = fill_header_blue
            else:
                cell.fill = fill_header_green

        ws_rep.row_dimensions[header_row].height = 30

        # Identify summable columns
        summable_col_indices = set()
        for c_idx, h in enumerate(table_headers, start=2):
            clean_h = str(h).lower()
            is_ex = any(ex in clean_h for ex in ["id", "tahun", "year", "persen", "percent", "%", "tenor", "kode", "code", "tanggal", "date", "cc", "usia"])
            is_met = any(inc in clean_h for inc in ["harga", "dp", "netto", "diskon", "nominal", "biaya", "cicilan", "total", "produksi", "tbs", "cpo", "jumlah", "nilai"])
            
            # Check if column has numbers
            has_numeric = any(
                isinstance(r.get(h), (int, float)) or
                (isinstance(r.get(h), str) and r.get(h).replace("-", "", 1).replace(".", "", 1).isdigit())
                for r in table_rows[:20]
            )
            if (is_met or not is_ex) and has_numeric and not is_ex:
                summable_col_indices.add(c_idx)

        # -------------------------------------------------------------
        # 3. Sheet 1: Data Rows (Row 5+) - 100% Faithful to table_rows
        # -------------------------------------------------------------
        start_data_row = 5
        curr_row = start_data_row

        has_subtotals = any(r.get("_is_subtotal") for r in table_rows) or any(
            any(str(v).strip().upper().startswith("TOTAL") for v in r.values() if v is not None)
            for r in table_rows
        )

        group_start_excel_row = None
        subtotal_excel_rows = []
        detail_counter = 1

        for r_idx, r in enumerate(table_rows, start=1):
            is_sub = bool(r.get("_is_subtotal")) or any(str(v).strip().upper() in ["TOTAL", "TOTAL KESELURUHAN"] for v in r.values() if v is not None)
            is_grand = bool(r.get("_is_grand_total")) or any(str(v).strip().upper() == "TOTAL KESELURUHAN" for v in r.values() if v is not None)

            if not is_sub:
                # Regular detail row
                if group_start_excel_row is None:
                    group_start_excel_row = curr_row

                # Col 1: Running No
                c_no = ws_rep.cell(row=curr_row, column=1, value=detail_counter)
                c_no.font = font_detail
                c_no.alignment = Alignment(horizontal="center", vertical="center")
                c_no.border = thin_border
                detail_counter += 1

                for c_idx, h in enumerate(table_headers, start=2):
                    val = r.get(h)
                    cell = ws_rep.cell(row=curr_row, column=c_idx)
                    cell.border = thin_border
                    cell.font = font_detail

                    num_val = None
                    if val is not None:
                        if isinstance(val, (int, float)):
                            num_val = val
                        elif isinstance(val, str) and val.replace("-", "", 1).replace(".", "", 1).isdigit() and not any(k in h.lower() for k in ["id", "tahun", "tenor", "no", "phone", "kode"]):
                            try:
                                num_val = float(val) if "." in val else int(val)
                            except Exception:
                                num_val = None

                    if num_val is not None:
                        cell.value = num_val
                        cell.number_format = num_fmt
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        if val is None or (isinstance(val, float) and pd.isna(val)):
                            cell.value = "-"
                            cell.alignment = Alignment(horizontal="center", vertical="center")
                        elif isinstance(val, (datetime, pd.Timestamp)):
                            cell.value = val.strftime("%Y-%m-%d")
                            cell.alignment = Alignment(horizontal="center", vertical="center")
                        else:
                            val_str = str(val).strip()
                            # If date string like 2024-07-08 00:00:00, clean to 2024-07-08
                            if len(val_str) == 19 and val_str[10] == " " and val_str[4] == "-" and val_str[7] == "-":
                                val_str = val_str[:10]
                            cell.value = val_str
                            cell.alignment = Alignment(
                                horizontal="center" if any(k in h.lower() for k in ["id", "tanggal", "tahun", "tipe", "kode"]) else "left",
                                vertical="center"
                            )

                ws_rep.row_dimensions[curr_row].height = 19
                curr_row += 1

            elif is_sub and not is_grand:
                # Group Subtotal row: 'TOTAL'
                group_end_excel_row = curr_row - 1
                subtotal_excel_rows.append(curr_row)

                c_no = ws_rep.cell(row=curr_row, column=1, value="")
                c_no.fill = fill_total
                c_no.border = total_border

                for c_idx, h in enumerate(table_headers, start=2):
                    cell = ws_rep.cell(row=curr_row, column=c_idx)
                    cell.fill = fill_total
                    cell.border = total_border
                    cell.font = font_total

                    if c_idx in summable_col_indices:
                        col_let = openpyxl.utils.get_column_letter(c_idx)
                        if group_start_excel_row is not None and group_end_excel_row >= group_start_excel_row:
                            cell.value = f"=SUM({col_let}{group_start_excel_row}:{col_let}{group_end_excel_row})"
                        else:
                            val = r.get(h)
                            cell.value = val if isinstance(val, (int, float)) else ""
                        cell.number_format = num_fmt
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        val = r.get(h)
                        val_str = str(val or "")
                        cell.value = val_str
                        cell.alignment = Alignment(
                            horizontal="center" if val_str.upper() == "TOTAL" else "left",
                            vertical="center"
                        )

                ws_rep.row_dimensions[curr_row].height = 22
                curr_row += 1
                group_start_excel_row = None  # Reset for next group

            else:
                # Grand Total row: 'TOTAL KESELURUHAN'
                c_no = ws_rep.cell(row=curr_row, column=1, value="")
                c_no.fill = fill_total
                c_no.border = total_border

                for c_idx, h in enumerate(table_headers, start=2):
                    cell = ws_rep.cell(row=curr_row, column=c_idx)
                    cell.fill = fill_total
                    cell.border = total_border
                    cell.font = font_total

                    if c_idx in summable_col_indices:
                        col_let = openpyxl.utils.get_column_letter(c_idx)
                        if subtotal_excel_rows:
                            sub_cells = [f"{col_let}{sr}" for sr in subtotal_excel_rows]
                            cell.value = f"=SUM({','.join(sub_cells)})"
                        else:
                            cell.value = f"=SUM({col_let}{start_data_row}:{col_let}{curr_row - 1})"
                        cell.number_format = num_fmt
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        val = r.get(h)
                        val_str = str(val or "")
                        cell.value = val_str
                        cell.alignment = Alignment(
                            horizontal="center" if "TOTAL" in val_str.upper() else "left",
                            vertical="center"
                        )

                ws_rep.row_dimensions[curr_row].height = 24
                curr_row += 1

        # -------------------------------------------------------------
        # 4. Sheet 1: Bottom TOTAL Row with Active Formula =SUM(...) (if not already included inline)
        # -------------------------------------------------------------
        if not has_subtotals:
            last_data_row = curr_row - 1
            total_row = curr_row
            c_tot = ws_rep.cell(row=total_row, column=1, value="TOTAL")
            c_tot.font = font_total
            c_tot.alignment = Alignment(horizontal="center", vertical="center")
            c_tot.fill = fill_total
            c_tot.border = total_border

            for c_idx in range(2, total_cols + 1):
                cell = ws_rep.cell(row=total_row, column=c_idx)
                cell.fill = fill_total
                cell.border = total_border
                if c_idx in summable_col_indices and last_data_row >= start_data_row:
                    col_let = openpyxl.utils.get_column_letter(c_idx)
                    cell.value = f"=SUM({col_let}{start_data_row}:{col_let}{last_data_row})"
                    cell.font = font_total
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    cell.number_format = num_fmt
                else:
                    cell.value = ""

            ws_rep.row_dimensions[total_row].height = 24
            curr_row += 1

        final_table_row = curr_row - 1

        # AutoFilter on headers through final table row
        ws_rep.auto_filter.ref = f"A{header_row}:{last_col_letter}{final_table_row}"

        # Auto-fit columns
        for col in ws_rep.columns:
            max_len = 0
            for cell in col[:60]:
                v = str(cell.value or "")
                if not v.startswith("="):
                    max_len = max(max_len, len(v))
            col_let = openpyxl.utils.get_column_letter(col[0].column)
            ws_rep.column_dimensions[col_let].width = max(max_len + 3, 11)
        ws_rep.column_dimensions["A"].width = 8

        # -------------------------------------------------------------
        # 5. Optional Sheet 2: Data Mentah (if raw_df is present)
        # -------------------------------------------------------------
        if raw_df is not None and not raw_df.empty:
            ws_raw = wb.create_sheet("Data Mentah")
            raw_headers = list(raw_df.columns)
            for c_idx, h in enumerate(raw_headers, start=1):
                c = ws_raw.cell(row=1, column=c_idx, value=str(h))
                c.font = font_header
                c.fill = fill_header_green
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.border = thin_border
            ws_raw.row_dimensions[1].height = 25

            for r_idx, (_, r_data) in enumerate(raw_df.iterrows(), start=2):
                for c_idx, h in enumerate(raw_headers, start=1):
                    val = r_data[h]
                    cell = ws_raw.cell(row=r_idx, column=c_idx)
                    cell.border = thin_border

                    if pd.isna(val) or val is None:
                        cell.value = "-"
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    elif isinstance(val, (int, float)):
                        cell.value = val
                        cell.number_format = num_fmt
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    elif isinstance(val, (datetime, pd.Timestamp)):
                        cell.value = val.strftime("%Y-%m-%d")
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    else:
                        val_str = str(val).strip()
                        if val_str.replace("-", "", 1).replace(".", "", 1).isdigit() and not any(k in str(h).lower() for k in ["id", "kode", "tahun", "no", "phone"]):
                            num_v = float(val_str) if "." in val_str else int(val_str)
                            cell.value = num_v
                            cell.number_format = num_fmt
                            cell.alignment = Alignment(horizontal="right", vertical="center")
                        else:
                            cell.value = val_str
                            cell.alignment = Alignment(horizontal="left", vertical="center")

            for col in ws_raw.columns:
                max_len = max(len(str(c.value or "")) for c in col[:50])
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws_raw.column_dimensions[col_letter].width = max(max_len + 4, 12)

        # -------------------------------------------------------------
        # 6. Save Workbook
        # -------------------------------------------------------------
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"{filename_prefix}_{timestamp_str}_{uuid.uuid4().hex[:6]}.xlsx"
        export_path = settings.EXPORT_DIR / export_filename
        wb.save(export_path)

        return export_path

    @classmethod
    def _export_tiered_report(
        cls,
        analysis_data: dict[str, Any],
        filename_prefix: str,
        df: pd.DataFrame,
        grouping_col: str,
        formula_plan: Optional[dict[str, Any]] = None
    ) -> Path:
        """
        Generates an authentic corporate PTPN / SAP standard tiered Excel report:
        - Sheet 1: 'Rekap Penjualan'
          - Row 1: Left branding ('SAP' / 'SMARTEXCEL'), Right header title & subtitle
          - Row 3: 'TANGGAL : [date]'
          - Row 4: Master Table Headers with vibrant PTPN green (#A9D08E) & soft blue (#9BC2E6),
                   with AutoFilter enabled
          - Hierarchical tabular rows: Group column cell is vertically merged across detail rows
          - Subtotal row for each group: 'TOTAL [MODEL]' highlighted in soft mint (#C6EFCE)
            with active Excel formula =SUM(start:end)
          - Final row: 'TOTAL KESELURUHAN' with active Excel formula =SUM(subtotals) and double bottom border
          - Continuous layout without disruptive repeating headers or empty gaps
        - Sheet 2: 'Data Mentah'
          - Complete 1,000 raw rows as immutable source of truth
        """
        wb = openpyxl.Workbook()
        ws_rep = wb.active
        ws_rep.title = "Rekap Penjualan"
        ws_raw = wb.create_sheet("Data Mentah")

        # Corporate PTPN / SAP Color Palette
        c_ptpn_light_green = "A9D08E" # PTPN Corporate Green Header
        c_subtotal_green = "C6EFCE"   # Soft Mint Subtotal Fill (Excel standard)
        c_accent_blue = "9BC2E6"      # Soft Blue for Netto / DP / Output columns
        c_black = "000000"

        font_brand = Font(name="Arial", size=16, bold=True, color="1F4E79")
        font_title = Font(name="Arial", size=13, bold=True, color="000000")
        font_subtitle = Font(name="Arial", size=10, bold=True, color="333333")
        font_header = Font(name="Arial", size=9, bold=True, color="000000")
        font_detail = Font(name="Arial", size=9)
        font_bold = Font(name="Arial", size=9, bold=True)
        font_group_val = Font(name="Arial", size=10, bold=True)
        font_grand_total = Font(name="Arial", size=10, bold=True, color="000000")

        fill_header_green = PatternFill(start_color=c_ptpn_light_green, end_color=c_ptpn_light_green, fill_type="solid")
        fill_header_blue = PatternFill(start_color=c_accent_blue, end_color=c_accent_blue, fill_type="solid")
        fill_subtotal = PatternFill(start_color=c_subtotal_green, end_color=c_subtotal_green, fill_type="solid")
        fill_grand_total = PatternFill(start_color=c_ptpn_light_green, end_color=c_ptpn_light_green, fill_type="solid")

        thin_side = Side(style="thin", color=c_black)
        double_side = Side(style="double", color=c_black)

        thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
        subtotal_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
        grand_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=double_side)

        num_fmt = '#,##0;(#,##0);"-"'

        # -------------------------------------------------------------
        # 1. Fill Sheet 2: Data Mentah (1,000 Raw Rows Source of Truth)
        # -------------------------------------------------------------
        raw_headers = list(df.columns)
        for c_idx, h in enumerate(raw_headers, start=1):
            c = ws_raw.cell(row=1, column=c_idx, value=str(h))
            c.font = font_header
            c.fill = fill_header_green
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = thin_border
        ws_raw.row_dimensions[1].height = 25

        for r_idx, (_, r_data) in enumerate(df.iterrows(), start=2):
            for c_idx, h in enumerate(raw_headers, start=1):
                val = r_data[h]
                cell = ws_raw.cell(row=r_idx, column=c_idx)
                cell.border = thin_border

                if pd.isna(val) or val is None:
                    cell.value = "-"
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif isinstance(val, (int, float)):
                    cell.value = val
                    cell.number_format = num_fmt
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif isinstance(val, (datetime, pd.Timestamp)):
                    cell.value = val.strftime("%Y-%m-%d")
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    val_str = str(val).strip()
                    if val_str.replace("-", "", 1).replace(".", "", 1).isdigit() and not any(k in h.lower() for k in ["id", "kode", "tahun", "no", "phone"]):
                        num_v = float(val_str) if "." in val_str else int(val_str)
                        cell.value = num_v
                        cell.number_format = num_fmt
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        cell.value = val_str
                        cell.alignment = Alignment(horizontal="left", vertical="center")

        for col in ws_raw.columns:
            max_len = max(len(str(c.value or "")) for c in col[:50])
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws_raw.column_dimensions[col_letter].width = max(max_len + 4, 12)

        # -------------------------------------------------------------
        # 2. Setup Report Table Structure
        # -------------------------------------------------------------
        summable_cols = [c for c in df.columns if FormulaPlanner.is_summable_column(c, df[c])]
        desc_cols = [
            c for c in df.columns 
            if c not in summable_cols and str(c).lower() not in ["id", "id_transaksi", "id_mobil", "id_sales", "no"]
        ]
        
        # Assemble columns: Grouping column + No + Descriptor columns + Summable columns
        rep_desc = [c for c in desc_cols if c != grouping_col][:6]
        # Include ID_Transaksi if present in dataset
        if "ID_Transaksi" in df.columns and "ID_Transaksi" not in rep_desc:
            rep_desc = ["ID_Transaksi"] + [c for c in rep_desc if c != "ID_Transaksi"][:5]

        report_columns = [grouping_col, "No"] + rep_desc + summable_cols
        total_cols = len(report_columns)
        last_col_letter = openpyxl.utils.get_column_letter(total_cols)
        metric_start_col = total_cols - len(summable_cols) + 1

        # -------------------------------------------------------------
        # 3. Sheet 1: Header / Branding Section (Rows 1-3)
        # -------------------------------------------------------------
        user_query = analysis_data.get("user_query", "Rekap Penjualan Mobil")
        is_car = any(w in user_query.lower() for w in ["mobil", "toyota", "avanza", "honda", "sales", "tipe"]) or "mobil" in filename_prefix.lower()

        # Row 1: Left SAP / SMARTEXCEL Logo
        ws_rep["A1"] = "SAP"
        ws_rep["A1"].font = font_brand
        ws_rep["A1"].alignment = Alignment(horizontal="left", vertical="center")

        # Row 1-2: Right Aligned Title & Subtitle (PTPN Standard)
        title_text = "LAPORAN REKAPITULASI PENJUALAN MOBIL" if is_car else "LAPORAN HARIAN PENGOLAHAN TBS"
        subtitle_text = "DI PKS PT. PERKEBUNAN NUSANTARA - IV REGIONAL - III"

        mid_col = max(3, total_cols // 2)
        ws_rep.merge_cells(start_row=1, start_column=mid_col, end_row=1, end_column=total_cols)
        ws_rep.cell(row=1, column=mid_col, value=title_text).font = font_title
        ws_rep.cell(row=1, column=mid_col).alignment = Alignment(horizontal="right", vertical="center")

        ws_rep.merge_cells(start_row=2, start_column=mid_col, end_row=2, end_column=total_cols)
        ws_rep.cell(row=2, column=mid_col, value=subtitle_text).font = font_subtitle
        ws_rep.cell(row=2, column=mid_col).alignment = Alignment(horizontal="right", vertical="center")

        ws_rep.row_dimensions[1].height = 24
        ws_rep.row_dimensions[2].height = 18

        # Row 3: Date row
        ws_rep["A3"] = "TANGGAL :"
        ws_rep["A3"].font = font_bold
        ws_rep["A3"].alignment = Alignment(horizontal="left", vertical="center")

        ws_rep["B3"] = datetime.now().strftime("%d-%b-%y")
        ws_rep["B3"].font = font_bold
        ws_rep["B3"].alignment = Alignment(horizontal="left", vertical="center")
        ws_rep.row_dimensions[3].height = 20

        # -------------------------------------------------------------
        # 4. Sheet 1: Master Table Header (Row 4)
        # -------------------------------------------------------------
        header_row = 4
        for c_idx, col_name in enumerate(report_columns, start=1):
            cell = ws_rep.cell(row=header_row, column=c_idx, value=col_name.replace("_", " ").upper())
            cell.font = font_header
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            # Columns like Netto, DP, CPO styled with soft blue
            if any(k in col_name.lower() for k in ["netto", "dp", "cpo", "sisa"]):
                cell.fill = fill_header_blue
            else:
                cell.fill = fill_header_green

        ws_rep.row_dimensions[header_row].height = 30

        # -------------------------------------------------------------
        # 5. Sheet 1: Data Rows with Hierarchical Merged Group Cells
        # -------------------------------------------------------------
        curr_row = 5
        subtotal_rows = []
        unique_groups = sorted([str(x).strip() for x in df[grouping_col].dropna().unique() if str(x).strip()])

        for group_val in unique_groups:
            group_df = df[df[grouping_col].astype(str).str.strip() == group_val]
            if group_df.empty:
                continue

            start_group_row = curr_row
            end_group_row = curr_row + len(group_df) - 1

            # Render detail rows
            for sub_no, (_, row_item) in enumerate(group_df.iterrows(), start=1):
                # Col 1: Group Column (value set on every row; merged vertically afterwards)
                ws_rep.cell(row=curr_row, column=1, value=group_val.upper())

                # Col 2: Running No
                cell_no = ws_rep.cell(row=curr_row, column=2, value=sub_no)
                cell_no.font = font_detail
                cell_no.alignment = Alignment(horizontal="center", vertical="center")
                cell_no.border = thin_border

                # Other columns
                for c_idx, h in enumerate(report_columns[2:], start=3):
                    val = row_item.get(h)
                    cell = ws_rep.cell(row=curr_row, column=c_idx)
                    cell.border = thin_border
                    cell.font = font_detail

                    if h in summable_cols:
                        num_val = 0
                        try:
                            if isinstance(val, (int, float)):
                                num_val = val
                            elif isinstance(val, str) and val.replace("-", "", 1).replace(".", "", 1).isdigit():
                                num_val = float(val) if "." in val else int(val)
                        except Exception:
                            num_val = 0
                        cell.value = num_val
                        cell.number_format = num_fmt
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        if isinstance(val, (datetime, pd.Timestamp)):
                            cell.value = val.strftime("%Y-%m-%d")
                            cell.alignment = Alignment(horizontal="center", vertical="center")
                        elif val is None or pd.isna(val):
                            cell.value = "-"
                            cell.alignment = Alignment(horizontal="center", vertical="center")
                        else:
                            cell.value = str(val).strip()
                            cell.alignment = Alignment(horizontal="left", vertical="center")

                ws_rep.row_dimensions[curr_row].height = 19
                curr_row += 1

            # Vertically merge Column 1 for this group
            if end_group_row >= start_group_row:
                ws_rep.merge_cells(start_row=start_group_row, start_column=1, end_row=end_group_row, end_column=1)
                top_group_cell = ws_rep.cell(row=start_group_row, column=1)
                top_group_cell.font = font_group_val
                top_group_cell.alignment = Alignment(horizontal="center", vertical="center")
                for r in range(start_group_row, end_group_row + 1):
                    ws_rep.cell(row=r, column=1).border = thin_border

            # ---------------------------------------------------------
            # Subtotal Row: 'TOTAL [MODEL]' in Soft Mint Green (#C6EFCE)
            # ---------------------------------------------------------
            sub_row_idx = curr_row
            subtotal_rows.append(sub_row_idx)

            # Left descriptor columns: Col 1 has 'TOTAL [MODEL]', cols 2 to metric_start_col-1 are blank
            for c in range(1, metric_start_col):
                c_cell = ws_rep.cell(row=sub_row_idx, column=c)
                c_cell.fill = fill_subtotal
                c_cell.border = subtotal_border
                if c == 1:
                    c_cell.value = f"TOTAL {group_val.upper()}"
                    c_cell.font = font_bold
                    c_cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    c_cell.value = ""

            # Metric Columns with Active Formula =SUM(...)
            for c_idx in range(metric_start_col, total_cols + 1):
                col_let = openpyxl.utils.get_column_letter(c_idx)
                c_cell = ws_rep.cell(row=sub_row_idx, column=c_idx)
                c_cell.value = f"=SUM({col_let}{start_group_row}:{col_let}{end_group_row})"
                c_cell.font = font_bold
                c_cell.alignment = Alignment(horizontal="right", vertical="center")
                c_cell.number_format = num_fmt
                c_cell.fill = fill_subtotal
                c_cell.border = subtotal_border

            ws_rep.row_dimensions[sub_row_idx].height = 22
            curr_row += 1

        # -------------------------------------------------------------
        # 6. Final Grand Total Row: 'TOTAL KESELURUHAN'
        # -------------------------------------------------------------
        grand_row_idx = curr_row
        for c in range(1, metric_start_col):
            c_cell = ws_rep.cell(row=grand_row_idx, column=c)
            c_cell.fill = fill_grand_total
            c_cell.border = grand_border
            if c == 1:
                c_cell.value = "TOTAL KESELURUHAN"
                c_cell.font = font_grand_total
                c_cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                c_cell.value = ""

        for c_idx in range(metric_start_col, total_cols + 1):
            col_let = openpyxl.utils.get_column_letter(c_idx)
            c_cell = ws_rep.cell(row=grand_row_idx, column=c_idx)
            if subtotal_rows:
                sub_cells = ", ".join([f"{col_let}{r}" for r in subtotal_rows])
                c_cell.value = f"=SUM({sub_cells})"
            else:
                c_cell.value = "-"
            c_cell.font = font_grand_total
            c_cell.alignment = Alignment(horizontal="right", vertical="center")
            c_cell.number_format = num_fmt
            c_cell.fill = fill_grand_total
            c_cell.border = grand_border

        ws_rep.row_dimensions[grand_row_idx].height = 26

        # AutoFilter on headers
        ws_rep.auto_filter.ref = f"A{header_row}:{last_col_letter}{grand_row_idx}"

        # -------------------------------------------------------------
        # 7. Auto-fit column widths on ws_rep
        # -------------------------------------------------------------
        for col in ws_rep.columns:
            max_len = 0
            for cell in col:
                val_str = str(cell.value or "")
                if not val_str.startswith("="):
                    max_len = max(max_len, len(val_str))
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws_rep.column_dimensions[col_letter].width = max(max_len + 3, 12)
        ws_rep.column_dimensions["A"].width = 16

        # -------------------------------------------------------------
        # 8. Save Workbook to storage/exports
        # -------------------------------------------------------------
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"{filename_prefix}_{timestamp_str}_{uuid.uuid4().hex[:6]}.xlsx"
        export_path = settings.EXPORT_DIR / export_filename
        wb.save(export_path)

        return export_path
