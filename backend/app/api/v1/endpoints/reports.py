from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.analysis import AnalysisHistory
from app.services.report_service import ReportService

router = APIRouter()

@router.post("/export/{analysis_id}")
def export_analysis(
    analysis_id: str,
    payload: dict = Body(default={}),
    db: Session = Depends(get_db)
):
    """
    Generate and export formatted Excel workbook with active native formulas.
    """
    analysis = db.query(AnalysisHistory).filter(AnalysisHistory.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Riwayat analisis tidak ditemukan")

    # Combine analysis fields
    export_payload = {
        "user_query": analysis.user_query,
        "formula_id": analysis.selected_formula_id,
        "formula_name": analysis.selected_formula_id,
        "generated_excel_formula": analysis.generated_excel_formula,
        "formula_explanation": analysis.formula_explanation,
        "table_headers": payload.get("table_headers") or analysis.calculation_results.get("headers", []),
        "table_rows": payload.get("table_rows") or [],
        "calculation_summary": payload.get("calculation_summary") or analysis.calculation_results.get("summary", {})
    }

    export_path = ReportService.export_analysis_to_excel(export_payload, filename_prefix="Laporan_PTPN")
    analysis.export_file_path = str(export_path)
    db.commit()

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
