from typing import Any, Dict, List, Optional, Tuple
from app.services.ml_classifier import ml_classifier

class FormulaDecisionResult(dict):
    """Result object supporting both dictionary key access and attribute property access."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    @property
    def formula_id(self) -> str:
        return self.get("formula", "")

    @property
    def ml_prediction(self) -> Optional[str]:
        return self.get("ml_candidate")

    @property
    def ml_confidence(self) -> float:
        return float(self.get("ml_confidence", 0.5))

    @property
    def rule_validation_status(self) -> str:
        return self.get("rule_status", "VALID")

    @property
    def rule_decision(self) -> str:
        return self.get("reason", "")

    @property
    def is_confident(self) -> bool:
        return self.get("decision_confidence", 1.0) >= 0.70 or self.get("rule_status") == "VALID"

class FormulaDecisionEngine:
    """
    Deterministic Decision Engine (Source of Truth).
    Evaluates:
    - Operation (SUM, AVERAGE, COUNT, MAX, MIN, LOOKUP, IF, IFS)
    - Condition count (0, 1, >=2)
    - Data type compatibility (Numeric vs Text for COUNT vs COUNTA)
    - Lookup modern priorities (XLOOKUP vs VLOOKUP)
    - Dual call signature: (operation, conditions_count, ...) or (intent, mock_columns)
    Overrides ML candidate when deterministic criteria are unambiguous.
    """

    @classmethod
    def decide_formula(
        cls,
        operation: Any = "SUM",
        conditions_count: Any = 0,
        target_data_type: Optional[str] = "Numeric",
        ml_candidate: Optional[str] = None,
        ml_confidence: float = 0.5,
        is_table: bool = False,
        logical_branches_count: int = 0
    ) -> FormulaDecisionResult:
        """
        Executes the deterministic decision matrix.
        Supports both new parameter syntax and legacy (intent, mock_columns) signature.
        """
        # Detect legacy signature: decide_formula(intent, mock_columns)
        if not isinstance(operation, str):
            intent_obj = operation
            mock_cols = conditions_count if isinstance(conditions_count, list) else []

            op_str = getattr(intent_obj, "operation", None) or getattr(intent_obj, "intent", "SUM")
            filters = getattr(intent_obj, "filters", []) or []
            cond_count = len(filters)

            target_field = getattr(intent_obj, "target_field", None)
            target_dtype = "Numeric"
            if mock_cols and target_field:
                for c in mock_cols:
                    c_name = getattr(c, "original_name", "") or getattr(c, "name", "")
                    if c_name.lower() == str(target_field).lower():
                        target_dtype = getattr(c, "inferred_type", "Numeric")
                        break

            ml_cand = None
            ml_conf = 0.5
            try:
                has_date = 1 if any("date" in str(getattr(f, "data_type", "")).lower() or getattr(f, "operator", "") == "BETWEEN" for f in filters) else 0
                feat = {
                    "operation": op_str,
                    "intent": getattr(intent_obj, "intent", "aggregation"),
                    "filter_count": len(filters),
                    "grouping_count": len(getattr(intent_obj, "group_by", []) or []),
                    "has_date_filter": has_date,
                    "has_multiple_criteria": 1 if len(filters) > 1 else 0,
                    "target_data_type": str(target_dtype).lower()
                }
                pred_res = ml_classifier.predict(feat)
                if isinstance(pred_res, dict):
                    ml_cand = pred_res.get("predicted_formula")
                    ml_conf = pred_res.get("confidence", 0.85)
            except Exception:
                pass

            return cls.decide_formula(
                operation=op_str,
                conditions_count=cond_count,
                target_data_type=target_dtype,
                ml_candidate=ml_cand,
                ml_confidence=ml_conf
            )

        op = str(operation).upper()
        final_formula = "SUM"
        reason = ""
        category = "Aggregation"
        rule_status = "VALID"
        decision_confidence = 1.0

        # 0. Retrieval / Filter (Non-aggregation row retrieval)
        if op in ["FILTER", "RETRIEVAL"]:
            final_formula = "FILTER"
            category = "Retrieval"
            reason = "Pengambilan baris data yang memenuhi kriteria filter."
            return FormulaDecisionResult({
                "formula": final_formula,
                "category": category,
                "reason": reason,
                "rule_status": "VALID",
                "decision_confidence": 1.0,
                "ml_candidate": ml_candidate,
                "ml_confidence": ml_confidence
            })

        # 1. Aggregation: SUM
        if op == "SUM":
            category = "Conditional Aggregation" if conditions_count > 0 else "Aggregation"
            if conditions_count == 0:
                final_formula = "SUM"
                reason = "Operasi penjumlahan tanpa kondisi filter."
            elif conditions_count == 1:
                final_formula = "SUMIF"
                reason = "Operasi penjumlahan dengan tepat satu kondisi filter."
            else:
                final_formula = "SUMIFS"
                reason = f"Operasi penjumlahan dengan {conditions_count} kondisi kriteria."

        # 2. Statistical: AVERAGE
        elif op == "AVERAGE":
            category = "Statistical"
            if conditions_count == 0:
                final_formula = "AVERAGE"
                reason = "Operasi rata-rata tanpa kondisi filter."
            elif conditions_count == 1:
                final_formula = "AVERAGEIF"
                reason = "Operasi rata-rata dengan tepat satu kondisi filter."
            else:
                final_formula = "AVERAGEIFS"
                reason = f"Operasi rata-rata dengan {conditions_count} kondisi kriteria."

        # 3. Counting: COUNT vs COUNTA
        elif op in ["COUNT", "COUNTA"]:
            category = "Counting"
            if conditions_count == 0:
                # Differentiate by data type
                if target_data_type in ["Numeric", "Integer", "Float"]:
                    final_formula = "COUNT"
                    reason = "Menghitung banyaknya baris pada kolom numerik."
                else:
                    final_formula = "COUNTA"
                    reason = "Menghitung banyaknya record terisi pada kolom teks/identifier."
            elif conditions_count == 1:
                final_formula = "COUNTIF"
                reason = "Menghitung frekuensi kemunculan dengan satu kondisi filter."
            else:
                final_formula = "COUNTIFS"
                reason = f"Menghitung frekuensi kemunculan dengan {conditions_count} kondisi kriteria."

        # 4. Statistical: MAX / MIN
        elif op == "MAX":
            category = "Statistical"
            if conditions_count > 0:
                final_formula = "MAXIFS"
                reason = f"Pencarian nilai maksimum dengan {conditions_count} kondisi kriteria."
            else:
                final_formula = "MAX"
                reason = "Pencarian nilai angka terbesar/maksimum tanpa filter."

        elif op == "MIN":
            category = "Statistical"
            if conditions_count > 0:
                final_formula = "MINIFS"
                reason = f"Pencarian nilai minimum dengan {conditions_count} kondisi kriteria."
            else:
                final_formula = "MIN"
                reason = "Pencarian nilai angka terkecil/minimum tanpa filter."

        # 5. Logical: IF / IFS
        elif op in ["IF", "IFS"]:
            category = "Logical"
            if logical_branches_count > 1 or conditions_count > 1:
                final_formula = "IFS"
                reason = "Evaluasi logika bertingkat / multi-kondisi jika-maka."
            else:
                final_formula = "IF"
                reason = "Evaluasi logika tunggal jika-maka."

        # 6. Lookup: XLOOKUP / VLOOKUP / INDEX / MATCH
        elif op in ["LOOKUP", "XLOOKUP", "VLOOKUP", "INDEX", "MATCH"]:
            category = "Lookup"
            if op == "VLOOKUP":
                final_formula = "VLOOKUP"
                reason = "Pencarian vertikal tabel spreadsheet referensi."
            elif op == "INDEX":
                final_formula = "INDEX"
                reason = "Pengambilan nilai koordinat sel baris/kolom."
            elif op == "MATCH":
                final_formula = "MATCH"
                reason = "Pencarian nomor urut baris suatu kunci."
            else:
                final_formula = "XLOOKUP"
                reason = "Fungsi lookup modern dua arah (XLOOKUP) sebagai prioritas utama."

        else:
            # Fallback to ML candidate if recognized
            if ml_candidate and ml_confidence >= 0.70:
                final_formula = ml_candidate
                reason = f"Dipilih berdasarkan prediksi model Random Forest ({ml_confidence*100:.1f}%)."
                decision_confidence = 0.80
            else:
                final_formula = "SUM"
                reason = "Operasi tidak spesifik, fallback ke agregasi standar SUM."
                decision_confidence = 0.50

        # 7. Compare with ML Candidate for Explainability & Corrections
        if ml_candidate and ml_candidate != final_formula:
            rule_status = "CORRECTED_BY_RULE"
            reason = f"Kandidat ML '{ml_candidate}' dikoreksi Rule Engine menjadi {final_formula} karena query terdeteksi memiliki {conditions_count} kondisi kriteria."
        elif ml_candidate and ml_candidate == final_formula:
            rule_status = "VALID"
            reason = f"{final_formula} dipilih secara konsisten oleh Decision Matrix dan kandidat ML ({ml_confidence*100:.1f}%)."

        return FormulaDecisionResult({
            "formula": final_formula,
            "category": category,
            "reason": reason,
            "rule_status": rule_status,
            "decision_confidence": decision_confidence,
            "ml_candidate": ml_candidate,
            "ml_confidence": ml_confidence
        })

