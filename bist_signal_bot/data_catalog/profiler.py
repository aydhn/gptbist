import uuid
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from bist_signal_bot.data_catalog.models import (
    DatasetFormat,
    DatasetProfile,
    DatasetRecord,
)
from bist_signal_bot.config.settings import Settings, get_settings


class DatasetProfiler:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir

    def _resolve_path(self, path_str: str) -> Path:
        p = Path(path_str)
        if self.base_dir and not p.is_absolute():
            return self.base_dir / p
        return p

    def profile_dataset(self, dataset: DatasetRecord) -> DatasetProfile:
        warnings = []
        df = None
        detected_format = dataset.dataset_format

        try:
            detected_format = self.detect_format(dataset)
            if detected_format in (DatasetFormat.CSV, DatasetFormat.PARQUET, DatasetFormat.JSONL):
                df = self.load_dataset_sample(dataset)
        except Exception as e:
            warnings.append(f"Could not load dataset for profiling: {e}")

        if df is not None and not df.empty:
            row_count = len(df)
            col_count = len(df.columns)
            columns = df.columns.tolist()

            null_ratios_dict = {}
            if self.settings.DATA_CATALOG_PROFILE_NULL_RATIOS:
                null_ratios_dict = self.null_ratios(df)

            dup_count = 0
            if self.settings.DATA_CATALOG_PROFILE_DUPLICATES:
                dup_count = self.duplicate_count(df)

            min_dates = {}
            max_dates = {}
            if self.settings.DATA_CATALOG_PROFILE_DATE_RANGES:
                 # Guess date columns (e.g. columns with "date" or "time")
                 date_cols = [c for c in columns if "date" in c.lower() or "time" in c.lower()]
                 date_ranges_dict = self.date_ranges(df, date_cols)
                 for col, ranges in date_ranges_dict.items():
                     min_dates[col] = ranges["min"]
                     max_dates[col] = ranges["max"]

            num_ranges = {}
            if self.settings.DATA_CATALOG_PROFILE_NUMERIC_RANGES:
                num_ranges = self.numeric_ranges(df)

        else:
            row_count = 0
            col_count = 0
            columns = []
            null_ratios_dict = {}
            dup_count = 0
            min_dates = {}
            max_dates = {}
            num_ranges = {}

        return DatasetProfile(
            profile_id=f"prof_{uuid.uuid4().hex[:12]}",
            dataset_id=dataset.dataset_id,
            created_at=datetime.now(timezone.utc),
            row_count=row_count,
            column_count=col_count,
            columns=columns,
            null_ratios=null_ratios_dict,
            duplicate_count=dup_count,
            min_dates=min_dates,
            max_dates=max_dates,
            numeric_ranges=num_ranges,
            detected_format=detected_format,
            warnings=warnings
        )

    def load_dataset_sample(self, dataset: DatasetRecord, max_rows: int | None = None) -> pd.DataFrame:
        if max_rows is None:
            max_rows = self.settings.DATA_CATALOG_PROFILE_MAX_ROWS

        path = self._resolve_path(dataset.path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset path does not exist: {path}")

        fmt = self.detect_format(dataset)

        if fmt == DatasetFormat.CSV:
            return pd.read_csv(path, nrows=max_rows)
        elif fmt == DatasetFormat.PARQUET:
            return pd.read_parquet(path) # parquet sampling is harder, read all for now or use filters
        elif fmt == DatasetFormat.JSONL:
            # Read line by line up to max_rows
            records = []
            with open(path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= max_rows:
                        break
                    if line.strip():
                        records.append(json.loads(line))
            return pd.DataFrame(records)
        else:
             raise ValueError(f"Unsupported format for sampling: {fmt}")

    def null_ratios(self, df: pd.DataFrame) -> dict[str, float]:
        if df.empty:
            return {}
        return (df.isnull().sum() / len(df)).to_dict()

    def duplicate_count(self, df: pd.DataFrame, key_columns: list[str] | None = None) -> int:
        if df.empty:
            return 0
        if key_columns:
            # only check keys that exist
            existing_keys = [k for k in key_columns if k in df.columns]
            if not existing_keys:
                 return 0
            return int(df.duplicated(subset=existing_keys).sum())
        return int(df.duplicated().sum())

    def date_ranges(self, df: pd.DataFrame, date_columns: list[str]) -> dict[str, dict[str, str | None]]:
        res = {}
        for col in date_columns:
            if col in df.columns:
                try:
                    s = pd.to_datetime(df[col], errors='coerce')
                    min_dt = s.min()
                    max_dt = s.max()
                    res[col] = {
                        "min": min_dt.isoformat() if pd.notnull(min_dt) else None,
                        "max": max_dt.isoformat() if pd.notnull(max_dt) else None
                    }
                except Exception:
                    res[col] = {"min": None, "max": None}
        return res

    def numeric_ranges(self, df: pd.DataFrame) -> dict[str, dict[str, float | None]]:
        res = {}
        # Select numeric columns
        num_df = df.select_dtypes(include=['number'])
        for col in num_df.columns:
            min_val = num_df[col].min()
            max_val = num_df[col].max()
            res[col] = {
                "min": float(min_val) if pd.notnull(min_val) else None,
                "max": float(max_val) if pd.notnull(max_val) else None
            }
        return res

    def detect_format(self, dataset: DatasetRecord) -> DatasetFormat:
        path = self._resolve_path(dataset.path)
        if path.is_dir():
            return DatasetFormat.DIRECTORY

        ext = path.suffix.lower()
        if ext == ".csv":
            return DatasetFormat.CSV
        if ext == ".json":
            return DatasetFormat.JSON
        if ext == ".jsonl":
            return DatasetFormat.JSONL
        if ext == ".parquet":
            return DatasetFormat.PARQUET
        if ext in (".db", ".sqlite", ".sqlite3"):
            return DatasetFormat.SQLITE
        if ext == ".md":
            return DatasetFormat.MARKDOWN

        return DatasetFormat.UNKNOWN
