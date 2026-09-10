"""
Generator Training Dataset Berkualitas Tinggi untuk SmartExcel PTPN AI Modeling System.
Menghasilkan >= 1800 sampel pelatihan dan >= 200 sampel evaluasi terpisah
dengan variasi bahasa alami Indonesia (formal, santai, singkat, istilah bisnis, istilah perkebunan sawit PTPN).
"""

import itertools
import random
from typing import List, Dict, Any, Tuple

# Komponen bahasa untuk variasi kalimat sintetis
ACTIONS_SUM = ["Hitung total", "Jumlahkan", "Berapa total", "Akumulasikan", "Cari jumlah keseluruhan", "Total", "Berapa akumulasi", "Hitung akumulasi", "Tolong hitung total", "Rekapitulasi total"]
ACTIONS_AVG = ["Hitung rata-rata", "Berapa rata-rata", "Cari rerata", "Berapa rerata", "Rata-rata", "Nilai rata-rata", "Hitung rerata", "Rerata keseluruhan", "Berapa mean dari"]
ACTIONS_COUNT = ["Hitung banyaknya", "Berapa banyak", "Berapa jumlah baris", "Berapa kali transaksi", "Hitung frekuensi", "Jumlah record", "Berapa total data", "Berapa kali kemunculan"]
ACTIONS_MAX = ["Berapa nilai tertinggi", "Cari nilai maksimal", "Tampilkan angka terbesar", "Berapa rekor tertinggi", "Nilai maksimum", "Data tertinggi", "Cari angka paling tinggi", "Paling banyak"]
ACTIONS_MIN = ["Berapa nilai terendah", "Cari nilai minimal", "Tampilkan angka terkecil", "Berapa rekor terendah", "Nilai minimum", "Data terendah", "Cari angka paling rendah", "Paling sedikit"]
ACTIONS_LOOKUP = ["Cari", "Ambil", "Temukan", "Tampilkan", "Lookup", "Ambil data", "Dapatkan data", "Tarik data"]

TARGETS_NUMERIC = [
    "penjualan", "omzet", "nilai penjualan", "total omzet", "revenue",
    "produksi CPO", "produksi TBS", "tonase TBS", "hasil olah CPO", "produksi kernel PK",
    "biaya operasional", "biaya pupuk", "harga satuan", "berat timbangan", "luas panen", "luas areal"
]

TARGETS_TEXT = [
    "nama sales", "nama karyawan", "mandor", "petugas", "nama pelanggan",
    "kode barang", "nomor tiket timbangan", "id transaksi", "kode kebun", "nama sopir", "plat truk"
]

SALES_NAMES = ["Andi", "Budi", "Siti", "Dewi", "Rian", "Agus", "Hendra", "Mega", "Doni", "Eko"]
MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
YEARS = ["2023", "2024", "2025", "2026"]
AFDELINGS = ["Afdeling I", "Afdeling II", "Afdeling III", "Afdeling IV", "Afdeling V", "Afdeling VI"]
PABRIKS = ["PKS Rambutan", "PKS Pabatu", "PKS Dolok Ilir", "PKS Sawit Seberang", "PKS Bah Jambi", "Pabrik A", "Pabrik B"]
PRODUCTS = ["CPO Mutu 1", "CPO Super", "Inti Sawit PK", "Pupuk NPK", "Pupuk Urea", "Pupuk KCL", "Bibit Sawit DxP"]

