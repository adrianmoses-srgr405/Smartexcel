import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.analysis import AnalysisHistory
from app.schemas.intent import (
    NaturalLanguageQueryRequest,
    AnalysisResponse,
    StructuredAnalysisIntent,
    FormulaDecisionResult,
    ExecutionResult,
    ClarificationPayload,
    FilterCriterion
)
from app.services.profiler_service import ProfilerService
from app.services.hybrid_ai_service import HybridAIService
from app.services.execution_engine import ExecutionEngine

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
def analyze_query(
    payload: NaturalLanguageQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Core Hybrid AI Pipeline:
    Natural Language Query -> Intent & Parameter Extraction -> Column Resolver
    -> Random Forest Candidate -> Deterministic Decision Matrix -> Formula Generator
    -> Formula Validator -> Safe Execution Engine -> Confidence Scorer -> Clarification Engine.
    """
    start_time = time.time()

    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset tidak ditemukan")

    file_path = Path(dataset.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File data fisik tidak ditemukan")

    selected_sheet = (dataset.dataset_metadata or {}).get("selected_sheet")
    df, _, _ = ProfilerService.load_dataset_file(file_path, sheet_name=selected_sheet)

    # Execute Hybrid AI pipeline
    hybrid_res = HybridAIService.process_query(
        query=payload.query,
        dataset=dataset,
        sample_df=df,
        db=db
    )

    # Build backward compatible legacy intent structure for frontend table views
    target_info = hybrid_res["columns"]["target"]
    target_col = target_info.get("matched_column") if target_info else None
    
    filters_list = []
    for cond in hybrid_res["columns"]["conditions"]:
        c_val = cond.get("value")
        if isinstance(c_val, dict) and "start" in c_val and "end" in c_val:
            c_val = [c_val["start"], c_val["end"]]
        filters_list.append(FilterCriterion(
            field=cond.get("matched_column") or cond.get("column_hint") or "Kolom",
            operator=cond.get("operator", "="),
            value=c_val,
            data_type=cond.get("data_type", "text")
        ))

    detected_group_by = (hybrid_res.get("formula_plan") or {}).get("grouping")
    if not detected_group_by and hybrid_res.get("parameters", {}).get("group_by"):
        detected_group_by = hybrid_res["parameters"]["group_by"][0]
    group_by_list = [detected_group_by] if detected_group_by else []

    parsed_intent = StructuredAnalysisIntent(
        intent="aggregation",
        operation=hybrid_res["parameters"]["operation"] or "SUM",
        target_field=target_col,
        group_by=group_by_list,
        filters=filters_list,
        confidence_score=hybrid_res["confidence"]["composite_score"],
        user_explanation=hybrid_res["explanation"]["formula_selection"]
    )

    decision_model = FormulaDecisionResult(
        formula_id=hybrid_res["formula_name"],
        formula_name=hybrid_res["formula_name"],
        category=hybrid_res["decision"]["category"],
        reason=hybrid_res["decision"]["reason"],
        syntax_pattern=hybrid_res["decision"]["syntax_pattern"],
        generated_excel_formula=hybrid_res["generated_formula"],
        affected_columns=hybrid_res["decision"]["affected_columns"],
        validation_status=hybrid_res["decision"]["validation_status"],
        validation_messages=hybrid_res["decision"]["validation_messages"],
        ml_prediction=hybrid_res["decision"]["ml_prediction"],
        ml_confidence=hybrid_res["decision"]["ml_confidence"],
        is_confident=hybrid_res["decision"]["is_confident"],
        rule_validation_status=hybrid_res["decision"]["rule_validation_status"],
        rule_decision=hybrid_res["decision"]["rule_decision"]
    )

    # Render data preview rows and summary for UI
    summary, headers, rows, chart_data = ExecutionEngine.execute(
        df=df,
        intent=parsed_intent,
        decision=decision_model,
        user_query=payload.query
    )

    # If safe formula execution succeeded, reflect its exact calculated result in summary
    if hybrid_res["execution"].get("executed") and not summary.get("has_subtotals"):
        summary["calculated_result"] = hybrid_res["execution"].get("result")
        summary["execution_status"] = "success"

    if hybrid_res.get("formula_plan"):
        summary["formula_plan"] = hybrid_res["formula_plan"]

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    return AnalysisResponse(
        analysis_id=hybrid_res["analysis_id"],
        dataset_id=dataset.id,
        user_query=payload.query,
        parsed_intent=parsed_intent,
        decision=decision_model,
        calculation_summary=summary,
        table_headers=headers,
        table_rows=rows,
        chart_data=chart_data,
        execution_time_ms=elapsed_ms,
        # Enhanced Hybrid AI fields:
        generated_formula=hybrid_res["generated_formula"],
        formula_name=hybrid_res["formula_name"],
        execution=ExecutionResult(**hybrid_res["execution"]),
        confidence=hybrid_res["confidence"],
        clarification=ClarificationPayload(**hybrid_res["clarification"]) if hybrid_res["clarification"] else None,
        explanation=hybrid_res["explanation"],
        validation=hybrid_res["validation"],
        # Multi-Task fields
        tasks=hybrid_res.get("tasks"),
        summary=hybrid_res.get("summary"),
        parameters=hybrid_res.get("parameters"),
        columns=hybrid_res.get("columns"),
        formula_plan=hybrid_res.get("formula_plan")
    )
