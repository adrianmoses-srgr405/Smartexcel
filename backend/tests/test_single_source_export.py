import pytest
from pathlib import Path
import pandas as pd
import openpyxl
from app.services.report_service import ReportService

DATASET_PATH = Path("../storage/uploads/98a687aad2384547923c8ed474cd637f_Data_Dummy_Penjualan_Mobil_Pekanbaru_1000 (1).xlsx")

def test_single_source_of_truth_panam_export():
    """
    Test Rule 1-13:
    When web table renders filtered data (e.g. Pekanbaru Panam 215 rows),
    export MUST be 100% faithful to table_rows:
    - Row 1: TRX0175
    - Row 2: TRX0057
    - Row 3: TRX0668
    - Row 4: TRX0655
    - Row 5: TRX0925
    - No other branches present
    - Total data rows == 215
    - Headers match table_headers
    - Total row has active =SUM formula
    """
    assert DATASET_PATH.exists()
    raw_df = pd.read_excel(DATASET_PATH, sheet_name="Data_Penjualan")
    assert len(raw_df) == 1000

    # Simulate web table data: filtered for Pekanbaru Panam and sorted by Model then Sales as in the screenshot
    panam_df = raw_df[raw_df["Cabang"] == "Pekanbaru Panam"].sort_values(by=["Model"]).copy()
    for col in panam_df.columns:
        panam_df[col] = panam_df[col].apply(lambda v: None if pd.isna(v) else str(v))
    
    table_rows = panam_df.to_dict(orient="records")
    table_headers = list(raw_df.columns)

    # Verify first 5 IDs in table_rows match the user screenshot
    expected_ids = ["TRX0175", "TRX0057", "TRX0668", "TRX0655", "TRX0925"]
    actual_top_ids = [r["ID_Transaksi"] for r in table_rows[:5]]
    assert actual_top_ids == expected_ids, f"Expected {expected_ids}, got {actual_top_ids}"

    # Build export payload as sent by frontend
    export_payload = {
        "user_query": "Buat rekap data cabang pekanbaru panam dan total kan",
        "formula_id": "FILTER",
        "formula_name": "FILTER",
        "table_headers": table_headers,
        "table_rows": table_rows,
        "raw_df": raw_df # Even if raw_df is passed, table_rows MUST take precedence as single source of truth!
    }

    export_path = ReportService.export_analysis_to_excel(export_payload, filename_prefix="Test_Export_Panam")
    assert export_path.exists()

    wb = openpyxl.load_workbook(export_path, data_only=False)
    assert "Rekap Penjualan" in wb.sheetnames
    ws = wb["Rekap Penjualan"]

    # Header row is row 4
    # Columns: No, ID_Transaksi, Tanggal, Sales, Cabang, Merek, Model, Tahun, Tipe, ...
    header_vals = [ws.cell(row=4, column=c).value for c in range(1, len(table_headers) + 2)]
    assert header_vals[0] == "NO"
    assert header_vals[1] == "ID TRANSAKSI"

    # Data rows: rows 5 to 219 (215 rows)
    data_ids = [ws.cell(row=r, column=2).value for r in range(5, 5 + len(table_rows))]
    assert len(data_ids) == 215

    # Verify first 5 rows in exported Excel
    assert data_ids[:5] == expected_ids, f"Expected {expected_ids}, got {data_ids[:5]}"

    # Verify NO other branches like Harapan Raya or Arengka are present
    cabang_col_idx = header_vals.index("CABANG") + 1
    for r in range(5, 5 + len(table_rows)):
        cabang_val = ws.cell(row=r, column=cabang_col_idx).value
        assert cabang_val == "Pekanbaru Panam", f"Row {r} has unexpected cabang {cabang_val}"

    # Total row is row 220
    total_row = 5 + len(table_rows)
    assert ws.cell(row=total_row, column=1).value == "TOTAL"
    
    # Check that financial column (e.g. Harga, Netto) has =SUM(start:end) formula
    # Let's find column for HARGA NETTO
    netto_col_idx = None
    for c_idx, h in enumerate(header_vals, start=1):
        if "NETTO" in str(h):
            netto_col_idx = c_idx
            break
    
    if netto_col_idx:
        netto_formula = ws.cell(row=total_row, column=netto_col_idx).value
        col_let = openpyxl.utils.get_column_letter(netto_col_idx)
        assert netto_formula == f"=SUM({col_let}5:{col_let}219)", f"Expected =SUM({col_let}5:{col_let}219), got {netto_formula}"
