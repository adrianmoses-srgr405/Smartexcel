"""
Data Seeder untuk 18 Formula Excel Utama SmartExcel PTPN AI Modeling System.
Mendefinisikan metadata lengkap, kategori, aturan sintaks, use-cases, dan parameter.
"""

FORMULAS_18_DATA = [
    {
        "id": "SUM",
        "formula_name": "SUM",
        "name": "SUM",
        "category": "Aggregation",
        "description": "Menjumlahkan seluruh angka dalam rentang sel tanpa kriteria/kondisi apa pun.",
        "use_case": "Menghitung total keseluruhan omzet, total produksi CPO, atau total biaya operasional.",
        "required_conditions": 0,
        "min_conditions": 0,
        "max_conditions": 0,
        "syntax_template": "=SUM({sum_range})",
        "parameter_definition": {
            "sum_range": "Rentang kolom numerik yang ingin dijumlahkan (misal: D:D atau Table1[Penjualan])"
        },
        "required_parameters": ["sum_range"],
        "compatible_data_types": ["Numeric", "Integer", "Float"],
        "keywords": ["total", "jumlah", "jumlahkan", "penjumlahan", "total keseluruhan", "akumulasi", "seluruh"],
        "priority": 1,
        "examples": [
            {"query": "Hitung total penjualan", "formula": "=SUM(D:D)", "explanation": "Menjumlahkan kolom Penjualan tanpa filter"},
            {"query": "Berapa total produksi CPO?", "formula": "=SUM(C:C)", "explanation": "Menjumlahkan total produksi CPO keseluruhan"}
        ],
        "explanation_template": "SUM dipilih karena query meminta akumulasi/penjumlahan nilai pada kolom target tanpa ada kriteria filter khusus."
    },
    {
        "id": "SUMIF",
        "formula_name": "SUMIF",
        "name": "SUMIF",
        "category": "Conditional Aggregation",
        "description": "Menjumlahkan nilai dalam rentang sel yang memenuhi tepat satu kriteria/kondisi tertentu.",
        "use_case": "Menghitung total penjualan untuk satu sales tertentu atau produksi pada satu afdeling tertentu.",
        "required_conditions": 1,
        "min_conditions": 1,
        "max_conditions": 1,
        "syntax_template": "=SUMIF({criteria_range}, \"{criteria}\", {sum_range})",
        "parameter_definition": {
            "criteria_range": "Rentang kolom yang diuji kondisinya (misal: B:B)",
            "criteria": "Nilai atau teks kriteria yang dicocokkan (misal: \"Andi\")",
            "sum_range": "Rentang kolom numerik yang dijumlahkan (misal: D:D)"
        },
        "required_parameters": ["criteria_range", "criteria", "sum_range"],
        "compatible_data_types": ["Numeric", "Integer", "Float"],
        "keywords": ["total untuk", "jumlahkan jika", "total berdasarkan", "omzet untuk", "penjualan sales", "produksi afdeling"],
        "priority": 2,
        "examples": [
            {"query": "Hitung total penjualan Andi", "formula": "=SUMIF(B:B, \"Andi\", D:D)", "explanation": "Menjumlahkan Penjualan khusus untuk Sales Andi"},
            {"query": "Total produksi TBS untuk Afdeling I", "formula": "=SUMIF(A:A, \"Afdeling I\", C:C)", "explanation": "Menjumlahkan TBS dengan kriteria Afdeling I"}
        ],
        "explanation_template": "SUMIF dipilih karena query meminta penjumlahan nilai dengan tepat satu kondisi filter."
    },
    {
        "id": "SUMIFS",
        "formula_name": "SUMIFS",
        "name": "SUMIFS",
        "category": "Conditional Aggregation",
        "description": "Menjumlahkan nilai dalam rentang sel yang memenuhi dua atau lebih kriteria/kondisi secara bersamaan.",
        "use_case": "Menghitung total penjualan seorang sales pada bulan tertentu atau total produksi kebun tertentu pada tahun tertentu.",
        "required_conditions": 2,
        "min_conditions": 2,
        "max_conditions": 99,
        "syntax_template": "=SUMIFS({sum_range}, {criteria_range1}, \"{criteria1}\", {criteria_range2}, \"{criteria2}\")",
        "parameter_definition": {
            "sum_range": "Rentang kolom numerik yang dijumlahkan (diletakkan di awal)",
            "criteria_range1": "Rentang kriteria pertama",
            "criteria1": "Nilai kriteria pertama",
            "criteria_range2": "Rentang kriteria kedua",
            "criteria2": "Nilai kriteria kedua"
        },
        "required_parameters": ["sum_range", "criteria_range1", "criteria1", "criteria_range2", "criteria2"],
        "compatible_data_types": ["Numeric", "Integer", "Float"],
        "keywords": ["total dan", "pada bulan", "untuk dan", "multi kriteria", "di afdeling tahun", "penjualan sales bulan"],
        "priority": 3,
        "examples": [
            {"query": "Hitung total penjualan Andi bulan Januari", "formula": "=SUMIFS(D:D, B:B, \"Andi\", C:C, \"Januari\")", "explanation": "Menjumlahkan Penjualan dengan 2 kondisi: Sales=Andi dan Bulan=Januari"},
            {"query": "Total produksi CPO Pabrik A tahun 2026", "formula": "=SUMIFS(C:C, A:A, \"Pabrik A\", B:B, \"2026\")", "explanation": "Menjumlahkan CPO dengan kriteria Pabrik dan Tahun"}
        ],
        "explanation_template": "SUMIFS dipilih karena query meminta penjumlahan nilai dengan dua kondisi atau lebih."
    },
    {
        "id": "AVERAGE",
        "formula_name": "AVERAGE",
        "name": "AVERAGE",
        "category": "Statistical",
        "description": "Menghitung nilai rata-rata aritmetika dari seluruh data dalam rentang sel tanpa kriteria.",
        "use_case": "Mengetahui rata-rata penjualan bulanan, rata-rata rendemen OER pabrik, atau rata-rata harga pasar.",
        "required_conditions": 0,
        "min_conditions": 0,
        "max_conditions": 0,
        "syntax_template": "=AVERAGE({range})",
        "parameter_definition": {
            "range": "Rentang kolom numerik yang ingin dihitung nilai rata-ratanya"
        },
        "required_parameters": ["range"],
        "compatible_data_types": ["Numeric", "Integer", "Float"],
        "keywords": ["rata-rata", "mean", "rerata", "rata rata", "average", "nilai tengah rata"],
        "priority": 1,
        "examples": [
            {"query": "Hitung rata-rata penjualan", "formula": "=AVERAGE(D:D)", "explanation": "Menghitung rata-rata nilai kolom penjualan tanpa filter"},
            {"query": "Berapa rata-rata rendemen CPO?", "formula": "=AVERAGE(C:C)", "explanation": "Menghitung rerata rendemen CPO"}
        ],
        "explanation_template": "AVERAGE dipilih karena query meminta nilai rata-rata keseluruhan dari kolom numerik tanpa syarat filter."
    },
    {
        "id": "AVERAGEIF",
        "formula_name": "AVERAGEIF",
        "name": "AVERAGEIF",
        "category": "Statistical",
        "description": "Menghitung nilai rata-rata dari sel-sel yang memenuhi tepat satu kriteria tertentu.",
        "use_case": "Menghitung rata-rata penjualan sales tertentu atau rata-rata FFA pada tangki tertentu.",
        "required_conditions": 1,
        "min_conditions": 1,
        "max_conditions": 1,
        "syntax_template": "=AVERAGEIF({criteria_range}, \"{criteria}\", {average_range})",
        "parameter_definition": {
            "criteria_range": "Rentang kolom kriteria",
            "criteria": "Nilai kriteria pemfilter",
            "average_range": "Rentang kolom numerik yang dirata-ratakan"
        },
        "required_parameters": ["criteria_range", "criteria", "average_range"],
        "compatible_data_types": ["Numeric", "Integer", "Float"],
        "keywords": ["rata-rata untuk", "rerata jika", "rata rata sales", "rata-rata berdasarkan"],
        "priority": 2,
        "examples": [
            {"query": "Hitung rata-rata penjualan Andi", "formula": "=AVERAGEIF(B:B, \"Andi\", D:D)", "explanation": "Menghitung rata-rata penjualan khusus sales Andi"},
            {"query": "Rata-rata OER untuk Kebun Sei Semayang", "formula": "=AVERAGEIF(A:A, \"Sei Semayang\", C:C)", "explanation": "Rata-rata OER kebun terkait"}
        ],
        "explanation_template": "AVERAGEIF dipilih karena query meminta rata-rata dari kolom data dengan tepat satu kondisi filter."
    },
    {
        "id": "AVERAGEIFS",
        "formula_name": "AVERAGEIFS",
        "name": "AVERAGEIFS",
        "category": "Statistical",
        "description": "Menghitung nilai rata-rata dari sel-sel yang memenuhi dua atau lebih kriteria.",
        "use_case": "Menghitung rata-rata penjualan sales tertentu pada bulan tertentu atau rata-rata produksi pada kondisi majemuk.",
        "required_conditions": 2,
        "min_conditions": 2,
        "max_conditions": 99,
        "syntax_template": "=AVERAGEIFS({average_range}, {criteria_range1}, \"{criteria1}\", {criteria_range2}, \"{criteria2}\")",
        "parameter_definition": {
            "average_range": "Rentang numerik yang dirata-ratakan (di awal)",
            "criteria_range1": "Rentang kriteria 1",
            "criteria1": "Nilai kriteria 1",
            "criteria_range2": "Rentang kriteria 2",
            "criteria2": "Nilai kriteria 2"
        },
        "required_parameters": ["average_range", "criteria_range1", "criteria1", "criteria_range2", "criteria2"],
        "compatible_data_types": ["Numeric", "Integer", "Float"],
        "keywords": ["rata-rata sales bulan", "rerata untuk dan", "rata-rata majemuk", "rata rata multi kriteria"],
        "priority": 3,
        "examples": [
            {"query": "Hitung rata-rata penjualan Andi bulan Januari", "formula": "=AVERAGEIFS(D:D, B:B, \"Andi\", C:C, \"Januari\")", "explanation": "Rerata penjualan dengan syarat sales=Andi dan bulan=Januari"}
        ],
        "explanation_template": "AVERAGEIFS dipilih karena query meminta rata-rata dengan dua atau lebih kriteria filter."
    },
    {
        "id": "COUNT",
        "formula_name": "COUNT",
        "name": "COUNT",
        "category": "Counting",
        "description": "Menghitung banyaknya sel yang memuat data numerik / angka.",
        "use_case": "Menghitung banyaknya transaksi numerik, banyaknya pengukuran berat tonase yang tercatat.",
        "required_conditions": 0,
        "min_conditions": 0,
        "max_conditions": 0,
        "syntax_template": "=COUNT({range})",
        "parameter_definition": {
            "range": "Rentang sel numerik yang ingin dihitung frekuensi barisnya"
        },
        "required_parameters": ["range"],
        "compatible_data_types": ["Numeric", "Integer", "Float"],
        "keywords": ["hitung jumlah baris angka", "berapa transaksi numerik", "frekuensi data angka", "banyaknya record nilai"],
        "priority": 1,
        "examples": [
            {"query": "Hitung banyaknya data nilai penjualan", "formula": "=COUNT(D:D)", "explanation": "Menghitung banyaknya baris berisi angka penjualan"}
        ],
        "explanation_template": "COUNT dipilih karena query meminta jumlah baris pada kolom numerik tanpa filter kriteria."
    },
    {
        "id": "COUNTA",
        "formula_name": "COUNTA",
        "name": "COUNTA",
        "category": "Counting",
        "description": "Menghitung banyaknya sel yang tidak kosong (baik berisi teks, angka, maupun kode).",
        "use_case": "Menghitung total karyawan aktif, total nomor tiket timbangan, atau total transaksi tercatat.",
        "required_conditions": 0,
        "min_conditions": 0,
        "max_conditions": 0,
        "syntax_template": "=COUNTA({range})",
        "parameter_definition": {
            "range": "Rentang sel berisi teks atau identifier yang ingin dihitung jumlah baris terisinya"
        },
        "required_parameters": ["range"],
        "compatible_data_types": ["Text", "Categorical", "String", "Date"],
        "keywords": ["berapa banyak baris", "hitung total transaksi", "total karyawan", "jumlah data terisi", "banyaknya record"],
        "priority": 1,
        "examples": [
            {"query": "Hitung jumlah seluruh transaksi", "formula": "=COUNTA(A:A)", "explanation": "Menghitung total baris yang terisi pada kolom Transaksi/ID"}
        ],
        "explanation_template": "COUNTA dipilih karena query meminta perhitungan banyaknya record/baris yang terisi pada kolom teks/identifier."
    },
    {
        "id": "COUNTIF",
        "formula_name": "COUNTIF",
        "name": "COUNTIF",
        "category": "Counting",
        "description": "Menghitung banyaknya sel yang memenuhi tepat satu kriteria tertentu.",
        "use_case": "Menghitung berapa kali sales Andi bertransaksi atau berapa trip pengangkutan TBS dari Afdeling I.",
        "required_conditions": 1,
        "min_conditions": 1,
        "max_conditions": 1,
        "syntax_template": "=COUNTIF({range}, \"{criteria}\")",
        "parameter_definition": {
            "range": "Rentang sel yang dihitung frekuensinya",
            "criteria": "Kriteria nilai yang dicari (misal: \"Andi\")"
        },
        "required_parameters": ["range", "criteria"],
        "compatible_data_types": ["Text", "Categorical", "Numeric", "Date"],
        "keywords": ["berapa jumlah transaksi", "berapa kali", "frekuensi sales", "hitung berapa data", "banyaknya transaksi untuk"],
        "priority": 2,
        "examples": [
            {"query": "Berapa jumlah transaksi Andi?", "formula": "=COUNTIF(B:B, \"Andi\")", "explanation": "Menghitung berapa kali nama Andi muncul dalam kolom Sales"},
            {"query": "Berapa banyak pengiriman dari Kebun A?", "formula": "=COUNTIF(A:A, \"Kebun A\")", "explanation": "Menghitung frekuensi kemunculan Kebun A"}
        ],
        "explanation_template": "COUNTIF dipilih karena query meminta frekuensi/banyaknya data dengan satu kriteria filter."
    },
    {
        "id": "COUNTIFS",
        "formula_name": "COUNTIFS",
        "name": "COUNTIFS",
        "category": "Counting",
        "description": "Menghitung banyaknya sel yang memenuhi dua atau lebih kriteria.",
        "use_case": "Menghitung berapa kali sales Andi bertransaksi di bulan Januari atau jumlah pengiriman TBS matang dari Blok A.",
        "required_conditions": 2,
        "min_conditions": 2,
        "max_conditions": 99,
        "syntax_template": "=COUNTIFS({criteria_range1}, \"{criteria1}\", {criteria_range2}, \"{criteria2}\")",
        "parameter_definition": {
            "criteria_range1": "Rentang kriteria 1",
            "criteria1": "Nilai kriteria 1",
            "criteria_range2": "Rentang kriteria 2",
            "criteria2": "Nilai kriteria 2"
        },
        "required_parameters": ["criteria_range1", "criteria1", "criteria_range2", "criteria2"],
        "compatible_data_types": ["Text", "Categorical", "Numeric", "Date"],
        "keywords": ["berapa transaksi sales di bulan", "frekuensi multi kriteria", "berapa kali untuk dan"],
        "priority": 3,
        "examples": [
            {"query": "Berapa jumlah transaksi Andi di bulan Januari?", "formula": "=COUNTIFS(B:B, \"Andi\", C:C, \"Januari\")", "explanation": "Menghitung baris transaksi dengan syarat Sales=Andi dan Bulan=Januari"}
        ],
        "explanation_template": "COUNTIFS dipilih karena query meminta frekuensi/banyaknya data dengan dua kriteria atau lebih."
    },
    {
        "id": "MAX",
        "formula_name": "MAX",
        "name": "MAX",
        "category": "Statistical",
        "description": "Mencari nilai angka tertinggi / maksimum dalam suatu rentang data numerik.",
        "use_case": "Mengetahui penjualan tertinggi, rekor produksi harian TBS tertinggi, atau suhu rendaman paling tinggi.",
        "required_conditions": 0,
        "min_conditions": 0,
        "max_conditions": 0,
        "syntax_template": "=MAX({range})",
        "parameter_definition": {
            "range": "Rentang kolom numerik"
        },
        "required_parameters": ["range"],
        "compatible_data_types": ["Numeric", "Integer", "Float"],
        "keywords": ["tertinggi", "maksimal", "maksimum", "terbesar", "paling tinggi", "rekor tertinggi", "max"],
        "priority": 1,
        "examples": [
            {"query": "Berapa penjualan tertinggi?", "formula": "=MAX(D:D)", "explanation": "Mencari nilai penjualan terbesar dalam kolom D"}
        ],
        "explanation_template": "MAX dipilih karena query meminta pencarian nilai terbesar/tertinggi dalam kumpulan data."
    },
    {
        "id": "MIN",
        "formula_name": "MIN",
        "name": "MIN",
        "category": "Statistical",
        "description": "Mencari nilai angka terendah / minimum dalam suatu rentang data numerik.",
        "use_case": "Mengetahui penjualan paling sedikit, kadar FFA terendah, atau biaya operasional paling hemat.",
        "required_conditions": 0,
        "min_conditions": 0,
        "max_conditions": 0,
        "syntax_template": "=MIN({range})",
        "parameter_definition": {
            "range": "Rentang kolom numerik"
        },
        "required_parameters": ["range"],
        "compatible_data_types": ["Numeric", "Integer", "Float"],
        "keywords": ["terendah", "minimal", "minimum", "terkecil", "paling rendah", "paling sedikit", "min"],
        "priority": 1,
        "examples": [
            {"query": "Berapa penjualan terendah?", "formula": "=MIN(D:D)", "explanation": "Mencari nilai penjualan terkecil dalam kolom D"}
        ],
        "explanation_template": "MIN dipilih karena query meminta pencarian nilai terkecil/terendah dalam kumpulan data."
    },
    {
        "id": "IF",
        "formula_name": "IF",
        "name": "IF",
        "category": "Logical",
        "description": "Menguji kondisi logika tunggal dan mengembalikan satu nilai jika BENAR, dan nilai lain jika SALAH.",
        "use_case": "Menentukan status bonus karyawan (Jika Penjualan > 100 Juta maka Bonus, jika tidak Tidak Bonus).",
        "required_conditions": 1,
        "min_conditions": 1,
        "max_conditions": 1,
        "syntax_template": "=IF({logical_test}, {value_if_true}, {value_if_false})",
        "parameter_definition": {
            "logical_test": "Ekspresi logika (misal: D2>100000000)",
            "value_if_true": "Nilai jika kondisi terpenuhi (misal: \"Tinggi\")",
            "value_if_false": "Nilai jika kondisi tidak terpenuhi (misal: \"Rendah\")"
        },
        "required_parameters": ["logical_test", "value_if_true", "value_if_false"],
        "compatible_data_types": ["Any"],
        "keywords": ["jika", "apabila", "kalau", "maka", "selain itu", "status capaian", "kategori kondisi"],
        "priority": 2,
        "examples": [
            {"query": "Jika penjualan lebih dari 100 juta maka Tinggi selain itu Rendah", "formula": "=IF(D2>100000000, \"Tinggi\", \"Rendah\")", "explanation": "Memberi label berdasarkan ambang batas 100 juta"}
        ],
        "explanation_template": "IF dipilih karena query menyatakan struktur evaluasi logika tunggal dengan kondisi jika-maka."
    },
    {
        "id": "IFS",
        "formula_name": "IFS",
        "name": "IFS",
        "category": "Logical",
        "description": "Menguji beberapa kondisi logika bertingkat secara berurutan dan mengembalikan nilai dari kondisi pertama yang terpenuhi.",
        "use_case": "Klasifikasi grade mutu CPO bertingkat (Grade A, Grade B, Afkir) atau grading capaian target sales.",
        "required_conditions": 2,
        "min_conditions": 2,
        "max_conditions": 99,
        "syntax_template": "=IFS({test1}, {val1}, {test2}, {val2}, TRUE, {val_default})",
        "parameter_definition": {
            "test1": "Kondisi logika 1",
            "val1": "Nilai jika kondisi 1 benar",
            "test2": "Kondisi logika 2",
            "val2": "Nilai jika kondisi 2 benar",
            "val_default": "Nilai fallback jika seluruh kondisi di atas salah"
        },
        "required_parameters": ["test1", "val1", "test2", "val2"],
        "compatible_data_types": ["Any"],
        "keywords": ["jika bertingkat", "kondisi jamak", "kriteria ganda maka", "grading capaian"],
        "priority": 3,
        "examples": [
            {"query": "Jika penjualan lebih dari 100 juta Tinggi, jika lebih dari 50 juta Sedang, selain itu Rendah", "formula": "=IFS(D2>100000000, \"Tinggi\", D2>50000000, \"Sedang\", TRUE, \"Rendah\")", "explanation": "Pengelompokan tingkatan dengan fungsi IFS"}
        ],
        "explanation_template": "IFS dipilih karena query menyatakan serangkaian pengujian logika bertingkat / multi-kondisi."
    },
    {
        "id": "XLOOKUP",
        "formula_name": "XLOOKUP",
        "name": "XLOOKUP",
        "category": "Lookup",
        "description": "Mencari nilai dalam suatu rentang atau tabel dan mengembalikan nilai yang bersesuaian di kolom lain secara fleksibel (kiri/kanan).",
        "use_case": "Mencari nama pegawai berdasarkan NIP, mencari harga berdasarkan kode barang, atau mencari kebun asal TBS.",
        "required_conditions": 1,
        "min_conditions": 1,
        "max_conditions": 1,
        "syntax_template": "=XLOOKUP(\"{lookup_value}\", {lookup_array}, {return_array}, \"Data Tidak Ditemukan\")",
        "parameter_definition": {
            "lookup_value": "Kunci pencarian yang dicari",
            "lookup_array": "Kolom tempat mencari kunci",
            "return_array": "Kolom tempat mengambil hasil",
            "if_not_found": "Nilai default jika kunci tidak ada"
        },
        "required_parameters": ["lookup_value", "lookup_array", "return_array"],
        "compatible_data_types": ["Any"],
        "keywords": ["cari berdasarkan", "ambil nama berdasarkan", "lookup", "temukan data berdasarkan", "cari harga barang", "xlookup"],
        "priority": 3,
        "examples": [
            {"query": "Cari nama berdasarkan ID", "formula": "=XLOOKUP(\"ID001\", A:A, B:B, \"Tidak Ditemukan\")", "explanation": "Mencari ID di kolom A dan mengambil Nama di kolom B"}
        ],
        "explanation_template": "XLOOKUP dipilih sebagai fungsi pencarian modern yang lebih aman dan fleksibel untuk mengambil data berdasarkan kunci unik."
    },
    {
        "id": "VLOOKUP",
        "formula_name": "VLOOKUP",
        "name": "VLOOKUP",
        "category": "Lookup",
        "description": "Mencari nilai pada kolom paling kiri dari tabel dan mengambil nilai pada nomor kolom tertentu di baris yang sama.",
        "use_case": "Kompatibilitas spreadsheet klasik untuk pencarian tabel kode barang atau master data karyawan.",
        "required_conditions": 1,
        "min_conditions": 1,
        "max_conditions": 1,
        "syntax_template": "=VLOOKUP(\"{lookup_value}\", {table_array}, {col_index_num}, FALSE)",
        "parameter_definition": {
            "lookup_value": "Nilai yang dicari pada kolom pertama",
            "table_array": "Rentang tabel referensi (misal: A:D)",
            "col_index_num": "Nomor indeks kolom hasil (1-based)",
            "range_lookup": "FALSE untuk pencarian eksak"
        },
        "required_parameters": ["lookup_value", "table_array", "col_index_num"],
        "compatible_data_types": ["Any"],
        "keywords": ["vlookup", "cari vertikal", "tabel referensi kolom", "cari di tabel"],
        "priority": 2,
        "examples": [
            {"query": "Cari data menggunakan VLOOKUP", "formula": "=VLOOKUP(\"KD01\", A:D, 2, FALSE)", "explanation": "Mengambil kolom kedua dari tabel berdasarkan kode"}
        ],
        "explanation_template": "VLOOKUP digunakan untuk pencarian nilai referensi vertikal berbasis indeks kolom."
    },
    {
        "id": "INDEX",
        "formula_name": "INDEX",
        "name": "INDEX",
        "category": "Lookup",
        "description": "Mengembalikan nilai dari suatu sel dalam rentang tabel berdasarkan nomor baris dan kolom yang ditentukan.",
        "use_case": "Kombinasi dinamis bersama fungsi MATCH untuk pencarian dua dimensi (baris x kolom).",
        "required_conditions": 1,
        "min_conditions": 1,
        "max_conditions": 2,
        "syntax_template": "=INDEX({array}, {row_num}, [{col_num}])",
        "parameter_definition": {
            "array": "Rentang sel sumber",
            "row_num": "Nomor baris yang diambil",
            "col_num": "Nomor kolom yang diambil (opsional)"
        },
        "required_parameters": ["array", "row_num"],
        "compatible_data_types": ["Any"],
        "keywords": ["index", "ambil sel baris", "indeks baris kolom", "pencarian dua dimensi"],
        "priority": 2,
        "examples": [
            {"query": "Ambil data baris ke 5 kolom ke 2", "formula": "=INDEX(A1:D100, 5, 2)", "explanation": "Mengambil nilai pada koordinat baris 5 kolom 2"}
        ],
        "explanation_template": "INDEX dipilih untuk mereferensikan sel spesifik berdasarkan nomor baris dan kolom."
    },
    {
        "id": "MATCH",
        "formula_name": "MATCH",
        "name": "MATCH",
        "category": "Lookup",
        "description": "Mencari posisi relatif suatu nilai dalam suatu rentang sel (mengembalikan nomor urut baris/kolom).",
        "use_case": "Menemukan letak baris suatu kode akun atau letak kolom bulan untuk dipasangkan dengan INDEX.",
        "required_conditions": 1,
        "min_conditions": 1,
        "max_conditions": 1,
        "syntax_template": "=MATCH(\"{lookup_value}\", {lookup_array}, 0)",
        "parameter_definition": {
            "lookup_value": "Nilai yang dicari posisinya",
            "lookup_array": "Rentang 1 dimensi (vektor baris atau kolom)",
            "match_type": "0 untuk pencarian posisi eksak"
        },
        "required_parameters": ["lookup_value", "lookup_array"],
        "compatible_data_types": ["Any"],
        "keywords": ["match", "posisi baris", "nomor urut", "pada baris ke berapa", "urutan ke berapa"],
        "priority": 2,
        "examples": [
            {"query": "Pada baris ke berapa kode PKS01 berada?", "formula": "=MATCH(\"PKS01\", A:A, 0)", "explanation": "Mencari posisi nomor baris kode PKS01"}
        ],
        "explanation_template": "MATCH dipilih untuk mengidentifikasi indeks atau nomor baris relatif dari suatu kunci pencarian."
    }
]
