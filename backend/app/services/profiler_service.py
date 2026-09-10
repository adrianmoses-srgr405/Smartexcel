import re
from typing import Any, Tuple, Optional
from pathlib import Path
import pandas as pd
import numpy as np
from app.services.semantic_column_detector import UniversalSemanticColumnDetector

def index_to_excel_col(idx: int) -> str:
    """Converts 0-based column index to Excel column letter (0 -> A, 25 -> Z, 26 -> AA, etc.)."""
    result = ""
    idx += 1
    while idx > 0:
        idx, remainder = divmod(idx - 1, 26)
        result = chr(65 + remainder) + result
    return result

def sanitize_column_name(name: str) -> str:
    """Sanitizes column name for internal processing."""
    clean = re.sub(r"[^\w\s]", "", str(name)).strip()
    clean = re.sub(r"\s+", "_", clean).lower()
    return clean or "column"

def infer_series_type(series: pd.Series) -> str:
    """
    Accurately infers column type into:
    Numeric, Date, Categorical, Boolean, or Text.
    """
    # Drop nulls for inference
    non_nulls = series.dropna()
    if non_nulls.empty:
        return "Text"

    # 1. Check Boolean
    if pd.api.types.is_bool_dtype(series):
        return "Boolean"
    unique_vals_lower = {str(x).strip().lower() for x in non_nulls.iloc[:100]}
    if unique_vals_lower.issubset({"true", "false", "1", "0", "ya", "tidak", "yes", "no"}):
        return "Boolean"

    # 2. Check Numeric
    if pd.api.types.is_numeric_dtype(series):
        return "Numeric"
    
    # Try converting string numbers with dots or commas
    try:
        sample_str = non_nulls.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        pd.to_numeric(sample_str, errors="raise")
        return "Numeric"
    except Exception:
        pass

    # 3. Check Date
    if pd.api.types.is_datetime64_any_dtype(series):
        return "Date"
    
    # Sample check for date string formats (Indonesian/English)
    date_success = 0
    sample_items = non_nulls.iloc[:min(20, len(non_nulls))]
    for val in sample_items:
        try:
            # Handle Indonesian day/month names by replacing common strings or using dateutil
            val_str = str(val)
            parsed = pd.to_datetime(val_str, errors="coerce")
            if pd.notnull(parsed):
                date_success += 1
        except Exception:
            pass
            
    if date_success / len(sample_items) >= 0.8:
        return "Date"

    # 4. Categorical vs Text
    unique_count = series.nunique()
    total_count = len(series)
    if unique_count <= 50 or (unique_count / max(total_count, 1) < 0.3):
        return "Categorical"

    return "Text"

