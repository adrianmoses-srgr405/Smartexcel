from typing import Any, Optional
from pydantic import BaseModel
from datetime import datetime

class ColumnProfilingSchema(BaseModel):
    id: Optional[str] = None
    original_name: str
    sanitized_name: str
    column_index: int
    excel_column_letter: str
    inferred_type: str # Numeric, Date, Categorical, Text, Boolean
    null_count: int
    unique_count: int
    null_percentage: float = 0.0
    unique_percentage: float = 0.0
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[Any] = None
    sample_values: list[Any] = []
    distribution: Optional[dict[str, int]] = None

class DatasetProfilingSummary(BaseModel):
    total_rows: int
    total_columns: int
    numeric_columns: list[str]
    date_columns: list[str]
    categorical_columns: list[str]
    text_columns: list[str]
    columns: list[ColumnProfilingSchema]

class DatasetCreateResponse(BaseModel):
    id: str
    filename: str
    row_count: int
    column_count: int
    file_size_bytes: int
    selected_sheet: Optional[str] = None
    available_sheets: list[str] = []
    columns: list[ColumnProfilingSchema] = []
    profiling: DatasetProfilingSummary
    preview_data: list[dict[str, Any]]
    created_at: datetime

class DatasetListItem(BaseModel):
    id: str
    filename: str
    row_count: int
    column_count: int
    file_size_bytes: int
    selected_sheet: Optional[str] = None
    created_at: datetime

class DatasetDetailResponse(BaseModel):
    id: str
    filename: str
    row_count: int
    column_count: int
    file_size_bytes: int
    selected_sheet: Optional[str] = None
    available_sheets: list[str] = []
    created_at: datetime
    columns: list[ColumnProfilingSchema]
    preview_data: list[dict[str, Any]]
