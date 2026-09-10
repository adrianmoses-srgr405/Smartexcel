from typing import Any, Dict, List, Optional
import time
import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.ml_training import EvaluationQuery, TrainingRun
from app.services.hybrid_ai_service import HybridAIService
from app.services.parameter_extractor import ParameterExtractor
from app.services.ml_classifier import MLClassifierService
from app.services.column_resolver import ColumnResolver
from app.services.decision_engine import FormulaDecisionEngine
from app.services.formula_generator import FormulaGenerator
from app.services.formula_validator import FormulaValidator
from app.services.execution_engine import ExecutionEngine

class EvaluationRunnerService:
    """
    Evaluates the complete Hybrid AI pipeline against hold-out evaluation samples.
    Produces granular research metrics:
    1. ML classification accuracy
    2. Intent / Operation extraction accuracy
    3. Formula selection accuracy (after Decision Matrix)
    4. Formula generation syntax validity
    5. End-to-end correctness
    6. Decision Matrix correction analysis (ML wrong -> fixed vs ML right -> kept)
    7. Full Confusion Matrix (Expected vs Final Formula after Decision Matrix)
    """

    @classmethod
    def run_benchmark(cls, db: Optional[Session] = None) -> Dict[str, Any]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            eval_queries = db.query(EvaluationQuery).all()
            total_samples = len(eval_queries)
            if total_samples == 0:
                return {"error": "No evaluation queries found in database."}

            # Standard test dataset schema for benchmark
            mock_columns = [
                {"original_name": "Sales", "inferred_type": "Text", "column_letter": "A", "sample_values": ["Andi", "Budi", "Siti", "Dewi"]},
                {"original_name": "Bulan", "inferred_type": "Text", "column_letter": "B", "sample_values": ["Januari", "Februari", "Maret"]},
                {"original_name": "Produk", "inferred_type": "Text", "column_letter": "C", "sample_values": ["TBS Sawit", "CPO", "Palm Kernel"]},
                {"original_name": "Penjualan", "inferred_type": "Numeric", "column_letter": "D", "sample_values": ["1000000", "2000000", "1500000"]},
                {"original_name": "Produksi", "inferred_type": "Numeric", "column_letter": "E", "sample_values": ["50000", "65000", "72000"]},
                {"original_name": "Kebun", "inferred_type": "Text", "column_letter": "F", "sample_values": ["Rambutan", "Sei Silau", "Tinjowan"]},
                {"original_name": "Divisi", "inferred_type": "Text", "column_letter": "G", "sample_values": ["Tanaman", "Teknik", "Pengolahan"]},
                {"original_name": "Nama", "inferred_type": "Text", "column_letter": "H", "sample_values": ["Andi", "Budi", "Cici"]},
                {"original_name": "Biaya", "inferred_type": "Numeric", "column_letter": "I", "sample_values": ["500000", "750000", "1200000"]}
            ]

            # Sample benchmark dataframe
            benchmark_df = pd.DataFrame({
                "Sales": ["Andi", "Budi", "Andi", "Siti", "Andi"],
                "Bulan": ["Januari", "Januari", "Februari", "Januari", "Januari"],
                "Produk": ["TBS Sawit", "CPO", "TBS Sawit", "Palm Kernel", "CPO"],
                "Penjualan": [1000000, 2000000, 1500000, 800000, 500000],
                "Produksi": [50000, 60000, 55000, 40000, 45000],
                "Kebun": ["Rambutan", "Sei Silau", "Rambutan", "Tinjowan", "Rambutan"],
                "Divisi": ["Tanaman", "Teknik", "Tanaman", "Pengolahan", "Tanaman"],
                "Nama": ["Andi", "Budi", "Cici", "Dedi", "Eka"],
                "Biaya": [500000, 750000, 1200000, 400000, 600000]
            })

            ml_correct = 0
            intent_correct = 0
            formula_selection_correct = 0
            valid_formula_count = 0
            end_to_end_correct = 0

            ml_wrong_fixed = 0
            ml_correct_kept = 0
            both_wrong = 0

            # Confusion matrix dictionary: expected -> actual -> count
            confusion_matrix: Dict[str, Dict[str, int]] = {}

            start_t = time.time()

            for item in eval_queries:
                q = item.query_text
                exp_f = item.expected_formula.upper()
                exp_op = item.expected_operation.upper()

                # Initialize confusion matrix key
                if exp_f not in confusion_matrix:
                    confusion_matrix[exp_f] = {}

                # 1. Parameter Extraction
                params = ParameterExtractor.extract_parameters(q, columns_profile=mock_columns, sample_df=benchmark_df)
                extracted_op = (params.get("operation") or "").upper()
                if extracted_op == exp_op or (exp_op == "SUM" and extracted_op in ["SUM", "AGGREGATION"]):
                    intent_correct += 1

                # 2. ML Candidate
                ml_res = MLClassifierService.predict_candidate(q)
                ml_cand = ml_res.get("candidate_formula", "").upper()
                is_ml_right = (ml_cand == exp_f)
                if is_ml_right:
                    ml_correct += 1

                # 3. Column Resolution
                col_res = ColumnResolver.resolve_columns(
                    target_term=params.get("target_term"),
                    conditions=params.get("conditions", []),
                    columns_profile=mock_columns,
                    operation=params.get("operation", "SUM")
                )

                # 4. Decision Matrix
                target_col = col_res.get("target_column")
                target_dtype = target_col.get("inferred_type", "Numeric") if target_col else "Numeric"
                decision = FormulaDecisionEngine.decide_formula(
                    operation=params.get("operation", "SUM"),
                    conditions_count=len(col_res.get("conditions", [])),
                    target_data_type=target_dtype,
                    ml_candidate=ml_cand,
                    ml_confidence=ml_res.get("confidence", 0.5),
                    logical_branches_count=len(params.get("logical_branches", []))
                )
                final_f = decision.get("formula", "SUM").upper()

                # Record into confusion matrix
                confusion_matrix[exp_f][final_f] = confusion_matrix[exp_f].get(final_f, 0) + 1

                is_decision_right = (final_f == exp_f)
                if is_decision_right:
                    formula_selection_correct += 1

                # Track ML vs Decision Matrix behavior
                if not is_ml_right and is_decision_right:
                    ml_wrong_fixed += 1
                elif is_ml_right and is_decision_right:
                    ml_correct_kept += 1
                elif not is_ml_right and not is_decision_right:
                    both_wrong += 1

                # 5. Formula Generation
                gen_f = FormulaGenerator.generate_formula(
                    formula_name=final_f,
                    target_mapping=col_res.get("target_column"),
                    conditions_mapping=col_res.get("conditions", []),
                    logical_branches=params.get("logical_branches")
                )

                # 6. Formula Validation
                val_res = FormulaValidator.validate(
                    formula_str=gen_f,
                    target_column_info=col_res.get("target_column"),
                    conditions_info=col_res.get("conditions", [])
                )
                if val_res.get("is_valid"):
                    valid_formula_count += 1

                # 7. Execution Check
                exec_res = ExecutionEngine.execute_formula_safe(
                    df=benchmark_df,
                    formula_name=final_f,
                    target_column=target_col.get("matched_column") if target_col else None,
                    conditions=col_res.get("conditions", []),
                    logical_branches=params.get("logical_branches")
                )

                if is_decision_right and val_res.get("is_valid") and exec_res.get("executed"):
                    end_to_end_correct += 1

            duration = round(time.time() - start_t, 2)

            ml_acc = round((ml_correct / total_samples) * 100, 2)
            intent_acc = round((intent_correct / total_samples) * 100, 2)
            sel_acc = round((formula_selection_correct / total_samples) * 100, 2)
            gen_val_rate = round((valid_formula_count / total_samples) * 100, 2)
            e2e_acc = round((end_to_end_correct / total_samples) * 100, 2)

            # Get active model info
            active_run = db.query(TrainingRun).filter(TrainingRun.is_active == True).first()

            return {
                "evaluation_samples_count": total_samples,
                "benchmark_duration_seconds": duration,
                "active_model_version": active_run.version if active_run else "formula_rf_v1",
                "metrics": {
                    "ml_classifier_accuracy": ml_acc,
                    "intent_extraction_accuracy": intent_acc,
                    "formula_selection_accuracy": sel_acc,
                    "formula_generation_validity_rate": gen_val_rate,
                    "end_to_end_correctness_accuracy": e2e_acc
                },
                "decision_matrix_impact": {
                    "ml_wrong_corrected_by_decision_matrix": ml_wrong_fixed,
                    "ml_correct_preserved_by_decision_matrix": ml_correct_kept,
                    "both_unresolved": both_wrong,
                    "accuracy_lift": round(sel_acc - ml_acc, 2)
                },
                "formula_selection_confusion_matrix": confusion_matrix
            }

        finally:
            if close_db:
                db.close()
