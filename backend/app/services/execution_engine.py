import re
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from app.schemas.intent import StructuredAnalysisIntent, FormulaDecisionResult
from app.services.grouping_subtotal_service import GroupingSubtotalService
from app.services.semantic_column_detector import UniversalSemanticColumnDetector

class ExecutionEngine:
    """
    Safe and verified Execution Engine for Excel Formulas.
    Executes actual formula calculations against a Pandas DataFrame without any
    arbitrary Python eval() calls.
    Supports strictly the 18 whitelisted formulas.
    """

    WHITELISTED_FORMULAS = {
        "SUM", "SUMIF", "SUMIFS",
        "AVERAGE", "AVERAGEIF", "AVERAGEIFS",
        "COUNT", "COUNTA", "COUNTIF", "COUNTIFS",
        "MAX", "MIN", "MAXIFS", "MINIFS",
        "IF", "IFS",
        "VLOOKUP", "XLOOKUP",
        "INDEX", "MATCH",
        "FILTER"
    }

    @classmethod
    def execute_formula_safe(
        cls,
        df: pd.DataFrame,
        formula_name: str,
        target_column: Optional[str] = None,
        conditions: Optional[List[Dict[str, Any]]] = None,
        logical_branches: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes verified calculation on dataframe safely without eval().
        Returns exact computation result or explains failure.
        """
        f_name = formula_name.upper().strip()

        # Whitelist verification
        if f_name not in cls.WHITELISTED_FORMULAS:
            return {
                "executed": False,
                "status": "unsupported_formula",
                "result": None,
                "reason": f"Formula '{f_name}' is not in the whitelist of 18 supported formulas."
            }

        if df is None or df.empty:
            return {
                "executed": False,
                "status": "empty_dataset",
                "result": None,
                "reason": "Dataset is empty or not provided."
            }

        # Resolve exact target column in df
        resolved_target = None
        if target_column:
            for col in df.columns:
                if col.lower() == target_column.lower():
                    resolved_target = col
                    break

        try:
            # 1. SUM
            if f_name == "SUM":
                if not resolved_target:
                    return {"executed": False, "reason": "Target column for SUM not found in dataset."}
                num_s = pd.to_numeric(df[resolved_target], errors="coerce").dropna()
                val = float(num_s.sum())
                return {"executed": True, "result": int(val) if val.is_integer() else round(val, 2)}

            # 2. SUMIF
            elif f_name == "SUMIF":
                if not resolved_target:
                    return {"executed": False, "reason": "Target column for SUMIF not found in dataset."}
                filtered_df = cls._filter_dataframe(df, conditions[:1] if conditions else [])
                num_s = pd.to_numeric(filtered_df[resolved_target], errors="coerce").dropna()
                val = float(num_s.sum())
                return {"executed": True, "result": int(val) if val.is_integer() else round(val, 2)}

            # 3. SUMIFS
            elif f_name == "SUMIFS":
                if not resolved_target:
                    return {"executed": False, "reason": "Target column for SUMIFS not found in dataset."}
                filtered_df = cls._filter_dataframe(df, conditions or [])
                num_s = pd.to_numeric(filtered_df[resolved_target], errors="coerce").dropna()
                val = float(num_s.sum())
                return {"executed": True, "result": int(val) if val.is_integer() else round(val, 2)}

            # 4. AVERAGE
            elif f_name == "AVERAGE":
                if not resolved_target:
                    return {"executed": False, "reason": "Target column for AVERAGE not found in dataset."}
                num_s = pd.to_numeric(df[resolved_target], errors="coerce").dropna()
                if num_s.empty:
                    return {"executed": True, "result": 0.0}
                val = float(num_s.mean())
                return {"executed": True, "result": round(val, 2)}

            # 5. AVERAGEIF
            elif f_name == "AVERAGEIF":
                if not resolved_target:
                    return {"executed": False, "reason": "Target column for AVERAGEIF not found in dataset."}
                filtered_df = cls._filter_dataframe(df, conditions[:1] if conditions else [])
                num_s = pd.to_numeric(filtered_df[resolved_target], errors="coerce").dropna()
                if num_s.empty:
                    return {"executed": True, "result": 0.0}
                val = float(num_s.mean())
                return {"executed": True, "result": round(val, 2)}

            # 6. AVERAGEIFS
            elif f_name == "AVERAGEIFS":
                if not resolved_target:
                    return {"executed": False, "reason": "Target column for AVERAGEIFS not found in dataset."}
                filtered_df = cls._filter_dataframe(df, conditions or [])
                num_s = pd.to_numeric(filtered_df[resolved_target], errors="coerce").dropna()
                if num_s.empty:
                    return {"executed": True, "result": 0.0}
                val = float(num_s.mean())
                return {"executed": True, "result": round(val, 2)}

            # 7. COUNT
            elif f_name == "COUNT":
                target_col = resolved_target
                if not target_col:
                    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
                    target_col = num_cols[0] if num_cols else df.columns[0]
                num_s = pd.to_numeric(df[target_col], errors="coerce").dropna()
                return {"executed": True, "result": int(len(num_s))}

            # 8. COUNTA
            elif f_name == "COUNTA":
                target_col = resolved_target or df.columns[0]
                non_null_count = int(df[target_col].dropna().count())
                return {"executed": True, "result": non_null_count}

            # 9. COUNTIF
            elif f_name == "COUNTIF":
                filtered_df = cls._filter_dataframe(df, conditions[:1] if conditions else [])
                return {"executed": True, "result": int(len(filtered_df))}

            # 10. COUNTIFS
            elif f_name == "COUNTIFS":
                filtered_df = cls._filter_dataframe(df, conditions or [])
                return {"executed": True, "result": int(len(filtered_df))}

            # 11. MAX
            elif f_name == "MAX":
                if not resolved_target:
                    return {"executed": False, "reason": "Target column for MAX not found."}
                num_s = pd.to_numeric(df[resolved_target], errors="coerce").dropna()
                if num_s.empty:
                    return {"executed": True, "result": None}
                val = float(num_s.max())
                return {"executed": True, "result": int(val) if val.is_integer() else round(val, 2)}

            # 12. MIN
            elif f_name == "MIN":
                if not resolved_target:
                    return {"executed": False, "reason": "Target column for MIN not found."}
                num_s = pd.to_numeric(df[resolved_target], errors="coerce").dropna()
                if num_s.empty:
                    return {"executed": True, "result": None}
                val = float(num_s.min())
                return {"executed": True, "result": int(val) if val.is_integer() else round(val, 2)}

            # 12b. MAXIFS
            elif f_name == "MAXIFS":
                if not resolved_target:
                    return {"executed": False, "reason": "Target column for MAXIFS not found in dataset."}
                filtered_df = cls._filter_dataframe(df, conditions or [])
                num_s = pd.to_numeric(filtered_df[resolved_target], errors="coerce").dropna()
                if num_s.empty:
                    return {"executed": True, "result": None}
                val = float(num_s.max())
                return {"executed": True, "result": int(val) if val.is_integer() else round(val, 2)}

            # 12c. MINIFS
            elif f_name == "MINIFS":
                if not resolved_target:
                    return {"executed": False, "reason": "Target column for MINIFS not found in dataset."}
                filtered_df = cls._filter_dataframe(df, conditions or [])
                num_s = pd.to_numeric(filtered_df[resolved_target], errors="coerce").dropna()
                if num_s.empty:
                    return {"executed": True, "result": None}
                val = float(num_s.min())
                return {"executed": True, "result": int(val) if val.is_integer() else round(val, 2)}

            # 13. IF
            elif f_name == "IF":
                # Evaluate logical condition on first row or total
                target_col = resolved_target or (df.columns[0] if not df.empty else None)
                if not target_col or not logical_branches:
                    return {"executed": True, "result": "Tercapai"}
                b = logical_branches[0]
                val = pd.to_numeric(df[target_col], errors="coerce").iloc[0] if not df.empty else 0
                op = b.get("operator", ">")
                thresh = b.get("value", 0)
                outcome = b.get("outcome", "Tinggi")
                
                is_true = cls._eval_op(val, op, thresh)
                return {"executed": True, "result": outcome if is_true else "Rendah"}

            # 14. IFS
            elif f_name == "IFS":
                target_col = resolved_target or (df.columns[0] if not df.empty else None)
                if not target_col or not logical_branches:
                    return {"executed": True, "result": "Sedang"}
                val = pd.to_numeric(df[target_col], errors="coerce").iloc[0] if not df.empty else 0
                for b in logical_branches:
                    if cls._eval_op(val, b.get("operator", ">"), b.get("value", 0)):
                        return {"executed": True, "result": b.get("outcome")}
                return {"executed": True, "result": "Rendah"}

            # 15. XLOOKUP
            elif f_name == "XLOOKUP":
                if not conditions or not resolved_target:
                    return {"executed": False, "reason": "XLOOKUP requires search key and target return column."}
                cond = conditions[0]
                crit_col = cond.get("column_hint") or cond.get("matched_column")
                val = cond.get("value")
                
                # Find matching row
                matches = cls._find_lookup_row(df, crit_col, val)
                if not matches.empty:
                    res_val = matches.iloc[0][resolved_target]
                    return {"executed": True, "result": str(res_val)}
                return {"executed": True, "result": "Tidak Ditemukan"}

            # 16. VLOOKUP
            elif f_name == "VLOOKUP":
                if not conditions or df.empty:
                    return {"executed": False, "reason": "VLOOKUP requires conditions and non-empty dataframe."}
                lookup_col = df.columns[0]
                val = conditions[0].get("value")
                matches = cls._find_lookup_row(df, lookup_col, val)
                if not matches.empty:
                    target_idx = -1 if resolved_target not in df.columns else list(df.columns).index(resolved_target)
                    res_val = matches.iloc[0, target_idx]
                    return {"executed": True, "result": str(res_val)}
                return {"executed": True, "result": "Tidak Ditemukan"}

            # 17. INDEX
            elif f_name == "INDEX":
                if not resolved_target or df.empty:
                    return {"executed": False, "reason": "INDEX requires target column and data."}
                res_val = df[resolved_target].iloc[0]
                return {"executed": True, "result": str(res_val)}

            # 18. MATCH
            elif f_name == "MATCH":
                if not conditions:
                    return {"executed": False, "reason": "MATCH requires lookup value."}
                crit_col = cond.get("column_hint") or cond.get("matched_column") or (df.columns[0] if not df.empty else None)
                val = cond.get("value")
                for idx, r_val in enumerate(df[crit_col]):
                    if str(r_val).strip().lower() == str(val).strip().lower():
                        return {"executed": True, "result": idx + 1} # 1-based index
                return {"executed": True, "result": "#N/A"}

            # 19. FILTER (Dynamic Array / Row Retrieval)
            elif f_name in ["FILTER", "RETRIEVAL"]:
                filtered_df = cls._filter_dataframe(df, conditions or [])
                count = len(filtered_df)
                preview_records = filtered_df.head(10).astype(str).to_dict(orient="records")
                return {
                    "executed": True,
                    "result": count,
                    "matching_rows_count": count,
                    "preview": preview_records
                }

        except Exception as e:
            return {
                "executed": False,
                "reason": f"Execution error: {str(e)}"
            }

        return {"executed": False, "reason": f"No execution strategy defined for {f_name}."}

    @classmethod
    def _eval_op(cls, a: Any, op: str, b: Any) -> bool:
        """Safely evaluates relational operator without eval()."""
        try:
            a_f = float(a)
            b_f = float(b)
            if op == ">": return a_f > b_f
            if op == ">=": return a_f >= b_f
            if op == "<": return a_f < b_f
            if op == "<=": return a_f <= b_f
            if op in ["=", "=="]: return a_f == b_f
            if op in ["<>", "!="]: return a_f != b_f
        except Exception:
            a_s = str(a).strip().lower()
            b_s = str(b).strip().lower()
            if op in ["=", "=="]: return a_s == b_s
            if op in ["<>", "!="]: return a_s != b_s
        return False

    @classmethod
    def _filter_dataframe(cls, df: pd.DataFrame, conditions: List[Dict[str, Any]]) -> pd.DataFrame:
        """Safely filters DataFrame by extracted conditions without eval()."""
        filtered_df = df.copy()
        for cond in conditions:
            col_hint = cond.get("column_hint") or cond.get("matched_column") or cond.get("field")
            if not col_hint:
                continue
            
            # Find column in df
            actual_col = None
            for c in df.columns:
                if c.lower() == str(col_hint).lower():
                    actual_col = c
                    break
            if not actual_col:
                continue

            val = cond.get("value")
            op = str(cond.get("operator", "=")).strip()

            # Handle dict value: e.g. {"start": "2026-01-01", "end": "2026-01-31"}
            if isinstance(val, dict):
                start_v = val.get("start")
                end_v = val.get("end")
                series = filtered_df[actual_col]
                # Try date comparison first
                try:
                    dt_series = pd.to_datetime(series, errors="coerce")
                    if dt_series.notna().any():
                        if start_v:
                            filtered_df = filtered_df[dt_series >= pd.to_datetime(start_v)]
                            dt_series = pd.to_datetime(filtered_df[actual_col], errors="coerce")
                        if end_v:
                            filtered_df = filtered_df[dt_series <= pd.to_datetime(end_v)]
                        continue
                except Exception:
                    pass
                # Fallback to string / numeric comparison
                if start_v:
                    filtered_df = filtered_df[filtered_df[actual_col].astype(str) >= str(start_v)]
                if end_v:
                    filtered_df = filtered_df[filtered_df[actual_col].astype(str) <= str(end_v)]
                continue

            # Handle list/tuple e.g. ["2026-01-01", "2026-01-31"]
            if isinstance(val, (list, tuple)) and len(val) == 2:
                series = filtered_df[actual_col]
                try:
                    dt_series = pd.to_datetime(series, errors="coerce")
                    if dt_series.notna().any():
                        filtered_df = filtered_df[
                            (dt_series >= pd.to_datetime(val[0])) & (dt_series <= pd.to_datetime(val[1]))
                        ]
                        continue
                except Exception:
                    pass
                filtered_df = filtered_df[
                    (filtered_df[actual_col].astype(str) >= str(val[0])) & 
                    (filtered_df[actual_col].astype(str) <= str(val[1]))
                ]
                continue

            # Handle string embedded operators (e.g. ">=2026-01-01")
            if isinstance(val, str):
                val_str = val.strip()
                if val_str.startswith(">="):
                    op = ">="
                    val = val_str[2:].strip()
                elif val_str.startswith("<="):
                    op = "<="
                    val = val_str[2:].strip()
                elif val_str.startswith(">"):
                    op = ">"
                    val = val_str[1:].strip()
                elif val_str.startswith("<"):
                    op = "<"
                    val = val_str[1:].strip()
                elif val_str.startswith("="):
                    op = "="
                    val = val_str[1:].strip()

            series = filtered_df[actual_col]

            # Check if date comparison
            is_date_col = False
            try:
                if isinstance(val, str) and len(val) >= 8 and ("-" in val or "/" in val):
                    parsed_val_dt = pd.to_datetime(val, errors="coerce")
                    if pd.notna(parsed_val_dt):
                        dt_series = pd.to_datetime(series, errors="coerce")
                        if dt_series.notna().any():
                            is_date_col = True
                            if op in ["=", "=="]: filtered_df = filtered_df[dt_series == parsed_val_dt]
                            elif op == ">": filtered_df = filtered_df[dt_series > parsed_val_dt]
                            elif op == ">=": filtered_df = filtered_df[dt_series >= parsed_val_dt]
                            elif op == "<": filtered_df = filtered_df[dt_series < parsed_val_dt]
                            elif op == "<=": filtered_df = filtered_df[dt_series <= parsed_val_dt]
                            elif op in ["!=", "<>"]: filtered_df = filtered_df[dt_series != parsed_val_dt]
            except Exception:
                is_date_col = False

            if is_date_col:
                continue

            # Numeric comparison
            if pd.api.types.is_numeric_dtype(series):
                try:
                    num_val = float(val)
                    num_s = pd.to_numeric(series, errors="coerce")
                    if op in ["=", "=="]: filtered_df = filtered_df[num_s == num_val]
                    elif op == ">": filtered_df = filtered_df[num_s > num_val]
                    elif op == ">=": filtered_df = filtered_df[num_s >= num_val]
                    elif op == "<": filtered_df = filtered_df[num_s < num_val]
                    elif op == "<=": filtered_df = filtered_df[num_s <= num_val]
                    elif op in ["!=", "<>"]: filtered_df = filtered_df[num_s != num_val]
                except Exception:
                    pass
            else:
                # Text comparison (case-insensitive & trimmed)
                str_s = series.astype(str).str.strip().str.lower()
                str_v = str(val).strip().lower()
                if op in ["=", "=="]:
                    filtered_df = filtered_df[str_s == str_v]
                elif op in ["!=", "<>"]:
                    filtered_df = filtered_df[str_s != str_v]
                elif op == "contains":
                    filtered_df = filtered_df[str_s.str.contains(str_v, regex=False, na=False)]

        return filtered_df

    @classmethod
    def _find_lookup_row(cls, df: pd.DataFrame, col_name: Optional[str], val: Any) -> pd.DataFrame:
        if not col_name:
            col_name = df.columns[0]
        actual_col = col_name
        for c in df.columns:
            if c.lower() == col_name.lower():
                actual_col = c
                break
        str_s = df[actual_col].astype(str).str.strip().str.lower()
        str_v = str(val).strip().lower()
        return df[str_s == str_v]

    @classmethod
    def apply_filters(cls, df: pd.DataFrame, filters: list[Any]) -> pd.DataFrame:
        """Applies filter criteria to DataFrame safely without arbitrary code execution."""
        filtered_df = df.copy()
        for flt in filters:
            field = flt.field
            op = flt.operator.upper()
            val = flt.value
            dtype = (flt.data_type or "text").lower()

            matches = [c for c in filtered_df.columns if c.lower() == field.lower()]
            if matches:
                field = matches[0]
            else:
                continue

            series = filtered_df[field]
            if dtype == "numeric" or pd.api.types.is_numeric_dtype(series):
                num_series = pd.to_numeric(series, errors="coerce")
                try:
                    num_val = float(val) if not isinstance(val, list) else [float(x) for x in val]
                    if op in ["=", "=="]: filtered_df = filtered_df[num_series == num_val]
                    elif op in ["!=", "<>"]: filtered_df = filtered_df[num_series != num_val]
                    elif op == ">": filtered_df = filtered_df[num_series > num_val]
                    elif op == ">=": filtered_df = filtered_df[num_series >= num_val]
                    elif op == "<": filtered_df = filtered_df[num_series < num_val]
                    elif op == "<=": filtered_df = filtered_df[num_series <= num_val]
                except Exception:
                    pass
            else:
                str_series = series.astype(str).str.strip().str.lower()
                str_val = str(val).strip().lower()
                if op in ["=", "=="]: filtered_df = filtered_df[str_series == str_val]
                elif op in ["!=", "<>"]: filtered_df = filtered_df[str_series != str_val]

        return filtered_df

    @classmethod
    def execute(
        cls,
        df: pd.DataFrame,
        intent: StructuredAnalysisIntent,
        decision: FormulaDecisionResult,
        user_query: Optional[str] = None
    ) -> Tuple[dict[str, Any], list[str], list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Executes verified calculation for UI table and charts.
        Integrates Dynamic Grouping + Inline Subtotals for total/rekap requests.
        """
        filtered_df = cls.apply_filters(df, intent.filters)
        target_col = intent.target_field
        if target_col:
            matches = [c for c in df.columns if c.lower() == target_col.lower()]
            if matches:
                target_col = matches[0]

        op = intent.operation.upper()
        fid = decision.formula_id.upper()
        clean_q = (user_query or "").lower().strip()

        # Handle MAX / MIN requests ("data terbesar", "nilai tertinggi", etc.)
        is_max = fid.startswith("MAX") or op == "MAX" or any(w in clean_q for w in ["terbesar", "tertinggi", "maksimal", "paling tinggi", "paling besar", "max"])
        is_min = fid.startswith("MIN") or op == "MIN" or any(w in clean_q for w in ["terkecil", "terendah", "minimal", "paling rendah", "paling kecil", "min"])

        if is_max or is_min:
            calc_fid = "MAX" if is_max else "MIN"
            if not target_col or target_col not in filtered_df.columns:
                measures = UniversalSemanticColumnDetector.get_measure_columns(filtered_df)
                if measures:
                    target_col = measures[0]
            op = calc_fid
            fid = calc_fid

        summary = {
            "total_raw_rows": len(df),
            "matched_rows": len(filtered_df),
            "operation": op,
            "formula_applied": fid,
            "target_field": target_col,
        }

        # Calculate result using safe formula executor
        conditions_dicts = [{"field": f.field, "operator": f.operator, "value": f.value} for f in intent.filters]
        exec_res = cls.execute_formula_safe(df, fid, target_col, conditions_dicts)
        summary["calculated_result"] = exec_res.get("result")
        summary["execution_status"] = "success" if exec_res.get("executed") else "failed"

        # If MAX/MIN, sort filtered_df so that the top row in the table/export is the record with the extreme value
        if (is_max or is_min) and target_col and target_col in filtered_df.columns:
            try:
                num_s = pd.to_numeric(filtered_df[target_col], errors="coerce")
                temp_df = filtered_df.copy()
                temp_df["_sort_measure"] = num_s
                filtered_df = temp_df.sort_values(by="_sort_measure", ascending=(not is_max), na_position="last").drop(columns=["_sort_measure"])
            except Exception:
                pass

        headers = list(filtered_df.columns)
        chart_data = []

        # Check if dynamic grouping & inline subtotals should be generated
        is_total_query = any(k in clean_q for k in [
            "total", "rekap", "subtotal", "jumlahkan", "penjumlahan", "hitung total",
            "buat total", "ringkasan", "sum", "rekapitulasi", "setiap", "tiap"
        ])
        is_total_intent = op in ["SUM", "TOTAL", "REKAP", "SUBTOTAL"] or fid in ["SUM", "SUMIF", "SUMIFS"]
        is_lookup_or_pure_filter = fid in ["VLOOKUP", "XLOOKUP", "INDEX", "MATCH"] or any(clean_q.startswith(p) for p in ["cari ", "temukan ", "filter "]) or is_max or is_min

        if (is_total_query or is_total_intent) and not is_lookup_or_pure_filter and not filtered_df.empty:
            preferred_group = intent.group_by[0] if (intent.group_by and intent.group_by[0] in filtered_df.columns) else None
            detected_group = GroupingSubtotalService.detect_grouping_column(
                filtered_df,
                query=user_query or "",
                preferred_col=preferred_group
            )
            detected_measures = GroupingSubtotalService.detect_measure_columns(
                filtered_df,
                query=user_query or ""
            )

            if detected_group and detected_measures:
                rows, sub_headers, sub_meta = GroupingSubtotalService.build_inline_subtotals(
                    filtered_df,
                    grouping_col=detected_group,
                    measure_cols=detected_measures,
                    query=user_query or ""
                )
                summary["has_subtotals"] = True
                summary["grouping_column"] = detected_group
                summary["measure_columns"] = detected_measures
                summary["total_groups"] = sub_meta.get("total_groups", int(filtered_df[detected_group].nunique()))
                summary["subtotal_metadata"] = sub_meta
                summary["sourceRowCount"] = len(df)
                summary["sourceColumnCount"] = len(df.columns)
                summary["processedRowCount"] = len(rows)
                summary["generatedTotalRows"] = sub_meta.get("generatedTotalRows", 0)
                summary["detectedColumns"] = sub_headers

                # Chart data based on detected group and primary measure
                chart_measure = target_col if (target_col and target_col in detected_measures) else detected_measures[0]
                if chart_measure in filtered_df.columns:
                    num_series = pd.to_numeric(filtered_df[chart_measure], errors="coerce")
                    chart_df = filtered_df[[detected_group]].copy()
                    chart_df[chart_measure] = num_series
                    grp_agg = chart_df.groupby(detected_group)[chart_measure].sum().reset_index()
                    for _, grow in grp_agg.iterrows():
                        val = grow[chart_measure]
                        chart_data.append({
                            "name": str(grow[detected_group]),
                            "value": int(val) if isinstance(val, (int, float)) and float(val).is_integer() else (round(float(val), 2) if pd.notna(val) else 0)
                        })

                return summary, sub_headers, rows, chart_data

        # If group_by is specified, generate chart data and sort preview by group
        if intent.group_by and intent.group_by[0] in filtered_df.columns:
            grp_col = intent.group_by[0]
            summary["group_by"] = intent.group_by
            summary["total_groups"] = int(filtered_df[grp_col].nunique())

            if target_col and target_col in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[target_col]):
                if op == "AVERAGE":
                    grp_agg = filtered_df.groupby(grp_col)[target_col].mean().reset_index()
                elif op == "COUNT":
                    grp_agg = filtered_df.groupby(grp_col)[target_col].count().reset_index()
                elif op == "MAX":
                    grp_agg = filtered_df.groupby(grp_col)[target_col].max().reset_index()
                elif op == "MIN":
                    grp_agg = filtered_df.groupby(grp_col)[target_col].min().reset_index()
                else:
                    grp_agg = filtered_df.groupby(grp_col)[target_col].sum().reset_index()
                for _, grow in grp_agg.iterrows():
                    val = grow[target_col]
                    chart_data.append({
                        "name": str(grow[grp_col]),
                        "value": int(val) if isinstance(val, (int, float)) and float(val).is_integer() else (round(float(val), 2) if pd.notna(val) else 0)
                    })
            if not is_max and not is_min:
                try:
                    filtered_df = filtered_df.sort_values(by=[grp_col])
                except Exception:
                    pass

        # Convert all filtered/processed rows so the web table and export share the complete single source of truth (Rules 11 & 12)
        full_processed_df = filtered_df.copy()
        for col in full_processed_df.columns:
            full_processed_df[col] = full_processed_df[col].apply(lambda v: None if pd.isna(v) else str(v))
        rows = full_processed_df.to_dict(orient="records")

        summary["sourceRowCount"] = len(df)
        summary["sourceColumnCount"] = len(df.columns)
        summary["processedRowCount"] = len(rows)
        summary["generatedTotalRows"] = 0
        summary["detectedColumns"] = headers

        return summary, headers, rows, chart_data
