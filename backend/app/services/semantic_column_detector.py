import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

class UniversalSemanticColumnDetector:
    """
    Universal Semantic Column Detector for SmartExcel.
    Classifies any column from any domain (PTPN, automotive, financial, logistics, etc.)
    into one of 5 semantic roles without hardcoding to specific datasets:

    1. IDENTIFIER: Unique keys, codes, IDs, line numbers, transaction codes.
       e.g.: No, ID, Kode, Plant, Plant Code, Kode Kebun, ID_Transaksi, VIN, NIK, NIP.
       -> STRICTLY NEVER SUMMED.
    2. DATE: Dates, timestamps, months, years, periods.
       e.g.: Tanggal, Tgl, Date, Waktu, Periode, Bulan, Tahun, Year.
       -> STRICTLY NEVER SUMMED (2024 + 2024 = 4048 is invalid).
    3. MEASURE: True quantitative metrics, financial amounts, weights, volumes.
       e.g.: TBS, CPO, PK, Harga, DP, Diskon, Harga_Netto, Jumlah, Pendapatan, Biaya,
             Produksi, Berat, Volume, Tonase, Nilai, Omzet, Cicilan.
       -> VALID CANDIDATES FOR SUM / AVERAGE / MAX / MIN.
    4. CATEGORY/GROUP: Categorical dimensions used to group or segment data.
       e.g.: Pabrik, PKS, Kebun, Group Pemilik, Sales, Cabang, Kota, Model, Merek,
             Tipe, Afdeling, Divisi, Distrik, Wilayah, Kategori, Segmen, Status, Vendor.
       -> PRIMARY CANDIDATES FOR GROUP BY / SUBTOTAL.
    5. TEXT/OTHER: General notes, descriptions, addresses, customer names.
    """

    IDENTIFIER_KEYWORDS = [
        "id", "kode", "code", "nomor", "no", "plant", "plant code", "kode kebun",
        "kode pks", "key", "trx", "transaksi", "id transaksi", "vin", "nip", "nik",
        "barcode", "sku", "ref", "reference", "no hp", "telepon", "phone"
    ]

    DATE_KEYWORDS = [
        "tanggal", "tgl", "date", "waktu", "time", "periode", "period",
        "bulan", "month", "tahun", "year", "thn", "bln"
    ]

    MEASURE_KEYWORDS = [
        "tbs", "cpo", "pk", "palm kernel", "rendemen", "ffa", "alb",
        "harga", "price", "tarif", "dp", "down payment", "uang muka",
        "netto", "harga netto", "bersih", "diskon", "discount", "potongan",
        "biaya", "cost", "ongkos", "beban", "jumlah", "qty", "kuantum",
        "volume", "tonase", "ton", "berat", "weight", "kg", "kuintal",
        "produksi", "production", "hasil panen", "output", "realisasi",
        "pendapatan", "revenue", "omzet", "omset", "penjualan", "sales amount",
        "sisa", "stock", "stok", "sisa awal", "sisa akhir", "saldo",
        "rkap", "budget", "anggaran", "luas", "hektar", "ha", "meter",
        "cicilan", "angsuran", "nominal", "nilai"
    ]

    NON_MEASURE_KEYWORDS = [
        "id", "kode", "code", "no", "nomor", "plant", "tahun", "year",
        "tanggal", "tgl", "date", "cc", "tenor", "usia", "age",
        "persen", "percent", "%", "rasio", "ratio", "score", "indeks", "index"
    ]

    CATEGORY_KEYWORDS = [
        "pabrik", "pks", "nama pks", "kebun", "nama kebun", "estate", "unit",
        "group pemilik", "pemilik", "holding", "sales", "nama sales", "petugas",
        "cabang", "branch", "kantor", "kota", "city", "model", "merek", "brand",
        "tipe", "type", "afdeling", "afd", "divisi", "departemen", "wilayah",
        "regional", "distrik", "sektor", "rayon", "lokasi", "kategori", "category",
        "jenis", "segmen", "status", "customer", "pelanggan", "nama pelanggan",
        "vendor", "supplier", "rekanan", "desc", "keterangan", "warna", "transmisi",
        "bahan bakar"
    ]

    @classmethod
    def classify_column(
        cls,
        col_name: str,
        series: Optional[pd.Series] = None
    ) -> str:
        """
        Classifies a single column into: 'IDENTIFIER', 'DATE', 'MEASURE', 'CATEGORY', or 'TEXT'.
        """
        c_clean = str(col_name).lower().replace("_", " ").strip()
        c_no_space = c_clean.replace(" ", "")

        # 1. Check if name is explicitly non-measure identifier
        for ex in cls.IDENTIFIER_KEYWORDS:
            if (
                c_clean == ex or 
                c_clean.startswith(f"{ex} ") or 
                c_clean.endswith(f" {ex}") or 
                f" {ex} " in c_clean or
                c_no_space == ex.replace(" ", "")
            ):
                return "IDENTIFIER"

        # 2. Check for MEASURE first (before DATE, so e.g. "TBS Diterima s/d Bulan Ini" is classified as MEASURE)
        is_measure_candidate = any(
            m == c_clean or 
            f"{m} " in c_clean or 
            f" {m}" in c_clean or 
            c_clean.startswith(f"{m} ") or 
            c_clean.endswith(f" {m}") or 
            f" {m} " in c_clean
            for m in cls.MEASURE_KEYWORDS
        )

        # Ensure not excluded from measure
        is_explicit_non_measure = any(
            nm == c_clean or 
            c_clean.startswith(f"{nm} ") or 
            c_clean.endswith(f" {nm}") or
            f" {nm} " in c_clean
            for nm in cls.NON_MEASURE_KEYWORDS
        )

        has_numeric = False
        if series is not None and not series.dropna().empty:
            if pd.api.types.is_numeric_dtype(series):
                has_numeric = True
            else:
                sample_num = pd.to_numeric(series.dropna().head(30), errors="coerce")
                if not sample_num.isna().all() and not sample_num.empty:
                    has_numeric = True

        if is_measure_candidate and not is_explicit_non_measure and has_numeric:
            return "MEASURE"

        # 3. Check for DATE (Tahun, Tanggal, Periode, Bulan)
        is_date = any(
            d == c_clean or 
            f"{d} " in c_clean or 
            f" {d}" in c_clean or 
            c_clean.startswith(f"{d} ") or 
            c_clean.endswith(f" {d}") or 
            f" {d} " in c_clean
            for d in cls.DATE_KEYWORDS
        )
        if is_date:
            return "DATE"
        if series is not None and pd.api.types.is_datetime64_any_dtype(series):
            return "DATE"

        # 4. Check for CATEGORY / GROUP
        is_cat_keyword = any(
            cat == c_clean or 
            f"{cat} " in c_clean or 
            f" {cat}" in c_clean or 
            c_clean.startswith(f"{cat} ") or 
            c_clean.endswith(f" {cat}") or 
            f" {cat} " in c_clean or
            c_no_space == cat.replace(" ", "")
            for cat in cls.CATEGORY_KEYWORDS
        )
        if is_cat_keyword:
            return "CATEGORY"

        # Check sample values for category indicators (e.g. text starting with 'PABRIK ', 'KEBUN ', etc.)
        if series is not None and not series.dropna().empty:
            samples_upper = [str(x).strip().upper() for x in series.dropna().head(20)]
            if any(s.startswith("PABRIK ") or s.startswith("KEBUN ") or s.startswith("PKS ") for s in samples_upper):
                return "CATEGORY"

            # If numeric column has very few unique values and was not marked as measure
            if has_numeric and not is_explicit_non_measure:
                unique_cnt = series.nunique(dropna=True)
                if unique_cnt > 10:
                    return "MEASURE"
                return "CATEGORY"

            # If text column with reasonable cardinality (2 to 80 unique groups)
            unique_cnt = series.nunique(dropna=True)
            total_cnt = len(series)
            if 2 <= unique_cnt <= 80 or (total_cnt > 0 and unique_cnt / total_cnt <= 0.25):
                return "CATEGORY"

        return "TEXT"

    @classmethod
    def detect_columns_schema(cls, df: pd.DataFrame) -> Dict[str, str]:
        """
        Returns a mapping of column name to semantic classification:
        { "PABRIK": "CATEGORY", "TBS_OLAH": "MEASURE", "TAHUN": "DATE", ... }
        """
        result = {}
        for col in df.columns:
            result[str(col)] = cls.classify_column(col, df[col])
        return result

    @classmethod
    def get_measure_columns(cls, df: pd.DataFrame) -> List[str]:
        """Returns all columns strictly classified as MEASURE."""
        measures = []
        for col in df.columns:
            if cls.classify_column(col, df[col]) == "MEASURE":
                measures.append(str(col))
        return measures

    @classmethod
    def get_groupable_columns(cls, df: pd.DataFrame) -> List[str]:
        """Returns all columns classified as CATEGORY suitable for grouping."""
        categories = []
        total_rows = len(df)
        for col in df.columns:
            sem_type = cls.classify_column(col, df[col])
            if sem_type == "CATEGORY":
                # Cardinality check
                unique_cnt = df[col].dropna().nunique()
                if 2 <= unique_cnt <= min(80, max(2, total_rows // 2)):
                    categories.append(str(col))
        return categories
