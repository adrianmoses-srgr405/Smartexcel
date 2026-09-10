import re
from typing import Any, Dict, List, Optional
import pandas as pd
from app.services.semantic_column_detector import UniversalSemanticColumnDetector
from app.services.grouping_subtotal_service import GroupingSubtotalService

class FormulaPlanner:
    """
    AI Formula Planner for SmartExcel.
    Transforms user natural language queries and datasets into verified
    multi-level / tiered formula plans dynamically for ANY dataset:
    - Identifies grouping dimension dynamically from dataset schema and content
    - Dynamically retrieves all unique groups from dataset
    - Distinguishes summable metric columns from identifiers, codes, dates, and attributes
    - Builds structured formula plan with per-group subtotals and grand total
    """

    NON_AGGREGATION_KEYWORDS = [
        "id", "kode", "code", "nomor", "no", "trx", "transaksi",
        "tanggal", "tgl", "date", "waktu", "time",
        "tahun", "year", "cc", "tenor", "usia", "age", "persen", "percent", "%",
        "plant", "desc", "distrik", "afdeling"
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
          "grouping": "<dimension>",
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

        is_group_query = any(k in clean_q for k in ["per", "setiap", "tiap", "masing", "berdasarkan", "dikelompokkan", "rekap"])

        if not grouping_col and is_group_query:
            if sample_df is not None and not sample_df.empty:
                grouping_col = GroupingSubtotalService.detect_grouping_column(sample_df, query=query)
            elif columns_profile:
                group_patterns = [
                    r"\b(?:setiap|tiap|masing-masing|masing\s+masing|per|berdasarkan|dikelompokkan\s+berdasarkan|dikelompokkan\s+per)\s+([a-zA-Z0-9_]+(?:\s+[a-zA-Z0-9_]+)?)\b"
                ]
                for pat in group_patterns:
                    m = re.search(pat, clean_q)
                    if m:
                        dim_raw = m.group(1).strip().lower()
                        for col in columns_profile:
                            c_orig = col.get("original_name", "")
                            c_l = c_orig.lower().replace("_", " ")
                            if c_l == dim_raw or dim_raw.startswith(c_l):
                                grouping_col = c_orig
                                break
                if not grouping_col:
                    for col in columns_profile:
                        if col.get("semantic_type") == "CATEGORY" or col.get("is_groupable"):
                            grouping_col = col.get("original_name")
                            break

        # 2. Extract Unique Groups dynamically from DataFrame or columns_profile
        unique_groups: List[str] = []
        if grouping_col and sample_df is not None and grouping_col in sample_df.columns:
            raw_groups = sample_df[grouping_col].dropna().unique()
            unique_groups = sorted([str(g).strip() for g in raw_groups if str(g).strip() and str(g).strip().upper() != "TOTAL"])
        elif grouping_col and columns_profile:
            for c in columns_profile:
                if c.get("original_name", "").lower() == grouping_col.lower():
                    unique_groups = sorted([str(v).strip() for v in (c.get("sample_values") or []) if str(v).strip()])
                    break

        # 3. Detect Requested Aggregation Function(s)
        has_average = any(w in clean_q for w in ["rata-rata", "rerata", "rata rata", "average", "mean"])
        has_count = any(w in clean_q for w in ["jumlah transaksi", "jumlah unit", "banyak unit", "banyaknya transaksi", "berapa transaksi", "count"])
        has_max = any(w in clean_q for w in ["tertinggi", "maksimal", "maksimum", "terbesar", "paling tinggi", "paling besar", "rekor tertinggi", "max"])
        has_min = any(w in clean_q for w in ["terendah", "minimal", "minimum", "terkecil", "paling rendah", "paling kecil", "min"])

        # 4. Detect targeted and summable columns
        aggregations: List[Dict[str, str]] = []
        summable_cols: List[str] = []

        if sample_df is not None and not sample_df.empty:
            summable_cols = UniversalSemanticColumnDetector.get_measure_columns(sample_df)
            if grouping_col in summable_cols:
                summable_cols.remove(grouping_col)
        elif columns_profile:
            for c in columns_profile:
                c_name = c.get("original_name", "")
                if grouping_col and c_name.lower() == str(grouping_col).lower():
                    continue
                if c.get("semantic_type") == "MEASURE" or c.get("is_summable"):
                    summable_cols.append(c_name)
                else:
                    inferred = (c.get("inferred_type") or "").lower()
                    if ("num" in inferred or "int" in inferred or "float" in inferred) and cls.is_summable_column(c_name, None):
                        summable_cols.append(c_name)

        # Build Aggregations according to Query intent
        if has_max:
            for c in summable_cols:
                aggregations.append({"column": c, "function": "MAX"})
        elif has_min:
            for c in summable_cols:
                aggregations.append({"column": c, "function": "MIN"})
        elif has_average:
            for c in summable_cols:
                aggregations.append({"column": c, "function": "AVERAGE"})
        elif has_count and not any(w in clean_q for w in ["total", "sum", "rekap"]):
            count_col = grouping_col or (summable_cols[0] if summable_cols else "Total")
            aggregations.append({"column": count_col, "function": "COUNT"})
        else:
            if any(u in clean_q for u in ["jumlah unit", "unit", "jumlah transaksi", "banyak unit", "banyak transaksi"]):
                first_measure = summable_cols[0] if summable_cols else "Total"
                aggregations.append({"column": first_measure, "function": "SUM"})
                aggregations.append({"column": "Jumlah_Unit", "function": "COUNT"})
                for c in summable_cols[1:]:
                    aggregations.append({"column": c, "function": "SUM"})
            else:
                for c in summable_cols:
                    aggregations.append({"column": c, "function": "SUM"})

        final_group = grouping_col or (sample_df.columns[0] if sample_df is not None and not sample_df.empty and is_group_query else "Kategori")

        return {
            "grouping": final_group,
            "groups": unique_groups,
            "aggregations": aggregations,
            "subtotal_formula_template": f'=SUMIF({final_group}, "{{group_name}}", {{column}})',
            "grand_total_formula": "=SUM({column})",
            "total_rows_processed": len(sample_df) if sample_df is not None else 0
        }
