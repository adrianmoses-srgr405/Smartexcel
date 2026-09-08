import json
from pathlib import Path
from typing import Any, Optional, Dict
from app.schemas.intent import StructuredAnalysisIntent, FormulaDecisionResult
from app.models.dataset import DatasetColumn
from app.services.ml_classifier import ml_classifier

class FormulaDecisionEngine:
    """
    HYBRID AI FORMULA DECISION ENGINE
    Pipeline:
    1. Feature Extraction from LLM Intent & Dataset Schema
    2. Machine Learning Formula Classifier (Random Forest) -> Predicted Formula + Confidence Score
    3. Rule-Based Engine & Knowledge Base Validation (Highest Priority Gatekeeper) -> Corrects / Validates ML
    4. Confidence Threshold Gate (< 0.70 prompts confirmation)
    5. Knowledge Base Metadata & Parameter Synthesis
    """

    def __init__(self, kb_path: Optional[Path] = None):
        if kb_path is None:
            kb_path = Path(__file__).resolve().parent.parent / "knowledge" / "formula_kb.json"
        
        self.kb_rules: dict[str, dict[str, Any]] = {}
        if kb_path.exists():
            with open(kb_path, "r", encoding="utf-8") as f:
                rules_list = json.load(f)
                for item in rules_list:
                    self.kb_rules[item["id"]] = item

    def _extract_ml_features(
        self,
        intent: StructuredAnalysisIntent,
        columns: list[DatasetColumn]
    ) -> Dict[str, Any]:
        """
        Extracts 8 normalized feature signals for the Machine Learning Classifier.
        """
        col_map = {col.original_name.lower(): col for col in columns}
        
        op = intent.operation.upper()
        filter_count = len(intent.filters)
        grouping_count = len(intent.group_by)
        
        has_date_filter = 0
        filter_data_types = []
        for flt in intent.filters:
            col = col_map.get(flt.field.lower())
            col_type = col.inferred_type.lower() if col else "categorical"
            if "date" in col_type or flt.operator.upper() in ["BETWEEN", "DATE_RANGE"]:
                has_date_filter = 1
                filter_data_types.append("date")
            elif "num" in col_type:
                filter_data_types.append("numeric")
            else:
                filter_data_types.append("categorical")

        filter_data_type = "none"
        if filter_data_types:
            filter_data_type = filter_data_types[0] if len(set(filter_data_types)) == 1 else "mixed"

        target_data_type = "numeric"
        if intent.target_field:
            target_col = col_map.get(intent.target_field.lower())
            if target_col:
                target_data_type = target_col.inferred_type.lower()

        has_multiple_criteria = 1 if (filter_count >= 2 or grouping_count >= 2 or (filter_count >= 1 and grouping_count >= 1)) else 0

        return {
            "operation": op,
            "intent": intent.intent.lower(),
            "filter_count": filter_count,
            "grouping_count": grouping_count,
            "has_date_filter": has_date_filter,
            "has_multiple_criteria": has_multiple_criteria,
            "target_data_type": target_data_type,
            "filter_data_type": filter_data_type
        }

    def decide_formula(
        self,
        intent: StructuredAnalysisIntent,
        columns: list[DatasetColumn]
    ) -> FormulaDecisionResult:
        """
        Executes the Hybrid AI Decision Pipeline.
        """
        col_map = {col.original_name.lower(): col for col in columns}
        validation_messages = []
        validation_status = "PASSED"

        # -------------------------------------------------------------
        # 1. Feature Extraction for ML
        # -------------------------------------------------------------
        features = self._extract_ml_features(intent, columns)
        
        # -------------------------------------------------------------
        # 2. Machine Learning Prediction (Random Forest)
        # -------------------------------------------------------------
        ml_result = ml_classifier.predict(features)
        ml_prediction = ml_result.get("predicted_formula", "SUM")
        ml_confidence = float(ml_result.get("confidence", 0.95))
        is_confident = ml_result.get("is_confident", True)
        probabilities = ml_result.get("probabilities", {})

        # -------------------------------------------------------------
        # 3. Rule-Based Engine & Knowledge Base Validation (Highest Priority)
        # -------------------------------------------------------------
        op = intent.operation.upper()
        num_filters = len(intent.filters)
        has_grouping = len(intent.group_by) > 0
        intent_type = intent.intent.lower()

        # Determine strictly valid mathematical formula according to business logic
        rule_target_formula = "SUM"
        rule_reason = ""

        if intent_type in ["filter_recap", "filter"] or op == "FILTER":
            rule_target_formula = "FILTER"
            filter_descs = [f"{f.field} {f.operator} {f.value}" for f in intent.filters]
            rule_reason = f"Ekstraksi seluruh baris data terfilter ({', '.join(filter_descs) if filter_descs else 'semua baris'}) ke dalam bentuk tabel data terstruktur."
        elif intent_type == "lookup" or op == "XLOOKUP":
            rule_target_formula = "XLOOKUP"
            rule_reason = "Intent analisis adalah pencarian data spesifik berdasarkan kunci referensi (XLOOKUP)."
        elif intent_type == "ranking" or op in ["MAX", "HIGHEST"]:
            rule_target_formula = "MAX"
            rule_reason = "Intent analisis adalah menemukan nilai kuantitatif maksimum/tertinggi."

        elif op in ["MIN", "LOWEST"]:
            rule_target_formula = "MIN"
            rule_reason = "Intent analisis adalah menemukan nilai kuantitatif minimum/terendah."
        elif has_grouping and intent_type in ["pivot_summary"]:
            rule_target_formula = "PIVOT"
            rule_reason = f"Laporan ringkasan matriks multi-dimensi per {', '.join(intent.group_by)}."
        elif has_grouping and intent_type in ["aggregation"]:
            if num_filters >= 1:
                rule_target_formula = "SUMIFS" if op == "SUM" else ("AVERAGEIFS" if op == "AVERAGE" else "COUNTIFS")
                rule_reason = f"Laporan rekapitulasi per {', '.join(intent.group_by)} dengan {num_filters} kriteria filter."
            else:
                rule_target_formula = "SUMIF" if op == "SUM" else ("AVERAGEIF" if op == "AVERAGE" else "COUNTIF")
                rule_reason = f"Laporan rekapitulasi per kategori {', '.join(intent.group_by)} menggunakan kalkulasi per-kategori."
        elif op == "SUM":
            if num_filters == 0:
                rule_target_formula = "SUM"
                rule_reason = "Total penjumlahan data numerik tanpa kriteria filter."
            elif num_filters == 1:
                rule_target_formula = "SUMIF"
                filter_desc = f"{intent.filters[0].field} {intent.filters[0].operator} {intent.filters[0].value}"
                rule_reason = f"Total penjumlahan data dengan tepat 1 kriteria filter ({filter_desc})."
            else:
                rule_target_formula = "SUMIFS"
                filter_descs = [f"{f.field} {f.operator} {f.value}" for f in intent.filters]
                rule_reason = f"Total penjumlahan data dengan multi-kriteria ({num_filters} filter: {', '.join(filter_descs)})."
        elif op == "AVERAGE":
            if num_filters == 0:
                rule_target_formula = "AVERAGE"
                rule_reason = "Nilai rata-rata keseluruhan tanpa kriteria filter."
            elif num_filters == 1:
                rule_target_formula = "AVERAGEIF"
                filter_desc = f"{intent.filters[0].field} {intent.filters[0].operator} {intent.filters[0].value}"
                rule_reason = f"Nilai rata-rata dengan tepat 1 kriteria filter ({filter_desc})."
            else:
                rule_target_formula = "AVERAGEIFS"
                filter_descs = [f"{f.field} {f.operator} {f.value}" for f in intent.filters]
                rule_reason = f"Nilai rata-rata dengan multi-kriteria ({num_filters} filter: {', '.join(filter_descs)})."
        elif op == "COUNT":
            if num_filters == 0:
                rule_target_formula = "COUNT"
                rule_reason = "Perhitungan total frekuensi/jumlah baris data."
            elif num_filters == 1:
                rule_target_formula = "COUNTIF"
                filter_desc = f"{intent.filters[0].field} {intent.filters[0].operator} {intent.filters[0].value}"
                rule_reason = f"Perhitungan frekuensi dengan 1 kriteria filter ({filter_desc})."
            else:
                rule_target_formula = "COUNTIFS"
                filter_descs = [f"{f.field} {f.operator} {f.value}" for f in intent.filters]
                rule_reason = f"Perhitungan frekuensi dengan {num_filters} kriteria filter."
        else:
            rule_target_formula = ml_prediction
            rule_reason = f"Operasi {op} diproses dengan formula {ml_prediction}."

        # RULE ENGINE EVALUATION & PRIORITY OVERRIDE
        if ml_prediction.upper() == rule_target_formula.upper():
            rule_validation_status = "VALID"
            rule_decision = f"Prediksi ML ({ml_prediction}) sesuai dengan aturan matematis Knowledge Base."
            final_formula_id = ml_prediction
        else:
            rule_validation_status = "CORRECTED_BY_RULE"
            rule_decision = f"Prediksi ML ({ml_prediction}) dikoreksi Rule Engine menjadi {rule_target_formula} ({rule_reason})."
            final_formula_id = rule_target_formula

        # -------------------------------------------------------------
        # 4. Confidence Threshold Gate
        # -------------------------------------------------------------
        if ml_confidence < 0.70:
            is_confident = False
            validation_messages.append(
                f"AI belum yakin dengan metode yang dipilih (Confidence: {int(ml_confidence*100)}% < 70%). Silakan konfirmasi kebutuhan laporan."
            )
            validation_status = "WARNING"

        # -------------------------------------------------------------
        # 5. Field Existence & Compatibility Validation
        # -------------------------------------------------------------
        affected_cols = []
        target_col_obj = None
        if intent.target_field:
            target_col_obj = col_map.get(intent.target_field.lower())
            if not target_col_obj:
                validation_status = "WARNING"
                validation_messages.append(f"Target field '{intent.target_field}' tidak ditemukan langsung di kolom dataset.")
            else:
                affected_cols.append({
                    "role": "target",
                    "column": target_col_obj.original_name,
                    "letter": target_col_obj.excel_column_letter,
                    "type": target_col_obj.inferred_type
                })
                if op in ["SUM", "AVERAGE"] and target_col_obj.inferred_type.lower() not in ["numeric", "integer", "float", "double"]:
                    validation_status = "WARNING"
                    validation_messages.append(f"Operasi {op} diaplikasikan pada kolom non-numeric ({target_col_obj.inferred_type}).")

        for grp in intent.group_by:
            grp_col = col_map.get(grp.lower())
            if grp_col:
                affected_cols.append({
                    "role": "group_by",
                    "column": grp_col.original_name,
                    "letter": grp_col.excel_column_letter,
                    "type": grp_col.inferred_type
                })
            else:
                validation_messages.append(f"Kolom grouping '{grp}' tidak ditemukan di dataset.")

        for flt in intent.filters:
            flt_col = col_map.get(flt.field.lower())
            if flt_col:
                affected_cols.append({
                    "role": "filter",
                    "column": flt_col.original_name,
                    "letter": flt_col.excel_column_letter,
                    "type": flt_col.inferred_type
                })
            else:
                validation_messages.append(f"Kolom filter '{flt.field}' tidak ditemukan di dataset.")

        # -------------------------------------------------------------
        # 6. Lookup Knowledge Base Info
        # -------------------------------------------------------------
        kb_info = self.kb_rules.get(final_formula_id, {
            "name": final_formula_id,
            "category": "Calculation",
            "syntax_template": f"={final_formula_id}(...)",
        })

        return FormulaDecisionResult(
            formula_id=final_formula_id,
            formula_name=kb_info.get("name", final_formula_id),
            category=kb_info.get("category", "Calculation"),
            reason=rule_reason,
            syntax_pattern=kb_info.get("syntax_template", ""),
            generated_excel_formula="", # Populated by FormulaGenerator
            affected_columns=affected_cols,
            validation_status=validation_status,
            validation_messages=validation_messages,
            ml_prediction=ml_prediction,
            ml_confidence=ml_confidence,
            is_confident=is_confident,
            rule_validation_status=rule_validation_status,
            rule_decision=rule_decision,
            probabilities=probabilities
        )

