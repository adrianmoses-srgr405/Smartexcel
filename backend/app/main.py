import pandas as pd
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.api.v1.router import api_router
from app.models.dataset import Dataset, DatasetColumn
from app.services.profiler_service import ProfilerService

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Automatic Excel Formula & Report Modeling System for PTPN",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def seed_sample_ptpn_dataset():
    """Seeds the specialized PKS CPO Production dataset automatically on first startup."""
    db = SessionLocal()
    try:
        from app.knowledge.pks_dataset_generator import generate_pks_cpo_dataset

        # Check if PKS dataset already exists
        existing_pks = db.query(Dataset).filter(Dataset.filename.like("%pks_cpo%")).first()
        if not existing_pks:
            df = generate_pks_cpo_dataset()
            sample_file_path = settings.SAMPLE_DIR / "sample_ptpn_pks_cpo_produksi.xlsx"
            df.to_excel(sample_file_path, index=False)

            summary, columns_profile, _ = ProfilerService.profile_dataframe(df)

            dataset = Dataset(
                filename="sample_ptpn_pks_cpo_produksi.xlsx",
                file_path=str(sample_file_path),
                file_size_bytes=sample_file_path.stat().st_size,
                row_count=summary["total_rows"],
                column_count=summary["total_columns"],
                dataset_metadata=summary
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
            print("[Startup] Seeded PKS CPO Production dataset successfully.")
    except Exception as e:
        print(f"[Startup] Error seeding PKS dataset: {e}")
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "active",
        "docs": "/docs"
    }
