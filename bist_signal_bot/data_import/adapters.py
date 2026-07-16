import re
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from bist_signal_bot.core.exceptions import DataImportAdapterError
from bist_signal_bot.data_import.models import (
    ImportAdapterCapability,
    ImportSourceFormat,
)


class LocalImportAdapterRegistry:
    def __init__(self, settings: Any = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir

    def adapter_for_path(self, path: Path) -> Any:
        fmt = self.infer_format(path)
        if fmt == ImportSourceFormat.UNKNOWN:
            raise DataImportAdapterError(f"Unsupported format for path: {path}")
        return fmt

    def infer_format(self, path: Path) -> ImportSourceFormat:
        if not path.is_file():
            return ImportSourceFormat.UNKNOWN

        ext = path.suffix.lower()
        if ext == ".csv":
            return ImportSourceFormat.CSV
        elif ext == ".json":
            return ImportSourceFormat.JSON
        elif ext == ".jsonl":
            return ImportSourceFormat.JSONL
        elif ext == ".parquet":
            return ImportSourceFormat.PARQUET
        elif ext in (".db", ".sqlite", ".sqlite3"):
            return ImportSourceFormat.SQLITE
        elif ext in (".xls", ".xlsx"):
            return ImportSourceFormat.EXCEL
        return ImportSourceFormat.UNKNOWN

    def supported_formats(self) -> list[ImportSourceFormat]:
        formats = [
            ImportSourceFormat.CSV,
            ImportSourceFormat.JSON,
            ImportSourceFormat.JSONL,
            ImportSourceFormat.SQLITE,
        ]

        # Check Parquet support
        try:
            import pyarrow  # noqa: F401

            formats.append(ImportSourceFormat.PARQUET)
        except ImportError:
            pass

        # Check Excel support
        try:
            import openpyxl  # noqa: F401

            formats.append(ImportSourceFormat.EXCEL)
        except ImportError:
            pass

        return formats

    def capabilities(self, fmt: ImportSourceFormat) -> list[ImportAdapterCapability]:
        base_caps = [
            ImportAdapterCapability.PREVIEW,
            ImportAdapterCapability.TYPE_INFER,
        ]
        if fmt in (ImportSourceFormat.CSV, ImportSourceFormat.JSONL, ImportSourceFormat.PARQUET):
            base_caps.append(ImportAdapterCapability.CHUNK_READ)
        return base_caps

    def read_preview(self, path: Path, max_rows: int = 20) -> list[dict[str, Any]]:
        fmt = self.infer_format(path)
        if fmt == ImportSourceFormat.CSV:
            df = pd.read_csv(path, nrows=max_rows)
            return df.to_dict(orient="records")
        elif fmt == ImportSourceFormat.JSONL:
            rows = []
            with open(path, "r", encoding="utf-8") as f:
                for _ in range(max_rows):
                    line = f.readline()
                    if not line:
                        break
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return rows
        elif fmt == ImportSourceFormat.JSON:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data[:max_rows]
                elif isinstance(data, dict) and len(data) > 0:
                    # attempt to find the first list
                    for k, v in data.items():
                        if isinstance(v, list):
                            return v[:max_rows]
            return []
        elif fmt == ImportSourceFormat.PARQUET:
            df = pd.read_parquet(path)
            return df.head(max_rows).to_dict(orient="records")
        elif fmt == ImportSourceFormat.SQLITE:
            try:
                conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                if not tables:
                    return []
                table_name = tables[0][0]
                # Strictly validate that the table name only contains safe characters
                if not re.fullmatch(r"^[a-zA-Z0-9_]+$", table_name):
                    raise DataImportAdapterError(f"Invalid table name detected: {table_name}")

                safe_table_name = f'"{table_name}"'
                query = f"SELECT * FROM {safe_table_name} LIMIT ?"
                df = pd.read_sql_query(query, conn, params=(max_rows,))  # nosec B608
                conn.close()
                return df.to_dict(orient="records")
            except Exception as e:
                raise DataImportAdapterError(f"SQLite read error: {e}")
        elif fmt == ImportSourceFormat.EXCEL:
            df = pd.read_excel(path, nrows=max_rows)
            return df.to_dict(orient="records")
        raise DataImportAdapterError(f"Preview not supported for {fmt}")

    def read_dataframe(self, path: Path, max_rows: int | None = None) -> pd.DataFrame:
        fmt = self.infer_format(path)
        if fmt == ImportSourceFormat.CSV:
            return pd.read_csv(path, nrows=max_rows)
        elif fmt == ImportSourceFormat.JSONL:
            return pd.read_json(path, lines=True, nrows=max_rows)
        elif fmt == ImportSourceFormat.JSON:
            df = pd.read_json(path)
            if max_rows:
                return df.head(max_rows)
            return df
        elif fmt == ImportSourceFormat.PARQUET:
            df = pd.read_parquet(path)
            if max_rows:
                return df.head(max_rows)
            return df
        elif fmt == ImportSourceFormat.SQLITE:
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            if not tables:
                return pd.DataFrame()
            table_name = tables[0][0]
            # Strictly validate that the table name only contains safe characters
            if not re.fullmatch(r"^[a-zA-Z0-9_]+$", table_name):
                raise DataImportAdapterError(f"Invalid table name detected: {table_name}")

            safe_table_name = f'"{table_name}"'
            query = f"SELECT * FROM {safe_table_name}"
            params = ()
            if max_rows:
                query += " LIMIT ?"
                params = (max_rows,)
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        elif fmt == ImportSourceFormat.EXCEL:
            return pd.read_excel(path, nrows=max_rows)
        raise DataImportAdapterError(f"Read dataframe not supported for {fmt}")

    def read_chunks(self, path: Path, chunk_size: int) -> Iterable[pd.DataFrame]:
        fmt = self.infer_format(path)
        if fmt == ImportSourceFormat.CSV:
            yield from pd.read_csv(path, chunksize=chunk_size)
        elif fmt == ImportSourceFormat.JSONL:
            yield from pd.read_json(path, lines=True, chunksize=chunk_size)
        elif fmt == ImportSourceFormat.PARQUET:
            # Parquet doesn't easily chunk in pandas without pyarrow.dataset,
            # so we might load all and yield chunks or use fastparquet/pyarrow
            import pyarrow.parquet as pq

            parquet_file = pq.ParquetFile(path)
            for batch in parquet_file.iter_batches(batch_size=chunk_size):
                yield batch.to_pandas()
        else:
            raise DataImportAdapterError(f"Chunking not supported for {fmt}")
