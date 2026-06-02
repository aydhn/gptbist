from typing import Any
from pathlib import Path
import uuid
from datetime import datetime, timezone
import pandas as pd

from bist_signal_bot.data_import.models import (
    ImportPreview,
    ImportDatasetType,
)
from bist_signal_bot.data_import.adapters import LocalImportAdapterRegistry

class ImportPreviewBuilder:
    def __init__(self, settings: Any = None, base_dir: Path | None = None):
        self.settings = settings
        self.registry = LocalImportAdapterRegistry(settings, base_dir)

    def build_preview(self, path: Path, dataset_type: ImportDatasetType, max_rows: int = 20) -> ImportPreview:
        adapter = self.registry.adapter_for_path(path)

        # Read preview rows
        raw_rows = self.registry.read_preview(path, max_rows)
        sanitized_rows = self.sanitize_sample_rows(raw_rows)

        columns = list(sanitized_rows[0].keys()) if sanitized_rows else []
        inferred_types = self.infer_types(sanitized_rows) if sanitized_rows else {}

        row_count = None
        if self.settings and getattr(self.settings, "DATA_IMPORT_ROW_COUNT_ESTIMATE", True):
             row_count = self.estimate_row_count(path)

        return ImportPreview(
            preview_id=str(uuid.uuid4()),
            source_id="tmp", # will be set by caller
            created_at=datetime.now(timezone.utc),
            row_count_estimate=row_count,
            column_count=len(columns),
            columns=columns,
            sample_rows=sanitized_rows,
            inferred_types=inferred_types
        )

    def infer_types(self, rows: list[dict[str, Any]]) -> dict[str, str]:
        if not rows:
            return {}

        df = pd.DataFrame(rows)
        type_map = {}
        for col, dtype in df.dtypes.items():
            if pd.api.types.is_integer_dtype(dtype):
                type_map[col] = "integer"
            elif pd.api.types.is_float_dtype(dtype):
                type_map[col] = "float"
            elif pd.api.types.is_bool_dtype(dtype):
                type_map[col] = "boolean"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                type_map[col] = "datetime"
            else:
                type_map[col] = "string"
        return type_map

    def estimate_row_count(self, path: Path) -> int | None:
        fmt = self.registry.infer_format(path)
        try:
             if fmt == "CSV":
                 with open(path, 'rb') as f:
                     return sum(1 for _ in f) - 1 # header
             elif fmt == "JSONL":
                 with open(path, 'rb') as f:
                     return sum(1 for _ in f)
        except Exception:
             pass
        return None

    def sanitize_sample_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # NaN / NaT vs None sanitization for JSON serialization
        import math
        sanitized = []
        for row in rows:
            new_row = {}
            for k, v in row.items():
                if pd.isna(v):
                    new_row[k] = None
                elif isinstance(v, float) and math.isnan(v):
                    new_row[k] = None
                else:
                    new_row[k] = v
            sanitized.append(new_row)
        return sanitized
