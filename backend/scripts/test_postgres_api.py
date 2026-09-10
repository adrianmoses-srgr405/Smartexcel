import sys
import io
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.core.config import settings

def test_api_with_postgresql():
    print("=== Testing FastAPI Endpoints directly connected to PostgreSQL 18 ===")
    print(f"Connected DB: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")

    client = TestClient(app)

    # 1. Test Root
    res = client.get("/")
    assert res.status_code == 200, res.text
    print(f"[PASS] GET / -> {res.json()}")

    # 2. Test Get Datasets from PostgreSQL
    res = client.get(f"{settings.API_V1_STR}/datasets")
    assert res.status_code == 200, res.text
    datasets = res.json()
    print(f"[PASS] GET /api/v1/datasets -> Found {len(datasets)} datasets in PostgreSQL.")
    for ds in datasets[:3]:
        print(f"       - ID: {ds['id'][:8]}... | File: {ds['filename']} | Rows: {ds['row_count']} | Cols: {ds['column_count']}")

    # 3. Test Upload Excel to PostgreSQL
    # Create sample in-memory Excel file
    sample_df = pd.DataFrame({
        "Tanggal": pd.date_range("2026-01-01", periods=10, freq="D").strftime("%Y-%m-%d"),
        "Divisi": ["PKS Unit 1", "PKS Unit 2"] * 5,
        "Produksi_CPO_Ton": [120.5, 140.2, 115.0, 155.8, 130.4, 125.1, 142.3, 118.9, 134.7, 150.0],
        "FFA_Persen": [3.2, 3.5, 3.1, 3.8, 3.4, 3.3, 3.6, 3.2, 3.5, 3.7]
    })
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        sample_df.to_excel(writer, sheet_name="Produksi_Harian", index=False)
    excel_buffer.seek(0)

    res = client.post(
        f"{settings.API_V1_STR}/datasets/upload",
        files={"file": ("test_ptpn_pg18.xlsx", excel_buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert res.status_code == 200, res.text
    uploaded_data = res.json()
    dataset_id = uploaded_data["id"]
    print(f"[PASS] POST /api/v1/datasets/upload -> Uploaded & Profiled in PostgreSQL!")
    print(f"       - New Dataset ID: {dataset_id}")
    print(f"       - Row count: {uploaded_data['row_count']}, Column count: {uploaded_data['column_count']}")

    # 4. Test Query Endpoint on the newly uploaded dataset
    query_payload = {
        "dataset_id": dataset_id,
        "query": "Berapa total Produksi_CPO_Ton untuk Divisi PKS Unit 1?"
    }
    res = client.post(f"{settings.API_V1_STR}/query/analyze", json=query_payload)
    assert res.status_code == 200, res.text
    query_result = res.json()
    print(f"[PASS] POST /api/v1/query/analyze -> Formula: {query_result.get('generated_excel_formula')}")
    print(f"       - Result Summary: {query_result.get('result_summary')}")
    print(f"       - Execution Time: {query_result.get('execution_time_ms')} ms")


    # 5. Test Evaluation Metrics in PostgreSQL
    res = client.get(f"{settings.API_V1_STR}/evaluation/metrics")
    assert res.status_code == 200, res.text
    eval_metrics = res.json()
    print(f"[PASS] GET /api/v1/evaluation/metrics -> Status 200 OK")

    # 6. Clean up the test dataset from PostgreSQL
    res = client.delete(f"{settings.API_V1_STR}/datasets/{dataset_id}")
    assert res.status_code == 200, res.text
    print(f"[PASS] DELETE /api/v1/datasets/{dataset_id} -> Deleted cleanly from PostgreSQL.")

    print("\n=== ALL FASTAPI & POSTGRESQL 18 INTEGRATION TESTS PASSED 100%! ===")
    return True

if __name__ == "__main__":
    success = test_api_with_postgresql()
    if not success:
        sys.exit(1)
