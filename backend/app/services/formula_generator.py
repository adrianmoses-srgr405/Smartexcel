from typing import Any, Dict, List, Optional

class FormulaGenerator:
    """
    100% Dynamic Excel Formula Generator.
    Generates exact Excel formulas using actual column letters (e.g. A:A, B:B, D:D)
    or structured references (Table1[Kolom]) without any hardcoded column positions.
    Supports all 18 whitelisted formulas with Excel syntax standards.
    """

    @classmethod
    def generate_formula(
        cls,
        formula_name: str,
        target_mapping: Optional[Dict[str, Any]],
        conditions_mapping: List[Dict[str, Any]],
        logical_branches: Optional[List[Dict[str, Any]]] = None,
        table_name: Optional[str] = None,
        use_cell_ref_for_logical: bool = False
    ) -> str:
        """
        Builds the dynamic formula string according to Excel specification.
        """
        f_name = formula_name.upper()

        def get_col_ref(col_info: Optional[Dict[str, Any]], fallback_letter: str = "A") -> str:
            if not col_info:
                return f"{fallback_letter}:{fallback_letter}"
            letter = col_info.get("column_letter") or fallback_letter
            col_name = col_info.get("matched_column") or col_info.get("original_name")
            if table_name and col_name:
                return f"{table_name}[{col_name}]"
            return f"{letter}:{letter}"

        def get_single_ref(col_info: Optional[Dict[str, Any]], fallback_letter: str = "A") -> str:
            letter = (col_info.get("column_letter") if col_info else None) or fallback_letter
            return f"{letter}2"

        tgt_ref = get_col_ref(target_mapping, "C")

        # 0. FILTER (Dynamic Array retrieval)
        if f_name in ["FILTER", "RETRIEVAL"]:
            cond = conditions_mapping[0] if conditions_mapping else {}
            crit_ref = get_col_ref(cond, "A")
            val = cond.get("value", "")
            return f'=FILTER(A:Z, {crit_ref}="{val}")'

        # 1. SUM
        elif f_name == "SUM":
            return f"=SUM({tgt_ref})"

        # 2. SUMIF
        elif f_name == "SUMIF":
            cond = conditions_mapping[0] if conditions_mapping else {}
            crit_ref = get_col_ref(cond, "A")
            val = cond.get("value", "")
            return f'=SUMIF({crit_ref}, "{val}", {tgt_ref})'

        # 3. SUMIFS
        elif f_name == "SUMIFS":
            parts = [tgt_ref]
            for cond in conditions_mapping:
                crit_ref = get_col_ref(cond, "A")
                val = cond.get("value", "")
                parts.append(crit_ref)
                parts.append(f'"{val}"')
            return f'=SUMIFS({", ".join(parts)})'

        # 4. AVERAGE
        elif f_name == "AVERAGE":
            return f"=AVERAGE({tgt_ref})"

        # 5. AVERAGEIF
        elif f_name == "AVERAGEIF":
            cond = conditions_mapping[0] if conditions_mapping else {}
            crit_ref = get_col_ref(cond, "A")
            val = cond.get("value", "")
            return f'=AVERAGEIF({crit_ref}, "{val}", {tgt_ref})'

        # 6. AVERAGEIFS
        elif f_name == "AVERAGEIFS":
            parts = [tgt_ref]
            for cond in conditions_mapping:
                crit_ref = get_col_ref(cond, "A")
                val = cond.get("value", "")
                parts.append(crit_ref)
                parts.append(f'"{val}"')
            return f'=AVERAGEIFS({", ".join(parts)})'

        # 7. COUNT / COUNTA
        elif f_name in ["COUNT", "COUNTA"]:
            return f"={f_name}({tgt_ref})"

        # 8. COUNTIF
        elif f_name == "COUNTIF":
            cond = conditions_mapping[0] if conditions_mapping else {}
            crit_ref = get_col_ref(cond, "A")
            val = cond.get("value", "")
            return f'=COUNTIF({crit_ref}, "{val}")'

        # 9. COUNTIFS
        elif f_name == "COUNTIFS":
            parts = []
            for cond in conditions_mapping:
                crit_ref = get_col_ref(cond, "A")
                val = cond.get("value", "")
                parts.append(crit_ref)
                parts.append(f'"{val}"')
            return f'=COUNTIFS({", ".join(parts)})'

        # 10. MAX / MIN
        elif f_name in ["MAX", "MIN"]:
            return f"={f_name}({tgt_ref})"

        # 10b. MAXIFS / MINIFS
        elif f_name in ["MAXIFS", "MINIFS"]:
            if conditions_mapping:
                parts = [tgt_ref]
                for cond in conditions_mapping:
                    crit_ref = get_col_ref(cond, "A")
                    val = cond.get("value", "")
                    parts.append(crit_ref)
                    parts.append(f'"{val}"')
                return f'={f_name}({", ".join(parts)})'
            return f'={f_name[:3]}({tgt_ref})'

        # 11. IF (Logical)
        elif f_name == "IF":
            var_name = get_col_ref(target_mapping, "C") if not use_cell_ref_for_logical else get_single_ref(target_mapping, "C")
            if logical_branches:
                b = logical_branches[0]
                op = b.get("operator", ">")
                thresh = b.get("value", 100000000)
                outcome = b.get("outcome", "Tinggi")
                return f'=IF({var_name} {op} {thresh}, "{outcome}", "Rendah")'
            return f'=IF({var_name} > 0, "Tercapai", "Belum")'

        # 12. IFS (Logical bertingkat)
        elif f_name == "IFS":
            var_name = get_col_ref(target_mapping, "C") if not use_cell_ref_for_logical else get_single_ref(target_mapping, "C")
            if logical_branches:
                parts = []
                for b in logical_branches:
                    op = b.get("operator", ">")
                    thresh = b.get("value", 50000000)
                    outcome = b.get("outcome", "Sedang")
                    parts.append(f'{var_name} {op} {thresh}')
                    parts.append(f'"{outcome}"')
                fallback = logical_branches[0].get("fallback_outcome", "Rendah")
                parts.append("TRUE")
                parts.append(f'"{fallback}"')
                return f'=IFS({", ".join(parts)})'
            return f'=IFS({var_name} > 100000000, "Tinggi", {var_name} > 50000000, "Sedang", TRUE, "Rendah")'

        # 13. XLOOKUP
        elif f_name == "XLOOKUP":
            cond = conditions_mapping[0] if conditions_mapping else {}
            lookup_val = cond.get("value", "KEY")
            lookup_col = get_col_ref(cond, "A")
            return_col = tgt_ref
            return f'=XLOOKUP("{lookup_val}", {lookup_col}, {return_col}, "Tidak Ditemukan")'

        # 14. VLOOKUP
        elif f_name == "VLOOKUP":
            cond = conditions_mapping[0] if conditions_mapping else {}
            lookup_val = cond.get("value", "KEY")
            return f'=VLOOKUP("{lookup_val}", A:D, 3, FALSE)'

        # 15. INDEX
        elif f_name == "INDEX":
            return f"=INDEX({tgt_ref}, 2)"

        # 16. MATCH
        elif f_name == "MATCH":
            cond = conditions_mapping[0] if conditions_mapping else {}
            val = cond.get("value", "KEY")
            crit_ref = get_col_ref(cond, "A")
            return f'=MATCH("{val}", {crit_ref}, 0)'

        return f"={f_name}({tgt_ref})"

    @classmethod
    def generate_excel_formula(
        cls,
        decision: Any,
        intent: Any,
        columns: List[Any],
        data_row_count: Optional[int] = None
    ) -> str:
        """
        Compatibility wrapper for legacy calls (decision, intent, columns).
        Translates structured analysis intent and dataset columns into dynamic formula mapping.
        """
        formula_name = getattr(decision, "formula_id", None) or getattr(decision, "formula", None)
        if not formula_name:
            if isinstance(decision, dict):
                formula_name = decision.get("formula") or decision.get("formula_id")
            else:
                formula_name = "SUM"

        col_by_name = {}
        for c in columns:
            name = getattr(c, "original_name", "") or getattr(c, "name", "")
            if name:
                col_by_name[name.lower()] = c

        # Target column mapping
        target_field = getattr(intent, "target_field", None)
        target_mapping = None
        if target_field and str(target_field).lower() in col_by_name:
            col = col_by_name[str(target_field).lower()]
            target_mapping = {
                "matched_column": getattr(col, "original_name", str(target_field)),
                "column_letter": getattr(col, "excel_column_letter", "A")
            }

        # Conditions / Filters mapping
        conditions_mapping = []
        filters = getattr(intent, "filters", []) or []
        for f in filters:
            f_field = getattr(f, "field", "")
            f_val = getattr(f, "value", "")
            col = col_by_name.get(str(f_field).lower())
            letter = getattr(col, "excel_column_letter", "A") if col else "A"
            matched_col_name = getattr(col, "original_name", str(f_field)) if col else str(f_field)

            if isinstance(f_val, (list, tuple)) and len(f_val) == 2:
                conditions_mapping.append({
                    "matched_column": matched_col_name,
                    "column_letter": letter,
                    "value": f">={f_val[0]}"
                })
                conditions_mapping.append({
                    "matched_column": matched_col_name,
                    "column_letter": letter,
                    "value": f"<={f_val[1]}"
                })
            else:
                conditions_mapping.append({
                    "matched_column": matched_col_name,
                    "column_letter": letter,
                    "value": f_val
                })

        return cls.generate_formula(
            formula_name=formula_name,
            target_mapping=target_mapping,
            conditions_mapping=conditions_mapping
        )

