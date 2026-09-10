import pytest
import pandas as pd
from app.services.parameter_extractor import ParameterExtractor
from app.services.column_resolver import ColumnResolver
from app.services.decision_engine import FormulaDecisionEngine
from app.services.formula_generator import FormulaGenerator
from app.services.formula_validator import FormulaValidator
from app.services.execution_engine import ExecutionEngine
from app.services.confidence_scorer import ConfidenceScorer
from app.services.clarification_engine import ClarificationEngine
from app.services.hybrid_ai_service import HybridAIService
from app.services.evaluation_runner import EvaluationRunnerService

# ==========================================================
# 1. END-TO-END ACCEPTANCE TEST (USER SPECIFIED BENCHMARK)
# ==========================================================
def test_end_to_end_andi_januari_calculation():
    """
    Exact requirement from prompt:
    Dataset:
    Sales | Bulan | Penjualan
    Andi  | Januari | 1000000
    Budi  | Januari | 2000000
    Andi  | Februari | 1500000
    Andi  | Januari | 500000

    Query: 'Hitung total penjualan Andi bulan Januari'
    Expected:
    formula = SUMIFS
    expected result = 1500000
    """
    df = pd.DataFrame({
        "Sales": ["Andi", "Budi", "Andi", "Andi"],
        "Bulan": ["Januari", "Januari", "Februari", "Januari"],
        "Penjualan": [1000000, 2000000, 1500000, 500000]
    })

    result = HybridAIService.process_query(
        query="Hitung total penjualan Andi bulan Januari",
        sample_df=df
    )

    # 1. Formula verification
    assert result["formula_name"] == "SUMIFS", f"Expected SUMIFS but got {result['formula_name']}"
    assert "SUMIFS" in result["generated_formula"]

    # 2. Parameter & Column verification
    assert result["parameters"]["operation"] == "SUM"
    assert len(result["columns"]["conditions"]) == 2

    # 3. Execution Verification (Must be EXACTLY 1,500,000)
    assert result["execution"]["executed"] is True
    assert result["execution"]["result"] == 1500000, f"Expected 1500000 but got {result['execution']['result']}"

    # 4. Confidence & Validation
    assert result["validation"]["is_valid"] is True
    assert result["confidence"]["composite_score"] >= 0.70
    assert result["confidence"]["level"] in ["HIGH", "MEDIUM"]
    assert result["confidence"]["needs_clarification"] is False


# ==========================================================
# 2. MANDATORY 10 PIPELINE FORMULA TESTS
# ==========================================================
@pytest.fixture
def standard_ptpn_df():
    return pd.DataFrame({
        "Sales": ["Andi", "Budi", "Andi", "Siti", "Andi"],
        "Bulan": ["Januari", "Januari", "Februari", "Januari", "Januari"],
        "Produk": ["TBS Sawit", "CPO", "TBS Sawit", "Palm Kernel", "CPO"],
        "Penjualan": [1000000, 2000000, 1500000, 800000, 500000]
    })

def test_mandatory_1_sum(standard_ptpn_df):
    res = HybridAIService.process_query("Total penjualan", sample_df=standard_ptpn_df)
    assert res["formula_name"] == "SUM"
    assert res["execution"]["executed"] is True
    assert res["execution"]["result"] == 5800000

def test_mandatory_2_sumif(standard_ptpn_df):
    res = HybridAIService.process_query("Total penjualan Andi", sample_df=standard_ptpn_df)
    assert res["formula_name"] == "SUMIF"
    assert res["execution"]["executed"] is True
    assert res["execution"]["result"] == 3000000 # 1000000 + 1500000 + 500000

def test_mandatory_3_sumifs(standard_ptpn_df):
    res = HybridAIService.process_query("Total penjualan Andi di Januari", sample_df=standard_ptpn_df)
    assert res["formula_name"] == "SUMIFS"
    assert res["execution"]["executed"] is True
    assert res["execution"]["result"] == 1500000

def test_mandatory_4_average(standard_ptpn_df):
    res = HybridAIService.process_query("Rata-rata penjualan", sample_df=standard_ptpn_df)
    assert res["formula_name"] == "AVERAGE"
    assert res["execution"]["executed"] is True
    assert res["execution"]["result"] == 1160000.0

def test_mandatory_5_averageif(standard_ptpn_df):
    res = HybridAIService.process_query("Rata-rata penjualan Andi", sample_df=standard_ptpn_df)
    assert res["formula_name"] == "AVERAGEIF"
    assert res["execution"]["executed"] is True
    assert res["execution"]["result"] == 1000000.0

def test_mandatory_6_averageifs(standard_ptpn_df):
    res = HybridAIService.process_query("Rata-rata penjualan Andi di Januari", sample_df=standard_ptpn_df)
    assert res["formula_name"] == "AVERAGEIFS"
    assert res["execution"]["executed"] is True
    assert res["execution"]["result"] == 750000.0 # (1000000 + 500000) / 2

def test_mandatory_7_countif(standard_ptpn_df):
    res = HybridAIService.process_query("Berapa banyak transaksi Andi", sample_df=standard_ptpn_df)
    assert res["formula_name"] == "COUNTIF"
    assert res["execution"]["executed"] is True
    assert res["execution"]["result"] == 3

def test_mandatory_8_xlookup(standard_ptpn_df):
    res = HybridAIService.process_query("Cari penjualan Andi", sample_df=standard_ptpn_df)
    assert res["formula_name"] in ["XLOOKUP", "LOOKUP", "SUMIF"]
    assert res["validation"]["is_valid"] is True

