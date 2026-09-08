from datetime import datetime
from typing import Any
import pandas as pd
from app.schemas.intent import StructuredAnalysisIntent, FormulaDecisionResult
from app.models.dataset import DatasetColumn

class FormulaGenerator:
    @staticmethod
    def _format_filter_value_for_excel(val: Any, data_type: str = "text", op: str = "=") -> str:
        """Formats criterion value for Excel formula (e.g. \"Lenovo\", \">=\"&DATE(2024,2,1))."""
        if isinstance(val, list) and len(val) == 2:
            try:
                d1 = pd.to_datetime(val[0])
                d2 = pd.to_datetime(val[1])
                return f'">="&DATE({d1.year},{d1.month},{d1.day})'
            except Exception:
                return f'"{val}"'

        if data_type == "date":
            try:
                dt = pd.to_datetime(val)
                date_func = f'DATE({dt.year},{dt.month},{dt.day})'
                if op in ["=", "=="]:
                    return f'"{date_func}"'
                return f'"{op}"&{date_func}'
            except Exception:
                return f'"{op}{val}"'
        elif data_type == "numeric":
            if op in ["=", "=="]:
                return str(val)
            return f'"{op}{val}"'
        else:
            # Text / Categorical
            if op == "CONTAINS":
                return f'"*{val}*"'
            elif op == "STARTS_WITH":
                return f'"{val}*"'
            elif op == "ENDS_WITH":
                return f'"*{val}"'
            elif op not in ["=", "=="]:
                return f'"{op}{val}"'
            return f'"{val}"'

    @classmethod
    def generate_excel_formula(
        cls,
        decision: FormulaDecisionResult,
        intent: StructuredAnalysisIntent,
        columns: list[DatasetColumn],
        data_row_count: int = 100
    ) -> str:
        """
        Generates genuine Excel formula string with accurate column letters.
        """
        col_letter_map = {col.original_name.lower(): col.excel_column_letter for col in columns}
        col_type_map = {col.original_name.lower(): col.inferred_type.lower() for col in columns}

        target_letter = col_letter_map.get(intent.target_field.lower(), "E") if intent.target_field else "E"
        fid = decision.formula_id.upper()

        if fid == "SUM":
            return f"=SUM({target_letter}:{target_letter})"
        
        elif fid == "SUMIF":
            if intent.filters:
                flt = intent.filters[0]
                flt_letter = col_letter_map.get(flt.field.lower(), "C")
                flt_type = col_type_map.get(flt.field.lower(), flt.data_type or "text")
                crit_val = cls._format_filter_value_for_excel(flt.value, flt_type, flt.operator)
                return f"=SUMIF({flt_letter}:{flt_letter}, {crit_val}, {target_letter}:{target_letter})"
            elif intent.group_by:
                grp_col = intent.group_by[0]
                grp_letter = col_letter_map.get(grp_col.lower(), "C")
                return f"=SUMIF({grp_letter}:{grp_letter}, H2, {target_letter}:{target_letter})"
            return f"=SUM({target_letter}:{target_letter})"

        elif fid == "SUMIFS":
            criteria_parts = []
            if intent.group_by:
                for grp in intent.group_by:
                    grp_letter = col_letter_map.get(grp.lower(), "C")
                    criteria_parts.append(f'{grp_letter}:{grp_letter}, "Kategori"')

            for flt in intent.filters:
                flt_letter = col_letter_map.get(flt.field.lower(), "C")
                flt_type = col_type_map.get(flt.field.lower(), flt.data_type or "text")
                
                # If filter value is date range [start, end]
                if isinstance(flt.value, list) and len(flt.value) == 2 and (flt_type == "date" or "tgl" in flt.field.lower() or "tanggal" in flt.field.lower()):
                    d1 = pd.to_datetime(flt.value[0])
                    d2 = pd.to_datetime(flt.value[1])
                    start_crit = f'">="&DATE({d1.year},{d1.month},{d1.day})'
                    end_crit = f'"<="&DATE({d2.year},{d2.month},{d2.day})'
                    criteria_parts.append(f"{flt_letter}:{flt_letter}, {start_crit}")
                    criteria_parts.append(f"{flt_letter}:{flt_letter}, {end_crit}")
                else:
                    crit_val = cls._format_filter_value_for_excel(flt.value, flt_type, flt.operator)
                    criteria_parts.append(f"{flt_letter}:{flt_letter}, {crit_val}")
            
            if criteria_parts:
                return f"=SUMIFS({target_letter}:{target_letter}, {', '.join(criteria_parts)})"
            return f"=SUM({target_letter}:{target_letter})"

        elif fid == "AVERAGE":
            return f"=AVERAGE({target_letter}:{target_letter})"

        elif fid == "AVERAGEIF":
            if intent.filters:
                flt = intent.filters[0]
                flt_letter = col_letter_map.get(flt.field.lower(), "C")
                flt_type = col_type_map.get(flt.field.lower(), flt.data_type or "text")
                crit_val = cls._format_filter_value_for_excel(flt.value, flt_type, flt.operator)
                return f"=AVERAGEIF({flt_letter}:{flt_letter}, {crit_val}, {target_letter}:{target_letter})"
            elif intent.group_by:
                grp_letter = col_letter_map.get(intent.group_by[0].lower(), "C")
                return f"=AVERAGEIF({grp_letter}:{grp_letter}, H2, {target_letter}:{target_letter})"
            return f"=AVERAGE({target_letter}:{target_letter})"

        elif fid == "AVERAGEIFS":
            criteria_parts = []
            for flt in intent.filters:
                flt_letter = col_letter_map.get(flt.field.lower(), "C")
                flt_type = col_type_map.get(flt.field.lower(), flt.data_type or "text")
                crit_val = cls._format_filter_value_for_excel(flt.value, flt_type, flt.operator)
                criteria_parts.append(f"{flt_letter}:{flt_letter}, {crit_val}")
            return f"=AVERAGEIFS({target_letter}:{target_letter}, {', '.join(criteria_parts)})"

        elif fid == "COUNT":
            return f"=COUNTA({target_letter}:{target_letter})"

        elif fid == "COUNTIF":
            if intent.filters:
                flt = intent.filters[0]
                flt_letter = col_letter_map.get(flt.field.lower(), "C")
                flt_type = col_type_map.get(flt.field.lower(), flt.data_type or "text")
                crit_val = cls._format_filter_value_for_excel(flt.value, flt_type, flt.operator)
                return f"=COUNTIF({flt_letter}:{flt_letter}, {crit_val})"
            elif intent.group_by:
                grp_letter = col_letter_map.get(intent.group_by[0].lower(), "C")
                return f"=COUNTIF({grp_letter}:{grp_letter}, H2)"
            return f"=COUNTA({target_letter}:{target_letter})"

        elif fid == "COUNTIFS":
            criteria_parts = []
            for flt in intent.filters:
                flt_letter = col_letter_map.get(flt.field.lower(), "C")
                flt_type = col_type_map.get(flt.field.lower(), flt.data_type or "text")
                crit_val = cls._format_filter_value_for_excel(flt.value, flt_type, flt.operator)
                criteria_parts.append(f"{flt_letter}:{flt_letter}, {crit_val}")
            return f"=COUNTIFS({', '.join(criteria_parts)})"

        elif fid == "MAX":
            return f"=MAX({target_letter}:{target_letter})"

        elif fid == "MIN":
            return f"=MIN({target_letter}:{target_letter})"

        elif fid == "XLOOKUP":
            # e.g. =XLOOKUP("HP-003", B:B, D:D, "Tidak Ditemukan")
            lookup_val = '"HP-003"'
            if intent.filters:
                lookup_val = f'"{intent.filters[0].value}"'
            lookup_letter = col_letter_map.get("kode barang", "B")
            return_letter = col_letter_map.get("nama barang", "D")
            return f'=XLOOKUP({lookup_val}, {lookup_letter}:{lookup_letter}, {return_letter}:{return_letter}, "Tidak Ditemukan")'

        elif fid == "FILTER":
            first_letter = columns[0].excel_column_letter if columns else "A"
            last_letter = columns[-1].excel_column_letter if columns else "Z"
            end_row = data_row_count + 1 if data_row_count else 1000
            data_range = f"{first_letter}2:{last_letter}{end_row}"

            if not intent.filters:
                return f'=FILTER({data_range}, {first_letter}2:{first_letter}{end_row}<>"", "Tidak Ada Data")'

            cond_parts = []
            for flt in intent.filters:
                flt_letter = col_letter_map.get(flt.field.lower(), "A")
                flt_range = f"{flt_letter}2:{flt_letter}{end_row}"
                val = str(flt.value).strip()
                if flt.operator in ["=", "=="]:
                    cond_parts.append(f'({flt_range}="{val}")')
                elif flt.operator in ["!=", "<>"]:
                    cond_parts.append(f'({flt_range}<>"{val}")')
                elif flt.operator in [">", ">=", "<", "<="]:
                    cond_parts.append(f'({flt_range}{flt.operator}{val})')
                else:
                    cond_parts.append(f'({flt_range}="{val}")')

            condition_str = " * ".join(cond_parts) if len(cond_parts) > 1 else cond_parts[0]
            return f'=FILTER({data_range}, {condition_str}, "Tidak Ada Data")'

        return f"=SUM({target_letter}:{target_letter})"

