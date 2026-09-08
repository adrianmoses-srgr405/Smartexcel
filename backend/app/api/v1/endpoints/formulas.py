import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.schemas.formula import FormulaKnowledgeItem
from app.services.ml_classifier import ml_classifier

router = APIRouter()

@router.get("/knowledge-base", response_model=list[FormulaKnowledgeItem])
def get_formula_knowledge_base():
    """Retrieve all cataloged Excel formulas and their decision rules."""
    kb_path = Path(__file__).resolve().parent.parent.parent / "knowledge" / "formula_kb.json"
    if kb_path.exists():
        with open(kb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [FormulaKnowledgeItem(**item) for item in data]
    return []

@router.post("/train")
def retrain_formula_model():
    """Trigger retraining of the Random Forest formula classifier."""
    success = ml_classifier.train_model()
    if not success:
        raise HTTPException(status_code=500, detail="Gagal melatih model AI.")
    return {
        "status": "success",
        "message": "Model AI Random Forest berhasil dilatih ulang!",
        "classes": list(ml_classifier.model.classes_) if ml_classifier.model else [],
        "features_count": len(ml_classifier.feature_columns),
    }