class ProfilerService:
    @staticmethod
    def get_available_sheets(file_path: Path) -> list[str]:
        """Returns list of sheet names if Excel file."""
        suffix = file_path.suffix.lower()
        if suffix in [".xlsx", ".xls"]:
            try:
                xls = pd.ExcelFile(file_path, engine="openpyxl" if suffix == ".xlsx" else None)
                return xls.sheet_names
            except Exception:
                return []
        return []

    @classmethod
    def detect_header_row(cls, file_path: Path, sheet_name: Optional[str] = None) -> int:
        """
        Intelligently detects the 0-indexed header row of an Excel sheet.
        Handles banner rows, title merges, and dates (e.g. Row 4 in LHP SAP).
        Scans top 20 rows and scores by non-empty string column count and diversity.
        """
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        if suffix not in [".xlsx", ".xls"]:
            return 0

        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb[sheet_name] if (sheet_name and sheet_name in wb.sheetnames) else wb.active
            rows = []
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i >= 20:
                    break
                rows.append(row)
            wb.close()

            if not rows:
                return 0

            best_row_idx = 0
            max_score = -1.0

            for idx, r in enumerate(rows):
                non_empty = [c for c in r if c is not None and str(c).strip() != ""]
                if not non_empty:
                    continue

                str_headers = []
                for c in non_empty:
                    c_str = str(c).strip()
                    if not c_str.replace(".", "").replace(",", "").replace("-", "").isdigit() and len(c_str) < 80:
                        str_headers.append(c_str)

                distinct_str_count = len(set(str_headers))
                total_cells = len(r)
                score = (distinct_str_count * 3) + (len(non_empty) * 1.5)
                # Penalize single-cell title banner merges across wide spreadsheets
                if distinct_str_count <= 2 and total_cells > 5:
                    score *= 0.2

                if score > max_score:
                    max_score = score
                    best_row_idx = idx

            return best_row_idx
        except Exception:
            return 0

    @classmethod
    def load_dataset_file(cls, file_path: Path, sheet_name: Optional[str] = None, known_sheets: Optional[list[str]] = None) -> Tuple[pd.DataFrame, str, list[str]]:
        """
        Reads Excel (.xlsx, .xls) or CSV files into DataFrame.
        Intelligently auto-selects the main data sheet if multiple sheets exist.
        Uses intelligent header detection to ensure table headers are read accurately.
        Returns: (df, selected_sheet_name, available_sheets)
        """
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        selected_sheet = sheet_name
        available_sheets = list(known_sheets) if known_sheets else []

        if suffix in [".xlsx", ".xls"]:
            if not available_sheets:
                available_sheets = cls.get_available_sheets(file_path)
            if not selected_sheet:
                if len(available_sheets) == 1:
                    selected_sheet = available_sheets[0]
                elif len(available_sheets) > 1:
                    # Intelligently find main data sheet:
                    # Skip 'README', 'INFO', 'COVER', 'PETUNJUK'
                    meta_names = {"readme", "info", "cover", "petunjuk", "catatan", "keterangan", "about"}
                    candidate_sheets = [s for s in available_sheets if s.strip().lower() not in meta_names]
                    
                    if candidate_sheets:
                        best_sheet = candidate_sheets[0]
                        max_cells = 0
                        for s in candidate_sheets:
                            try:
                                temp_df = pd.read_excel(file_path, sheet_name=s, engine="openpyxl" if suffix == ".xlsx" else None)
                                cells = temp_df.shape[0] * temp_df.shape[1]
                                if cells > max_cells:
                                    max_cells = cells
                                    best_sheet = s
                            except Exception:
                                pass
                        selected_sheet = best_sheet
                    else:
                        selected_sheet = available_sheets[0]

            header_idx = cls.detect_header_row(file_path, sheet_name=selected_sheet)
            df = pd.read_excel(
                file_path,
                sheet_name=selected_sheet,
                header=header_idx,
                engine="openpyxl" if suffix == ".xlsx" else None
            )
            # Remove trailing rows that are completely empty
            df = df.dropna(how="all").reset_index(drop=True)
        elif suffix == ".csv":
            try:
                df = pd.read_csv(file_path, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="latin1")
            df = df.dropna(how="all").reset_index(drop=True)
            selected_sheet = "CSV_Data"
            available_sheets = ["CSV_Data"]
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Only .xlsx, .xls, .csv are supported.")
        
        return df, selected_sheet or "Sheet1", available_sheets

    @staticmethod
    def extract_preview_data(df: pd.DataFrame, limit: int = 1000) -> list[dict[str, Any]]:
        """Fast helper to extract JSON-safe preview records for first N rows (or all if limit <= 0)."""
        preview_df = df.head(limit).copy() if limit and limit > 0 else df.copy()
        for col in preview_df.columns:
            if pd.api.types.is_datetime64_any_dtype(preview_df[col]):
                preview_df[col] = preview_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                preview_df[col] = preview_df[col].apply(
                    lambda v: None if pd.isna(v) else (int(v) if isinstance(v, (np.integer, int)) else (float(v) if isinstance(v, (np.floating, float)) else str(v)))
                )
        return preview_df.to_dict(orient="records")

    @classmethod
    def profile_dataframe(cls, df: pd.DataFrame) -> Tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Profiles the entire dataframe and returns:
        1. summary metadata
        2. column profiling statistics list
        3. preview data (up to 1000 rows)
        """
        total_rows, total_cols = df.shape
        columns_profile = []
        numeric_cols = []
        date_cols = []
        categorical_cols = []
        text_cols = []

        for idx, col_name in enumerate(df.columns):
            series = df[col_name]
            excel_letter = index_to_excel_col(idx)
            sanitized = sanitize_column_name(col_name)
            inferred_type = infer_series_type(series)

            null_count = int(series.isna().sum())
            null_pct = round((null_count / max(total_rows, 1)) * 100, 2)
            unique_count = int(series.nunique(dropna=True))
            unique_pct = round((unique_count / max(total_rows, 1)) * 100, 2)

            # Sample values (clean JSON serializable) - allow up to 100 for categorical/text to capture all categories/models
            max_samples = 100 if inferred_type in ["Categorical", "Text"] or unique_count <= 100 else 20
            non_null_samples = series.dropna().unique()[:max_samples]
            sample_values = [str(x) if isinstance(x, (pd.Timestamp, np.datetime64)) else (float(x) if isinstance(x, (np.floating, float)) else (int(x) if isinstance(x, (np.integer, int)) else str(x))) for x in non_null_samples]

            min_val = None
            max_val = None
            mean_val = None
            distribution = None

            if inferred_type == "Numeric":
                numeric_cols.append(col_name)
                num_series = pd.to_numeric(series, errors="coerce")
                if not num_series.dropna().empty:
                    min_val = str(round(float(num_series.min()), 2))
                    max_val = str(round(float(num_series.max()), 2))
                    mean_val = str(round(float(num_series.mean()), 2))
            elif inferred_type == "Date":
                date_cols.append(col_name)
                dt_series = pd.to_datetime(series, errors="coerce")
                valid_dts = dt_series.dropna()
                if not valid_dts.empty:
                    min_val = valid_dts.min().strftime("%Y-%m-%d")
                    max_val = valid_dts.max().strftime("%Y-%m-%d")
            elif inferred_type == "Categorical":
                categorical_cols.append(col_name)
                top_counts = series.value_counts(dropna=True).head(5).to_dict()
                distribution = {str(k): int(v) for k, v in top_counts.items()}
            else:
                text_cols.append(col_name)

            # Semantic classification
            sem_type = UniversalSemanticColumnDetector.classify_column(col_name, series)

            col_data = {
                "original_name": str(col_name),
                "sanitized_name": sanitized,
                "column_index": idx,
                "excel_column_letter": excel_letter,
                "inferred_type": inferred_type,
                "semantic_type": sem_type,
                "is_groupable": (sem_type == "CATEGORY"),
                "is_summable": (sem_type == "MEASURE"),
                "null_count": null_count,
                "null_percentage": null_pct,
                "unique_count": unique_count,
                "unique_percentage": unique_pct,
                "min_value": min_val,
                "max_value": max_val,
                "mean_value": mean_val,
                "sample_values": sample_values,
                "distribution": distribution,
            }
            columns_profile.append(col_data)

        summary = {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "numeric_columns": numeric_cols,
            "date_columns": date_cols,
            "categorical_columns": categorical_cols,
            "text_columns": text_cols,
            "semantic_columns": {str(c): UniversalSemanticColumnDetector.classify_column(c, df[c]) for c in df.columns}
        }

        preview_data = cls.extract_preview_data(df, limit=1000)
        return summary, columns_profile, preview_data
