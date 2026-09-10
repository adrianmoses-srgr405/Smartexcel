import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from app.services.task_decomposer import TaskDecomposer
from app.services.hybrid_ai_service import HybridAIService
from app.services.decision_engine import FormulaDecisionEngine
from app.services.formula_generator import FormulaGenerator
from app.services.formula_validator import FormulaValidator
from app.services.execution_engine import ExecutionEngine
from app.schemas.intent import AnalysisResponse

@pytest.fixture
def plantation_df():
    """Realistic plantation dataset with multiple afdelings and date range."""
    return pd.DataFrame({
        "Tanggal": [
            "2026-01-05", "2026-01-10", "2026-01-15", "2026-01-20",
            "2026-02-01", "2026-02-05", "2026-01-12", "2026-01-25"
        ],
        "Afdeling": ["A", "A", "A", "B", "A", "B", "A", "B"],
        "Produksi_TBS": [100.0, 150.0, 200.0, 300.0, 50.0, 400.0, 250.0, 180.0],
        "Produksi_CPO": [20.0, 30.0, 45.0, 60.0, 10.0, 80.0, 50.0, 35.0],
        "Keterangan": ["Normal", "Normal", "Normal", "Lembur", "Normal", "Lembur", "Normal", "Normal"]
    })

def test_a_single_task(plantation_df):
    """Test A: Single task decomposition and execution."""
    query = "Hitung total TBS untuk afdeling A"
    res = HybridAIService.process_query(query=query, sample_df=plantation_df)
    assert len(res["tasks"]) == 1
    assert res["summary"]["total_tasks"] == 1
    assert res["formula_name"] == "SUMIF"
    assert res["execution"]["executed"] is True
    # Rows for Afdeling A: 100 + 150 + 200 + 50 + 250 = 750
    assert res["execution"]["result"] == 750

def test_b_two_tasks(plantation_df):
    """Test B: Two tasks decomposition and execution."""
    query = "Hitung total dan rata-rata produksi TBS"
    res = HybridAIService.process_query(query=query, sample_df=plantation_df)
    assert len(res["tasks"]) == 2
    assert res["summary"]["total_tasks"] == 2
    assert res["tasks"][0]["operation"] == "SUM"
    assert res["tasks"][1]["operation"] == "AVERAGE"
    assert res["tasks"][0]["execution"]["executed"] is True
    assert res["tasks"][1]["execution"]["executed"] is True

def test_c_three_tasks(plantation_df):
    """Test C: Three tasks decomposition."""
    query = "Hitung total, rata-rata, lalu maksimum TBS"
    res = HybridAIService.process_query(query=query, sample_df=plantation_df)
    assert len(res["tasks"]) == 3
    assert res["tasks"][0]["operation"] == "SUM"
    assert res["tasks"][1]["operation"] == "AVERAGE"
    assert res["tasks"][2]["operation"] == "MAX"

def test_d_and_end_to_end_five_tasks(plantation_df):
    """
    Test D & E2E (Section 33 & 34):
    Complex 5-task query with shared context inheritance (Afdeling A & Januari 2026).
    All 5 tasks MUST execute genuinely and produce correct results on DataFrame.
    """
    query = (
        "Hitung total TBS, rata-rata TBS, TBS tertinggi, TBS terendah, "
        "dan jumlah data TBS untuk afdeling A bulan Januari 2026."
    )
    res = HybridAIService.process_query(query=query, sample_df=plantation_df)
    
    tasks = res["tasks"]
    summary = res["summary"]
    
    assert len(tasks) == 5, f"Expected 5 tasks, got {len(tasks)}"
    assert summary["total_tasks"] == 5
    assert summary["successful_tasks"] == 5
    assert summary["failed_tasks"] == 0

    expected_ops = ["SUM", "AVERAGE", "MAX", "MIN", "COUNT"]
    expected_formulas = ["SUMIFS", "AVERAGEIFS", "MAXIFS", "MINIFS", "COUNTIFS"]

    for idx, task in enumerate(tasks):
        assert task["operation"] == expected_ops[idx], f"Task {idx} op mismatch: {task['operation']}"
        assert task["formula_name"] == expected_formulas[idx], f"Task {idx} formula mismatch: {task['formula_name']}"
        assert task["generated_formula"].startswith("=" + expected_formulas[idx])
        assert task["validation"]["is_valid"] is True
        assert task["execution"]["executed"] is True
        assert task["status"] == "success"

    # Verify actual calculated results on DataFrame:
    # Afdeling A in Januari 2026 rows:
    # 2026-01-05: 100.0
    # 2026-01-10: 150.0
    # 2026-01-15: 200.0
    # 2026-01-12: 250.0
    # Total = 700.0, Average = 175.0, Max = 250.0, Min = 100.0, Count = 4
    assert tasks[0]["execution"]["result"] == 700
    assert tasks[1]["execution"]["result"] == 175.0
    assert tasks[2]["execution"]["result"] == 250
    assert tasks[3]["execution"]["result"] == 100
    assert tasks[4]["execution"]["result"] == 4

