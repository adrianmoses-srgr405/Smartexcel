import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.analysis import AnalysisHistory
from app.schemas.intent import NaturalLanguageQueryRequest, AnalysisResponse
from app.services.profiler_service import ProfilerService
from app.services.ai_service import AIService
from app.services.decision_engine import FormulaDecisionEngine
from app.services.formula_generator import FormulaGenerator
from app.services.execution_engine import ExecutionEngine

router = APIRouter()
decision_engine = FormulaDecisionEngine()

@router.post("/analyze", response_model=AnalysisResponse)
def analyze_query(
    payload: NaturalLanguageQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Core AI NLP + Deterministic Formula Decision Pipeline.
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
    columns = dataset.columns

    # 1. AI Intent Parsing
    parsed_intent = AIService.parse_query(payload.query, columns)

    # 2. Formula Decision Engine
    decision = decision_engine.decide_formula(parsed_intent, columns)

    # 3. Exact Excel Formula Generation
    generated_formula = FormulaGenerator.generate_excel_formula(
        decision=decision,
        intent=parsed_intent,
        columns=columns,
        data_row_count=dataset.row_count
    )
    decision.generated_excel_formula = generated_formula

    # 4. Calculation & Execution
    summary, headers, rows, chart_data = ExecutionEngine.execute(
        df=df,
        intent=parsed_intent,
        decision=decision
    )

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    # 5. Persist Analysis History
    analysis_record = AnalysisHistory(
        dataset_id=dataset.id,
        user_query=payload.query,
        parsed_intent=parsed_intent.model_dump(),
        selected_formula_id=decision.formula_id,
        generated_excel_formula=generated_formula,
        formula_explanation=decision.reason,
        calculation_results={
            "summary": summary,
            "headers": headers,
            "row_count": len(rows),
        },
        result_summary=str(summary.get("grand_total") or summary.get("calculated_result") or f"{len(rows)} baris hasil"),
        execution_time_ms=elapsed_ms
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)

    return AnalysisResponse(
        analysis_id=analysis_record.id,
        dataset_id=dataset.id,
        user_query=payload.query,
        parsed_intent=parsed_intent,
        decision=decision,
        calculation_summary=summary,
        table_headers=headers,
        table_rows=rows,
        chart_data=chart_data,
        execution_time_ms=elapsed_ms
    )
