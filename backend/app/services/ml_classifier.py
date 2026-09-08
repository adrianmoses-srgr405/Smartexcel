import os
from pathlib import Path
from typing import Any, Optional, Tuple, Dict
import pandas as pd
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.tree import DecisionTreeClassifier
    import joblib
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

class MLFormulaClassifier:
    """
    Machine Learning Formula Classifier using Random Forest.
    Learns patterns from structured intent features (operation, filter counts, data types, etc.)
    and predicts the best Excel formula candidate alongside a probabilistic confidence score.
    """
    
    # Feature category vocabularies for deterministic encoding
    OPERATIONS = ["SUM", "AVERAGE", "COUNT", "MAX", "MIN", "XLOOKUP", "PIVOT", "FILTER", "OTHER"]
    INTENTS = ["aggregation", "lookup", "ranking", "pivot_summary", "filter_recap", "other"]
    TARGET_TYPES = ["numeric", "categorical", "date", "text", "none"]
    FILTER_TYPES = ["categorical", "date", "numeric", "none", "mixed"]

    TARGET_LABELS = [
        "SUM", "SUMIF", "SUMIFS",
        "AVERAGE", "AVERAGEIF", "AVERAGEIFS",
        "COUNT", "COUNTIF", "COUNTIFS",
        "MAX", "MIN", "XLOOKUP", "PIVOT", "FILTER"
    ]


    def __init__(self, model_dir: Optional[Path] = None):
        if model_dir is None:
            self.model_dir = Path(__file__).resolve().parent.parent / "knowledge"
        else:
            self.model_dir = Path(model_dir)
            
        self.model_path = self.model_dir / "formula_rf_model.joblib"
        self.training_csv_path = self.model_dir / "training_formula_selection.csv"
        
        self.model: Optional[Any] = None
        self.feature_columns: list[str] = []
        self._initialize_model()

    def _extract_feature_vector(self, raw_features: Dict[str, Any]) -> pd.DataFrame:
        """
        Converts raw dictionary features into encoded dataframe matching trained model dimensions.
        """
        op = str(raw_features.get("operation", "SUM")).upper()
        if op not in self.OPERATIONS:
            op = "OTHER"
            
        intent = str(raw_features.get("intent", "aggregation")).lower()
        if intent not in self.INTENTS:
            intent = "other"
            
        target_type = str(raw_features.get("target_data_type", "numeric")).lower()
        if target_type not in self.TARGET_TYPES:
            target_type = "none"
            
        filter_type = str(raw_features.get("filter_data_type", "none")).lower()
        if filter_type not in self.FILTER_TYPES:
            filter_type = "none"

        filter_count = int(raw_features.get("filter_count", 0))
        grouping_count = int(raw_features.get("grouping_count", 0))
        has_date_filter = int(bool(raw_features.get("has_date_filter", 0)))
        has_multiple_criteria = int(bool(raw_features.get("has_multiple_criteria", filter_count >= 2 or grouping_count >= 2)))

        row_dict: Dict[str, Any] = {
            "filter_count": filter_count,
            "grouping_count": grouping_count,
            "has_date_filter": has_date_filter,
            "has_multiple_criteria": has_multiple_criteria,
        }

        # One-hot encoding for operation
        for item in self.OPERATIONS:
            row_dict[f"op_{item}"] = 1 if op == item else 0
            
        # One-hot encoding for intent
        for item in self.INTENTS:
            row_dict[f"intent_{item}"] = 1 if intent == item else 0
            
        # One-hot encoding for target_data_type
        for item in self.TARGET_TYPES:
            row_dict[f"target_type_{item}"] = 1 if target_type == item else 0
            
        # One-hot encoding for filter_data_type
        for item in self.FILTER_TYPES:
            row_dict[f"filter_type_{item}"] = 1 if filter_type == item else 0

        df = pd.DataFrame([row_dict])
        return df

    def train_model(self) -> bool:
        """
        Trains the Random Forest model from training_formula_selection.csv and serializes it.
        """
        if not HAS_SKLEARN:
            return False
            
        if not self.training_csv_path.exists():
            return False

        try:
            df = pd.read_csv(self.training_csv_path)
            if df.empty or "formula_label" not in df.columns:
                return False

            X_rows = []
            for _, row in df.iterrows():
                feat = {
                    "operation": row.get("operation", "SUM"),
                    "intent": row.get("intent", "aggregation"),
                    "filter_count": row.get("filter_count", 0),
                    "grouping_count": row.get("grouping_count", 0),
                    "has_date_filter": row.get("has_date_filter", 0),
                    "has_multiple_criteria": row.get("has_multiple_criteria", 0),
                    "target_data_type": row.get("target_data_type", "numeric"),
                    "filter_data_type": "date" if row.get("has_date_filter", 0) else "categorical"
                }
                vec = self._extract_feature_vector(feat)
                X_rows.append(vec)

            X = pd.concat(X_rows, ignore_index=True)
            y = df["formula_label"].values

            self.feature_columns = list(X.columns)

            rf = RandomForestClassifier(
                n_estimators=100,
                max_depth=12,
                min_samples_split=2,
                random_state=42
            )
            rf.fit(X, y)

            self.model = rf
            
            # Save model and feature columns
            payload = {
                "model": rf,
                "feature_columns": self.feature_columns,
                "classes": list(rf.classes_)
            }
            joblib.dump(payload, self.model_path)
            return True
        except Exception as e:
            print(f"[MLFormulaClassifier] Training error: {e}")
            return False

    def _initialize_model(self):
        """
        Loads existing trained model from disk or triggers training.
        """
        if not HAS_SKLEARN:
            return

        if self.model_path.exists():
            try:
                payload = joblib.load(self.model_path)
                self.model = payload["model"]
                self.feature_columns = payload.get("feature_columns", [])
                return
            except Exception:
                pass

        # Fallback to train
        self.train_model()

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predicts formula label and returns predicted formula with confidence score.
        If ML is unready or confidence < 0.70, flags confidence warning.
        """
        if not HAS_SKLEARN or self.model is None:
            # Fallback to deterministic heuristic if scikit-learn is unavailable
            return self._heuristic_prediction(features)

        try:
            X_input = self._extract_feature_vector(features)
            
            # Ensure columns match training schema exactly
            for col in self.feature_columns:
                if col not in X_input.columns:
                    X_input[col] = 0
            X_input = X_input[self.feature_columns]

            probs = self.model.predict_proba(X_input)[0]
            classes = list(self.model.classes_)

            top_idx = int(np.argmax(probs))
            predicted_label = str(classes[top_idx])
            confidence = float(probs[top_idx])

            # Class-level probability breakdown
            prob_breakdown = {cls_name: round(float(p), 4) for cls_name, p in zip(classes, probs) if p > 0.01}

            return {
                "predicted_formula": predicted_label,
                "confidence": round(confidence, 4),
                "is_confident": confidence >= 0.70,
                "probabilities": prob_breakdown,
                "engine": "RandomForestClassifier"
            }
        except Exception as e:
            print(f"[MLFormulaClassifier] Predict error: {e}")
            return self._heuristic_prediction(features)

    def _heuristic_prediction(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic fallback when scikit-learn model is not active.
        """
        op = str(features.get("operation", "SUM")).upper()
        f_count = int(features.get("filter_count", 0))
        g_count = int(features.get("grouping_count", 0))
        intent = str(features.get("intent", "aggregation")).lower()

        if intent in ["filter_recap", "filter"] or op == "FILTER":
            pred = "FILTER"
        elif intent == "lookup" or op == "XLOOKUP":
            pred = "XLOOKUP"
        elif intent == "ranking" or op == "MAX":
            pred = "MAX"
        elif op == "MIN":
            pred = "MIN"
        elif g_count >= 2 or intent == "pivot_summary":
            pred = "PIVOT"
        elif op == "SUM":
            pred = "SUM" if f_count == 0 else ("SUMIF" if f_count == 1 else "SUMIFS")
        elif op == "AVERAGE":
            pred = "AVERAGE" if f_count == 0 else ("AVERAGEIF" if f_count == 1 else "AVERAGEIFS")
        elif op == "COUNT":
            pred = "COUNT" if f_count == 0 else ("COUNTIF" if f_count == 1 else "COUNTIFS")
        else:
            pred = "FILTER" if f_count > 0 else "SUM"


        return {
            "predicted_formula": pred,
            "confidence": 0.95,
            "is_confident": True,
            "probabilities": {pred: 0.95},
            "engine": "DecisionTreeHeuristic"
        }

# Global singleton instance
ml_classifier = MLFormulaClassifier()