def test_e_shared_context_inheritance():
    """Test E: Shared context (target and date and afdeling) inherited across tasks."""
    query = "total, rata-rata, maksimum dan minimum TBS afdeling A bulan Januari 2026"
    tasks = TaskDecomposer.decompose(query)
    assert len(tasks) == 4
    for t in tasks:
        assert t["target_term"] == "TBS"
        fields = [f["field"] for f in t["filters"]]
        assert "Afdeling" in fields
        assert "Tanggal" in fields

def test_f_context_override():
    """Test F: Clause-specific context overrides shared context."""
    query = "Hitung total TBS afdeling A dan rata-rata TBS afdeling B"
    tasks = TaskDecomposer.decompose(query)
    assert len(tasks) == 2
    
    t1 = tasks[0]
    t2 = tasks[1]
    
    assert t1["operation"] == "SUM"
    afd1 = next((f["value"] for f in t1["filters"] if f["field"] == "Afdeling"), None)
    assert afd1 == "A"

    assert t2["operation"] == "AVERAGE"
    afd2 = next((f["value"] for f in t2["filters"] if f["field"] == "Afdeling"), None)
    assert afd2 == "B"

def test_g_different_target_columns(plantation_df):
    """Test G: Different target columns per task."""
    query = "total TBS dan rata-rata CPO"
    res = HybridAIService.process_query(query=query, sample_df=plantation_df)
    assert len(res["tasks"]) == 2
    t1 = res["tasks"][0]
    t2 = res["tasks"][1]
    assert t1["columns"]["target"]["matched_column"] == "Produksi_TBS"
    assert t2["columns"]["target"]["matched_column"] == "Produksi_CPO"

def test_h_different_filters(plantation_df):
    """Test H: Different filters evaluated correctly."""
    query = "total TBS afdeling A dan total TBS afdeling B"
    res = HybridAIService.process_query(query=query, sample_df=plantation_df)
    assert len(res["tasks"]) == 2
    # Afdeling A total: 750, Afdeling B total: 300 + 400 + 180 = 880
    assert res["tasks"][0]["execution"]["result"] == 750
    assert res["tasks"][1]["execution"]["result"] == 880

def test_i_group_by():
    """Test I: Group by per afdeling preserved."""
    query = "Hitung total TBS per afdeling dan rata-rata TBS per afdeling"
    tasks = TaskDecomposer.decompose(query)
    assert len(tasks) == 2
    for t in tasks:
        assert "Afdeling" in t.get("group_by", [])

def test_j_maxifs_support(plantation_df):
    """Test J: MAXIFS selection, generation, validation, and safe execution."""
    query = "TBS tertinggi untuk afdeling A"
    res = HybridAIService.process_query(query=query, sample_df=plantation_df)
    assert res["formula_name"] == "MAXIFS"
    assert res["validation"]["is_valid"] is True
    assert res["execution"]["executed"] is True
    assert res["execution"]["result"] == 250

def test_k_minifs_support(plantation_df):
    """Test K: MINIFS selection, generation, validation, and safe execution."""
    query = "TBS terendah untuk afdeling A"
    res = HybridAIService.process_query(query=query, sample_df=plantation_df)
    assert res["formula_name"] == "MINIFS"
    assert res["validation"]["is_valid"] is True
    assert res["execution"]["executed"] is True
    assert res["execution"]["result"] == 50

def test_l_countifs_support(plantation_df):
    """Test L: COUNTIFS with multiple conditions."""
    query = "jumlah data TBS untuk afdeling A bulan Januari 2026"
    res = HybridAIService.process_query(query=query, sample_df=plantation_df)
    assert res["formula_name"] == "COUNTIFS"
    assert res["validation"]["is_valid"] is True
    assert res["execution"]["executed"] is True
    assert res["execution"]["result"] == 4

def test_m_gemini_online_mock(plantation_df):
    """Test M: Gemini online mock returns structured tasks."""
    mock_gemini_tasks = [
        {"task_id": "task_1", "operation": "SUM", "target_term": "TBS", "filters": [], "group_by": [], "confidence": 0.98},
        {"task_id": "task_2", "operation": "AVERAGE", "target_term": "TBS", "filters": [], "group_by": [], "confidence": 0.98}
    ]
    with patch("app.services.ai_service.AIService.parse_tasks_with_gemini", return_value=mock_gemini_tasks):
        tasks = TaskDecomposer.decompose("Hitung total dan rata-rata TBS", sample_df=plantation_df)
        assert len(tasks) == 2
        assert tasks[0]["operation"] == "SUM"
        assert tasks[1]["operation"] == "AVERAGE"

def test_n_gemini_offline_fallback(plantation_df):
    """Test N: Fallback to local heuristic parser when Gemini returns None."""
    with patch("app.services.ai_service.AIService.parse_tasks_with_gemini", return_value=None):
        tasks = TaskDecomposer.decompose("Hitung total dan rata-rata TBS", sample_df=plantation_df)
        assert len(tasks) == 2
        assert tasks[0]["operation"] == "SUM"
        assert tasks[1]["operation"] == "AVERAGE"

