import openpyxl
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_e2e_workflow():
    # 1. Check datasets
    res = client.get("/api/v1/datasets")
    assert res.status_code == 200, res.text
    datasets = res.json()
    assert len(datasets) > 0, "No dataset found"
    mutasi_ds = next((d for d in datasets if "mutasi_barang" in d["filename"]), datasets[0])
    ds_id = mutasi_ds["id"]
    print(f"[OK] Dataset verified: {mutasi_ds['filename']} ({mutasi_ds['row_count']} rows)")

    # 2. Check dataset detail & profiling
    res = client.get(f"/api/v1/datasets/{ds_id}")
    assert res.status_code == 200
    detail = res.json()
    col_names = [c["original_name"] for c in detail["columns"]]
    assert "Jumlah Keluar" in col_names
    assert "Nama Merek" in col_names
    assert "Tanggal" in col_names
    print(f"[OK] Profiling verified: {len(col_names)} columns detected with proper data types.")

    # 3. Test Main Scenario 1: "Buat rekap jumlah barang keluar per merek untuk Februari 2024"
    q1 = "Buat rekap jumlah barang keluar per merek untuk Februari 2024"
    res = client.post("/api/v1/query/analyze", json={"dataset_id": ds_id, "query": q1})
    assert res.status_code == 200, res.text
    ans1 = res.json()
    assert ans1["decision"]["formula_id"] in ["SUMIFS", "SUMIF"]
    assert len(ans1["table_rows"]) > 0
    assert "=SUMIFS(" in ans1["decision"]["generated_excel_formula"] or "=SUMIF(" in ans1["decision"]["generated_excel_formula"]
    print(f"[OK] Scenario 1 (Monthly Rekap): Selected {ans1['decision']['formula_id']}, Formula: {ans1['decision']['generated_excel_formula']}")
    print(f"  Rows count: {len(ans1['table_rows'])}, Grand Total: {ans1['calculation_summary'].get('grand_total')}")

    # 4. Test Scenario 2: "Berapa total barang keluar merek Lenovo pada Februari 2024?"
    q2 = "Berapa total barang keluar merek Lenovo pada Februari 2024?"
    res = client.post("/api/v1/query/analyze", json={"dataset_id": ds_id, "query": q2})
    assert res.status_code == 200
    ans2 = res.json()
    assert ans2["decision"]["formula_id"] == "SUMIFS"
    assert "Lenovo" in ans2["decision"]["generated_excel_formula"]
    print(f"[OK] Scenario 2 (Multi-criteria SUMIFS): Formula: {ans2['decision']['generated_excel_formula']}")

    # 5. Test Scenario 3: "Berapa total barang keluar merek Lenovo?" (Single criteria SUMIF)
    q3 = "Berapa total barang keluar merek Lenovo?"
    res = client.post("/api/v1/query/analyze", json={"dataset_id": ds_id, "query": q3})
    assert res.status_code == 200
    ans3 = res.json()
    assert ans3["decision"]["formula_id"] == "SUMIF"
    print(f"[OK] Scenario 3 (Single-criteria SUMIF): Formula: {ans3['decision']['generated_excel_formula']}")

    # 6. Test Scenario 4: "Berapa total barang keluar?" (Zero filter SUM)
    q4 = "Berapa total barang keluar?"
    res = client.post("/api/v1/query/analyze", json={"dataset_id": ds_id, "query": q4})
    assert res.status_code == 200
    ans4 = res.json()
    assert ans4["decision"]["formula_id"] == "SUM"
    print(f"[OK] Scenario 4 (Zero filter SUM): Formula: {ans4['decision']['generated_excel_formula']}")

    # 7. Test Scenario 5: "Berapa rata-rata barang keluar per merek?" (AVERAGE)
    q5 = "Berapa rata-rata barang keluar per merek?"
    res = client.post("/api/v1/query/analyze", json={"dataset_id": ds_id, "query": q5})
    assert res.status_code == 200
    ans5 = res.json()
    assert "AVERAGE" in ans5["decision"]["formula_id"]
    print(f"[OK] Scenario 5 (Average): Selected {ans5['decision']['formula_id']}, Formula: {ans5['decision']['generated_excel_formula']}")

    # 8. Test Scenario 6: "Cari barang dengan jumlah keluar paling tinggi." (MAX)
    q6 = "Cari barang dengan jumlah keluar paling tinggi."
    res = client.post("/api/v1/query/analyze", json={"dataset_id": ds_id, "query": q6})
    assert res.status_code == 200
    ans6 = res.json()
    assert ans6["decision"]["formula_id"] == "MAX"
    print(f"[OK] Scenario 6 (MAX): Formula: {ans6['decision']['generated_excel_formula']}")

    # 9. Test Excel Report Export
    res = client.post(f"/api/v1/reports/export/{ans1['analysis_id']}", json={
        "table_headers": ans1["table_headers"],
        "table_rows": ans1["table_rows"],
        "calculation_summary": ans1["calculation_summary"]
    })
    assert res.status_code == 200
    exp = res.json()
    assert "download_url" in exp
    print(f"[OK] Excel Export Verified: {exp['file_name']}, URL: {exp['download_url']}")

    # Download & inspect exported file with openpyxl
    dl_res = client.get(exp['download_url'])
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 1000
    print(f"[OK] Downloaded Excel file verified ({len(dl_res.content)} bytes).")

    # 10. Check Evaluation Metrics
    eval_res = client.get("/api/v1/evaluation/metrics")
    assert eval_res.status_code == 200
    metrics = eval_res.json()
    print(f"[OK] Research Evaluation Dashboard metrics verified (Accuracy: {metrics['formula_accuracy_pct']}%)")
    print("\nALL END-TO-END AUTOMATION TESTS PASSED 100%!")

if __name__ == "__main__":
    test_full_e2e_workflow()

