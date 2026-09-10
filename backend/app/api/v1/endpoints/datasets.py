import gc
import shutil
import uuid
from pathlib import Path

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.dataset import Dataset, DatasetColumn
from app.schemas.dataset import DatasetCreateResponse, DatasetListItem, DatasetDetailResponse, ColumnProfilingSchema, DatasetProfilingSummary
from app.services.profiler_service import ProfilerService

router = APIRouter()

@router.post("/upload", response_model=DatasetCreateResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload Excel/CSV file, save to storage, profile columns & infer data types.
    """
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".xlsx", ".xls", ".csv"]:
        raise HTTPException(
            status_code=400,
            detail=f"Format file '{file_ext}' tidak didukung. Harap upload .xlsx, .xls, atau .csv"
        )

    # Save to upload dir
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = settings.UPLOAD_DIR / unique_filename
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run Profiling with Intelligent Sheet Selection
    try:
        df, selected_sheet, available_sheets = ProfilerService.load_dataset_file(save_path)
        summary, columns_profile, preview_data = ProfilerService.profile_dataframe(df)
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Gagal memproses file Excel: {str(e)}")

    file_size = save_path.stat().st_size

    # Persist in Database
    dataset = Dataset(
        filename=file.filename,
        file_path=str(save_path),
        file_size_bytes=file_size,
        row_count=summary["total_rows"],
        column_count=summary["total_columns"],
        dataset_metadata={
            **summary,
            "selected_sheet": selected_sheet,
            "available_sheets": available_sheets
        }
    )
    db.add(dataset)
    db.flush()

    for col in columns_profile:
        col_entity = DatasetColumn(
            dataset_id=dataset.id,
            original_name=col["original_name"],
            sanitized_name=col["sanitized_name"],
            column_index=col["column_index"],
            excel_column_letter=col["excel_column_letter"],
            inferred_type=col["inferred_type"],
            null_count=col["null_count"],
            unique_count=col["unique_count"],
            min_value=col["min_value"],
            max_value=col["max_value"],
            mean_value=col["mean_value"],
            sample_values=col["sample_values"]
        )
        db.add(col_entity)

    db.commit()
    db.refresh(dataset)

    # Transform to response schema
    columns_schema = [ColumnProfilingSchema(**c) for c in columns_profile]
    profiling_summary = DatasetProfilingSummary(
        total_rows=summary["total_rows"],
        total_columns=summary["total_columns"],
        numeric_columns=summary["numeric_columns"],
        date_columns=summary["date_columns"],
        categorical_columns=summary["categorical_columns"],
        text_columns=summary["text_columns"],
        columns=columns_schema
    )

    return DatasetCreateResponse(
        id=dataset.id,
        filename=dataset.filename,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        file_size_bytes=dataset.file_size_bytes,
        selected_sheet=selected_sheet,
        available_sheets=available_sheets,
        columns=columns_schema,
        profiling=profiling_summary,
        preview_data=preview_data,
        created_at=dataset.created_at
    )

@router.get("", response_model=list[DatasetListItem])
def list_datasets(db: Session = Depends(get_db)):
    """List all uploaded datasets."""
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    results = []
    for d in datasets:
        sheet = (d.dataset_metadata or {}).get("selected_sheet")
        results.append(DatasetListItem(
            id=d.id,
            filename=d.filename,
            row_count=d.row_count,
            column_count=d.column_count,
            file_size_bytes=d.file_size_bytes,
            selected_sheet=sheet,
            created_at=d.created_at
        ))
    return results

@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset_detail(dataset_id: str, db: Session = Depends(get_db)):
    """Get dataset detail with columns and first 50 rows preview."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset tidak ditemukan")

    file_path = Path(dataset.file_path)
    preview_data = []
    selected_sheet = (dataset.dataset_metadata or {}).get("selected_sheet")
    available_sheets = (dataset.dataset_metadata or {}).get("available_sheets", [])

    if file_path.exists():
        df, s_sheet, a_sheets = ProfilerService.load_dataset_file(
            file_path,
            sheet_name=selected_sheet,
            known_sheets=available_sheets
        )
        preview_data = ProfilerService.extract_preview_data(df, limit=1000)
        if not selected_sheet:
            selected_sheet = s_sheet
        if not available_sheets:
            available_sheets = a_sheets

    columns_schema = [
        ColumnProfilingSchema(
            id=col.id,
            original_name=col.original_name,
            sanitized_name=col.sanitized_name,
            column_index=col.column_index,
            excel_column_letter=col.excel_column_letter,
            inferred_type=col.inferred_type,
            null_count=col.null_count,
            unique_count=col.unique_count,
            null_percentage=round((col.null_count / max(dataset.row_count, 1)) * 100, 2),
            unique_percentage=round((col.unique_count / max(dataset.row_count, 1)) * 100, 2),
            min_value=col.min_value,
            max_value=col.max_value,
            mean_value=col.mean_value,
            sample_values=col.sample_values or []
        )
        for col in dataset.columns
    ]

    return DatasetDetailResponse(
        id=dataset.id,
        filename=dataset.filename,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        file_size_bytes=dataset.file_size_bytes,
        selected_sheet=selected_sheet,
        available_sheets=available_sheets,
        created_at=dataset.created_at,
        columns=columns_schema,
        preview_data=preview_data
    )