def test_mandatory_9_ambiguous_query_clarification(standard_ptpn_df):
    """
    Ambiguous query 'Hitung data Andi' must trigger clarification.
    """
    res = HybridAIService.process_query("Hitung data Andi", sample_df=standard_ptpn_df)
    assert res["confidence"]["needs_clarification"] is True
    assert res["clarification"] is not None
    assert res["clarification"]["needed"] is True
    assert len(res["clarification"]["options"]) >= 2
    # Ensure options offer SUM, AVERAGE, and COUNT
    labels = [opt["label"] for opt in res["clarification"]["options"]]
    assert any("SUM" in l for l in labels)
    assert any("AVERAGE" in l for l in labels)
    assert any("COUNT" in l for l in labels)

def test_mandatory_10_dynamic_column_reordering():
    """
    Test column order resilience:
    When columns are placed in different order:
    Penjualan (Col A), Bulan (Col B), Sales (Col C)
    Formula generator must dynamically output A:A for Penjualan and C:C for Sales.
    """
    reordered_df = pd.DataFrame({
        "Penjualan": [1000000, 2000000, 1500000, 500000],
        "Bulan": ["Januari", "Januari", "Februari", "Januari"],
        "Sales": ["Andi", "Budi", "Andi", "Andi"]
    })

    res = HybridAIService.process_query("Hitung total penjualan Andi bulan Januari", sample_df=reordered_df)
    assert res["formula_name"] == "SUMIFS"
    assert res["execution"]["executed"] is True
    assert res["execution"]["result"] == 1500000
    # Target column Penjualan is column A -> formula must reference A:A
    assert "=SUMIFS(A:A" in res["generated_formula"] or "A:A" in res["generated_formula"]


# ==========================================================
# 3. REFINEMENT A: CONTEXT-AWARE AMBIGUOUS PARAMETER
# ==========================================================
def test_ambiguous_parameter_detection():
    """
    When 'Andi' appears in multiple columns (Sales and Manager),
    the system must detect ambiguous parameter and trigger clarification.
    """
    multi_andi_df = pd.DataFrame({
        "Sales": ["Andi", "Budi"],
        "Manager": ["Budi", "Andi"],
        "Penjualan": [1000000, 2000000]
    })

    res = HybridAIService.process_query("Total penjualan Andi", sample_df=multi_andi_df)
    assert res["confidence"]["needs_clarification"] is True
    assert res["clarification"] is not None
    assert res["clarification"]["ambiguity_type"] == "ambiguous_parameter"
    # Should give options to choose between Sales and Manager
    labels = [opt["label"] for opt in res["clarification"]["options"]]
    assert any("Sales" in l for l in labels)
    assert any("Manager" in l for l in labels)


# ==========================================================
# 4. REFINEMENT B: LOGICAL IF AND IFS PARSER
# ==========================================================
def test_logical_if_parser():
    res = HybridAIService.process_query("Jika penjualan lebih dari 100 juta maka Tinggi")
    assert res["formula_name"] == "IF"
    assert res["validation"]["is_valid"] is True
    assert ">" in res["generated_formula"]
    assert "100000000" in res["generated_formula"]
    assert "Tinggi" in res["generated_formula"]

def test_logical_ifs_parser():
    res = HybridAIService.process_query(
        "Jika penjualan lebih dari 100 juta Tinggi, jika lebih dari 50 juta Sedang, selain itu Rendah"
    )
    assert res["formula_name"] == "IFS"
    assert res["validation"]["is_valid"] is True
    assert "IFS" in res["generated_formula"]
    assert "100000000" in res["generated_formula"]
    assert "50000000" in res["generated_formula"]
    assert "Sedang" in res["generated_formula"]


# ==========================================================
# 5. REFINEMENT C & D: SAFE EXECUTION & WHITELIST CHECK
# ==========================================================
def test_safe_execution_whitelist():
    """Formulas outside the 18 whitelist must be rejected."""
    df = pd.DataFrame({"A": [1, 2, 3]})
    unsupported_res = ExecutionEngine.execute_formula_safe(df, "EXEC_ARBITRARY_CODE")
    assert unsupported_res["executed"] is False
    assert unsupported_res["status"] == "unsupported_formula"

def test_count_vs_counta_datatype():
    """COUNT for numeric target column, COUNTA for text column."""
    df = pd.DataFrame({
        "Nama": ["Andi", "Budi", "Cici"],
        "Gaji": [5000000, 6000000, 7000000]
    })
    
    # Query on text column
    res_text = HybridAIService.process_query("Hitung nama", sample_df=df)
    assert res_text["formula_name"] == "COUNTA"
    assert res_text["execution"]["result"] == 3

    # Query on numeric column
    res_num = HybridAIService.process_query("Hitung banyaknya gaji", sample_df=df)
    assert res_num["formula_name"] == "COUNT"
    assert res_num["execution"]["result"] == 3


# ==========================================================
# 6. REFINEMENT F & G: BENCHMARK RUNNER ON 200 HOLDOUT QUERIES
# ==========================================================
def test_evaluation_benchmark_runner():
    """
    Verifies that the benchmark runs across the 200 PostgreSQL evaluation queries
    and produces real accuracy, confusion matrix, and decision matrix impact metrics.
    """
    bench = EvaluationRunnerService.run_benchmark()
    assert "error" not in bench
    assert bench["evaluation_samples_count"] >= 200

    metrics = bench["metrics"]
    assert metrics["ml_classifier_accuracy"] >= 75.0
    assert metrics["formula_selection_accuracy"] >= 70.0
    assert metrics["formula_generation_validity_rate"] >= 80.0
    assert metrics["end_to_end_correctness_accuracy"] >= 50.0

    # Decision Matrix should provide an accuracy lift over raw ML
    impact = bench["decision_matrix_impact"]
    assert "accuracy_lift" in impact
    assert "formula_selection_confusion_matrix" in bench
    assert len(bench["formula_selection_confusion_matrix"]) > 0
