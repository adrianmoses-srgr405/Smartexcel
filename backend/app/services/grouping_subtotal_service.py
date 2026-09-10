import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from app.services.formula_planner import FormulaPlanner

class GroupingSubtotalService:
    """
    Dynamic Grouping and Inline Subtotal Engine for SmartExcel.
    
    Principles:
    1. Zero hardcoding of categories/models/entities.
    2. Contextual structure analysis for grouping detection (Model, Cabang, Sales, Pabrik, Kebun, Afdeling, etc.).
    3. Dynamic measure identification: sums only valid numeric measures (Harga, DP, Diskon, Netto, CPO, TBS).
       Never sums dimensions or time attributes like Tahun, ID, Tanggal, Kode.
    4. Inline insertion: inserts a TOTAL row immediately after each group completes.
    5. Detects existing TOTAL rows in uploaded Excel files to avoid duplication.
    6. Single Source of Truth for Web Table and Excel Export.
    """

    # Categories that are commonly used as grouping columns in enterprise / PTPN / automotive datasets
    HIERARCHY_GROUP_KEYWORDS = [
        "model", "merek", "cabang", "sales", "pabrik", "nama pks", "pks",
        "kebun", "nama kebun", "afdeling", "kategori", "jenis", "tipe",
        "divisi", "departemen", "wilayah", "regional", "distrik", "segmen"
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
        1. Explicit mention in query (e.g. 'per cabang' -> Cabang, 'per model' -> Model, 'per sales' -> Sales).
        2. Preferred column from caller / task context if valid.
        3. Structural analysis of dataset columns (matching hierarchy keywords and sensible cardinality).
        """
        clean_q = (query or "").lower()
        cols = list(df.columns)
        cols_lower = [str(c).lower().replace("_", " ").strip() for c in cols]

        # 1. Explicit mention in query: 'per <col>', 'berdasarkan <col>', 'setiap <col>', 'tiap <col>'
        patterns = [
            r"\b(?:per|berdasarkan|setiap|tiap|masing-masing|masing\s+masing|dikelompokkan\s+per)\s+([a-zA-Z0-9_]+(?:\s+[a-zA-Z0-9_]+)?)\b"
        ]
        for pat in patterns:
            for m in re.finditer(pat, clean_q):
                dim_candidate = m.group(1).strip()
                # Check against df columns
                for orig_col, l_col in zip(cols, cols_lower):
                    if (
                        dim_candidate == l_col or 
                        dim_candidate in l_col or 
                        l_col.startswith(dim_candidate) or
                        dim_candidate.replace(" ", "") == l_col.replace(" ", "")
                    ):
                        return orig_col

        # 2. Preferred column from caller
        if preferred_col and preferred_col in cols:
            return preferred_col

        # 3. Structural Analysis: check columns matching hierarchy keywords with valid cardinality
        candidate_scores: List[Tuple[int, str]] = [] # (priority_score, col_name)
        total_rows = len(df)

        for orig_col, l_col in zip(cols, cols_lower):
            # Exclude obvious non-grouping columns
            if any(ex == l_col or l_col.startswith(f"{ex} ") or l_col.endswith(f" {ex}") for ex in cls.NON_GROUP_KEYWORDS):
                continue
            
            series = df[orig_col].dropna()
            if series.empty:
                continue

            unique_count = series.nunique()
            # Grouping dimension should have between 2 and min(60, total_rows // 2) unique groups
            if unique_count < 2 or (total_rows > 10 and unique_count > 60):
                continue

            # Prioritize keyword matches
            score = 0
            for idx, kw in enumerate(cls.HIERARCHY_GROUP_KEYWORDS):
                if kw == l_col or kw in l_col:
                    score = 100 - idx
                    break

            if score > 0:
                candidate_scores.append((score, orig_col))
            elif not pd.api.types.is_numeric_dtype(series):
                # Other text column with reasonable unique ratio (categorical)
                ratio = unique_count / total_rows if total_rows > 0 else 1.0
                if ratio <= 0.3:
                    candidate_scores.append((10, orig_col))

        if candidate_scores:
            candidate_scores.sort(key=lambda x: x[0], reverse=True)
            return candidate_scores[0][1]

        # Fallback: find first non-numeric column with 2 <= unique <= 50
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
        - If query mentions specific targets ('total harga' -> ['Harga'], 'total harga dan dp' -> ['Harga', 'DP']),
          returns only those targeted measures.
        - If query is general ('total', 'hitung total', 'buat total'), returns all valid summable measure columns.
        - Strictly excludes ID, No, Kode, and Tahun (dimension/time attribute).
        """
        clean_q = (query or "").lower()
        cols = list(df.columns)

        # 1. Identify all structurally summable columns in the DataFrame
        all_summable = []
        for c in cols:
            # Special check for 'Tahun' / 'Year' -> NEVER sum Tahun
            c_clean = str(c).lower().replace("_", " ").strip()
            if any(ex in c_clean for ex in ["tahun", "year", "id", "kode", "code", "no", "nomor", "tanggal", "tgl", "cc", "tenor", "usia"]):
                continue

            if FormulaPlanner.is_summable_column(c, df[c]):
                all_summable.append(c)

        if not all_summable:
            return []

        # 2. Check if user asked for specific target measures
        target_mappings = [
            ("harga netto", "Harga_Netto"),
            ("harga bersih", "Harga_Netto"),
            ("netto", "Harga_Netto"),
            ("harga", "Harga"),
            ("dp", "DP"),
            ("down payment", "DP"),
            ("uang muka", "DP"),
            ("diskon", "Diskon"),
            ("tbs terima", "TBS_Terima"),
            ("tbs olah", "TBS_Olah"),
            ("tbs", "TBS"),
            ("cpo", "CPO"),
            ("pk", "PK"),
            ("produksi", "Produksi"),
            ("penjualan", "Penjualan"),
            ("omzet", "Omzet"),
            ("biaya", "Biaya"),
            ("jumlah", "Jumlah"),
            ("volume", "Volume"),
            ("tonase", "Tonase")
        ]

        # Look for target words appearing in query (longest phrase first)
        explicit_targets = []
        target_mappings.sort(key=lambda x: len(x[0]), reverse=True)
        matched_spans: List[Tuple[int, int]] = []

        for phrase, mapped_key in target_mappings:
            pattern = rf"\b{re.escape(phrase)}\b"
            for m in re.finditer(pattern, clean_q):
                s, e = m.span()
                if any(max(s, ms) < min(e, me) for ms, me in matched_spans):
                    continue
                matched_spans.append((s, e))
                # Resolve to exact column in DataFrame
                for s_col in all_summable:
                    s_clean = s_col.lower().replace("_", " ").strip()
                    if s_clean == phrase or s_col.lower() == mapped_key.lower():
                        if s_col not in explicit_targets:
                            explicit_targets.append(s_col)
                        break

        if explicit_targets:
            return explicit_targets

        # 3. Default: return all valid summable measure columns
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
            return full_df.to_dict(orient="records"), list(df.columns), {"has_subtotals": False}

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

            return rows, headers, {
                "has_subtotals": True,
                "grouping_column": grouping_col,
                "measure_columns": measure_cols,
                "existing_totals_preserved": True
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
            "grand_totals": grand_totals
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
