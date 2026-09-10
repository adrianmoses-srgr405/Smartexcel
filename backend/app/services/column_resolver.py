import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple
from app.knowledge.domain_synonyms import DOMAIN_SYNONYMS

class ColumnResolver:
    """
    Intelligent Column Resolver with Multi-Tier Matching, Domain Synonyms,
    Fuzzy Matching, Data Type Compatibility & Ambiguity Detection.
    """

    FUZZY_THRESHOLD = 0.75
    AMBIGUITY_DELTA = 0.05

    @classmethod
    def resolve_column(
        cls,
        term: str,
        columns: List[Dict[str, Any]],
        expected_type: Optional[str] = None # "Numeric", "Text", "Date", None
    ) -> Dict[str, Any]:
        """
        Resolves a user-provided term to a specific dataset column.
        """
        if not term or not columns:
            return {"resolved": False, "matched_column": None, "column_letter": None, "confidence": 0.0}

        clean_term = cls._normalize_text(term)

        # 1. Exact Match (Normalized)
        for col in columns:
            col_name = col.get("original_name", "")
            if cls._normalize_text(col_name) == clean_term:
                return cls._build_result(col, 1.0, "exact_match", expected_type)

        # 2. Exact Domain Synonym Match
        synonym_candidates = cls._get_synonyms(clean_term)
        for col in columns:
            col_norm = cls._normalize_text(col.get("original_name", ""))
            if col_norm in synonym_candidates:
                return cls._build_result(col, 0.95, "synonym_match", expected_type)

        # 3. Substring Containment Match (Only if clean_term matches a complete token or longer)
        # Sort columns so longer/more specific column names don't get wrongly shadowed
        sorted_cols = sorted(columns, key=lambda c: len(cls._normalize_text(c.get("original_name", ""))), reverse=True)
        for col in sorted_cols:
            col_norm = cls._normalize_text(col.get("original_name", ""))
            # Require word boundary or equality
            if col_norm == clean_term:
                return cls._build_result(col, 1.0, "exact_match", expected_type)
            if re.search(rf"\b{re.escape(clean_term)}\b", col_norm) or re.search(rf"\b{re.escape(col_norm)}\b", clean_term):
                return cls._build_result(col, 0.85, "substring_match", expected_type)

        # 4. Synonym Substring Match
        for col in sorted_cols:
            col_norm = cls._normalize_text(col.get("original_name", ""))
            for syn in synonym_candidates:
                if len(syn) >= 3 and (re.search(rf"\b{re.escape(syn)}\b", col_norm) or re.search(rf"\b{re.escape(col_norm)}\b", syn)):
                    return cls._build_result(col, 0.80, "synonym_substring", expected_type)

        # 5. Strict Fuzzy Matching with Ambiguity Detection
        scored_matches = []
        for col in columns:
            col_norm = cls._normalize_text(col.get("original_name", ""))
            ratio = SequenceMatcher(None, clean_term, col_norm).ratio()
            if ratio >= cls.FUZZY_THRESHOLD:
                scored_matches.append((col, ratio))

        if scored_matches:
            scored_matches.sort(key=lambda x: x[1], reverse=True)
            top_col, top_score = scored_matches[0]

            # Check if second match is too close (Ambiguity)
            if len(scored_matches) > 1:
                second_col, second_score = scored_matches[1]
                if abs(top_score - second_score) <= cls.AMBIGUITY_DELTA:
                    return {
                        "resolved": False,
                        "status": "ambiguous_column",
                        "candidates": [top_col.get("original_name"), second_col.get("original_name")],
                        "matched_column": None,
                        "column_letter": None,
                        "confidence": 0.50
                    }

            return cls._build_result(top_col, round(top_score, 3), "fuzzy_match", expected_type)

        return {"resolved": False, "matched_column": None, "column_letter": None, "confidence": 0.0}

    @classmethod
    def resolve_all_mappings(
        cls,
        target_term: Optional[str],
        conditions: List[Dict[str, Any]],
        columns: List[Dict[str, Any]],
        operation: str
    ) -> Dict[str, Any]:
        """
        Resolves both target column and condition columns against dataset schema.
        """
        mapping_result = {
            "target": None,
            "conditions": [],
            "all_resolved": True,
            "overall_column_confidence": 1.0,
            "validation_errors": []
        }

        # 1. Resolve Target Column
        target_expected_type = "Numeric" if operation in ["SUM", "SUMIF", "SUMIFS", "AVERAGE", "AVERAGEIF", "AVERAGEIFS", "MAX", "MIN"] else None
        
        if target_term and cls._normalize_text(target_term) not in ["data", "nilai", "seluruh data", "semua data", "angka"]:
            res_target = cls.resolve_column(target_term, columns, expected_type=target_expected_type)
            mapping_result["target"] = res_target
            if not res_target.get("resolved"):
                mapping_result["all_resolved"] = False
                mapping_result["validation_errors"].append(f"Kolom target '{target_term}' tidak ditemukan dalam dataset.")
            elif res_target.get("type_incompatible"):
                mapping_result["all_resolved"] = False
                mapping_result["validation_errors"].append(f"Kolom '{res_target['matched_column']}' bertipe {res_target['inferred_type']}, tidak kompatibel untuk operasi numerik {operation}.")
        else:
            # Pick first available MEASURE column from columns
            measure_col = None
            for c in columns:
                if c.get("semantic_type") == "MEASURE" or c.get("is_summable"):
                    measure_col = c
                    break
            if not measure_col:
                for c in columns:
                    inferred = (c.get("inferred_type") or "").lower()
                    c_name = c.get("original_name", "").lower()
                    if ("num" in inferred or "float" in inferred or "int" in inferred) and not any(ex in c_name for ex in ["id", "no", "kode", "tahun", "plant", "tgl", "tanggal"]):
                        measure_col = c
                        break
            if measure_col and target_expected_type == "Numeric":
                res_target = cls._build_result(measure_col, 0.90, "default_primary_measure", target_expected_type)
                mapping_result["target"] = res_target
            elif operation in ["SUM", "AVERAGE"]:
                mapping_result["all_resolved"] = False
                mapping_result["validation_errors"].append(f"Operasi {operation} memerlukan kolom target numerik yang jelas.")

        # 2. Resolve Condition Columns
        cond_confidences = []
        for cond in conditions:
            hint = cond.get("column_hint") or cond.get("field") or cond.get("matched_column")
            res_cond = cls.resolve_column(hint, columns)
            cond_copy = dict(cond)
            cond_copy["column_hint"] = hint
            cond_copy["matched_column"] = res_cond.get("matched_column")
            cond_copy["resolved_column"] = res_cond.get("matched_column")
            cond_copy["column_letter"] = res_cond.get("column_letter")
            cond_copy["column_index"] = res_cond.get("column_index")
            cond_copy["confidence"] = res_cond.get("confidence", 0.0)
            
            cond_confidences.append(res_cond.get("confidence", 0.0))
            if not res_cond.get("resolved"):
                mapping_result["all_resolved"] = False
                mapping_result["validation_errors"].append(f"Kolom kriteria untuk '{hint}' tidak ditemukan dalam dataset.")
            
            mapping_result["conditions"].append(cond_copy)

        # Compute overall confidence
        all_confs = []
        if mapping_result["target"]:
            all_confs.append(mapping_result["target"].get("confidence", 0.0))
        all_confs.extend(cond_confidences)

        if all_confs:
            mapping_result["overall_column_confidence"] = round(sum(all_confs) / len(all_confs), 3)
        else:
            mapping_result["overall_column_confidence"] = 0.80

        return mapping_result

    @classmethod
    def resolve_columns(
        cls,
        target_term: Optional[str],
        conditions: List[Dict[str, Any]],
        columns_profile: List[Dict[str, Any]],
        operation: str = "SUM"
    ) -> Dict[str, Any]:
        mapping = cls.resolve_all_mappings(target_term, conditions, columns_profile, operation)
        return {
            "target_column": mapping.get("target"),
            "conditions": mapping.get("conditions", []),
            "column_confidence": mapping.get("overall_column_confidence", 0.90),
            "validation_errors": mapping.get("validation_errors", [])
        }

    @staticmethod
    def _normalize_text(text: str) -> str:
        t = re.sub(r"[_\-\s]+", " ", text.strip().lower())
        return t

    @classmethod
    def _get_synonyms(cls, clean_term: str) -> List[str]:
        synonyms = [clean_term]
        # Direct lookup
        if clean_term in DOMAIN_SYNONYMS:
            val = DOMAIN_SYNONYMS[clean_term]
            if isinstance(val, list):
                synonyms.extend(val)
            else:
                synonyms.append(str(val))
        # Reverse lookup
        for key, syn_list in DOMAIN_SYNONYMS.items():
            s_list = syn_list if isinstance(syn_list, list) else [syn_list]
            if clean_term in s_list:
                synonyms.append(key)
                synonyms.extend(s_list)
        return list(set(synonyms))

    @staticmethod
    def _build_result(col: Dict[str, Any], conf: float, match_type: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
        inferred_type = col.get("inferred_type", "Text")
        type_incompatible = False

        if expected_type == "Numeric" and inferred_type not in ["Numeric", "Integer", "Float"]:
            type_incompatible = True

        return {
            "resolved": not type_incompatible,
            "matched_column": col.get("original_name"),
            "original_name": col.get("original_name"),
            "column_letter": col.get("excel_column_letter") or col.get("column_letter", "A"),
            "column_index": col.get("column_index", 0),
            "inferred_type": inferred_type,
            "type_incompatible": type_incompatible,
            "confidence": conf if not type_incompatible else 0.30,
            "match_type": match_type
        }
