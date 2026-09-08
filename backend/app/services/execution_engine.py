from typing import Any, Tuple
import pandas as pd
import numpy as np
from app.schemas.intent import StructuredAnalysisIntent, FormulaDecisionResult

class ExecutionEngine:
    @classmethod
    def apply_filters(cls, df: pd.DataFrame, filters: list[Any]) -> pd.DataFrame:
        """Applies filter criteria to DataFrame safely without arbitrary code execution."""
        filtered_df = df.copy()

        for flt in filters:
            field = flt.field
            op = flt.operator.upper()
            val = flt.value
            dtype = (flt.data_type or "text").lower()

            if field not in filtered_df.columns:
                # Find matching column case-insensitively
                matches = [c for c in filtered_df.columns if c.lower() == field.lower()]
                if matches:
                    field = matches[0]
                else:
                    continue

            series = filtered_df[field]

            if dtype == "date" or pd.api.types.is_datetime64_any_dtype(series):
                dt_series = pd.to_datetime(series, errors="coerce")
                if op == "BETWEEN" or (isinstance(val, list) and len(val) == 2):
                    start_d = pd.to_datetime(val[0])
                    end_d = pd.to_datetime(val[1])
                    filtered_df = filtered_df[(dt_series >= start_d) & (dt_series <= end_d)]
                elif op in [">=", ">"]:
                    target_d = pd.to_datetime(val)
                    filtered_df = filtered_df[dt_series >= target_d if op == ">=" else dt_series > target_d]
                elif op in ["<=", "<"]:
                    target_d = pd.to_datetime(val)
                    filtered_df = filtered_df[dt_series <= target_d if op == "<=" else dt_series < target_d]
                elif op in ["=", "=="]:
                    # Match by month/year or exact date
                    if isinstance(val, str) and len(val) == 7: # "2024-02"
                        filtered_df = filtered_df[dt_series.dt.strftime("%Y-%m") == val]
                    else:
                        target_d = pd.to_datetime(val)
                        filtered_df = filtered_df[dt_series.dt.date == target_d.date()]

            elif dtype == "numeric" or pd.api.types.is_numeric_dtype(series):
                num_series = pd.to_numeric(series, errors="coerce")
                try:
                    num_val = float(val) if not isinstance(val, list) else [float(x) for x in val]
                    if op in ["=", "=="]:
                        filtered_df = filtered_df[num_series == num_val]
                    elif op in ["!=", "<>"]:
                        filtered_df = filtered_df[num_series != num_val]
                    elif op == ">":
                        filtered_df = filtered_df[num_series > num_val]
                    elif op == ">=":
                        filtered_df = filtered_df[num_series >= num_val]
                    elif op == "<":
                        filtered_df = filtered_df[num_series < num_val]
                    elif op == "<=":
                        filtered_df = filtered_df[num_series <= num_val]
                    elif op == "BETWEEN" and isinstance(num_val, list):
                        filtered_df = filtered_df[(num_series >= num_val[0]) & (num_series <= num_val[1])]
                except Exception:
                    pass

            else:
                # Text / Categorical filter
                str_series = series.astype(str).str.strip().str.lower()
                str_val = str(val).strip().lower()

                if op in ["=", "=="]:
                    filtered_df = filtered_df[str_series == str_val]
                elif op in ["!=", "<>"]:
                    filtered_df = filtered_df[str_series != str_val]
                elif op == "CONTAINS":
                    filtered_df = filtered_df[str_series.str.contains(str_val, na=False, regex=False)]
                elif op == "STARTS_WITH":
                    filtered_df = filtered_df[str_series.str.startswith(str_val, na=False)]
                elif op == "ENDS_WITH":
                    filtered_df = filtered_df[str_series.str.endswith(str_val, na=False)]
                elif op == "IN" and isinstance(val, list):
                    vals_lower = [str(x).strip().lower() for x in val]
                    filtered_df = filtered_df[str_series.isin(vals_lower)]

        return filtered_df

    @classmethod
    def execute(
        cls,
        df: pd.DataFrame,
        intent: StructuredAnalysisIntent,
        decision: FormulaDecisionResult
    ) -> Tuple[dict[str, Any], list[str], list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Executes the verified calculation on dataframe.
        Returns:
        1. summary_dict
        2. table_headers
        3. table_rows
        4. chart_data
        """
        filtered_df = cls.apply_filters(df, intent.filters)
        target_col = intent.target_field

        # Find actual target col
        if target_col:
            matches = [c for c in df.columns if c.lower() == target_col.lower()]
            if matches:
                target_col = matches[0]

        op = intent.operation.upper()
        fid = decision.formula_id.upper()
        group_cols = []
        for g in intent.group_by:
            m = [c for c in df.columns if c.lower() == g.lower()]
            if m:
                group_cols.append(m[0])

        headers = []
        rows = []
        chart_data = []
        summary = {
            "total_raw_rows": len(df),
            "matched_rows": len(filtered_df),
            "operation": op,
            "formula_applied": fid,
            "target_field": target_col,
            "groups": group_cols,
        }

        # Case 0: Data Filtering / Table Extraction (e.g. "ambil data mobil brio" or "rangkap data")
        if fid == "FILTER" or op == "FILTER" or intent.intent in ["filter_recap", "filter"]:
            headers = list(filtered_df.columns)
            preview = filtered_df.head(500).copy()
            for col in preview.columns:
                preview[col] = preview[col].apply(lambda v: None if pd.isna(v) else str(v))
            rows = preview.to_dict(orient="records")

            # Smart Total Calculation for Recap
            grand_total_val = None
            if not target_col:
                priority_numeric = ["harga_netto", "harga", "total", "produksi_cpo_kg", "tbs_olah_kg", "jumlah_keluar", "tbs_terima_ton", "volume_liter"]
                for p in priority_numeric:
                    m = [c for c in filtered_df.columns if p in c.lower().replace(" ", "_")]
                    if m:
                        target_col = m[0]
                        break
                if not target_col:
                    num_cols = [c for c in filtered_df.columns if pd.api.types.is_numeric_dtype(filtered_df[c])]
                    if num_cols:
                        target_col = num_cols[0]

            # Comprehensive Raw vs Filtered Reconciliation Proof
            summary["total_raw_rows"] = len(df)
            summary["matched_rows"] = len(filtered_df)
            summary["match_percentage"] = round((len(filtered_df) / max(len(df), 1)) * 100, 1)

            if target_col and target_col in filtered_df.columns:
                num_s = pd.to_numeric(filtered_df[target_col], errors="coerce").dropna()
                raw_s = pd.to_numeric(df[target_col], errors="coerce").dropna() if target_col in df.columns else pd.Series([])
                raw_sum = round(float(raw_s.sum()), 2) if not raw_s.empty else 0
                summary["raw_total_sum"] = raw_sum

                if not num_s.empty:
                    grand_total_val = round(float(num_s.sum()), 2)
                    avg_val = round(float(num_s.mean()), 2)
                    min_val = round(float(num_s.min()), 2)
                    max_val = round(float(num_s.max()), 2)
                    share_pct = round((grand_total_val / max(raw_sum, 1)) * 100, 1) if raw_sum > 0 else 100.0

                    summary["grand_total"] = grand_total_val
                    summary["average_val"] = avg_val
                    summary["min_val"] = min_val
                    summary["max_val"] = max_val
                    summary["share_of_total_pct"] = share_pct
                    summary["target_field"] = target_col
                    summary["calculated_result"] = f"{len(filtered_df)} baris (Total: {grand_total_val:,.0f})"
                else:
                    summary["calculated_result"] = f"{len(filtered_df)} baris data"
                    summary["grand_total"] = len(filtered_df)
            else:
                summary["calculated_result"] = f"{len(filtered_df)} baris data"
                summary["grand_total"] = len(filtered_df)

            summary["total_filtered_rows"] = len(filtered_df)

            # Generate chart_data for recap breakdown
            if not filtered_df.empty and target_col:
                cat_candidates = ["model", "merek", "cabang", "sales", "tipe", "afdeling", "kebun", "pks", "nama_barang"]
                cat_col = None
                for c in cat_candidates:
                    m = [col for col in filtered_df.columns if c in col.lower()]
                    if m and m[0] != target_col:
                        cat_col = m[0]
                        break
                if cat_col:
                    try:
                        chart_df = filtered_df.copy()
                        chart_df[target_col] = pd.to_numeric(chart_df[target_col], errors="coerce").fillna(0)
                        top_chart = chart_df.groupby(cat_col, as_index=False)[target_col].sum().sort_values(by=target_col, ascending=False).head(8)
                        chart_data = [{"name": str(r[cat_col]), "value": float(r[target_col])} for _, r in top_chart.iterrows()]
                    except Exception:
                        pass

            return summary, headers, rows, chart_data

        # Case 1: Group By Aggregation (e.g. Rekap per Merek)
        if group_cols and target_col:
            # Ensure target is numeric
            num_series = pd.to_numeric(filtered_df[target_col], errors="coerce").fillna(0)
            work_df = filtered_df.copy()
            work_df[target_col] = num_series


            if op == "SUM":
                agg_df = work_df.groupby(group_cols, as_index=False)[target_col].sum()
            elif op == "AVERAGE":
                agg_df = work_df.groupby(group_cols, as_index=False)[target_col].mean()
            elif op == "COUNT":
                agg_df = work_df.groupby(group_cols, as_index=False)[target_col].count()
            elif op == "MAX":
                agg_df = work_df.groupby(group_cols, as_index=False)[target_col].max()
            elif op == "MIN":
                agg_df = work_df.groupby(group_cols, as_index=False)[target_col].min()
            else:
                agg_df = work_df.groupby(group_cols, as_index=False)[target_col].sum()

            agg_label = f"Total {target_col}" if op == "SUM" else (f"Rata-rata {target_col}" if op == "AVERAGE" else f"{op} {target_col}")
            agg_df.rename(columns={target_col: agg_label}, inplace=True)
            agg_df[agg_label] = agg_df[agg_label].round(2)

            headers = group_cols + [agg_label]
            rows = agg_df.to_dict(orient="records")

            # Add TOTAL Row at bottom for SUM
            if op == "SUM" and not agg_df.empty:
                grand_total = round(float(agg_df[agg_label].sum()), 2)
                summary["grand_total"] = grand_total
                chart_data = [{"name": str(r[group_cols[0]]), "value": float(r[agg_label])} for r in rows]
            elif not agg_df.empty:
                chart_data = [{"name": str(r[group_cols[0]]), "value": float(r[agg_label])} for r in rows]

        # Case 2: Single Aggregation Result (No Grouping)
        elif target_col:
            num_series = pd.to_numeric(filtered_df[target_col], errors="coerce").dropna()
            raw_s = pd.to_numeric(df[target_col], errors="coerce").dropna() if target_col in df.columns else pd.Series([])
            raw_sum = round(float(raw_s.sum()), 2) if not raw_s.empty else 0
            summary["raw_total_sum"] = raw_sum

            result_val = 0
            if op == "SUM":
                result_val = round(float(num_series.sum()), 2) if not num_series.empty else 0
            elif op == "AVERAGE":
                result_val = round(float(num_series.mean()), 2) if not num_series.empty else 0
            elif op == "COUNT":
                result_val = int(len(filtered_df))
            elif op == "MAX":
                result_val = round(float(num_series.max()), 2) if not num_series.empty else 0
            elif op == "MIN":
                result_val = round(float(num_series.min()), 2) if not num_series.empty else 0

            summary["calculated_result"] = result_val
            summary["grand_total"] = round(float(num_series.sum()), 2) if not num_series.empty else 0
            summary["average_val"] = round(float(num_series.mean()), 2) if not num_series.empty else 0
            summary["min_val"] = round(float(num_series.min()), 2) if not num_series.empty else 0
            summary["max_val"] = round(float(num_series.max()), 2) if not num_series.empty else 0
            summary["total_filtered_rows"] = len(filtered_df)
            summary["matched_rows"] = len(filtered_df)
            summary["total_raw_rows"] = len(df)
            summary["match_percentage"] = round((len(filtered_df) / max(len(df), 1)) * 100, 1)
            summary["share_of_total_pct"] = round((summary["grand_total"] / max(raw_sum, 1)) * 100, 1) if raw_sum > 0 else 100.0

            # Return the actual filtered transaction records so the table displays the data rows!
            headers = list(filtered_df.columns)
            preview = filtered_df.head(500).copy()
            for col in preview.columns:
                if col == target_col:
                    preview[col] = pd.to_numeric(preview[col], errors="coerce").fillna(0)
                else:
                    preview[col] = preview[col].apply(lambda v: None if pd.isna(v) else str(v))
            rows = preview.to_dict(orient="records")


        # Case 3: Filter Preview / Table View
        else:
            headers = list(filtered_df.columns)
            preview = filtered_df.head(50).copy()
            for col in preview.columns:
                preview[col] = preview[col].apply(lambda v: None if pd.isna(v) else str(v))
            rows = preview.to_dict(orient="records")

        return summary, headers, rows, chart_data