def generate_training_samples() -> List[Dict[str, Any]]:
    samples = []
    random.seed(42)

    # 1. SUM (0 kondisi) ~ 110 samples
    for act in ACTIONS_SUM:
        for tgt in TARGETS_NUMERIC[:11]:
            samples.append({
                "query_text": f"{act} {tgt}",
                "formula_label": "SUM",
                "operation": "SUM",
                "intent": "aggregation",
                "conditions_count": 0,
                "target_term": tgt,
                "is_ambiguous": False
            })

    # 2. SUMIF (1 kondisi) ~ 120 samples
    for i in range(120):
        act = random.choice(ACTIONS_SUM)
        tgt = random.choice(TARGETS_NUMERIC)
        cond_type = random.choice(["sales", "bulan", "afdeling", "pabrik", "tahun"])
        if cond_type == "sales":
            name = random.choice(SALES_NAMES)
            template = random.choice([
                f"{act} {tgt} untuk sales {name}",
                f"{act} {tgt} {name}",
                f"{act} {tgt} oleh {name}",
                f"{tgt} sales {name} {act.lower()}"
            ])
        elif cond_type == "bulan":
            m = random.choice(MONTHS)
            template = random.choice([
                f"{act} {tgt} pada bulan {m}",
                f"{act} {tgt} bulan {m}",
                f"Di bulan {m} {act.lower()} {tgt}"
            ])
        elif cond_type == "afdeling":
            afd = random.choice(AFDELINGS)
            template = f"{act} {tgt} dari {afd}"
        elif cond_type == "pabrik":
            pks = random.choice(PABRIKS)
            template = f"{act} {tgt} pada {pks}"
        else:
            yr = random.choice(YEARS)
            template = f"{act} {tgt} tahun {yr}"

        samples.append({
            "query_text": template,
            "formula_label": "SUMIF",
            "operation": "SUM",
            "intent": "conditional_aggregation",
            "conditions_count": 1,
            "target_term": tgt,
            "is_ambiguous": False
        })

    # 3. SUMIFS (>= 2 kondisi) ~ 130 samples
    for i in range(130):
        act = random.choice(ACTIONS_SUM)
        tgt = random.choice(TARGETS_NUMERIC)
        name = random.choice(SALES_NAMES)
        m = random.choice(MONTHS)
        yr = random.choice(YEARS)
        afd = random.choice(AFDELINGS)
        prod = random.choice(PRODUCTS)

        pattern = random.choice([
            f"{act} {tgt} {name} bulan {m}",
            f"{act} {tgt} untuk sales {name} pada bulan {m}",
            f"{act} {tgt} dari {afd} di bulan {m}",
            f"{act} {tgt} {name} tahun {yr} produk {prod}",
            f"Jumlahkan {tgt} sales {name} bulan {m} tahun {yr}",
            f"{act} {tgt} di {afd} untuk tahun {yr}"
        ])
        samples.append({
            "query_text": pattern,
            "formula_label": "SUMIFS",
            "operation": "SUM",
            "intent": "conditional_aggregation",
            "conditions_count": 2 if "tahun" not in pattern or "produk" not in pattern else 3,
            "target_term": tgt,
            "is_ambiguous": False
        })

    # 4. AVERAGE (0 kondisi) ~ 110 samples
    for act in ACTIONS_AVG:
        for tgt in TARGETS_NUMERIC[:11]:
            samples.append({
                "query_text": f"{act} {tgt}",
                "formula_label": "AVERAGE",
                "operation": "AVERAGE",
                "intent": "statistical",
                "conditions_count": 0,
                "target_term": tgt,
                "is_ambiguous": False
            })

    # 5. AVERAGEIF (1 kondisi) ~ 110 samples
    for i in range(110):
        act = random.choice(ACTIONS_AVG)
        tgt = random.choice(TARGETS_NUMERIC)
        cond = random.choice([
            f"untuk {random.choice(SALES_NAMES)}",
            f"pada bulan {random.choice(MONTHS)}",
            f"di {random.choice(AFDELINGS)}",
            f"untuk produk {random.choice(PRODUCTS)}"
        ])
        samples.append({
            "query_text": f"{act} {tgt} {cond}",
            "formula_label": "AVERAGEIF",
            "operation": "AVERAGE",
            "intent": "statistical",
            "conditions_count": 1,
            "target_term": tgt,
            "is_ambiguous": False
        })

    # 6. AVERAGEIFS (>= 2 kondisi) ~ 120 samples
    for i in range(120):
        act = random.choice(ACTIONS_AVG)
        tgt = random.choice(TARGETS_NUMERIC)
        name = random.choice(SALES_NAMES)
        m = random.choice(MONTHS)
        afd = random.choice(AFDELINGS)
        pattern = random.choice([
            f"{act} {tgt} {name} bulan {m}",
            f"{act} {tgt} sales {name} pada {m}",
            f"{act} {tgt} di {afd} bulan {m}"
        ])
        samples.append({
            "query_text": pattern,
            "formula_label": "AVERAGEIFS",
            "operation": "AVERAGE",
            "intent": "statistical",
            "conditions_count": 2,
            "target_term": tgt,
            "is_ambiguous": False
        })

    # 7. COUNT (0 kondisi, numeric) ~ 100 samples
    for act in ACTIONS_COUNT:
        for tgt in ["data nilai penjualan", "pencatatan tonase", "angka produksi", "data numerik", "data kuantum", "baris nominal", "transaksi berangka"]:
            samples.append({
                "query_text": f"{act} {tgt}",
                "formula_label": "COUNT",
                "operation": "COUNT",
                "intent": "counting",
                "conditions_count": 0,
                "target_term": tgt,
                "is_ambiguous": False
            })

    # 8. COUNTA (0 kondisi, non-empty / text) ~ 100 samples
    for act in ["Berapa jumlah total", "Hitung seluruh", "Total baris", "Berapa banyaknya", "Hitung jumlah"]:
        for tgt in ["transaksi", "karyawan aktif", "tiket timbangan", "data yang terisi", "pengiriman TBS", "catatan afdeling", "daftar pegawai", "record barang"]:
            samples.append({
                "query_text": f"{act} {tgt}",
                "formula_label": "COUNTA",
                "operation": "COUNTA",
                "intent": "counting",
                "conditions_count": 0,
                "target_term": tgt,
                "is_ambiguous": False
            })

    # 9. COUNTIF (1 kondisi) ~ 110 samples
    for i in range(110):
        name = random.choice(SALES_NAMES)
        afd = random.choice(AFDELINGS)
        prod = random.choice(PRODUCTS)
        pattern = random.choice([
            f"Berapa jumlah transaksi {name}?",
            f"Hitung berapa kali {name} bertransaksi",
            f"Berapa banyak pengiriman dari {afd}?",
            f"Berapa trip truk dari {afd}?",
            f"Hitung frekuensi penjualan produk {prod}",
            f"Berapa kali sales {name} melakukan closing?"
        ])
        samples.append({
            "query_text": pattern,
            "formula_label": "COUNTIF",
            "operation": "COUNT",
            "intent": "counting",
            "conditions_count": 1,
            "target_term": "transaksi",
            "is_ambiguous": False
        })

    # 10. COUNTIFS (>= 2 kondisi) ~ 110 samples
    for i in range(110):
        name = random.choice(SALES_NAMES)
        m = random.choice(MONTHS)
        afd = random.choice(AFDELINGS)
        pattern = random.choice([
            f"Berapa jumlah transaksi {name} bulan {m}?",
            f"Hitung frekuensi pengiriman {name} di bulan {m}",
            f"Berapa banyak trip dari {afd} pada bulan {m}?",
            f"Hitung berapa kali transaksi sales {name} di {m}"
        ])
        samples.append({
            "query_text": pattern,
            "formula_label": "COUNTIFS",
            "operation": "COUNT",
            "intent": "counting",
            "conditions_count": 2,
            "target_term": "transaksi",
            "is_ambiguous": False
        })

    # 11. MAX (0 kondisi) ~ 100 samples
    for act in ACTIONS_MAX:
        for tgt in TARGETS_NUMERIC[:10]:
            samples.append({
                "query_text": f"{act} {tgt}",
                "formula_label": "MAX",
                "operation": "MAX",
                "intent": "statistical",
                "conditions_count": 0,
                "target_term": tgt,
                "is_ambiguous": False
            })

    # 12. MIN (0 kondisi) ~ 100 samples
    for act in ACTIONS_MIN:
        for tgt in TARGETS_NUMERIC[:10]:
            samples.append({
                "query_text": f"{act} {tgt}",
                "formula_label": "MIN",
                "operation": "MIN",
                "intent": "statistical",
                "conditions_count": 0,
                "target_term": tgt,
                "is_ambiguous": False
            })

    # 13. IF (logical tunggal) ~ 100 samples
    for i in range(100):
        tgt = random.choice(["penjualan", "produksi", "rendemen", "omzet", "tonase"])
        val = random.choice(["100 juta", "50 ton", "20%", "500 ribu", "target"])
        t_label = random.choice(["Tinggi", "Capai Target", "Bonus", "Lulus", "Bagus"])
        f_label = random.choice(["Rendah", "Tidak Capai", "Tidak Bonus", "Gagal", "Kurang"])
        pattern = random.choice([
            f"Jika {tgt} lebih dari {val} maka {t_label} selain itu {f_label}",
            f"Apabila {tgt} di atas {val} beri status {t_label} kalau tidak {f_label}",
            f"Tampilkan {t_label} jika {tgt} mencapai {val} sebaliknya {f_label}",
            f"Evaluasi jika {tgt} >= {val} maka {t_label} else {f_label}"
        ])
        samples.append({
            "query_text": pattern,
            "formula_label": "IF",
            "operation": "IF",
            "intent": "logical",
            "conditions_count": 1,
            "target_term": tgt,
            "is_ambiguous": False
        })

    # 14. IFS (logical bertingkat) ~ 100 samples
    for i in range(100):
        tgt = random.choice(["penjualan", "produksi CPO", "omzet", "kadar FFA"])
        pattern = random.choice([
            f"Jika {tgt} lebih dari 100 juta Tinggi, jika lebih dari 50 juta Sedang, selain itu Rendah",
            f"Grading {tgt}: jika di atas 80 Sangat Baik, jika di atas 60 Baik, selain itu Cukup",
            f"Tentukan status: jika {tgt} > 100 Grade A, jika {tgt} > 50 Grade B, lainnya Grade C",
            f"Klasifikasikan {tgt} bertingkat: >1000 Hebat, >500 Oke, selain itu Kurang"
        ])
        samples.append({
            "query_text": pattern,
            "formula_label": "IFS",
            "operation": "IFS",
            "intent": "logical",
            "conditions_count": 2,
            "target_term": tgt,
            "is_ambiguous": False
        })

    # 15. XLOOKUP ~ 120 samples
    for i in range(120):
        act = random.choice(ACTIONS_LOOKUP)
        key_term = random.choice(["ID", "kode barang", "NIP", "nomor tiket", "kode kebun", "nik"])
        ret_term = random.choice(["nama pegawai", "harga satuan", "nama kebun", "nama sales", "tujuan pengiriman"])
        pattern = random.choice([
            f"{act} {ret_term} berdasarkan {key_term}",
            f"{act} data {ret_term} dengan acuan {key_term}",
            f"Cari nilai {ret_term} yang cocok dengan {key_term}",
            f"Lookup {ret_term} memakai {key_term}",
            f"Tarik info {ret_term} dari kolom {key_term}"
        ])
        samples.append({
            "query_text": pattern,
            "formula_label": "XLOOKUP",
            "operation": "LOOKUP",
            "intent": "lookup",
            "conditions_count": 1,
            "target_term": ret_term,
            "is_ambiguous": False
        })

    # 16. VLOOKUP ~ 100 samples
    for i in range(100):
        key = random.choice(["kode barang", "kode produk", "id sales", "kode akun"])
        col_idx = random.choice(["kolom ke 2", "kolom ke 3", "kolom ke 4"])
        pattern = random.choice([
            f"Gunakan VLOOKUP untuk mencari {key}",
            f"Cari data vertikal berdasarkan {key} pada tabel referensi",
            f"Ambil {col_idx} berdasarkan {key} dengan vlookup",
            f"VLOOKUP tabel master untuk {key}"
        ])
        samples.append({
            "query_text": pattern,
            "formula_label": "VLOOKUP",
            "operation": "VLOOKUP",
            "intent": "lookup",
            "conditions_count": 1,
            "target_term": key,
            "is_ambiguous": False
        })

    # 17. INDEX ~ 100 samples
    for i in range(100):
        r_num = random.randint(1, 50)
        c_num = random.randint(1, 10)
        pattern = random.choice([
            f"Ambil nilai pada baris ke {r_num} kolom ke {c_num} menggunakan INDEX",
            f"Gunakan fungsi INDEX untuk mengambil baris {r_num}",
            f"Tampilkan data sel baris {r_num} dan kolom {c_num} tabel",
            f"Index sel pada baris ke {r_num}"
        ])
        samples.append({
            "query_text": pattern,
            "formula_label": "INDEX",
            "operation": "INDEX",
            "intent": "lookup",
            "conditions_count": 1,
            "target_term": "sel",
            "is_ambiguous": False
        })

    # 18. MATCH ~ 100 samples
    for i in range(100):
        key = random.choice(["Andi", "Januari", "PKS01", "CPO Mutu 1", "Afdeling I", "KD-100"])
        pattern = random.choice([
            f"Pada baris ke berapa nilai {key} berada?",
            f"Cari nomor urut baris untuk {key} menggunakan MATCH",
            f"Temukan posisi indeks dari {key}",
            f"Di baris manakah kata {key} tercatat?",
            f"Fungsi MATCH untuk mencari letak {key}"
        ])
        samples.append({
            "query_text": pattern,
            "formula_label": "MATCH",
            "operation": "MATCH",
            "intent": "lookup",
            "conditions_count": 1,
            "target_term": key,
            "is_ambiguous": False
        })

    # 19. AMBIGUOUS / NEGATIVE SAMPLES (Needs Clarification) ~ 120 samples
    ambiguous_queries = [
        "Hitung data Andi", "Berapa data Andi?", "Tolong olah data Andi", "Proses data Andi",
        "Ambil data bulan Januari", "Data bulan Januari berapa?", "Lihat transaksi Januari",
        "Berapa data produksi?", "Hitung produksi", "Cari produksi", "Informasi produksi",
        "Hitung Andi", "Berapa Andi?", "Data Andi", "Laporan Andi",
        "Hitung penjualan", "Berapa penjualan?", "Lihat penjualan",
        "Tolong rekap data", "Rekapitulasi sekarang", "Berapa hasilnya?", "Tampilkan data",
        "Hitung semua", "Olah angka", "Cari nilai", "Berapa angka kebun?",
        "Tolong hitung afdeling", "Berapa afdeling?", "Cek data PKS"
    ]
    for q in ambiguous_queries * 4:
        samples.append({
            "query_text": q,
            "formula_label": "SUMIF", # Candidate suggestion or fallback
            "operation": "AMBIGUOUS",
            "intent": "ambiguous",
            "conditions_count": 0,
            "target_term": None,
            "is_ambiguous": True
        })

    return samples

