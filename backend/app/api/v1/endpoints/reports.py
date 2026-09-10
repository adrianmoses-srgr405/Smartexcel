from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.analysis import AnalysisHistory
from app.models.dataset import Dataset
from app.services.report_service import ReportService
from app.services.profiler_service import ProfilerService

router = APIRouter()

@router.post("/export/{analysis_id}")
def export_analysis(
    analysis_id: str,
    payload: dict = Body(default={}),
    db: Session = Depends(get_db)
):
    """
    Generate and export formatted Excel workbook with active native formulas.
    Processes the entire raw dataset (all rows, e.g. 1,000 rows) into a tiered report.
    """
    analysis = db.query(AnalysisHistory).filter(AnalysisHistory.id == analysis_id).first()
    raw_df = None
    dataset_sheet_name = None

    # Single Source of Truth (Rules 2, 3, 11):
    # If table_rows is provided by frontend, do NOT reload raw_df from disk.
    table_rows_input = payload.get("table_rows") or []
    if not table_rows_input:
        if analysis and analysis.dataset:
            ds = analysis.dataset
            fpath = Path(ds.file_path)
            if fpath.exists():
                dataset_sheet_name = (ds.dataset_metadata or {}).get("selected_sheet")
                try:
                    raw_df, _, _ = ProfilerService.load_dataset_file(fpath, sheet_name=dataset_sheet_name)
                except Exception:
                    pass
        elif payload.get("dataset_id"):
            ds = db.query(Dataset).filter(Dataset.id == payload.get("dataset_id")).first()
            if ds:
                fpath = Path(ds.file_path)
                if fpath.exists():
                    dataset_sheet_name = (ds.dataset_metadata or {}).get("selected_sheet")
                    try:
                        raw_df, _, _ = ProfilerService.load_dataset_file(fpath, sheet_name=dataset_sheet_name)
                    except Exception:
                        pass

    if analysis:
        tasks = payload.get("tasks") or (analysis.parsed_intent.get("tasks", []) if isinstance(analysis.parsed_intent, dict) else [])
        calc_summary = payload.get("calculation_summary") or (analysis.calculation_results.get("summary", {}) if isinstance(analysis.calculation_results, dict) else {})
        f_plan = payload.get("formula_plan") or calc_summary.get("formula_plan")
        grp_by = payload.get("group_by") or (analysis.parsed_intent.get("group_by") if isinstance(analysis.parsed_intent, dict) else [])

        export_payload = {
            "user_query": payload.get("user_query") or analysis.user_query,
            "formula_id": payload.get("formula_id") or analysis.selected_formula_id,
            "formula_name": payload.get("formula_name") or analysis.selected_formula_id,
            "generated_excel_formula": payload.get("generated_excel_formula") or analysis.generated_excel_formula,
            "formula_explanation": payload.get("formula_explanation") or analysis.formula_explanation,
            "tasks": tasks,
            "table_headers": payload.get("table_headers") or (analysis.calculation_results.get("headers", []) if isinstance(analysis.calculation_results, dict) else []),
            "table_rows": payload.get("table_rows") or [],
            "calculation_summary": calc_summary,
            "formula_plan": f_plan,
            "group_by": grp_by,
            "raw_df": raw_df,
            "sheet_name": dataset_sheet_name
        }
    else:
        # Resilient fallback: build report directly from frontend payload if data is provided
        table_headers = payload.get("table_headers", [])
        table_rows = payload.get("table_rows", [])
        user_query = payload.get("user_query") or "Analisis Data Excel"
        formula_id = payload.get("formula_id") or payload.get("formula_name") or "FILTER"
        gen_formula = payload.get("generated_excel_formula") or "-"

        if not table_headers and not table_rows and gen_formula == "-" and raw_df is None:
            raise HTTPException(status_code=404, detail="Riwayat analisis tidak ditemukan")

        calc_summary = payload.get("calculation_summary") or {}
        export_payload = {
            "user_query": user_query,
            "formula_id": formula_id,
            "formula_name": payload.get("formula_name") or formula_id,
            "generated_excel_formula": gen_formula,
            "formula_explanation": payload.get("formula_explanation") or "Dihasilkan secara otomatis oleh Smart Excel AI",
            "tasks": payload.get("tasks") or [],
            "table_headers": table_headers,
            "table_rows": table_rows,
            "calculation_summary": calc_summary,
            "formula_plan": payload.get("formula_plan") or calc_summary.get("formula_plan"),
            "group_by": payload.get("group_by") or [],
            "raw_df": raw_df,
            "sheet_name": dataset_sheet_name
        }

    user_q = export_payload.get("user_query", "").lower()
    prefix = "Laporan_Penjualan_Mobil" if any(w in user_q for w in ["mobil", "toyota", "avanza", "honda", "sales", "tipe"]) else "Laporan_PTPN"
    export_path = ReportService.export_analysis_to_excel(export_payload, filename_prefix=prefix)
    if analysis:
        analysis.export_file_path = str(export_path)
        try:
            db.commit()
        except Exception:
            db.rollback()

    return {
        "message": "Laporan Excel berhasil di-generate",
        "file_name": export_path.name,
        "download_url": f"/api/v1/reports/download/{export_path.name}"
    }

@router.get("/download/{filename}")
def download_report_file(filename: str):
    """Download exported Excel file."""
    file_path = settings.EXPORT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File laporan tidak ditemukan di storage")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
