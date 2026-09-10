import pytest
import pandas as pd
from app.services.hybrid_ai_service import HybridAIService
from app.services.parameter_extractor import ParameterExtractor

@pytest.fixture
def dummy_penjualan_df():
    """
    Simulated dummy sales DataFrame matching Data_Dummy_Penjualan_Mobil_Pekanbaru_1000 structure.
    """
    data = {
        "ID_Transaksi": [f"TRX{i:04d}" for i in range(1, 101)],
        "Tanggal": ["2024-01-15"] * 100,
        "Sales": ["Yoga Pratama"] * 30 + ["Rina Amelia"] * 25 + ["Bagus Santoso"] * 25 + ["Ayu Lestari"] * 20,
        "Cabang": ["Sukajadi"] * 50 + ["Pekanbaru Kota"] * 50,
        "Merek": ["Toyota"] * 60 + ["Honda"] * 40,
        "Model": ["Avanza"] * 50 + ["Brio"] * 50,
        "Harga": [250000000] * 100
    }
    return pd.DataFrame(data)

def test_count_yoga_pratama_exact_user_query(dummy_penjualan_df):
    """
    User query: 'Hitung ada berapa jumlah sales Yoga Pratama di data ini'
    Must yield COUNTIF on Sales column, no ID_Transaksi as target, high confidence, no clarification.
    """
    query = "Hitung ada berapa jumlah sales Yoga Pratama di data ini"
    result = HybridAIService.process_query(query, sample_df=dummy_penjualan_df)

    assert result["formula_name"] == "COUNTIF"
    assert "COUNTIF" in result["generated_formula"]
    assert "Yoga Pratama" in result["generated_formula"]
    assert result["parameters"]["target_term"] is None
    assert len(result["parameters"]["conditions"]) == 1
    
    cond = result["parameters"]["conditions"][0]
    assert cond["resolved_column"] == "Sales"
    assert cond["value"] == "Yoga Pratama"
    assert cond.get("verified_in_dataset") is True
    
    assert result["confidence"]["composite_score"] >= 0.85
    assert result["confidence"]["level"] == "HIGH"
    assert result["confidence"]["needs_clarification"] is False
    assert result["execution"]["executed"] is True
    assert result["execution"]["result"] == 30

def test_count_yoga_pratama_query_variations(dummy_penjualan_df):
    """
    Test variations:
    1. 'berapa jumlah sales Yoga Pratama'
    2. 'jumlah transaksi Yoga Pratama'
    3. 'berapa kali Yoga Pratama melakukan penjualan'
    """
    queries = [
        "berapa jumlah sales Yoga Pratama",
        "jumlah transaksi Yoga Pratama",
        "berapa kali Yoga Pratama melakukan penjualan"
    ]
    for q in queries:
        result = HybridAIService.process_query(q, sample_df=dummy_penjualan_df)
        assert result["formula_name"] == "COUNTIF", f"Failed for query '{q}': got {result['formula_name']}"
        assert result["parameters"]["target_term"] is None
        assert len(result["parameters"]["conditions"]) == 1
        assert result["parameters"]["conditions"][0]["resolved_column"] == "Sales"
        assert result["parameters"]["conditions"][0]["value"] == "Yoga Pratama"
        assert result["confidence"]["level"] == "HIGH"
        assert result["confidence"]["needs_clarification"] is False
        assert result["execution"]["result"] == 30

def test_count_other_sales_name(dummy_penjualan_df):
    """
    Test another sales person from dataset (Rina Amelia).
    """
    query = "Berapa kali Rina Amelia melakukan penjualan?"
    result = HybridAIService.process_query(query, sample_df=dummy_penjualan_df)

    assert result["formula_name"] == "COUNTIF"
    assert result["parameters"]["conditions"][0]["resolved_column"] == "Sales"
    assert result["parameters"]["conditions"][0]["value"] == "Rina Amelia"
    assert result["confidence"]["level"] == "HIGH"
    assert result["confidence"]["needs_clarification"] is False
    assert result["execution"]["result"] == 25

def test_count_unverified_sales_name_structural_fallback(dummy_penjualan_df):
    """
    Test sales name not present in dataset (Zack Snyder).
    Should still extract condition via structural fallback, result in 0 executions without breaking.
    """
    query = "Hitung ada berapa sales Zack Snyder di data ini"
    result = HybridAIService.process_query(query, sample_df=dummy_penjualan_df)

    assert result["formula_name"] == "COUNTIF"
    assert len(result["parameters"]["conditions"]) == 1
    assert result["parameters"]["conditions"][0]["resolved_column"] == "Sales"
    assert "Zack Snyder" in result["parameters"]["conditions"][0]["value"]
    assert result["execution"]["executed"] is True
    assert result["execution"]["result"] == 0

def test_count_zero_filter_no_forced_id_transaksi(dummy_penjualan_df):
    """
    Test counting with 0 filters:
    'Hitung total transaksi di data ini' or 'Hitung ada berapa data di dataset ini'
    Should generate COUNT or COUNTA, but not incorrectly force filters.
    """
    query = "Hitung ada berapa data di dataset ini"
    result = HybridAIService.process_query(query, sample_df=dummy_penjualan_df)

    assert result["formula_name"] in ["COUNT", "COUNTA"]
    assert len(result["parameters"]["conditions"]) == 0
    assert result["execution"]["executed"] is True
    assert result["execution"]["result"] == 100

def test_count_two_filters_generates_countifs(dummy_penjualan_df):
    """
    Test counting with 2 conditions:
    'Berapa kali Yoga Pratama melakukan penjualan di cabang Sukajadi?'
    Should generate COUNTIFS with criteria on Sales and Cabang.
    """
    query = "Berapa kali Yoga Pratama melakukan penjualan di cabang Sukajadi?"
    result = HybridAIService.process_query(query, sample_df=dummy_penjualan_df)

    assert result["formula_name"] == "COUNTIFS"
    assert len(result["parameters"]["conditions"]) == 2
    
    col_hints = [c["resolved_column"] for c in result["parameters"]["conditions"]]
    assert "Sales" in col_hints
    assert "Cabang" in col_hints
    
    vals = [c["value"] for c in result["parameters"]["conditions"]]
    assert "Yoga Pratama" in vals
    assert "Sukajadi" in vals

    assert result["confidence"]["level"] == "HIGH"
    assert result["confidence"]["needs_clarification"] is False
    assert result["execution"]["executed"] is True
    # 30 Yoga Pratama total, first 50 rows are Sukajadi -> all 30 are in Sukajadi
    assert result["execution"]["result"] == 30

def test_ambiguous_parameter_still_requests_clarification():
    """
    When an entity value exists identically across multiple columns without explicit clarification,
    the pipeline must still mark ambiguous and request clarification.
    """
    df = pd.DataFrame({
        "Sales": ["Pekanbaru", "Andi"],
        "Cabang": ["Pekanbaru", "Dumai"]
    })
    query = "Hitung berapa Pekanbaru di data ini"
    result = HybridAIService.process_query(query, sample_df=df)

    assert result["parameters"]["conditions"][0]["is_ambiguous"] is True
    assert result["confidence"]["needs_clarification"] is True
    assert result["clarification"] is not None
