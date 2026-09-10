import re
from typing import Any, Dict, List, Optional
import pandas as pd

class FormulaPlanner:
    """
    AI Formula Planner for SmartExcel.
    Transforms user natural language queries and datasets into verified
    multi-level / tiered formula plans:
    - Identifies grouping dimension dynamically from dataset schema and content
    - Dynamically retrieves all unique groups from dataset (e.g. 20 car models)
    - Distinguishes summable metric columns from identifiers, codes, dates, and attributes
    - Builds structured formula plan with per-group subtotals and grand total
    """

    NON_AGGREGATION_KEYWORDS = [
        "id", "kode", "code", "nomor", "no", "trx", "transaksi",
        "tanggal", "tgl", "date", "waktu", "time",
        "tahun", "year", "cc", "tenor", "usia", "age", "persen", "percent", "%"
    ]

    METRIC_KEYWORDS = [
        "harga", "netto", "diskon", "dp", "nominal", "biaya", "cicilan", "total",
        "nilai", "jumlah", "volume", "tbs", "cpo", "pk", "tonase", "produksi",
        "omzet", "omset", "penjualan", "revenue", "sales"
    ]

    @classmethod
    def is_summable_column(cls, col_name: str, series: Optional[pd.Series] = None) -> bool:
        """Determines if a column is an aggregatable numeric metric or an excluded attribute/identifier."""
        col_clean = str(col_name).lower().replace("_", " ").strip()

        # Check explicit excluded keywords
        for ex in cls.NON_AGGREGATION_KEYWORDS:
            if (
                ex == col_clean or 
                f"{ex} " in col_clean or 
                f" {ex}" in col_clean or 
                col_clean.startswith(f"{ex} ") or 
                col_clean.endswith(f" {ex}") or
                col_clean == f"{ex}"
            ):
                return False

        if series is not None:
            if not pd.api.types.is_numeric_dtype(series):
                num_s = pd.to_numeric(series.dropna().head(25), errors="coerce")
                if num_s.isna().all() or num_s.empty:
                    return False

        # Positive indicator or numeric column not excluded
        return True

    @classmethod
    def plan_formula(
        cls,
        query: str,
        tasks: Optional[List[Dict[str, Any]]] = None,
        columns_profile: Optional[List[Dict[str, Any]]] = None,
        sample_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Builds the structured Formula Planner response:
        {
          "grouping": "Model",
          "groups": [...semua tipe unik...],
          "aggregations": [
            {
              "column": "...",
              "function": "SUM"
            }
          ]
        }
        """
        clean_q = (query or "").strip().lower()

        # 1. Identify Grouping Dimension
        grouping_col = None
        if tasks:
            for t in tasks:
                t_groups = t.get("group_by", [])
                if t_groups and len(t_groups) > 0:
                    grouping_col = t_groups[0]
                    break

        if not grouping_col:
            # Check query patterns for grouping
            group_patterns = [
                r"\b(?:setiap|tiap|masing-masing|masing\s+masing|per|berdasarkan|dikelompokkan\s+berdasarkan|dikelompokkan\s+per)\s+([a-zA-Z0-9_]+(?:\s+[a-zA-Z0-9_]+)?)\b"
            ]
            for pat in group_patterns:
                m = re.search(pat, clean_q)
                if m:
                    dim_raw = m.group(1).strip().lower()
                    if dim_raw in ["tipe mobil", "model mobil", "nama mobil", "mobil", "model", "tipe"]:
                        if sample_df is not None:
                            for c in sample_df.columns:
                                if c.lower() == "model":
                                    grouping_col = c
                                    break
                            if not grouping_col:
                                for c in sample_df.columns:
                                    if c.lower() == "tipe":
                                        grouping_col = c
                                        break
                        elif columns_profile:
                            for c in columns_profile:
                                if c.get("original_name", "").lower() == "model":
                                    grouping_col = c.get("original_name")
                                    break
                            if not grouping_col:
                                for c in columns_profile:
                                    if c.get("original_name", "").lower() == "tipe":
                                        grouping_col = c.get("original_name")
                                        break
                    if not grouping_col and sample_df is not None:
                        for c in sample_df.columns:
                            c_l = c.lower().replace("_", " ")
                            if c_l == dim_raw or dim_raw.startswith(c_l):
                                grouping_col = c
                                break

        # 2. Extract Unique Groups dynamically from DataFrame
        unique_groups: List[str] = []
        if grouping_col and sample_df is not None and grouping_col in sample_df.columns:
            raw_groups = sample_df[grouping_col].dropna().unique()
            unique_groups = sorted([str(g).strip() for g in raw_groups if str(g).strip()])
        elif grouping_col and columns_profile:
            for c in columns_profile:
                if c.get("original_name", "").lower() == grouping_col.lower():
                    unique_groups = sorted([str(v).strip() for v in (c.get("sample_values") or []) if str(v).strip()])
                    break

        # 3. Detect Requested Aggregation Function(s)
        has_average = any(w in clean_q for w in ["rata-rata", "rerata", "rata rata", "average", "mean"])
        has_count = any(w in clean_q for w in ["jumlah transaksi", "jumlah unit", "banyak unit", "banyaknya transaksi", "berapa transaksi", "count"])
        
        # 4. Detect targeted and summable columns
        aggregations: List[Dict[str, str]] = []
        summable_cols: List[str] = []

        if sample_df is not None:
            for c in sample_df.columns:
                if c == grouping_col:
                    continue
                if cls.is_summable_column(c, sample_df[c]):
                    summable_cols.append(c)
        elif columns_profile:
            for c in columns_profile:
                c_name = c.get("original_name", "")
                if c_name.lower() == str(grouping_col).lower():
                    continue
                inferred = (c.get("inferred_type") or "").lower()
                if "num" in inferred or "int" in inferred or "float" in inferred:
                    if cls.is_summable_column(c_name, None):
                        summable_cols.append(c_name)

        # Build Aggregations according to Query intent
        if has_average:
            # Look for target column: e.g. Harga_Netto / Penjualan or Harga
            primary_tgt = next((c for c in summable_cols if "netto" in c.lower() or "penjualan" in c.lower()), None)
            if not primary_tgt and summable_cols:
                primary_tgt = summable_cols[0]
            if primary_tgt:
                aggregations.append({"column": primary_tgt, "function": "AVERAGE"})
            for c in summable_cols:
                if c != primary_tgt:
                    aggregations.append({"column": c, "function": "AVERAGE"})
        elif has_count and not any(w in clean_q for w in ["total", "sum", "rekap"]):
            # Count transactions per group
            count_col = "ID_Transaksi" if sample_df is not None and "ID_Transaksi" in sample_df.columns else "Transaksi"
            aggregations.append({"column": count_col, "function": "COUNT"})
        else:
            # SUM aggregations
            # If query specifies "total harga dan jumlah unit"
            if "unit" in clean_q or "jumlah unit" in clean_q:
                # Add Harga: SUM, Unit: COUNT
                harga_col = next((c for c in summable_cols if c.lower() == "harga"), None)
                if harga_col:
                    aggregations.append({"column": harga_col, "function": "SUM"})
                aggregations.append({"column": "Jumlah_Unit", "function": "COUNT"})
                for c in summable_cols:
                    if c != harga_col and not any(a["column"] == c for a in aggregations):
                        aggregations.append({"column": c, "function": "SUM"})
            else:
                # Primary target column placed first (e.g. Harga_Netto / Total Penjualan)
                primary_tgt = next((c for c in summable_cols if "netto" in c.lower() or "penjualan" in c.lower()), None)
                if primary_tgt:
                    aggregations.append({"column": primary_tgt, "function": "SUM"})
                for c in summable_cols:
                    if c != primary_tgt:
                        aggregations.append({"column": c, "function": "SUM"})

        return {
            "grouping": grouping_col or "Model",
            "groups": unique_groups,
            "aggregations": aggregations,
            "subtotal_formula_template": f'=SUMIF({grouping_col or "Model"}, "{{group_name}}", {{column}})',
            "grand_total_formula": "=SUM({column})",
            "total_rows_processed": len(sample_df) if sample_df is not None else 0
        }
