import pytest
from app.schemas.intent import StructuredAnalysisIntent, FilterCriterion
from app.models.dataset import DatasetColumn
from app.services.ml_classifier import MLFormulaClassifier
from app.services.decision_engine import FormulaDecisionEngine

@pytest.fixture
def mock_columns():
    return [
        DatasetColumn(original_name="Tanggal", sanitized_name="tanggal", inferred_type="Date", excel_column_letter="A", column_index=0),
        DatasetColumn(original_name="Merek", sanitized_name="merek", inferred_type="Categorical", excel_column_letter="B", column_index=1),
        DatasetColumn(original_name="Kota", sanitized_name="kota", inferred_type="Categorical", excel_column_letter="C", column_index=2),
        DatasetColumn(original_name="Harga_Netto", sanitized_name="harga_netto", inferred_type="Numeric", excel_column_letter="D", column_index=3),
    ]


def test_ml_classifier_predictions():
    classifier = MLFormulaClassifier()
    assert classifier.model is not None

    # Test SUM with 0 filters -> SUM
    res_sum = classifier.predict({
        "operation": "SUM", "intent": "aggregation", "filter_count": 0, "grouping_count": 0,
        "has_date_filter": 0, "has_multiple_criteria": 0, "target_data_type": "numeric"
    })
    assert res_sum["predicted_formula"] == "SUM"
    assert res_sum["confidence"] >= 0.70

    # Test SUM with 1 filter -> SUMIF
    res_sumif = classifier.predict({
        "operation": "SUM", "intent": "aggregation", "filter_count": 1, "grouping_count": 0,
        "has_date_filter": 0, "has_multiple_criteria": 0, "target_data_type": "numeric"
    })
    assert res_sumif["predicted_formula"] == "SUMIF"

    # Test SUM with 2 filters + date -> SUMIFS
    res_sumifs = classifier.predict({
        "operation": "SUM", "intent": "aggregation", "filter_count": 2, "grouping_count": 0,
        "has_date_filter": 1, "has_multiple_criteria": 1, "target_data_type": "numeric"
    })
    assert res_sumifs["predicted_formula"] == "SUMIFS"

    # Test XLOOKUP
    res_lookup = classifier.predict({
        "operation": "XLOOKUP", "intent": "lookup", "filter_count": 1, "grouping_count": 0,
        "has_date_filter": 0, "has_multiple_criteria": 0, "target_data_type": "text"
    })
    assert res_lookup["predicted_formula"] == "XLOOKUP"

    # Test MAX
    res_max = classifier.predict({
        "operation": "MAX", "intent": "ranking", "filter_count": 0, "grouping_count": 0,
        "has_date_filter": 0, "has_multiple_criteria": 0, "target_data_type": "numeric"
    })
    assert res_max["predicted_formula"] == "MAX"

def test_hybrid_decision_engine_rule_validation(mock_columns):
    engine = FormulaDecisionEngine()

    # Case 1: Toyota in Pekanbaru on Feb 2024 (2 filters -> SUMIFS)
    intent = StructuredAnalysisIntent(
        intent="aggregation",
        operation="SUM",
        target_field="Harga_Netto",
        group_by=[],
        filters=[
            FilterCriterion(field="Merek", operator="=", value="Toyota", data_type="text"),
            FilterCriterion(field="Tanggal", operator="BETWEEN", value=["2024-02-01", "2024-02-29"], data_type="date"),
        ]
    )

    decision = engine.decide_formula(intent, mock_columns)
    assert decision.formula_id == "SUMIFS"
    assert decision.ml_prediction in ["SUMIFS", "SUMIF"]
    assert decision.ml_confidence is not None
    assert decision.rule_validation_status in ["VALID", "CORRECTED_BY_RULE"]
    assert decision.is_confident is True

def test_rule_engine_correction_priority(mock_columns, monkeypatch):
    """
    Simulate ML intentionally returning an incorrect formula (e.g. SUMIF for 3 filters),
    verifying that the Rule Engine gatekeeper STRICTLY corrects it to SUMIFS.
    """
    engine = FormulaDecisionEngine()

    # Monkeypatch ML to return faulty 'SUMIF'
    from app.services import decision_engine
    monkeypatch.setattr(
        decision_engine.ml_classifier,
        "predict",
        lambda feat: {"predicted_formula": "SUMIF", "confidence": 0.88, "is_confident": True, "probabilities": {"SUMIF": 0.88}}
    )

    intent_multi = StructuredAnalysisIntent(
        intent="aggregation",
        operation="SUM",
        target_field="Harga_Netto",
        filters=[
            FilterCriterion(field="Merek", operator="=", value="Toyota"),
            FilterCriterion(field="Kota", operator="=", value="Pekanbaru"),
        ]
    )

    decision = engine.decide_formula(intent_multi, mock_columns)
    assert decision.formula_id == "SUMIFS"  # Corrected by Rule Engine
    assert decision.ml_prediction == "SUMIF"
    assert decision.rule_validation_status == "CORRECTED_BY_RULE"
    assert "dikoreksi Rule Engine menjadi SUMIFS" in decision.rule_decision
