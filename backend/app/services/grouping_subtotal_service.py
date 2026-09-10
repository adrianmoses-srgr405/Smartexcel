import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from app.services.semantic_column_detector import UniversalSemanticColumnDetector

class GroupingSubtotalService:
    """
    Universal Dynamic Grouping and Inline Subtotal Engine for SmartExcel.
    
    Principles:
    1. Zero hardcoding of categories/models/entities.
    2. Universal semantic column classification (Identifier, Date, Measure, Category).
    3. Resolves grouping by column names AND sample values (e.g. 'per pabrik' -> 'Group Pemilik' containing 'PABRIK TANAH PUTIH').
    4. Dynamic measure identification: sums only genuine MEASUREs (Harga, DP, Diskon, Netto, CPO, TBS).
       Never sums dimensions, codes, or time attributes (Tahun, ID, Tanggal, Kode, Plant).
    5. Inline insertion: inserts a 'TOTAL' row immediately after each group completes.
    6. Uniform label: group totals are strictly 'TOTAL', grand total is 'TOTAL KESELURUHAN'.
    7. Single Source of Truth for Web Table and Excel Export.
    """

    # Categories that are commonly used as grouping columns in enterprise / PTPN / automotive datasets
    HIERARCHY_GROUP_KEYWORDS = [
        "pabrik", "pks", "nama pks", "kebun", "nama kebun", "group pemilik",
        "model", "merek", "cabang", "sales", "afdeling", "kategori", "jenis", "tipe",
        "divisi", "departemen", "wilayah", "regional", "distrik", "segmen", "desc"
    ]

    # Explicitly excluded from grouping
    NON_GROUP_KEYWORDS = [
        "id", "transaksi", "trx", "no", "nomor", "kode", "code",
        "tanggal", "tgl", "date", "waktu", "time", "tahun", "year",
        "harga", "dp", "diskon", "netto", "biaya", "jumlah", "nilai",
        "tbs", "cpo", "pk", "produksi", "tonase"
    ]

    @classmethod
    def detect_grouping_column(
        cls,
        df: pd.DataFrame,
        query: str = "",
        preferred_col: Optional[str] = None
    ) -> Optional[str]:
        """
        Detects the grouping column dynamically without any hardcoding.
        Order of priority:
        1. Explicit mention in query (e.g. 'per cabang' -> Cabang, 'per pabrik' -> Group Pemilik / Pabrik).
        2. Matching sample values of categorical columns.
        3. Preferred column from caller / task context if valid.
        4. Structural analysis of dataset columns (matching hierarchy keywords and sensible cardinality).
        """
        clean_q = (query or "").lower()
        cols = list(df.columns)
        cols_lower = [str(c).lower().replace("_", " ").strip() for c in cols]

        # 1. Explicit mention in query: 'per <col>', 'berdasarkan <col>', 'setiap <col>', 'tiap <col>'
        patterns = [
            r"\b(?:per|berdasarkan|setiap|tiap|masing-masing|masing\s+masing|dikelompokkan\s+per|dikelompokkan\s+berdasarkan)\s+([a-zA-Z0-9_]+(?:\s+[a-zA-Z0-9_]+)?)\b"
        ]
        explicit_dim = None
        for pat in patterns:
            m = re.search(pat, clean_q)
            if m:
                explicit_dim = m.group(1).strip().lower()
                break

        if explicit_dim:
            # Check against direct column names
            for orig_col, l_col in zip(cols, cols_lower):
                if (
                    explicit_dim == l_col or 
                    explicit_dim in l_col or 
                    l_col.startswith(explicit_dim) or
                    explicit_dim.replace(" ", "") == l_col.replace(" ", "")
                ):
                    return orig_col

            # Check against sample values of text / categorical columns
            for orig_col in cols:
                s = df[orig_col].dropna()
                if not pd.api.types.is_numeric_dtype(s) and not s.empty:
                    samples_lower = [str(x).strip().lower() for x in s.head(30)]
                    if any(explicit_dim in sv or sv.startswith(explicit_dim) for sv in samples_lower):
                        return orig_col

        # 2. Preferred column from caller
        if preferred_col and preferred_col in cols:
            return preferred_col

        # 3. Structural Analysis: check columns matching hierarchy keywords with valid cardinality
        groupable = UniversalSemanticColumnDetector.get_groupable_columns(df)
        if groupable:
            scored = []
            for col in groupable:
                c_clean = str(col).lower().replace("_", " ").strip()
                score = 0
                for idx, kw in enumerate(cls.HIERARCHY_GROUP_KEYWORDS):
                    if kw == c_clean or kw in c_clean:
                        score = 100 - idx
                        break
                if score == 0:
                    score = 10
                scored.append((score, col))
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]

        # 4. Fallback: find first non-numeric column with 2 <= unique <= 50
        for orig_col in cols:
            s = df[orig_col].dropna()
            if not pd.api.types.is_numeric_dtype(s):
                if 2 <= s.nunique() <= 50:
                    return orig_col

        return cols[0] if cols else None

    @classmethod
    def detect_measure_columns(
        cls,
        df: pd.DataFrame,
        query: str = ""
    ) -> List[str]:
        """
        Dynamically detects which numeric columns are valid measures to SUM.
        - If query mentions specific targets ('total harga' -> ['Harga'], 'total tbs terima' -> ['TBS TERIMA HI']),
          returns only those targeted measures.
        - If query is general ('total', 'hitung total', 'buat total'), returns all valid summable measure columns.
        - Strictly excludes ID, No, Kode, Plant, and Tahun.
        """
        clean_q = (query or "").lower()
        cols = list(df.columns)

        # 1. Identify all structurally summable columns using UniversalSemanticColumnDetector
        all_summable = UniversalSemanticColumnDetector.get_measure_columns(df)
        if not all_summable:
            return []

        # 2. Check if user asked for specific target measures directly matching column names
        explicit_targets = []
        for col in all_summable:
            c_clean = str(col).lower().replace("_", " ").strip()
            # If the column name is in clean_q
            if c_clean in clean_q:
                explicit_targets.append(col)
            else:
                tokens = [t for t in c_clean.split() if len(t) > 2 and t not in ["total", "hitung", "dan", "dari", "setiap", "per", "semua", "seluruh", "data"]]
                if tokens and all(t in clean_q for t in tokens):
                    explicit_targets.append(col)

        if explicit_targets:
            return explicit_targets

        # 3. Check target synonyms / common business terms
        target_mappings = [
            ("harga netto", ["harga_netto", "harganetto", "netto"]),
            ("harga bersih", ["harga_netto", "harganetto", "netto"]),
            ("harga", ["harga"]),
            ("dp", ["dp", "down_payment", "uang_muka"]),
            ("diskon", ["diskon", "discount"]),
            ("tbs terima", ["tbs terima", "tbs_terima"]),
            ("tbs olah", ["tbs olah", "tbs_olah"]),
            ("tbs", ["tbs"]),
            ("cpo", ["cpo"]),
            ("pk", ["pk", "kernel"]),
            ("produksi", ["prod", "produksi"]),
            ("penjualan", ["penjualan", "sales"]),
            ("omzet", ["omzet", "omset", "revenue"]),
            ("biaya", ["biaya", "cost"]),
            ("jumlah", ["jumlah", "qty", "kuantitas", "volume"]),
            ("tonase", ["tonase", "tbs", "cpo", "pk"])
        ]

        for phrase, candidates in target_mappings:
            pattern = rf"\b{re.escape(phrase)}\b"
            if re.search(pattern, clean_q):
                for s_col in all_summable:
                    s_clean = s_col.lower().replace("_", " ").strip()
                    if any(cand in s_clean for cand in candidates):
                        if s_col not in explicit_targets:
                            explicit_targets.append(s_col)

        if explicit_targets:
            return explicit_targets

        # 4. Default: return all valid summable measure columns
        return all_summable

    @classmethod
    def has_existing_totals(cls, df: pd.DataFrame, grouping_col: Optional[str] = None) -> bool:
        """
        Checks if the dataset already contains 'TOTAL' rows.
        """
        check_cols = [grouping_col] if grouping_col and grouping_col in df.columns else list(df.columns[:4])
        for col in check_cols:
            if col not in df.columns:
                continue
            str_series = df[col].astype(str).str.strip().str.upper()
            if str_series.str.startswith("TOTAL").any():
                return True
        return False

    @classmethod
    def build_inline_subtotals(
        cls,
        df: pd.DataFrame,
        grouping_col: str,
        measure_cols: List[str],
        query: str = ""
    ) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, Any]]:
        """
        Constructs the processed dataset with inline subtotal rows:
        [Data group 1]
        ...
        [TOTAL row for group 1]
        [Data group 2]
        ...
        [TOTAL row for group 2]
        ...
        [TOTAL KESELURUHAN row]
        
        Returns:
        (rows_list, headers_list, metadata_dict)
        """
        if df.empty or not grouping_col or grouping_col not in df.columns or not measure_cols:
            full_df = df.copy()
            for c in full_df.columns:
                full_df[c] = full_df[c].apply(lambda v: None if pd.isna(v) else str(v))
            return full_df.to_dict(orient="records"), list(df.columns), {
                "has_subtotals": False,
                "sourceRowCount": len(df),
                "sourceColumnCount": len(df.columns),
                "processedRowCount": len(df),
                "generatedTotalRows": 0,
                "detectedColumns": list(df.columns)
            }

        headers = list(df.columns)

        # Check if TOTAL rows already exist in the incoming dataset
        already_has_total = cls.has_existing_totals(df, grouping_col)
        if already_has_total:
            # Preserve existing structure and update/verify measure sums if needed
            rows = []
            for _, r in df.iterrows():
                r_dict = {}
                for c in headers:
                    val = r[c]
                    r_dict[c] = None if pd.isna(val) else val
                
                # Check if this row is a total row
                val_grp = str(r_dict.get(grouping_col) or "").strip().upper()
                val_first = str(r_dict.get(headers[0]) or "").strip().upper()
                is_tot = val_grp.startswith("TOTAL") or val_first.startswith("TOTAL")
                r_dict["_is_subtotal"] = is_tot
                rows.append(r_dict)

            tot_rows_count = sum(1 for r in rows if r.get("_is_subtotal"))
            return rows, headers, {
                "has_subtotals": True,
                "grouping_column": grouping_col,
                "measure_columns": measure_cols,
                "existing_totals_preserved": True,
                "sourceRowCount": len(df),
                "sourceColumnCount": len(headers),
                "processedRowCount": len(rows),
                "generatedTotalRows": tot_rows_count,
                "detectedColumns": headers
            }

        # Stable sort by grouping_col so all rows of the same group are consecutive
        sorted_df = df.sort_values(by=[grouping_col], kind="stable").copy()

        result_rows: List[Dict[str, Any]] = []
        unique_groups = []
        for g in sorted_df[grouping_col].dropna().unique():
            g_str = str(g).strip()
            if g_str and g_str.upper() != "TOTAL" and g_str not in unique_groups:
                unique_groups.append(g_str)

        grand_totals: Dict[str, float] = {m: 0.0 for m in measure_cols}
        current_data_row_counter = 1 # 1-based index for detail rows

        for group_val in unique_groups:
            group_mask = sorted_df[grouping_col].astype(str).str.strip() == group_val
            group_df = sorted_df[group_mask]
            if group_df.empty:
                continue

            group_start_idx = current_data_row_counter
            group_sums: Dict[str, float] = {m: 0.0 for m in measure_cols}

            # 1. Add all detail rows for this group
            for _, r in group_df.iterrows():
                row_dict: Dict[str, Any] = {}
                for c in headers:
                    val = r[c]
                    if pd.isna(val) or val is None:
                        row_dict[c] = None
                    elif c in measure_cols:
                        num_v = cls._parse_numeric(val)
                        row_dict[c] = num_v if num_v is not None else val
                        if num_v is not None:
                            group_sums[c] += num_v
                            grand_totals[c] += num_v
                    else:
                        row_dict[c] = val

                row_dict["_is_subtotal"] = False
                row_dict["_group_val"] = group_val
                row_dict["_running_no"] = current_data_row_counter
                result_rows.append(row_dict)
                current_data_row_counter += 1

            group_end_idx = current_data_row_counter - 1

            # 2. Insert inline Subtotal row: 'TOTAL'
            subtotal_row: Dict[str, Any] = {}
            for c in headers:
                if c == grouping_col:
                    subtotal_row[c] = "TOTAL"
                elif c in measure_cols:
                    subtotal_val = group_sums[c]
                    subtotal_row[c] = int(subtotal_val) if subtotal_val.is_integer() else round(subtotal_val, 2)
                elif c.lower() in ["id", "id_transaksi", "no", "kode"]:
                    subtotal_row[c] = ""
                else:
                    subtotal_row[c] = ""

            subtotal_row["_is_subtotal"] = True
            subtotal_row["_group_val"] = group_val
            subtotal_row["_group_start_idx"] = group_start_idx
            subtotal_row["_group_end_idx"] = group_end_idx
            result_rows.append(subtotal_row)

        # 3. Insert Final Grand Total Row: 'TOTAL KESELURUHAN'
        if result_rows:
            grand_total_row: Dict[str, Any] = {}
            for c in headers:
                if c == grouping_col:
                    grand_total_row[c] = "TOTAL KESELURUHAN"
                elif c in measure_cols:
                    gt_val = grand_totals[c]
                    grand_total_row[c] = int(gt_val) if gt_val.is_integer() else round(gt_val, 2)
                elif c.lower() in ["id", "id_transaksi", "no", "kode"]:
                    grand_total_row[c] = ""
                else:
                    grand_total_row[c] = ""

            grand_total_row["_is_subtotal"] = True
            grand_total_row["_is_grand_total"] = True
            result_rows.append(grand_total_row)

        summary_meta = {
            "has_subtotals": True,
            "grouping_column": grouping_col,
            "measure_columns": measure_cols,
            "total_groups": len(unique_groups),
            "groups": unique_groups,
            "grand_totals": grand_totals,
            "sourceRowCount": len(df),
            "sourceColumnCount": len(headers),
            "processedRowCount": len(result_rows),
            "generatedTotalRows": len(unique_groups) + (1 if result_rows else 0),
            "detectedColumns": headers
        }

        return result_rows, headers, summary_meta

    @staticmethod
    def _parse_numeric(val: Any) -> Optional[float]:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        if isinstance(val, (int, float)):
            return float(val)
        try:
            s = str(val).strip().replace(",", "")
            return float(s)
        except Exception:
            return None
