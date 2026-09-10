import os
import pytest
import pandas as pd
from pathlib import Path

from app.services.semantic_column_detector import UniversalSemanticColumnDetector
from app.services.profiler_service import ProfilerService
from app.services.grouping_subtotal_service import GroupingSubtotalService
from app.services.execution_engine import ExecutionEngine
from app.services.formula_planner import FormulaPlanner
from app.schemas.intent import StructuredAnalysisIntent, FormulaDecisionResult


@pytest.fixture
def sales_car_df():
    data = [
        {"ID_Transaksi": "TRX001", "Sales": "Andi", "Cabang": "Pekanbaru Panam", "Merek": "Wuling", "Model": "Almaz", "Tahun": 2024, "Tipe": "V", "Harga": 380000000, "Diskon": 10000000, "Harga_Netto": 370000000, "DP": 70000000},
        {"ID_Transaksi": "TRX002", "Sales": "Bagus", "Cabang": "Pekanbaru Sudirman", "Merek": "Wuling", "Model": "Almaz", "Tahun": 2024, "Tipe": "G", "Harga": 350000000, "Diskon": 5000000, "Harga_Netto": 345000000, "DP": 60000000},
        {"ID_Transaksi": "TRX003", "Sales": "Sari", "Cabang": "Pekanbaru Panam", "Merek": "Wuling", "Model": "Alvez", "Tahun": 2024, "Tipe": "EX", "Harga": 220000000, "Diskon": 5000000, "Harga_Netto": 215000000, "DP": 40000000},
        {"ID_Transaksi": "TRX004", "Sales": "Yoga", "Cabang": "Pekanbaru Harapan Raya", "Merek": "Wuling", "Model": "Alvez", "Tahun": 2024, "Tipe": "CE", "Harga": 200000000, "Diskon": 4000000, "Harga_Netto": 196000000, "DP": 35000000},
        {"ID_Transaksi": "TRX005", "Sales": "Rina", "Cabang": "Pekanbaru Panam", "Merek": "Toyota", "Model": "Avanza", "Tahun": 2024, "Tipe": "G", "Harga": 260000000, "Diskon": 8000000, "Harga_Netto": 252000000, "DP": 50000000},
    ]
    return pd.DataFrame(data)


@pytest.fixture
def lhp_ptpn_df():
    data = [
        {"Company Code": "PTPN4", "Plant": "PKS01", "Desc.": "PKS Sei Galuh", "Group Pemilik": "PABRIK SEI GALUH", "Kebun": "KB01", "Nama Kebun": "Kebun Sei Galuh", "TBS Olah HI": 1250.5, "TBS Terima HI": 1300.0, "CPO Produksi HI": 280.2},
        {"Company Code": "PTPN4", "Plant": "PKS01", "Desc.": "PKS Sei Galuh", "Group Pemilik": "PABRIK SEI GALUH", "Kebun": "KB02", "Nama Kebun": "Kebun Kota Garo", "TBS Olah HI": 980.0, "TBS Terima HI": 1010.5, "CPO Produksi HI": 215.6},
        {"Company Code": "PTPN4", "Plant": "PKS02", "Desc.": "PKS Tanah Putih", "Group Pemilik": "PABRIK TANAH PUTIH", "Kebun": "KB03", "Nama Kebun": "Kebun Tanah Putih", "TBS Olah HI": 1500.0, "TBS Terima HI": 1520.0, "CPO Produksi HI": 330.0},
        {"Company Code": "PTPN4", "Plant": "PKS02", "Desc.": "PKS Tanah Putih", "Group Pemilik": "PABRIK TANAH PUTIH", "Kebun": "KB04", "Nama Kebun": "Kebun Tanjung Medan", "TBS Olah HI": 1100.0, "TBS Terima HI": 1150.0, "CPO Produksi HI": 242.0},
    ]
    return pd.DataFrame(data)


