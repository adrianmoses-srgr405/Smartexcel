import sys
import uuid
from pathlib import Path
from datetime import datetime

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, engine
from app.models.dataset import Dataset, DatasetColumn
from app.models.analysis import AnalysisHistory
from app.models.formula import FormulaKnowledge
from app.models.evaluation import EvaluationMetric, ReportTemplate

def test_postgresql_crud():
    print("=== Testing PostgreSQL 18 CRUD Operations ===")
    db = SessionLocal()
    test_ds_id = str(uuid.uuid4())
    test_col_id = str(uuid.uuid4())
    test_ah_id = str(uuid.uuid4())

    try:
        # 1. Test INSERT
        print("\n1. Testing INSERT...")
        new_ds = Dataset(
            id=test_ds_id,
            filename="test_postgres_migration.xlsx",
            file_path="storage/uploads/test_postgres_migration.xlsx",
            file_size_bytes=1024,
            row_count=50,
            column_count=2,
            dataset_metadata={"origin": "PostgreSQL 18 Integration Test"}
        )
        db.add(new_ds)

        new_col = DatasetColumn(
            id=test_col_id,
            dataset_id=test_ds_id,
            original_name="Produksi_Ton",
            sanitized_name="produksi_ton",
            column_index=0,
            excel_column_letter="A",
            inferred_type="Numeric",
            sample_values=[10.5, 20.0, 35.2]
        )
        db.add(new_col)
        db.commit()
        print("   [PASS] Inserted Dataset and DatasetColumn successfully.")

        # 2. Test SELECT
        print("\n2. Testing SELECT...")
        fetched_ds = db.query(Dataset).filter_by(id=test_ds_id).first()
        assert fetched_ds is not None, "Dataset not found in DB!"
        assert fetched_ds.filename == "test_postgres_migration.xlsx"
        assert len(fetched_ds.columns) == 1
        assert fetched_ds.columns[0].original_name == "Produksi_Ton"
        print(f"   [PASS] Retrieved Dataset: {fetched_ds.filename} with column {fetched_ds.columns[0].original_name}")

        # 3. Test UPDATE
        print("\n3. Testing UPDATE...")
        fetched_ds.row_count = 100
        fetched_ds.dataset_metadata = {"origin": "Updated Metadata", "status": "verified"}
        db.commit()

        updated_ds = db.query(Dataset).filter_by(id=test_ds_id).first()
        assert updated_ds.row_count == 100
        assert updated_ds.dataset_metadata.get("status") == "verified"
        print(f"   [PASS] Updated Dataset: row_count={updated_ds.row_count}, metadata status={updated_ds.dataset_metadata['status']}")

        # 4. Test DELETE
        print("\n4. Testing DELETE (Cascade)...")
        db.delete(updated_ds)
        db.commit()

        check_ds = db.query(Dataset).filter_by(id=test_ds_id).first()
        check_col = db.query(DatasetColumn).filter_by(id=test_col_id).first()
        assert check_ds is None, "Dataset should have been deleted!"
        assert check_col is None, "Associated DatasetColumn should have been cascade deleted!"
        print("   [PASS] Deleted Dataset and verified cascade deletion on columns.")

        print("\n=== ALL CRUD TESTS PASSED ON POSTGRESQL 18! ===")
        return True

    except Exception as e:
        db.rollback()
        print(f"\n[FAIL] CRUD test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_postgresql_crud()
    if not success:
        sys.exit(1)
