export interface ColumnProfiling {
  id?: string;
  original_name: string;
  sanitized_name: string;
  column_index: number;
  excel_column_letter: string;
  inferred_type: 'Numeric' | 'Date' | 'Categorical' | 'Text' | 'Boolean';
  null_count: number;
  unique_count: number;
  null_percentage: number;
  unique_percentage: number;
  min_value?: string | number | null;
  max_value?: string | number | null;
  mean_value?: string | number | null;
  sample_values: (string | number)[];
  distribution?: Record<string, number>;
  semantic_type?: string;
  is_groupable?: boolean;
  is_summable?: boolean;
}

export interface DatasetSummary {
  total_rows: number;
  total_columns: number;
  numeric_columns: string[];
  date_columns: string[];
  categorical_columns: string[];
  text_columns: string[];
  columns: ColumnProfiling[];
}

export interface Dataset {
  id: string;
  filename: string;
  row_count: number;
  column_count: number;
  file_size_bytes: number;
  selected_sheet?: string;
  available_sheets?: string[];
  created_at: string;
  columns?: ColumnProfiling[];
  columns_profile?: ColumnProfiling[];
  preview_data?: Record<string, any>[];
  profiling?: DatasetSummary;
}

export interface FilterCriterion {
  field: string;
  operator: string;
  value: any;
  data_type?: string;
}

export interface StructuredIntent {
  intent: string;
  operation: string;
  target_field?: string;
  group_by: string[];
  filters: FilterCriterion[];
  time_granularity: string;
  confidence_score: number;
  user_explanation?: string;
}

export interface AffectedColumn {
  role: string;
  column: string;
  letter: string;
  type?: string;
}

export interface FormulaDecision {
  formula_id: string;
  formula_name: string;
  category: string;
  reason: string;
  syntax_pattern: string;
  generated_excel_formula: string;
  affected_columns: AffectedColumn[];
  validation_status: 'PASSED' | 'WARNING' | 'FAILED';
  validation_messages: string[];
  ml_prediction?: string;
  ml_confidence?: number;
  is_confident?: boolean;
  rule_validation_status?: 'VALID' | 'CORRECTED_BY_RULE' | 'WARNING';
  rule_decision?: string;
  probabilities?: Record<string, number>;
}


export interface AnalysisResult {
  analysis_id: string;
  dataset_id: string;
  user_query: string;
  parsed_intent: StructuredIntent;
  decision: FormulaDecision;
  calculation_summary: Record<string, any>;
  table_headers: string[];
  table_rows: Record<string, any>[];
  chart_data?: { name: string; value: number }[];
  execution_time_ms: number;
  formula_name?: string;
  generated_formula?: string;
  explanation?: {
    formula_selection?: string;
    target_column?: string;
    filters_applied?: any[];
  };
  tasks?: Array<{
    task_id?: string;
    task_type?: string;
    operation?: string;
    formula_name?: string;
    generated_formula?: string;
    target?: string;
    target_term?: string;
    columns?: Record<string, any>;
    execution?: {
      executed?: boolean;
      result?: any;
      status?: string;
    };
    confidence?: any;
    status?: string;
  }>;
  summary?: Record<string, any>;
  parameters?: Record<string, any>;
  columns?: Record<string, any>;
  formula_plan?: Record<string, any>;
  group_by?: string[];
}

export interface FormulaKnowledgeItem {
  id: string;
  name: string;
  category: string;
  keywords: string[];
  description: string;
  syntax_template: string;
  required_parameters: string[];
  compatible_data_types: string[];
  min_filters: number;
  max_filters: number;
  use_cases: string[];
  examples: string[];
  explanation_template: string;
  validation_rules: string[];
}

export interface EvaluationItem {
  id: string;
  analysis_id: string;
  user_query: string;
  expected_formula?: string;
  actual_formula: string;
  is_formula_correct: boolean;
  is_filter_correct: boolean;
  is_result_correct: boolean;
  manual_time_seconds: number;
  ai_time_seconds: number;
  time_saved_percentage: number;
  execution_time_ms: number;
  notes?: string;
  evaluated_at: string;
}

export interface EvaluationSummary {
  total_evaluations: number;
  formula_accuracy_pct: number;
  filter_accuracy_pct: number;
  result_accuracy_pct: number;
  avg_manual_time_sec: number;
  avg_ai_time_sec: number;
  total_time_saved_hours: number;
  formula_confusion_matrix: Record<string, Record<string, number>>;
  recent_evaluations: EvaluationItem[];
}
