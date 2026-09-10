from typing import Any, Optional
from pydantic import BaseModel
from datetime import datetime

class FormulaKnowledgeItem(BaseModel):
    id: str
    name: str
    category: str
    keywords: list[str] = []
    description: str = ""
    syntax_template: str = ""
    required_parameters: list[str] = []
    compatible_data_types: list[str] = []
    min_filters: int = 0
    max_filters: int = 99
    use_cases: list[str] = []
    examples: list[Any] = []
    explanation_template: str = ""
    validation_rules: list[str] = []
    is_active: bool = True

class EvaluationBenchmarkItem(BaseModel):
    id: str
    analysis_id: str
    user_query: str
    expected_formula: Optional[str]
    actual_formula: str
    is_formula_correct: bool
    is_filter_correct: bool
    is_result_correct: bool
    manual_time_seconds: float
    ai_time_seconds: float
    time_saved_percentage: float
    execution_time_ms: float
    notes: Optional[str]
    evaluated_at: datetime

class EvaluationMetricsSummary(BaseModel):
    total_evaluations: int
    formula_accuracy_pct: float
    filter_accuracy_pct: float
    result_accuracy_pct: float
    avg_manual_time_sec: float
    avg_ai_time_sec: float
    total_time_saved_hours: float
    formula_confusion_matrix: dict[str, Any] = {}
    recent_evaluations: list[EvaluationBenchmarkItem] = []

