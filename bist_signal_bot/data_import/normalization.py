from typing import Any
import pandas as pd
import numpy as np

from bist_signal_bot.data_import.models import (
    SchemaMapping,
    ImportDatasetType,
)
from bist_signal_bot.data_import.schema_mapping import SchemaMappingEngine

class ImportNormalizer:
    def __init__(self, settings: Any = None):
        self.settings = settings
        self.mapping_engine = SchemaMappingEngine(settings)

    def normalize_dataframe(self, df: pd.DataFrame, mapping: SchemaMapping, dataset_type: ImportDatasetType) -> tuple[pd.DataFrame, dict[str, Any]]:
        # Map columns first
        df_norm = self.mapping_engine.apply_mapping(df.copy(), mapping)

        stats = {
            "duplicate_rows_removed": 0,
            "invalid_rows_removed": 0
        }

        # Apply normalization based on semantic types from mapping
        for col_mapping in mapping.column_mappings:
            target_col = col_mapping.target_column
            if target_col not in df_norm.columns:
                continue

            sem_type = col_mapping.semantic_type

            if sem_type == "SYMBOL" and getattr(self.settings, "DATA_IMPORT_NORMALIZE_SYMBOLS", True):
                df_norm[target_col] = df_norm[target_col].apply(self.normalize_symbol)
            elif sem_type in ("DATE", "DATETIME") and getattr(self.settings, "DATA_IMPORT_NORMALIZE_DATES", True):
                df_norm[target_col] = df_norm[target_col].apply(self.normalize_date)
            elif sem_type in ("NUMERIC", "OPEN", "HIGH", "LOW", "CLOSE", "ADJUSTED_CLOSE", "VOLUME") or getattr(sem_type, "value", sem_type) in ("NUMERIC", "OPEN", "HIGH", "LOW", "CLOSE", "ADJUSTED_CLOSE", "VOLUME"):
                 if getattr(self.settings, "DATA_IMPORT_NORMALIZE_DECIMAL_COMMA", True):
                     df_norm[target_col] = df_norm[target_col].apply(self.normalize_numeric)
                 df_norm[target_col] = pd.to_numeric(df_norm[target_col], errors='coerce')

        # Drop invalid required
        if getattr(self.settings, "DATA_IMPORT_DROP_INVALID_REQUIRED_ROWS", True):
            req_cols = [m.target_column for m in mapping.column_mappings if m.required and m.target_column in df_norm.columns]
            if req_cols:
                 df_norm, invalid_count = self.drop_invalid_required(df_norm, req_cols)
                 stats["invalid_rows_removed"] = invalid_count

        # Deduplicate
        if getattr(self.settings, "DATA_IMPORT_DEDUPLICATE", True):
            key_cols = []
            if dataset_type == ImportDatasetType.OHLCV:
                 key_cols = [c for c in ["symbol", "date"] if c in df_norm.columns]
            elif dataset_type == ImportDatasetType.FINANCIALS:
                 key_cols = [c for c in ["symbol", "period"] if c in df_norm.columns]

            if key_cols:
                 df_norm, dup_count = self.deduplicate(df_norm, key_cols)
                 stats["duplicate_rows_removed"] = dup_count

        return df_norm, stats

    def normalize_symbol(self, value: Any) -> str | None:
        if pd.isna(value):
            return None
        val_str = str(value).strip().upper()
        if val_str.endswith(".IS"):
             return val_str
        return val_str

    def normalize_date(self, value: Any) -> str | None:
        if pd.isna(value):
            return None
        try:
             # deterministic parse
             dt = pd.to_datetime(value)
             if pd.isna(dt):
                 return None
             return dt.strftime("%Y-%m-%d")
        except Exception:
             return None

    def normalize_numeric(self, value: Any) -> float | None:
        if pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)

        val_str = str(value).strip()
        # handle decimal comma e.g. "1.234,56" or "1,23"
        # naive approach: if both . and , exist, assume the last one is decimal
        if "," in val_str and "." in val_str:
            last_comma = val_str.rfind(",")
            last_dot = val_str.rfind(".")
            if last_comma > last_dot:
                 # comma is decimal
                 val_str = val_str.replace(".", "").replace(",", ".")
            else:
                 # dot is decimal
                 val_str = val_str.replace(",", "")
        elif "," in val_str:
             val_str = val_str.replace(",", ".")

        try:
            return float(val_str)
        except ValueError:
            return None

    def normalize_text(self, value: Any) -> str | None:
        if pd.isna(value):
            return None
        return str(value).strip()

    def deduplicate(self, df: pd.DataFrame, key_columns: list[str]) -> tuple[pd.DataFrame, int]:
        initial_len = len(df)
        # only deduplicate if all key columns exist
        missing_keys = [c for c in key_columns if c not in df.columns]
        if missing_keys:
             return df, 0

        df_dedup = df.drop_duplicates(subset=key_columns, keep="last")
        removed = initial_len - len(df_dedup)
        return df_dedup, removed

    def drop_invalid_required(self, df: pd.DataFrame, required_columns: list[str]) -> tuple[pd.DataFrame, int]:
        initial_len = len(df)
        existing_req = [c for c in required_columns if c in df.columns]
        if not existing_req:
             return df, 0

        df_valid = df.dropna(subset=existing_req)
        removed = initial_len - len(df_valid)
        return df_valid, removed
