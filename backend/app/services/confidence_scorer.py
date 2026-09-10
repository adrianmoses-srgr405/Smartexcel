from typing import Any, Dict, Optional

class ConfidenceScorer:
    """
    Computes Composite Confidence Score for Hybrid AI Architecture.
    Weights:
    - 35% ML Candidate Probability / Confidence
    - 30% Deterministic Decision Matrix Confidence
    - 25% Column Resolution Quality
    - 10% Parameter Extraction Completeness
    """

    ML_WEIGHT = 0.35
    DECISION_WEIGHT = 0.30
    COLUMN_WEIGHT = 0.25
    PARAMETER_WEIGHT = 0.10

    @classmethod
    def calculate_confidence(
        cls,
        ml_confidence: float = 0.90,
        decision_confidence: float = 0.95,
        column_confidence: float = 0.90,
        parameter_confidence: float = 0.90,
        is_ambiguous: bool = False,
        ambiguity_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes composite confidence and categorizes level.
        """
        # Ensure values are bounded between 0.0 and 1.0
        ml_c = max(0.0, min(1.0, float(ml_confidence)))
        dec_c = max(0.0, min(1.0, float(decision_confidence)))
        col_c = max(0.0, min(1.0, float(column_confidence)))
        param_c = max(0.0, min(1.0, float(parameter_confidence)))

        raw_composite = (
            (cls.ML_WEIGHT * ml_c) +
            (cls.DECISION_WEIGHT * dec_c) +
            (cls.COLUMN_WEIGHT * col_c) +
            (cls.PARAMETER_WEIGHT * param_c)
        )

        # Cap if ambiguous parameter or query detected
        if is_ambiguous:
            raw_composite = min(raw_composite, 0.55)

        composite_score = round(raw_composite, 4)

        if composite_score >= 0.85:
            level = "HIGH"
            needs_clarification = False
        elif composite_score >= 0.65:
            level = "MEDIUM"
            needs_clarification = False
        else:
            level = "LOW"
            needs_clarification = True

        return {
            "composite_score": composite_score,
            "level": level,
            "needs_clarification": needs_clarification or is_ambiguous,
            "weights": {
                "ml": cls.ML_WEIGHT,
                "decision": cls.DECISION_WEIGHT,
                "column": cls.COLUMN_WEIGHT,
                "parameter": cls.PARAMETER_WEIGHT
            },
            "components": {
                "ml_confidence": round(ml_c, 3),
                "decision_confidence": round(dec_c, 3),
                "column_confidence": round(col_c, 3),
                "parameter_confidence": round(param_c, 3)
            },
            "ambiguity_reason": ambiguity_reason
        }