@router.post("/{dataset_id}/switch-sheet", response_model=DatasetDetailResponse)
def switch_dataset_sheet(
    dataset_id: str,
    payload: dict,
    db: Session = Depends(get_db)
):
    """Switch active sheet in multi-sheet Excel file and re-profile."""
    sheet_name = payload.get("sheet_name")
    if not sheet_name:
        raise HTTPException(status_code=400, detail="sheet_name wajib disertakan")

    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset tidak ditemukan")

    file_path = Path(dataset.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File fisik tidak ditemukan")

    df, selected_sheet, available_sheets = ProfilerService.load_dataset_file(file_path, sheet_name=sheet_name)
    summary, columns_profile, preview_data = ProfilerService.profile_dataframe(df)

    # Update Dataset metadata
    dataset.row_count = summary["total_rows"]
    dataset.column_count = summary["total_columns"]
    dataset.dataset_metadata = {
        **summary,
        "selected_sheet": selected_sheet,
        "available_sheets": available_sheets
    }

    # Remove old columns and insert new sheet columns
    db.query(DatasetColumn).filter(DatasetColumn.dataset_id == dataset.id).delete()
    db.flush()

    for col in columns_profile:
        col_entity = DatasetColumn(
            dataset_id=dataset.id,
            original_name=col["original_name"],
            sanitized_name=col["sanitized_name"],
            column_index=col["column_index"],
            excel_column_letter=col["excel_column_letter"],
            inferred_type=col["inferred_type"],
            null_count=col["null_count"],
            unique_count=col["unique_count"],
            min_value=col["min_value"],
            max_value=col["max_value"],
            mean_value=col["mean_value"],
            sample_values=col["sample_values"]
        )
        db.add(col_entity)

    db.commit()
    db.refresh(dataset)

    columns_schema = [ColumnProfilingSchema(**c) for c in columns_profile]
    return DatasetDetailResponse(
        id=dataset.id,
        filename=dataset.filename,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        file_size_bytes=dataset.file_size_bytes,
        selected_sheet=selected_sheet,
        available_sheets=available_sheets,
        created_at=dataset.created_at,
        columns=columns_schema,
        preview_data=preview_data
    )

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Delete dataset and its associated file."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset tidak ditemukan")

    file_path = Path(dataset.file_path)
    try:
        file_path.unlink(missing_ok=True)
    except Exception:
        gc.collect()
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass


    db.delete(dataset)
    db.commit()
    return {"message": "Dataset berhasil dihapus"}

