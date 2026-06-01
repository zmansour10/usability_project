from dataclasses import dataclass
from typing import Any, List, Optional, Dict
import pandas as pd

@dataclass
class ColumnMetadata:
    name: str
    filter_type: str  # "categorical" | "numeric" | "datetime" | "boolean" | "text" | "id"
    min_val: Optional[Any] = None
    max_val: Optional[Any] = None
    unique_values: Optional[List[Any]] = None

class SchemaInference:
    @staticmethod
    def infer_schema(df: pd.DataFrame) -> Dict[str, ColumnMetadata]:
        """Dynamically infers data type, filter strategy, and boundary values for each column in df."""
        schema = {}
        
        for col in df.columns:
            # Check if column is datetime
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                schema[col] = ColumnMetadata(
                    name=col,
                    filter_type="datetime",
                    min_val=df[col].min(),
                    max_val=df[col].max()
                )
                continue
                
            # If object/string, try to infer if it represents dates (e.g. contains 'Date' in name)
            if df[col].dtype == object or isinstance(df[col].dtype, pd.CategoricalDtype):
                # Clean strings
                non_nulls = df[col].dropna().astype(str).str.strip()
                if non_nulls.empty:
                    cardinality = 0
                    unique_vals = []
                else:
                    unique_vals = sorted(non_nulls.unique())
                    cardinality = len(unique_vals)
                
                # Check for ID columns
                if "ID" in col or col.lower().endswith("id"):
                    schema[col] = ColumnMetadata(
                        name=col,
                        filter_type="id"
                    )
                    continue
                
                # Check if it represents date
                if "date" in col.lower() or "timestamp" in col.lower():
                    # Attempt conversion to see if it is a datetime column
                    try:
                        converted = pd.to_datetime(df[col], errors='coerce')
                        if converted.notna().sum() > 0.5 * len(df):  # at least 50% are valid dates
                            schema[col] = ColumnMetadata(
                                name=col,
                                filter_type="datetime",
                                min_val=converted.min(),
                                max_val=converted.max()
                            )
                            continue
                    except Exception:
                        pass
                
                # If cardinality is low, or it represents a standard category (e.g., gender, status, country)
                # Up to 350 unique categories can be managed by the multiselect search dropdown
                if cardinality <= 350:
                    schema[col] = ColumnMetadata(
                        name=col,
                        filter_type="categorical",
                        unique_values=unique_vals
                    )
                else:
                    schema[col] = ColumnMetadata(
                        name=col,
                        filter_type="text"
                    )
            
            # Check for Boolean columns
            elif pd.api.types.is_bool_dtype(df[col]):
                schema[col] = ColumnMetadata(
                    name=col,
                    filter_type="boolean",
                    unique_values=[True, False]
                )
            
            # Numeric columns (int or float)
            elif pd.api.types.is_numeric_dtype(df[col]):
                non_nulls = df[col].dropna()
                if non_nulls.empty:
                    min_v, max_v = 0.0, 100.0
                else:
                    min_v, max_v = non_nulls.min(), non_nulls.max()
                
                # If numeric column has very few unique values, could be categorical/boolean
                unique_vals = sorted(non_nulls.unique())
                if len(unique_vals) <= 5:
                    schema[col] = ColumnMetadata(
                        name=col,
                        filter_type="categorical",
                        unique_values=unique_vals
                    )
                else:
                    schema[col] = ColumnMetadata(
                        name=col,
                        filter_type="numeric",
                        min_val=min_v,
                        max_val=max_v
                    )
            else:
                # Fallback to general text
                schema[col] = ColumnMetadata(
                    name=col,
                    filter_type="text"
                )
                
        return schema