def test_semantic_classification_universal(sales_car_df, lhp_ptpn_df):
    """Verifies that non-measures are never classified as MEASURE and valid metrics are correctly identified."""
    # 1. Car dataset
    car_schema = UniversalSemanticColumnDetector.detect_columns_schema(sales_car_df)
    assert car_schema["ID_Transaksi"] == "IDENTIFIER"
    assert car_schema["Tahun"] in ["IDENTIFIER", "DATE"] # 2024 attribute, never summed
    assert car_schema["Harga"] == "MEASURE"
    assert car_schema["DP"] == "MEASURE"
    assert car_schema["Model"] == "CATEGORY"

    car_measures = UniversalSemanticColumnDetector.get_measure_columns(sales_car_df)
    assert "Tahun" not in car_measures
    assert "ID_Transaksi" not in car_measures
    assert "Harga" in car_measures

    # 2. LHP PTPN dataset
    lhp_schema = UniversalSemanticColumnDetector.detect_columns_schema(lhp_ptpn_df)
    assert lhp_schema["Plant"] == "IDENTIFIER"
    assert lhp_schema["Company Code"] == "IDENTIFIER"
    assert lhp_schema["Group Pemilik"] == "CATEGORY"
    assert lhp_schema["TBS Olah HI"] == "MEASURE"
    assert lhp_schema["CPO Produksi HI"] == "MEASURE"

    lhp_measures = UniversalSemanticColumnDetector.get_measure_columns(lhp_ptpn_df)
    assert "Plant" not in lhp_measures
    assert "Company Code" not in lhp_measures
    assert "TBS Olah HI" in lhp_measures
    assert "CPO Produksi HI" in lhp_measures


def test_lhp_grouping_and_subtotal(lhp_ptpn_df):
    """Tests grouping by Pabrik / Group Pemilik on LHP data, strict TOTAL labels, and integrity metadata."""
    grp_col = GroupingSubtotalService.detect_grouping_column(lhp_ptpn_df, query="rekap total per pabrik")
    assert grp_col in ["Group Pemilik", "Desc."]

    measures = GroupingSubtotalService.detect_measure_columns(lhp_ptpn_df, query="total")
    assert "TBS Olah HI" in measures
    assert "CPO Produksi HI" in measures
    assert "Plant" not in measures

    rows, headers, meta = GroupingSubtotalService.build_inline_subtotals(
        lhp_ptpn_df,
        grouping_col=grp_col,
        measure_cols=measures,
        query="rekap total per pabrik"
    )

    # Subtotal rows check
    subtotal_rows = [r for r in rows if r.get("_is_subtotal")]
    # 2 groups + 1 grand total = 3 total rows
    assert len(subtotal_rows) == 3

    # Group subtotal labels must be strictly "TOTAL"
    assert subtotal_rows[0][grp_col] == "TOTAL"
    assert subtotal_rows[1][grp_col] == "TOTAL"

    # Grand total label must be strictly "TOTAL KESELURUHAN"
    assert subtotal_rows[2][grp_col] == "TOTAL KESELURUHAN"

    # Verify Data Integrity Metadata
    assert meta["sourceRowCount"] == 4
    assert meta["sourceColumnCount"] == len(lhp_ptpn_df.columns)
    assert meta["processedRowCount"] == 4 + 3 # 4 details + 3 totals
    assert meta["generatedTotalRows"] == 3
    assert meta["detectedColumns"] == list(lhp_ptpn_df.columns)


def test_sales_car_grouping_and_subtotal(sales_car_df):
    """Tests grouping by Model on car data, strict TOTAL labels, and integrity metadata."""
    grp_col = GroupingSubtotalService.detect_grouping_column(sales_car_df, query="total per Model")
    assert grp_col == "Model"

    measures = GroupingSubtotalService.detect_measure_columns(sales_car_df, query="total harga")
    assert measures == ["Harga"]

    rows, headers, meta = GroupingSubtotalService.build_inline_subtotals(
        sales_car_df,
        grouping_col=grp_col,
        measure_cols=measures,
        query="total harga per Model"
    )

    # Models: Almaz (2), Alvez (2), Avanza (1) -> 3 groups + 1 grand total = 4 total rows
    subtotal_rows = [r for r in rows if r.get("_is_subtotal")]
    assert len(subtotal_rows) == 4

    # Group subtotal labels
    for r in subtotal_rows[:-1]:
        assert r[grp_col] == "TOTAL"
    assert subtotal_rows[-1][grp_col] == "TOTAL KESELURUHAN"

    # Grand total value for Harga: 380 + 350 + 220 + 200 + 260 = 1,410,000,000
    assert subtotal_rows[-1]["Harga"] == 1410000000


