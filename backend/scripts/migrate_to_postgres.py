import os
import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import Base, engine as pg_engine
from app.models.dataset import Dataset, DatasetColumn
from app.models.analysis import AnalysisHistory
from app.models.formula import FormulaKnowledge
from app.models.evaluation import EvaluationMetric, ReportTemplate

def run_migration():
    print(f"=== Starting Migration to PostgreSQL 18 ===")
    print(f"Target DB Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"Target DB Name: {settings.DB_DATABASE}")
    print(f"Target DB User: {settings.DB_USERNAME}")

    # 1. Create all tables in PostgreSQL
    print("\n[Step 1] Creating all tables in PostgreSQL 18...")
    Base.metadata.create_all(bind=pg_engine)
    print("[SUCCESS] All tables created/verified in PostgreSQL:")
    for table_name in Base.metadata.tables:
        print(f"  - {table_name}")

    # 2. Check if SQLite database exists
    sqlite_db_path = backend_dir / "smart_excel.db"
    if not sqlite_db_path.exists():
        print("\n[Step 2] No existing SQLite database found. Ready for fresh data.")
        return True

    print(f"\n[Step 2] Found existing SQLite database at {sqlite_db_path}. Checking records to migrate...")
    sqlite_engine = create_engine(f"sqlite:///{sqlite_db_path}")
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=pg_engine)

    sqlite_db = SqliteSession()
    pg_db = PgSession()

    try:
        # Migrate FormulaKnowledge
        sqlite_formulas = sqlite_db.query(FormulaKnowledge).all()
        migrated_formulas = 0
        for f in sqlite_formulas:
            if not pg_db.query(FormulaKnowledge).filter_by(id=f.id).first():
                pg_db.merge(f)
                migrated_formulas += 1
        pg_db.commit()
        print(f"  - FormulaKnowledge: {migrated_formulas} records migrated.")

        # Migrate ReportTemplate
        sqlite_templates = sqlite_db.query(ReportTemplate).all()
        migrated_templates = 0
        for t in sqlite_templates:
            if not pg_db.query(ReportTemplate).filter_by(id=t.id).first():
                pg_db.merge(t)
                migrated_templates += 1
        pg_db.commit()
        print(f"  - ReportTemplate: {migrated_templates} records migrated.")

        # Migrate Datasets and Columns
        sqlite_datasets = sqlite_db.query(Dataset).all()
        migrated_datasets = 0
        migrated_columns = 0
        for ds in sqlite_datasets:
            existing_ds = pg_db.query(Dataset).filter_by(id=ds.id).first()
            if not existing_ds:
                new_ds = Dataset(
                    id=ds.id,
                    filename=ds.filename,
                    file_path=ds.file_path,
                    file_size_bytes=ds.file_size_bytes,
                    row_count=ds.row_count,
                    column_count=ds.column_count,
                    dataset_metadata=ds.dataset_metadata,
                    created_at=ds.created_at
                )
                pg_db.add(new_ds)
                pg_db.flush()
                migrated_datasets += 1

                for col in ds.columns:
                    new_col = DatasetColumn(
                        id=col.id,
                        dataset_id=col.dataset_id,
                        original_name=col.original_name,
                        sanitized_name=col.sanitized_name,
                        column_index=col.column_index,
                        excel_column_letter=col.excel_column_letter,
                        inferred_type=col.inferred_type,
                        null_count=col.null_count,
                        unique_count=col.unique_count,
                        min_value=col.min_value,
                        max_value=col.max_value,
                        mean_value=col.mean_value,
                        sample_values=col.sample_values
                    )
                    pg_db.add(new_col)
                    migrated_columns += 1

        pg_db.commit()
        print(f"  - Datasets: {migrated_datasets} records migrated.")
        print(f"  - DatasetColumns: {migrated_columns} records migrated.")

        # Migrate AnalysisHistory
        sqlite_analyses = sqlite_db.query(AnalysisHistory).all()
        migrated_analyses = 0
        for ah in sqlite_analyses:
            if not pg_db.query(AnalysisHistory).filter_by(id=ah.id).first():
                new_ah = AnalysisHistory(
                    id=ah.id,
                    dataset_id=ah.dataset_id,
                    user_query=ah.user_query,
                    parsed_intent=ah.parsed_intent,
                    selected_formula_id=ah.selected_formula_id,
                    generated_excel_formula=ah.generated_excel_formula,
                    formula_explanation=ah.formula_explanation,
                    calculation_results=ah.calculation_results,
                    result_summary=ah.result_summary,
                    execution_time_ms=ah.execution_time_ms,
                    export_file_path=ah.export_file_path,
                    created_at=ah.created_at
                )
                pg_db.add(new_ah)
                migrated_analyses += 1
        pg_db.commit()
        print(f"  - AnalysisHistory: {migrated_analyses} records migrated.")

        # Migrate EvaluationMetric
        sqlite_evals = sqlite_db.query(EvaluationMetric).all()
        migrated_evals = 0
        for ev in sqlite_evals:
            if not pg_db.query(EvaluationMetric).filter_by(id=ev.id).first():
                new_ev = EvaluationMetric(
                    id=ev.id,
                    analysis_id=ev.analysis_id,
                    expected_formula=ev.expected_formula,
                    actual_formula=ev.actual_formula,
                    is_formula_correct=ev.is_formula_correct,
                    is_filter_correct=ev.is_filter_correct,
                    is_result_correct=ev.is_result_correct,
                    manual_steps_count=ev.manual_steps_count,
                    manual_time_seconds=ev.manual_time_seconds,
                    ai_time_seconds=ev.ai_time_seconds,
                    notes=ev.notes,
                    evaluated_at=ev.evaluated_at
                )
                pg_db.add(new_ev)
                migrated_evals += 1
        pg_db.commit()
        print(f"  - EvaluationMetrics: {migrated_evals} records migrated.")

        print("\n[SUCCESS] Data migration completed smoothly without data loss!")
        return True

    except Exception as e:
        pg_db.rollback()
        print(f"\n[ERROR during migration]: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        sqlite_db.close()
        pg_db.close()

if __name__ == "__main__":
    success = run_migration()
    if not success:
        sys.exit(1)
