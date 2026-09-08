import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_uploaded_multisheet_excel():
    upload_files = list(Path("storage/uploads").glob("*.xlsx")) or list(Path("../storage/uploads").glob("*.xlsx"))
    upload_file = upload_files[0]
    print(f"Uploading file: {upload_file.name}")
    
    with open(upload_file, "rb") as f:
        res = requests.post(f"{BASE_URL}/datasets/upload", files={"file": (upload_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    
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
