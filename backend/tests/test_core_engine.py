import pytest
import pandas as pd
from app.services.profiler_service import ProfilerService, index_to_excel_col
from app.services.decision_engine import FormulaDecisionEngine
from app.services.formula_generator import FormulaGenerator
from app.services.execution_engine import ExecutionEngine
from app.services.ai_service import AIService
from app.models.dataset import DatasetColumn

def test_index_to_excel_col():
    assert index_to_excel_col(0) == "A"
    assert index_to_excel_col(1) == "B"
    assert index_to_excel_col(4) == "E"
    assert index_to_excel_col(25) == "Z"
    assert index_to_excel_col(26) == "AA"

def test_data_profiling():
    data = {
        "Tanggal": ["2024-02-04", "2024-02-05", "2024-02-06"],
        "Kode Barang": ["HP-003", "LE-001", "LE-002"],
        "Nama Merek": ["HP", "Lenovo", "Lenovo"],
        "Nama Barang": ["245 G10", "V14 G3", "Yoga 7i"],
        "Jumlah Keluar": [78, 89, 78]
    }
    df = pd.DataFrame(data)
    summary, cols, preview = ProfilerService.profile_dataframe(df)

    assert summary["total_rows"] == 3
    assert summary["total_columns"] == 5
    assert "Jumlah Keluar" in summary["numeric_columns"]
    assert "Tanggal" in summary["date_columns"]

def test_decision_engine_and_formula_generation():
    engine = FormulaDecisionEngine()
    
    mock_cols = [
        DatasetColumn(original_name="Tanggal", excel_column_letter="A", inferred_type="Date"),
        DatasetColumn(original_name="Kode Barang", excel_column_letter="B", inferred_type="Text"),
        DatasetColumn(original_name="Nama Merek", excel_column_letter="C", inferred_type="Categorical", sample_values=["Lenovo", "HP", "MacBook"]),
        DatasetColumn(original_name="Nama Barang", excel_column_letter="D", inferred_type="Text"),
        DatasetColumn(original_name="Jumlah Keluar", excel_column_letter="E", inferred_type="Numeric"),
    ]

    # Test Case 1: Total barang keluar merek Lenovo pada Februari 2024
    intent = AIService._heuristic_rule_parser(
        "Total barang keluar merek Lenovo pada Februari 2024",
        mock_cols
    )
    decision = engine.decide_formula(intent, mock_cols)
    assert decision.formula_id == "SUMIFS"
    
    formula_str = FormulaGenerator.generate_excel_formula(decision, intent, mock_cols)
    assert "=SUMIFS(E:E" in formula_str
    assert "Lenovo" in formula_str

    # Test Case 2: Total barang keluar merek Lenovo (1 filter)
    intent_sumif = AIService._heuristic_rule_parser(
        "Total barang keluar merek Lenovo",
        mock_cols
    )
    decision_sumif = engine.decide_formula(intent_sumif, mock_cols)
    assert decision_sumif.formula_id == "SUMIF"
    formula_sumif = FormulaGenerator.generate_excel_formula(decision_sumif, intent_sumif, mock_cols)
    assert "=SUMIF(C:C" in formula_sumif
    assert "Lenovo" in formula_sumif

    # Test Case 3: Total tanpa syarat
    intent_sum = AIService._heuristic_rule_parser("Berapa total barang keluar?", mock_cols)
    decision_sum = engine.decide_formula(intent_sum, mock_cols)
    assert decision_sum.formula_id == "SUM"
    formula_sum = FormulaGenerator.generate_excel_formula(decision_sum, intent_sum, mock_cols)
    assert formula_str != ""
    assert formula_sum == "=SUM(E:E)"
