from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.formula import FormulaKnowledge
from app.schemas.formula import FormulaKnowledgeItem
from app.services.ml_classifier import MLClassifierService

router = APIRouter()

@router.get("/knowledge-base", response_model=List[FormulaKnowledgeItem])
def get_formula_knowledge_base(db: Session = Depends(get_db)):
    """Retrieve all 18 cataloged Excel formulas and their decision rules from PostgreSQL."""
    db_formulas = db.query(FormulaKnowledge).filter(FormulaKnowledge.is_active == True).order_by(FormulaKnowledge.priority).all()
    if db_formulas:
        result = []
        for f in db_formulas:
            examples = []
            if f.examples and isinstance(f.examples, list):
                for ex in f.examples:
                    if isinstance(ex, dict):
                        examples.append(ex.get("formula", "") or ex.get("query", ""))
                    elif isinstance(ex, str):
                        examples.append(ex)

            result.append(FormulaKnowledgeItem(
                id=str(f.id),
                name=str(f.name or f.formula_name or f.id),
                category=str(f.category or "General"),
                keywords=f.keywords if isinstance(f.keywords, list) else [],
                description=str(f.description or ""),
                syntax_template=str(f.syntax_template or ""),
                required_parameters=f.required_parameters if isinstance(f.required_parameters, list) else [],
                compatible_data_types=f.compatible_data_types if isinstance(f.compatible_data_types, list) else [],
                min_filters=int(f.min_filters if f.min_filters is not None else 0),
                max_filters=int(f.max_filters if f.max_filters is not None else 99),
                use_cases=f.use_cases if isinstance(f.use_cases, list) else ([f.use_case] if f.use_case else []),
                examples=examples,
                explanation_template=str(f.explanation_template or ""),
                validation_rules=f.validation_rules if isinstance(f.validation_rules, list) else [],
                is_active=bool(f.is_active if f.is_active is not None else True)
            ))
        return result
    return []

@router.post("/train")
def retrain_formula_model(db: Session = Depends(get_db)):
    """Trigger zero-leakage retraining of the Random Forest formula classifier on PostgreSQL."""
    try:
        run_info = MLClassifierService.train_model(db=db)
        return {
            "status": "success",
            "message": "Model AI Random Forest berhasil dilatih ulang dengan data PostgreSQL!",
            "training_run": run_info,
            "classes": run_info.get("classes", []),
            "accuracy": run_info.get("accuracy", 0.0),
            "f1_score": run_info.get("f1_score", 0.0),
            "samples": run_info.get("samples", 0),
            "features_count": run_info.get("features_count", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal melatih model AI: {str(e)}")