def test_max_min_query_execution(lhp_ptpn_df, sales_car_df):
    """Tests 'data terbesar' query: sorts top row by measure descending and executes MAX safely."""
    # 1. On LHP dataset
    intent = StructuredAnalysisIntent(
        intent="CALCULATION",
        operation="MAX",
        target_field="TBS Olah HI",
        filters=[],
        group_by=[],
        confidence_score=0.95
    )
    decision = FormulaDecisionResult(
        formula_id="MAX",
        formula_name="MAX",
        category="AGGREGATION",
        reason="Menghitung nilai terbesar",
        syntax_pattern="=MAX(range)",
        generated_excel_formula="=MAX(TBS_Olah_HI)"
    )
    summary, headers, rows, chart = ExecutionEngine.execute(
        df=lhp_ptpn_df,
        intent=intent,
        decision=decision,
        user_query="data terbesar"
    )
    assert summary["calculated_result"] == 1500.0
    # Top row in table preview must be the record with max TBS Olah HI (1500.0, PKS Tanah Putih)
    assert rows[0]["TBS Olah HI"] == "1500.0" or rows[0]["TBS Olah HI"] == 1500.0
    assert "Tanah Putih" in rows[0]["Desc."]

    # Integrity metadata in summary
    assert summary["sourceRowCount"] == 4
    assert summary["sourceColumnCount"] == len(lhp_ptpn_df.columns)
    assert summary["processedRowCount"] == 4
    assert summary["generatedTotalRows"] == 0

    # 2. On Car dataset with auto measure detection
    car_intent = StructuredAnalysisIntent(
        intent="CALCULATION",
        operation="MAX",
        target_field=None,
        filters=[],
        group_by=[],
        confidence_score=0.90
    )
    car_decision = FormulaDecisionResult(
        formula_id="MAX",
        formula_name="MAX",
        category="AGGREGATION",
        reason="Menghitung nilai terbesar",
        syntax_pattern="=MAX(range)",
        generated_excel_formula="=MAX(Harga)"
    )
    car_summary, _, car_rows, _ = ExecutionEngine.execute(
        df=sales_car_df,
        intent=car_intent,
        decision=car_decision,
        user_query="cari data terbesar"
    )
    assert car_summary["calculated_result"] == 380000000
    assert car_rows[0]["Harga"] == "380000000" or car_rows[0]["Harga"] == 380000000


def test_header_detection_lhp_sap():
    """Tests header row detection on LHP SAP file with row 4 (0-indexed 3) title banner."""
    candidate_paths = [
        Path("../storage/uploads/450e1081f9fd473387efc9f8ec5d10bb_LHP SAP 31 Agustus 2026 rev 1.xlsx"),
        Path("storage/uploads/450e1081f9fd473387efc9f8ec5d10bb_LHP SAP 31 Agustus 2026 rev 1.xlsx")
    ]
    lhp_file = next((p for p in candidate_paths if p.exists()), None)
    if not lhp_file:
        pytest.skip("LHP SAP test file not present in local storage.")

    header_idx = ProfilerService.detect_header_row(str(lhp_file), sheet_name="PROD PKS REGIONAL III")
    assert header_idx == 3 # 0-indexed row 3 = row 4 in Excel

    df, _, _ = ProfilerService.load_dataset_file(str(lhp_file), sheet_name="PROD PKS REGIONAL III")
    assert "Company Code" in df.columns
    assert "NAMA PKS" in df.columns
    assert "Group Pemilik" in df.columns
    assert len(df.columns) >= 48
