import time
import uuid
import json
import logging
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from app.models.dataset import Dataset, DatasetColumn
from app.models.analysis import AnalysisHistory
from app.services.task_decomposer import TaskDecomposer
from app.services.parameter_extractor import ParameterExtractor
from app.services.ml_classifier import MLClassifierService
from app.services.column_resolver import ColumnResolver
from app.services.decision_engine import FormulaDecisionEngine
from app.services.formula_generator import FormulaGenerator
from app.services.formula_validator import FormulaValidator
from app.services.execution_engine import ExecutionEngine
from app.services.confidence_scorer import ConfidenceScorer
from app.services.clarification_engine import ClarificationEngine
from app.services.formula_planner import FormulaPlanner

logger = logging.getLogger(__name__)

class HybridAIService:
    """
    Central Orchestrator for the Research-Ready Hybrid AI Multi-Task Excel Engine.
    Pipeline:
    Query -> Semantic Understanding & Multi-Task Decomposition (TaskDecomposer)
    -> Per-Task Processing:
       -> Context-Aware Parameter Extraction & Override
       -> ML Classifier (Random Forest candidate)
       -> Independent Column Resolution (ColumnResolver)
       -> Deterministic Decision Matrix (FormulaDecisionEngine)
       -> Dynamic Formula Generation (FormulaGenerator)
       -> Formula Validation (FormulaValidator)
       -> Safe Execution against Dataset (ExecutionEngine)
       -> Composite Confidence Scoring & Clarification Check
    -> Multi-Result Aggregation (tasks[], summary{})
    -> Deterministic Primary Task (Zero Breaking Changes for legacy API consumers)
    -> PostgreSQL History Persistence.
    """

    @classmethod
    def _process_single_task(
        cls,
        task_context: Dict[str, Any],
        raw_query: str,
        columns_profile: List[Dict[str, Any]],
        schema_col_names: List[str],
        sample_df: Optional[pd.DataFrame] = None,
        is_table: bool = False,
        table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes a single decomposed task through the complete AI/ML pipeline independently.
        """
        task_id = task_context.get("task_id", "task_1")
        op_context = task_context.get("operation", "SUM")

        # 1. Parameter Extraction with Task-Specific Context & Filter Overrides
        params = ParameterExtractor.extract_parameters(
            query=raw_query,
            columns_profile=columns_profile,
            sample_df=sample_df,
            task_context=task_context
        )

        is_ambiguous = params.get("is_ambiguous", False)
        ambiguity_status = params.get("ambiguity_status", "ok")
        ambiguity_reason = params.get("ambiguity_reason")

        # 2. Candidate Generation from ML Classifier (Random Forest)
        ml_prediction = MLClassifierService.predict_candidate(raw_query)
        ml_candidate = ml_prediction.get("candidate_formula", "SUM")
        ml_confidence = ml_prediction.get("confidence", 0.5)

        op_param = params.get("operation") or op_context
        if not op_param or op_param == "UNKNOWN":
            if ml_candidate and ml_candidate.startswith("AVERAGE"):
                op_param = "AVERAGE"
            elif ml_candidate and ml_candidate.startswith("COUNT"):
                op_param = "COUNT"
            elif ml_candidate and ml_candidate in ["MAX", "MIN", "MAXIFS", "MINIFS", "IF", "IFS", "XLOOKUP", "VLOOKUP"]:
                op_param = ml_candidate
            else:
                op_param = "SUM"

        # Calibrate ML confidence if verified entities exist in dataset and no query ambiguity
        has_verified_cond = any(c.get("verified_in_dataset", False) for c in params.get("conditions", []))
        calibrated_ml_confidence = ml_confidence
        if has_verified_cond and not is_ambiguous:
            calibrated_ml_confidence = max(ml_confidence, 0.90)

        # 3. Independent Intelligent Column Resolution
        col_res = ColumnResolver.resolve_columns(
            target_term=params.get("target_term"),
            conditions=params.get("conditions", []),
            columns_profile=columns_profile,
            operation=op_param
        )

        target_mapping = col_res.get("target_column")
        conditions_mapping = col_res.get("conditions", [])
        column_confidence = col_res.get("column_confidence", 0.90)

        # 4. Deterministic Decision Matrix (Source of Truth per task)
        num_conditions = len(conditions_mapping)
        target_type = target_mapping.get("inferred_type", "Numeric") if target_mapping else "Numeric"
        num_logical = len(params.get("logical_branches", []))

        decision = FormulaDecisionEngine.decide_formula(
            operation=op_param,
            conditions_count=num_conditions,
            target_data_type=target_type,
            ml_candidate=ml_candidate,
            ml_confidence=calibrated_ml_confidence,
            is_table=is_table,
            logical_branches_count=num_logical
        )

        selected_formula = decision.get("formula", "SUM")
        decision_confidence = decision.get("decision_confidence", 0.95)

        # 5. Dynamic Formula Generation per task
        generated_formula = FormulaGenerator.generate_formula(
            formula_name=selected_formula,
            target_mapping=target_mapping,
            conditions_mapping=conditions_mapping,
            logical_branches=params.get("logical_branches"),
            table_name=table_name if is_table else None
        )

        # 6. Formula Validation per task
        validation = FormulaValidator.validate(
            formula_str=generated_formula,
            target_column_info=target_mapping,
            conditions_info=conditions_mapping,
            schema_columns=schema_col_names
        )

        # 7. Safe Formula Execution on DataFrame per task
        execution_res = {"executed": False, "result": None, "reason": "No execution attempted"}
        if sample_df is not None and not sample_df.empty:
            target_col_name = target_mapping.get("matched_column") if target_mapping else None
            execution_res = ExecutionEngine.execute_formula_safe(
                df=sample_df,
                formula_name=selected_formula,
                target_column=target_col_name,
                conditions=conditions_mapping,
                logical_branches=params.get("logical_branches")
            )

        # 8. Composite Confidence Scoring
        confidence_report = ConfidenceScorer.calculate_confidence(
            ml_confidence=calibrated_ml_confidence,
            decision_confidence=decision_confidence,
            column_confidence=column_confidence,
            parameter_confidence=params.get("confidence", 0.90),
            is_ambiguous=is_ambiguous,
            ambiguity_reason=ambiguity_reason
        )

        # 9. Clarification Engine Check
        clarification_payload = None
        if confidence_report.get("needs_clarification") or is_ambiguous:
            entity_val = conditions_mapping[0].get("value") if conditions_mapping else None
            candidate_cols = [c.get("original_name") for c in columns_profile] if columns_profile else []
            clarification_payload = ClarificationEngine.generate_clarification(
                query=raw_query,
                reason=ambiguity_reason,
                ambiguity_type=ambiguity_status,
                candidate_columns=candidate_cols,
                entity_value=entity_val
            )

        # 10. Explanation Payload
        explanation = {
            "formula_selection": decision.get("reason"),
            "ml_vs_decision": (
                f"Kandidat ML '{ml_candidate}' ({ml_confidence*100:.1f}%) diverifikasi dan dipertahankan oleh Decision Matrix."
                if ml_candidate == selected_formula
                else f"Decision Matrix mengoreksi kandidat ML '{ml_candidate}' ({ml_confidence*100:.1f}%) menjadi '{selected_formula}' berdasarkan kriteria terdeteksi."
            ),
            "column_mapping": [
                f"Target dihubungkan ke kolom '{target_mapping.get('matched_column')}' ({target_mapping.get('column_letter')})"
                if target_mapping else "Target kolom menggunakan fallback standar."
            ] + [
                f"Kriteria '{c.get('value')}' dipetakan ke kolom '{c.get('matched_column')}' ({c.get('column_letter')})"
                for c in conditions_mapping
            ],
            "execution_note": "Hasil dihitung secara riil terhadap dataset tanpa eval()." if execution_res.get("executed") else execution_res.get("reason")
        }

        task_type = task_context.get("task_type") or ("retrieval" if op_param in ["FILTER", "RETRIEVAL"] else "calculation")

        # Determine task execution status
        task_status = "success" if execution_res.get("executed") else ("warning" if validation.get("is_valid") else "failed")

        return {
            "task_id": task_id,
            "task_type": task_type,
            "operation": op_param,
            "target": target_mapping.get("matched_column") if target_mapping else None,
            "target_term": params.get("target_term"),
            "filters": [
                {
                    "field": c.get("resolved_column") or c.get("matched_column") or c.get("column_hint"),
                    "column_letter": c.get("column_letter"),
                    "operator": c.get("operator", "="),
                    "value": c.get("value")
                }
                for c in conditions_mapping
            ],
            "formula": generated_formula,
            "formula_name": selected_formula,
            "generated_formula": generated_formula,
            "parameters": {
                "operation": op_param,
                "target_term": params.get("target_term"),
                "conditions": conditions_mapping,
                "logical_branches": params.get("logical_branches"),
                "group_by": task_context.get("group_by", [])
            },
            "columns": {
                "target": target_mapping,
                "conditions": conditions_mapping
            },
            "validation": validation,
            "execution": execution_res,
            "result": execution_res.get("result"),
            "status": task_status,
            "confidence": confidence_report,
            "clarification": clarification_payload,
            "explanation": explanation,
            "decision": {
                "formula_id": selected_formula,
                "formula_name": selected_formula,
                "category": decision.get("category", "Aggregation"),
                "reason": decision.get("reason", ""),
                "syntax_pattern": f"={selected_formula}(...)",
                "generated_excel_formula": generated_formula,
                "affected_columns": [
                    {"role": "target", "column": target_mapping.get("matched_column", ""), "letter": target_mapping.get("column_letter", "")}
                ] if target_mapping else [],
                "validation_status": "PASSED" if validation.get("is_valid") else "WARNING",
                "validation_messages": validation.get("errors", []) + validation.get("warnings", []),
                "ml_prediction": ml_candidate,
                "ml_confidence": ml_confidence,
                "is_confident": not confidence_report.get("needs_clarification", False),
                "rule_validation_status": decision.get("rule_status", "VALID"),
                "rule_decision": decision.get("reason")
            }
        }

    @classmethod
    def process_query(
        cls,
        query: str,
        dataset: Optional[Dataset] = None,
        sample_df: Optional[pd.DataFrame] = None,
        db: Optional[Session] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        analysis_id = str(uuid.uuid4())

        # 1. Build Column Profiles from Dataset & Schema
        columns_profile: List[Dict[str, Any]] = []
        schema_col_names: List[str] = []
        is_table = False
        table_name = None

        if dataset:
            meta = getattr(dataset, "dataset_metadata", None) if isinstance(getattr(dataset, "dataset_metadata", None), dict) else {}
            is_table = bool(getattr(dataset, "is_excel_table", False) or meta.get("is_excel_table", False))
            table_name = getattr(dataset, "table_name", None) or meta.get("table_name", "Table1")
            for col in dataset.columns:
                schema_col_names.append(col.original_name)
                columns_profile.append({
                    "original_name": col.original_name,
                    "inferred_type": col.inferred_type,
                    "column_letter": col.excel_column_letter,
                    "sample_values": col.sample_values or []
                })
        elif sample_df is not None:
            schema_col_names = list(sample_df.columns)
            import openpyxl.utils
            for idx, col_name in enumerate(sample_df.columns):
                letter = openpyxl.utils.get_column_letter(idx + 1)
                is_num = pd.api.types.is_numeric_dtype(sample_df[col_name])
                columns_profile.append({
                    "original_name": col_name,
                    "inferred_type": "Numeric" if is_num else "Text",
                    "column_letter": letter,
                    "sample_values": list(sample_df[col_name].dropna().head(5).astype(str))
                })

        # 2. Decompose Query into Multiple Tasks (Semantic Decomposition)
        decomposed_tasks = TaskDecomposer.decompose(
            query=query,
            columns_profile=columns_profile,
            sample_df=sample_df
        )

        if not decomposed_tasks:
            decomposed_tasks = [{
                "task_id": "task_1",
                "operation": "SUM",
                "target_term": None,
                "filters": [],
                "group_by": [],
                "confidence": 0.50
            }]

        # 3. Process Each Task Independently (Per-Task Pipeline)
        task_results: List[Dict[str, Any]] = []
        for task_ctx in decomposed_tasks:
            task_res = cls._process_single_task(
                task_context=task_ctx,
                raw_query=query,
                columns_profile=columns_profile,
                schema_col_names=schema_col_names,
                sample_df=sample_df,
                is_table=is_table,
                table_name=table_name
            )
            task_results.append(task_res)

        # 4. Multi-Task Aggregation & Summary with Formula Plan
        formula_plan = FormulaPlanner.plan_formula(
            query=query,
            tasks=task_results,
            columns_profile=columns_profile,
            sample_df=sample_df
        )

        total_tasks_count = len(task_results)
        successful_tasks_count = sum(1 for t in task_results if t.get("status") == "success" or t.get("execution", {}).get("executed"))
        failed_tasks_count = total_tasks_count - successful_tasks_count

        summary_stats = {
            "total_tasks": total_tasks_count,
            "successful_tasks": successful_tasks_count,
            "failed_tasks": failed_tasks_count,
            "formula_plan": formula_plan
        }

        # 5. Deterministic Primary Task Selection (Task 1 / First Task)
        # Guarantees ZERO BREAKING CHANGES for legacy endpoints
        primary_task = task_results[0]

        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        # 6. Persist to AnalysisHistory in PostgreSQL with complete multi-task information
        if db and dataset:
            try:
                # Prepare clean serializable representations
                tasks_serializable = []
                for t in task_results:
                    tasks_serializable.append({
                        "task_id": t.get("task_id"),
                        "operation": t.get("operation"),
                        "formula_name": t.get("formula_name"),
                        "generated_formula": t.get("generated_formula"),
                        "execution": t.get("execution"),
                        "validation": {"is_valid": t.get("validation", {}).get("is_valid")},
                        "confidence": t.get("confidence", {}).get("composite_score"),
                        "status": t.get("status")
                    })

                raw_parsed_intent = {
                    "total_tasks": total_tasks_count,
                    "tasks": tasks_serializable,
                    "primary_operation": primary_task.get("operation"),
                    "primary_target": primary_task.get("columns", {}).get("target")
                }
                raw_calc_results = {
                    "summary": summary_stats,
                    "primary_execution": primary_task.get("execution"),
                    "all_results": [
                        {"task_id": t.get("task_id"), "result": t.get("execution", {}).get("result"), "executed": t.get("execution", {}).get("executed")}
                        for t in task_results
                    ]
                }

                # Ensure strict JSON serializability for PostgreSQL JSON columns
                safe_parsed_intent = json.loads(json.dumps(raw_parsed_intent, default=str))
                safe_calc_results = json.loads(json.dumps(raw_calc_results, default=str))

                history_record = AnalysisHistory(
                    id=analysis_id,
                    dataset_id=dataset.id,
                    user_query=query,
                    parsed_intent=safe_parsed_intent,
                    selected_formula_id=primary_task.get("formula_name", "SUM"),
                    generated_excel_formula=primary_task.get("generated_formula", "=SUM(A:A)"),
                    formula_explanation=primary_task.get("explanation", {}).get("formula_selection", ""),
                    calculation_results=safe_calc_results,
                    result_summary=f"Processed {total_tasks_count} tasks ({successful_tasks_count} success, {failed_tasks_count} failed). Primary formula: {primary_task.get('formula_name')}",
                    execution_time_ms=execution_time_ms
                )
                db.add(history_record)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"[HybridAIService] Could not persist history: {e}")

        # Assemble unified response matching all specifications:
        # 1. Backward-compatible top-level legacy fields (derived from primary task)
        # 2. Complete multi-task array (tasks[])
        # 3. Aggregated execution statistics (summary{})
        return {
            "analysis_id": analysis_id,
            "dataset_id": dataset.id if dataset else None,
            "user_query": query,
            # Legacy fields mapped deterministically to primary task
            "formula_name": primary_task["formula_name"],
            "generated_formula": primary_task["generated_formula"],
            "parameters": primary_task["parameters"],
            "columns": primary_task["columns"],
            "execution": primary_task["execution"],
            "validation": primary_task["validation"],
            "confidence": primary_task["confidence"],
            "clarification": primary_task.get("clarification"),
            "explanation": primary_task["explanation"],
            "decision": primary_task["decision"],
            # Multi-Task & Formula Planner Extensions
            "tasks": task_results,
            "summary": summary_stats,
            "formula_plan": formula_plan,
            "execution_time_ms": execution_time_ms
        }
