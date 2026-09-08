import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_pks_cpo_queries():
    res = requests.get(f"{BASE_URL}/datasets")
    assert res.status_code == 200
    datasets = res.json()
    pks_ds = next((d for d in datasets if "pks_cpo" in d["filename"]), datasets[0])
    ds_id = pks_ds["id"]
    print(f"[OK] Testing PKS CPO Dataset: {pks_ds['filename']} ({pks_ds['row_count']} rows, {pks_ds['column_count']} cols)")

    # 1. Test Tutup Buku: "Buat rekap produksi CPO per asal kebun untuk Februari 2024"
    q1 = "Buat rekap produksi CPO per asal kebun untuk Februari 2024"
    res1 = requests.post(f"{BASE_URL}/query/analyze", json={"dataset_id": ds_id, "query": q1})
    assert res1.status_code == 200, res1.text
    ans1 = res1.json()
    print(f"[OK] PKS Tutup Buku Rekap per Kebun: Formula = {ans1['decision']['generated_excel_formula']}")
    print(f"     Target Field: {ans1['parsed_intent']['target_field']}, Group By: {ans1['parsed_intent']['group_by']}")
    print(f"     Rows: {len(ans1['table_rows'])}, Grand Total CPO: {ans1['calculation_summary'].get('grand_total'):,} Kg")

    # 2. Test Rendemen Average: "Berapa rata-rata rendemen CPO per asal kebun?"
    q2 = "Berapa rata-rata rendemen CPO per asal kebun?"
    res2 = requests.post(f"{BASE_URL}/query/analyze", json={"dataset_id": ds_id, "query": q2})
    assert res2.status_code == 200
    ans2 = res2.json()
    print(f"[OK] Rata-rata Rendemen OER per Kebun: Formula = {ans2['decision']['generated_excel_formula']}")

    # 3. Test Quality Mutu ALB: "Berapa rata-rata kadar ALB per asal kebun?"
    q3 = "Berapa rata-rata kadar ALB per asal kebun?"
    res3 = requests.post(f"{BASE_URL}/query/analyze", json={"dataset_id": ds_id, "query": q3})
    assert res3.status_code == 200
    ans3 = res3.json()
    print(f"[OK] Monitoring Mutu ALB/FFA: Formula = {ans3['decision']['generated_excel_formula']}")

    # 4. Test Single Kebun: "Berapa total produksi CPO Kebun Tandun pada Februari 2024?"
    q4 = "Berapa total produksi CPO Kebun Tandun pada Februari 2024?"
    res4 = requests.post(f"{BASE_URL}/query/analyze", json={"dataset_id": ds_id, "query": q4})
    assert res4.status_code == 200
    ans4 = res4.json()
    print(f"[OK] Total Produksi CPO Kebun Tandun: Formula = {ans4['decision']['generated_excel_formula']}")

    print("\nALL PKS CPO PRODUCTION AUTOMATION TESTS PASSED 100%!")

if __name__ == "__main__":
    test_pks_cpo_queries()
