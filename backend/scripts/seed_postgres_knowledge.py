import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, Base, engine
from app.models.formula import FormulaKnowledge, FormulaExample
from app.models.ml_training import TrainingSample, EvaluationQuery
from app.knowledge.formula_seed_data import FORMULAS_18_DATA
from app.knowledge.training_dataset_generator import generate_training_samples, generate_evaluation_queries

def seed_knowledge_and_datasets():
    print("=== SEEDING POSTGRESQL 18: KNOWLEDGE BASE & TRAINING DATASETS ===")
    db = SessionLocal()

    try:
        # 1. Pastikan skema formula_knowledge dan formula_examples ter-update
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("DROP TABLE IF EXISTS formula_examples CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS formula_knowledge CASCADE;"))
            conn.commit()

        Base.metadata.create_all(bind=engine)


        # 2. Seed 18 Formula Knowledge Base
        print("\n[Step 1] Seeding 18 Formula Knowledge Base ke PostgreSQL...")
        for item in FORMULAS_18_DATA:
            existing = db.query(FormulaKnowledge).filter_by(id=item["id"]).first()
            if not existing:
                f_obj = FormulaKnowledge(
                    id=item["id"],
                    formula_name=item["formula_name"],
                    name=item["name"],
                    category=item["category"],
                    description=item["description"],
                    use_case=item["use_case"],
                    syntax_template=item["syntax_template"],
                    parameter_definition=item["parameter_definition"],
                    required_parameters=item["required_parameters"],
                    compatible_data_types=item["compatible_data_types"],
                    required_conditions=item["required_conditions"],
                    min_conditions=item["min_conditions"],
                    max_conditions=item["max_conditions"],
                    min_filters=item["min_conditions"],
                    max_filters=item["max_conditions"],
                    use_cases=[item["use_case"]],
                    examples=[ex["formula"] for ex in item.get("examples", [])],
                    explanation_template=item["explanation_template"],
                    validation_rules=item.get("validation_rules", []),
                    priority=item.get("priority", 1),
                    is_active=True,
                    enabled=True,
                    keywords=item.get("keywords", [])
                )
                db.add(f_obj)
                db.flush()

                # Add examples
                for ex in item.get("examples", []):
                    ex_obj = FormulaExample(
                        formula_id=item["id"],
                        example_query=ex["query"],
                        example_formula=ex["formula"],
                        explanation=ex.get("explanation", "")
                    )
                    db.add(ex_obj)
            else:
                # Update attributes to ensure up-to-date metadata
                existing.description = item["description"]
                existing.use_case = item["use_case"]
                existing.syntax_template = item["syntax_template"]
                existing.keywords = item.get("keywords", [])
                existing.priority = item.get("priority", 1)
                existing.min_conditions = item["min_conditions"]
                existing.max_conditions = item["max_conditions"]
                existing.required_conditions = item["required_conditions"]
                existing.parameter_definition = item["parameter_definition"]
                existing.compatible_data_types = item["compatible_data_types"]
                existing.explanation_template = item["explanation_template"]

        db.commit()
        total_kb = db.query(FormulaKnowledge).count()
        print(f"  -> Total Formula Knowledge Base di PostgreSQL: {total_kb} formula.")

        # 3. Seed Training Samples (>= 1800 samples)
        print("\n[Step 2] Generating & Seeding Training Samples...")
        raw_samples = generate_training_samples()
        print(f"  -> Generated {len(raw_samples)} rich training samples.")

        # Hapus data sintetis lama jika ingin fresh populate atau hanya tambah jika kosong
        current_sample_count = db.query(TrainingSample).count()
        if current_sample_count < 1800:
            db.query(TrainingSample).filter_by(source="synthetic_ptpn").delete()
            db.flush()

            for s in raw_samples:
                ts = TrainingSample(
                    query_text=s["query_text"],
                    formula_label=s["formula_label"],
                    operation=s["operation"],
                    intent=s["intent"],
                    conditions_count=s["conditions_count"],
                    target_term=s.get("target_term"),
                    is_ambiguous=s.get("is_ambiguous", False),
                    source="synthetic_ptpn"
                )
                db.add(ts)
            db.commit()
            print(f"  -> Successfully seeded {len(raw_samples)} training samples to PostgreSQL.")
        else:
            print(f"  -> Training samples already populated ({current_sample_count} records).")

        # 4. Seed Evaluation Queries (>= 200 samples)
        print("\n[Step 3] Seeding Evaluation Queries (Hold-out test dataset)...")
        current_eval_count = db.query(EvaluationQuery).count()
        if current_eval_count < 200:
            db.query(EvaluationQuery).delete()
            db.flush()

            raw_evals = generate_evaluation_queries()
            for ev in raw_evals:
                eq = EvaluationQuery(
                    query_text=ev["query_text"],
                    expected_formula=ev["expected_formula"],
                    expected_operation=ev["expected_operation"],
                    expected_conditions_count=ev.get("expected_conditions_count", 0),
                    difficulty=ev.get("difficulty", "medium"),
                    is_ambiguous=ev.get("is_ambiguous", False)
                )
                db.add(eq)
            db.commit()
            print(f"  -> Successfully seeded {len(raw_evals)} evaluation queries to PostgreSQL.")
        else:
            print(f"  -> Evaluation queries already populated ({current_eval_count} records).")

        print("\n=== POSTGRESQL SEEDING COMPLETED SUCCESSFULLY! ===")
        return True

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR during seeding]: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    ok = seed_knowledge_and_datasets()
    if not ok:
        sys.exit(1)