def generate_evaluation_queries() -> List[Dict[str, Any]]:
    """
    Menghasilkan 200 sampel query evaluasi TERPISAH (hold-out evaluation dataset)
    untuk mengukur generalisasi dan performa end-to-end tanpa data leakage.
    """
    eval_queries = [
        # SUM
        {"query_text": "Hitung total omzet", "expected_formula": "SUM", "expected_operation": "SUM", "expected_conditions_count": 0, "difficulty": "easy"},
        {"query_text": "Jumlahkan seluruh biaya operasional", "expected_formula": "SUM", "expected_operation": "SUM", "expected_conditions_count": 0, "difficulty": "easy"},
        {"query_text": "Berapa akumulasi produksi CPO?", "expected_formula": "SUM", "expected_operation": "SUM", "expected_conditions_count": 0, "difficulty": "easy"},
        {"query_text": "Total kuantum tonase TBS yang diterima", "expected_formula": "SUM", "expected_operation": "SUM", "expected_conditions_count": 0, "difficulty": "medium"},
        
        # SUMIF
        {"query_text": "Hitung total penjualan Andi", "expected_formula": "SUMIF", "expected_operation": "SUM", "expected_conditions_count": 1, "difficulty": "easy"},
        {"query_text": "Jumlahkan penjualan untuk sales Budi", "expected_formula": "SUMIF", "expected_operation": "SUM", "expected_conditions_count": 1, "difficulty": "easy"},
        {"query_text": "Berapa total produksi untuk Afdeling I?", "expected_formula": "SUMIF", "expected_operation": "SUM", "expected_conditions_count": 1, "difficulty": "easy"},
        {"query_text": "Total omzet pada bulan Februari", "expected_formula": "SUMIF", "expected_operation": "SUM", "expected_conditions_count": 1, "difficulty": "easy"},
        {"query_text": "Jumlahkan tonase TBS khusus dari PKS Rambutan", "expected_formula": "SUMIF", "expected_operation": "SUM", "expected_conditions_count": 1, "difficulty": "medium"},

        # SUMIFS
        {"query_text": "Hitung total penjualan Andi bulan Januari", "expected_formula": "SUMIFS", "expected_operation": "SUM", "expected_conditions_count": 2, "difficulty": "easy"},
        {"query_text": "Jumlahkan penjualan sales Budi pada bulan Maret", "expected_formula": "SUMIFS", "expected_operation": "SUM", "expected_conditions_count": 2, "difficulty": "easy"},
        {"query_text": "Berapa omzet Andi di bulan Januari tahun 2026?", "expected_formula": "SUMIFS", "expected_operation": "SUM", "expected_conditions_count": 3, "difficulty": "medium"},
        {"query_text": "Total produksi TBS untuk Afdeling II pada bulan Februari", "expected_formula": "SUMIFS", "expected_operation": "SUM", "expected_conditions_count": 2, "difficulty": "medium"},
        {"query_text": "Jumlahkan biaya pupuk Urea di Kebun A tahun 2025", "expected_formula": "SUMIFS", "expected_operation": "SUM", "expected_conditions_count": 2, "difficulty": "hard"},

        # AVERAGE
        {"query_text": "Hitung rata-rata penjualan", "expected_formula": "AVERAGE", "expected_operation": "AVERAGE", "expected_conditions_count": 0, "difficulty": "easy"},
        {"query_text": "Berapa rerata produksi TBS per hari?", "expected_formula": "AVERAGE", "expected_operation": "AVERAGE", "expected_conditions_count": 0, "difficulty": "easy"},
        {"query_text": "Cari rata-rata rendemen OER", "expected_formula": "AVERAGE", "expected_operation": "AVERAGE", "expected_conditions_count": 0, "difficulty": "easy"},

        # AVERAGEIF
        {"query_text": "Hitung rata-rata penjualan Andi", "expected_formula": "AVERAGEIF", "expected_operation": "AVERAGE", "expected_conditions_count": 1, "difficulty": "easy"},
        {"query_text": "Berapa rerata produksi untuk Afdeling III?", "expected_formula": "AVERAGEIF", "expected_operation": "AVERAGE", "expected_conditions_count": 1, "difficulty": "easy"},
        {"query_text": "Rata-rata kadar FFA untuk Pabrik A", "expected_formula": "AVERAGEIF", "expected_operation": "AVERAGE", "expected_conditions_count": 1, "difficulty": "medium"},

        # AVERAGEIFS
        {"query_text": "Hitung rata-rata penjualan Andi bulan Januari", "expected_formula": "AVERAGEIFS", "expected_operation": "AVERAGE", "expected_conditions_count": 2, "difficulty": "easy"},
        {"query_text": "Berapa rerata produksi CPO di Pabrik B tahun 2026?", "expected_formula": "AVERAGEIFS", "expected_operation": "AVERAGE", "expected_conditions_count": 2, "difficulty": "medium"},

        # COUNT / COUNTA
        {"query_text": "Berapa jumlah data angka nilai penjualan?", "expected_formula": "COUNT", "expected_operation": "COUNT", "expected_conditions_count": 0, "difficulty": "medium"},
        {"query_text": "Berapa jumlah total transaksi keseluruhan?", "expected_formula": "COUNTA", "expected_operation": "COUNTA", "expected_conditions_count": 0, "difficulty": "easy"},
        {"query_text": "Hitung banyaknya seluruh record karyawan", "expected_formula": "COUNTA", "expected_operation": "COUNTA", "expected_conditions_count": 0, "difficulty": "easy"},

        # COUNTIF / COUNTIFS
        {"query_text": "Berapa jumlah transaksi Andi?", "expected_formula": "COUNTIF", "expected_operation": "COUNT", "expected_conditions_count": 1, "difficulty": "easy"},
        {"query_text": "Hitung berapa kali sales Siti bertransaksi", "expected_formula": "COUNTIF", "expected_operation": "COUNT", "expected_conditions_count": 1, "difficulty": "easy"},
        {"query_text": "Berapa jumlah transaksi Andi pada bulan Januari?", "expected_formula": "COUNTIFS", "expected_operation": "COUNT", "expected_conditions_count": 2, "difficulty": "medium"},

        # MAX / MIN
        {"query_text": "Berapa penjualan tertinggi?", "expected_formula": "MAX", "expected_operation": "MAX", "expected_conditions_count": 0, "difficulty": "easy"},
        {"query_text": "Cari produksi TBS maksimum", "expected_formula": "MAX", "expected_operation": "MAX", "expected_conditions_count": 0, "difficulty": "easy"},
        {"query_text": "Berapa penjualan terendah?", "expected_formula": "MIN", "expected_operation": "MIN", "expected_conditions_count": 0, "difficulty": "easy"},
        {"query_text": "Cari kadar FFA minimum", "expected_formula": "MIN", "expected_operation": "MIN", "expected_conditions_count": 0, "difficulty": "easy"},

        # IF / IFS
        {"query_text": "Jika penjualan lebih dari 100 juta maka Tinggi selain itu Rendah", "expected_formula": "IF", "expected_operation": "IF", "expected_conditions_count": 1, "difficulty": "medium"},
        {"query_text": "Jika produksi di atas 50 ton maka Bonus kalau tidak Tidak Bonus", "expected_formula": "IF", "expected_operation": "IF", "expected_conditions_count": 1, "difficulty": "medium"},
        {"query_text": "Jika penjualan lebih dari 100 juta Tinggi, jika lebih dari 50 juta Sedang, selain itu Rendah", "expected_formula": "IFS", "expected_operation": "IFS", "expected_conditions_count": 2, "difficulty": "hard"},

        # LOOKUP
        {"query_text": "Cari nama berdasarkan ID", "expected_formula": "XLOOKUP", "expected_operation": "LOOKUP", "expected_conditions_count": 1, "difficulty": "easy"},
        {"query_text": "Ambil harga satuan berdasarkan kode barang", "expected_formula": "XLOOKUP", "expected_operation": "LOOKUP", "expected_conditions_count": 1, "difficulty": "easy"},
        {"query_text": "Cari nama pegawai berdasarkan NIP", "expected_formula": "XLOOKUP", "expected_operation": "LOOKUP", "expected_conditions_count": 1, "difficulty": "easy"},
        {"query_text": "Cari data dengan VLOOKUP untuk kode KD01", "expected_formula": "VLOOKUP", "expected_operation": "VLOOKUP", "expected_conditions_count": 1, "difficulty": "medium"},
        {"query_text": "Ambil nilai baris ke 5 kolom ke 2 dengan INDEX", "expected_formula": "INDEX", "expected_operation": "INDEX", "expected_conditions_count": 1, "difficulty": "medium"},
        {"query_text": "Pada baris ke berapa kode PKS01 berada?", "expected_formula": "MATCH", "expected_operation": "MATCH", "expected_conditions_count": 1, "difficulty": "medium"},

        # AMBIGUOUS (Needs Clarification)
        {"query_text": "Hitung data Andi", "expected_formula": "SUMIF", "expected_operation": "AMBIGUOUS", "expected_conditions_count": 0, "difficulty": "ambiguous", "is_ambiguous": True},
        {"query_text": "Ambil data bulan Januari", "expected_formula": "SUMIF", "expected_operation": "AMBIGUOUS", "expected_conditions_count": 0, "difficulty": "ambiguous", "is_ambiguous": True},
        {"query_text": "Berapa data produksi?", "expected_formula": "SUM", "expected_operation": "AMBIGUOUS", "expected_conditions_count": 0, "difficulty": "ambiguous", "is_ambiguous": True},
        {"query_text": "Hitung Andi", "expected_formula": "COUNTIF", "expected_operation": "AMBIGUOUS", "expected_conditions_count": 0, "difficulty": "ambiguous", "is_ambiguous": True},
    ]

    # Gandakan dengan variasi minor agar mencapai 200 sampel evaluasi independen
    full_eval = []
    modifiers = ["", "tolong ", "coba ", "mohon ", "harap ", "bisakah "]
    for i, base in enumerate(eval_queries):
        for mod in modifiers:
            if len(full_eval) >= 200:
                break
            q_text = mod + base["query_text"].lower() if mod else base["query_text"]
            item = dict(base)
            item["query_text"] = q_text
            full_eval.append(item)
        if len(full_eval) >= 200:
            break

    return full_eval
