from typing import Any, Optional, Union, List, Dict
from pydantic import BaseModel, Field

class FilterCriterion(BaseModel):
    field: str
    operator: str = Field(..., description="=, !=, >, <, >=, <=, BETWEEN, CONTAINS, STARTS_WITH, ENDS_WITH, IN")
    value: Union[str, int, float, list[Any], dict[str, Any], Any]
    data_type: Optional[str] = Field("text", description="date, numeric, text")

class StructuredAnalysisIntent(BaseModel):
    intent: str = Field(..., description="aggregation, lookup, ranking, filter_recap, time_series, pivot_summary")
    operation: str = Field(..., description="SUM, AVERAGE, COUNT, MAX, MIN, XLOOKUP, GROWTH_RATE")
    target_field: Optional[str] = Field(None, description="Quantitative column to aggregate or measure")
    group_by: list[str] = Field(default_factory=list, description="Categorical/Dimension columns for grouping")
    filters: list[FilterCriterion] = Field(default_factory=list, description="Filter constraints")
    time_granularity: str = Field("none", description="day, month, quarter, year, none")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0)
    ambiguous_fields: list[dict[str, Any]] = Field(default_factory=list, description="Low confidence column matches that need clarification")
    user_explanation: Optional[str] = Field(None, description="Short natural language explanation of the understood requirement")

class NaturalLanguageQueryRequest(BaseModel):
    dataset_id: str
    query: str
    user_override_mappings: Optional[dict[str, str]] = None

class FormulaDecisionResult(BaseModel):
    formula_id: str
    formula_name: str
    category: str
    reason: str
    syntax_pattern: str
    generated_excel_formula: str
    affected_columns: list[dict[str, str]] = [] # e.g. [{"role": "target", "column": "Jumlah Keluar", "letter": "E"}]
    validation_status: str = "PASSED" # "PASSED", "WARNING", "FAILED"
    validation_messages: list[str] = []
    # Hybrid AI fields:
    ml_prediction: Optional[str] = None
    ml_confidence: Optional[float] = None
    is_confident: bool = True
    rule_validation_status: str = "VALID" # "VALID", "CORRECTED_BY_RULE", "WARNING"
    rule_decision: Optional[str] = None
    probabilities: Optional[dict[str, float]] = None

class CalculationResultRow(BaseModel):
    group_values: dict[str, Any] = {}
    aggregated_value: Any
    row_count: int
    formula_cell_repr: Optional[str] = None

class ExecutionResult(BaseModel):
    executed: bool
    result: Optional[Any] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    details: Optional[dict[str, Any]] = None

class ClarificationOption(BaseModel):
    id: str
    label: str
    description: Optional[str] = None
    suggested_formula: Optional[str] = None
    suggested_override: Optional[dict[str, Any]] = None

class ClarificationPayload(BaseModel):
    needed: bool = False
    status: Optional[str] = None
    ambiguity_type: Optional[str] = None
    reason: Optional[str] = None
    options: List[ClarificationOption] = []

class AnalysisResponse(BaseModel):
    analysis_id: str
    dataset_id: str
    user_query: str
    parsed_intent: StructuredAnalysisIntent
    decision: FormulaDecisionResult
    calculation_summary: dict[str, Any]
    table_headers: list[str]
    table_rows: list[dict[str, Any]]
    chart_data: Optional[list[dict[str, Any]]] = None
    execution_time_ms: float
    # Research-ready Hybrid AI Extensions:
    generated_formula: Optional[str] = None
    formula_name: Optional[str] = None
    execution: Optional[ExecutionResult] = None
    confidence: Optional[dict[str, Any]] = None
    clarification: Optional[ClarificationPayload] = None
    explanation: Optional[dict[str, Any]] = None
    validation: Optional[dict[str, Any]] = None
    # Multi-Task & Formula Planner Extensions:
    tasks: Optional[List[Dict[str, Any]]] = None
    summary: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    columns: Optional[Dict[str, Any]] = None
    formula_plan: Optional[Dict[str, Any]] = None