def test_o_gemini_malformed_response_fallback(plantation_df):
    """Test O: When Gemini returns malformed response, fallback works."""
    with patch("app.services.ai_service.AIService.parse_tasks_with_gemini", return_value="invalid_non_list_garbage"):
        tasks = TaskDecomposer.decompose("Hitung total dan rata-rata TBS", sample_df=plantation_df)
        assert len(tasks) == 2

def test_p_ambiguous_columns():
    """Test P: Ambiguity handling triggers clarification."""
    # When query has ambiguous parameter
    query = "Hitung total untuk 100"
    res = HybridAIService.process_query(query=query)
    # Shouldn't invent fake high confidence
    assert res["confidence"]["composite_score"] <= 0.85

def test_q_low_confidence_empty_or_greeting():
    """Test Q: Empty or greeting query does not default to fake SUM."""
    res = HybridAIService.process_query(query="halo selamat pagi")
    # Must indicate clarification or unsupported intent
    assert res["confidence"]["composite_score"] < 0.70 or res.get("clarification") is not None

def test_r_partial_task_failure(plantation_df):
    """Test R: Partial failure does not crash whole request."""
    # Create two tasks where second task refers to non-existent column
    tasks_spec = [
        {"task_id": "task_1", "operation": "SUM", "target_term": "TBS", "filters": []},
        {"task_id": "task_2", "operation": "SUM", "target_term": "KOLOM_GAIB_XYZ", "filters": []}
    ]
    with patch.object(TaskDecomposer, "decompose", return_value=tasks_spec):
        res = HybridAIService.process_query("custom query", sample_df=plantation_df)
        assert res["summary"]["total_tasks"] == 2
        assert res["summary"]["successful_tasks"] == 1
        assert res["summary"]["failed_tasks"] == 1
        assert res["tasks"][0]["status"] == "success"
        assert res["tasks"][1]["status"] != "success"

def test_s_duplicate_tasks_deduplication():
    """Test S: Duplicate tasks are deduplicated deterministically."""
    query = "Hitung total TBS dan total TBS"
    tasks = TaskDecomposer.decompose(query)
    assert len(tasks) == 1

def test_t_task_ordering():
    """Test T: User order preserved (AVERAGE -> SUM -> MAX)."""
    query = "Hitung rata-rata, total, lalu maksimum TBS"
    tasks = TaskDecomposer.decompose(query)
    assert len(tasks) == 3
    assert tasks[0]["operation"] == "AVERAGE"
    assert tasks[1]["operation"] == "SUM"
    assert tasks[2]["operation"] == "MAX"

def test_u_postgresql_persistence(plantation_df):
    """Test U: PostgreSQL AnalysisHistory persists tasks."""
    mock_db = MagicMock()
    mock_dataset = MagicMock()
    mock_dataset.id = "ds-123"
    mock_dataset.columns = []
    
    res = HybridAIService.process_query(
        query="Hitung total dan rata-rata TBS",
        dataset=mock_dataset,
        sample_df=plantation_df,
        db=mock_db
    )
    assert mock_db.add.called
    assert mock_db.commit.called
    saved_record = mock_db.add.call_args[0][0]
    assert "tasks" in saved_record.parsed_intent
    assert len(saved_record.parsed_intent["tasks"]) == 2

def test_v_feedback_endpoint():
    """Test V: Feedback accepts task_id."""
    from app.api.v1.endpoints.evaluation import submit_feedback
    mock_db = MagicMock()
    payload = {
        "analysis_id": "an-123",
        "task_id": "task_2",
        "is_correct": False,
        "corrected_formula": "=AVERAGE(C:C)",
        "notes": "Target kolom seharusnya CPO"
    }
    feedback_res = submit_feedback(payload=payload, db=mock_db)
    assert feedback_res["status"] == "success"
    assert feedback_res["task_id"] == "task_2"
    saved_fb = mock_db.add.call_args[0][0]
    assert "[task_id: task_2]" in saved_fb.user_feedback_text

def test_w_api_backward_compatibility(plantation_df):
    """Test W: Zero breaking changes - Legacy root fields populated from primary task."""
    query = "Hitung total dan rata-rata TBS"
    res = HybridAIService.process_query(query=query, sample_df=plantation_df)
    
    # Legacy fields exist at root
    assert "formula_name" in res
    assert "generated_formula" in res
    assert "parameters" in res
    assert "columns" in res
    assert "execution" in res
    assert "validation" in res
    assert "confidence" in res
    assert "decision" in res
    
    # Matches primary task (first task)
    assert res["formula_name"] == res["tasks"][0]["formula_name"]
    assert res["generated_formula"] == res["tasks"][0]["generated_formula"]
    assert res["execution"]["result"] == res["tasks"][0]["execution"]["result"]
    
    # New multi-task fields exist
    assert "tasks" in res
    assert "summary" in res
    assert res["summary"]["total_tasks"] == 2
