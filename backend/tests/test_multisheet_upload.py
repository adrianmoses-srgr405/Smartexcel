from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_uploaded_multisheet_excel():
    possible_dirs = [Path("storage/uploads"), Path("../storage/uploads")]
    upload_files = []
    for d in possible_dirs:
        if d.exists():
            upload_files.extend(list(d.glob("*.xlsx")))
    
    priority_files = [f for f in upload_files if "Penjualan_Mobil" in f.name]
    assert len(priority_files) > 0 or len(upload_files) > 0, "No sample upload file found"
    upload_file = priority_files[0] if priority_files else upload_files[0]
    print(f"Uploading file: {upload_file.name}")
    
    with open(upload_file, "rb") as f:
        res = client.post(
            "/api/v1/datasets/upload",
            files={"file": (upload_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    
    assert res.status_code == 200, res.text
    data = res.json()
    print(f"[OK] Auto-selected Sheet: '{data['selected_sheet']}'")
    print(f"[OK] Available Sheets in file: {data['available_sheets']}")
    print(f"[OK] Row count: {data['row_count']}, Column count: {data['column_count']}")
    print(f"[OK] Columns: {[c['original_name'] for c in data['columns'][:6]]}")
    assert data['row_count'] == 1000, f"Expected 1000 rows in Data_Penjualan, got {data['row_count']}"
    assert data['column_count'] == 24, f"Expected 24 columns in Data_Penjualan, got {data['column_count']}"
    print("\nSUCCESS: Multi-sheet intelligent detection worked perfectly!")

if __name__ == "__main__":
    test_uploaded_multisheet_excel()

