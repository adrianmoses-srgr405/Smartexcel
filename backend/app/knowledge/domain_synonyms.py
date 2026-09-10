"""
Kamus Sinonim Domain Bisnis & Perkebunan Kelapa Sawit (PTPN).
Digunakan oleh Column Resolver dan Parameter Extractor untuk mencocokkan
terminologi pengguna dalam bahasa alami ke kolom dataset aktual secara akurat.
"""

# Pemetaan sinonim istilah ke canonical term / konsep kolom
DOMAIN_SYNONYMS = {
    # Penjualan / Revenue / Otomotif
    "omzet": ["penjualan", "total penjualan", "pendapatan", "revenue", "sales", "nilai penjualan", "total omzet"],
    "penjualan": ["omzet", "sales", "total penjualan", "jumlah terjual", "volume penjualan"],
    "harga": ["harga", "harga jual", "price", "tarif", "unit price", "harga satuan", "harga per kg"],
    "harga_netto": ["harga netto", "netto", "harga bersih", "net price", "harga setelah diskon"],
    "dp": ["dp", "uang muka", "down payment", "uang panjar", "dp mobil"],
    "model": ["model", "tipe mobil", "jenis mobil", "nama model", "varian model"],
    "merek": ["merek", "brand", "pabrikan", "nama merek", "merk"],
    "biaya": ["cost", "pengeluaran", "ongkos", "beban", "total biaya", "biaya produksi"],
    
    # Karyawan / Sales
    "sales": ["nama sales", "nama karyawan", "petugas", "staf", "pegawai", "tenaga kerja", "mandor", "nama pegawai", "salesperson", "nama agen"],
    "nama": ["nama sales", "nama karyawan", "nama pegawai", "nama barang", "nama produk", "nama pelanggan", "karyawan"],
    "karyawan": ["pegawai", "staf", "sales", "mandor", "nama karyawan", "pekerja"],

    # Waktu
    "bulan": ["periode", "waktu", "month", "bln", "tanggal", "periode bulan"],
    "tahun": ["year", "thn", "periode tahun", "tahun tanam", "tahun produksi"],
    "tanggal": ["tgl", "date", "waktu", "hari", "tanggal transaksi", "tanggal panen"],

    # Produksi Perkebunan Sawit / PTPN
    "produksi": ["hasil panen", "produksi ton", "total produksi", "tonase", "produksi cpo", "produksi tbs", "output", "realisasi produksi"],
    "tbs": ["tandan buah segar", "buah sawit", "tbs olah", "tbs panen", "panen tbs", "tbs masak"],
    "cpo": ["crude palm oil", "minyak sawit", "produksi cpo", "minyak kelapa sawit", "cpo olah", "hasil cpo"],
    "pk": ["palm kernel", "inti sawit", "kernel", "produksi pk"],
    "rendemen": ["oer", "oil extraction rate", "ker", "kernel extraction rate", "persentase rendemen", "kadar minyak"],
    "oer": ["oil extraction rate", "rendemen cpo", "rendemen minyak", "rendemen"],
    "ker": ["kernel extraction rate", "rendemen inti", "rendemen kernel", "rendemen pk"],
    "afdeling": ["divisi", "afd", "rayon", "blok", "wilayah", "kebun", "unit kebun", "sektor"],
    "kebun": ["afdeling", "unit", "estate", "wilayah", "pabrik", "pks"],
    "pabrik": ["pks", "pabrik kelapa sawit", "mill", "unit pengolahan"],
    "pks": ["pabrik kelapa sawit", "pabrik", "mill", "unit pabrik"],
    "ffa": ["asam lemak bebas", "alb", "kadar ffa", "kualitas cpo", "free fatty acid"],
    "pupuk": ["pemupukan", "jenis pupuk", "dosis pupuk", "aplikasi pupuk", "urea", "npk", "kcl", "rock phosphate"],
    "tonase": ["berat", "timbangan", "netto", "kuantum", "ton", "kg", "volume"],
    "luas": ["luas lahan", "hektar", "ha", "areal", "luas areal"],

    # Barang & Produk
    "produk": ["nama produk", "barang", "item", "komoditas", "tipe", "kategori", "kode barang"],
    "kategori": ["jenis", "kategori barang", "grup", "golongan", "klasifikasi"],
    "stok": ["persediaan", "sisa barang", "stok akhir", "stok awal", "inventory"],
    "jumlah": ["kuantiti", "qty", "volume", "total unit", "banyaknya", "transaksi", "jumlah keluar", "jumlah masuk"],
}

# Daftar stopwords bahasa Indonesia untuk preprocessing query
INDONESIAN_STOPWORDS = {
    "yang", "di", "ke", "dari", "pada", "dalam", "untuk", "dengan", "dan", "atau",
    "ini", "itu", "ada", "adalah", "sebagai", "oleh", "saat", "oleh", "tentang",
    "mohon", "tolong", "coba", "bisa", "kah", "lah", "saja", "pun", "dong", "ya"
}
