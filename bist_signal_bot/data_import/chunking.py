from typing import Any, Iterable
import pandas as pd
from pathlib import Path

from bist_signal_bot.data_import.models import SchemaMapping, ImportDatasetType
from bist_signal_bot.data_import.adapters import LocalImportAdapterRegistry
from bist_signal_bot.data_import.normalization import ImportNormalizer
from bist_signal_bot.core.exceptions import ImportChunkingError

class ImportChunkReader:
    def __init__(self, settings: Any = None, base_dir: Path | None = None):
        self.settings = settings
        self.registry = LocalImportAdapterRegistry(settings, base_dir)
        self.normalizer = ImportNormalizer(settings)

    def read_in_chunks(self, path: Path, chunk_size: int) -> Iterable[pd.DataFrame]:
        try:
            yield from self.registry.read_chunks(path, chunk_size)
        except Exception as e:
            raise ImportChunkingError(f"Failed to read chunks from {path}: {e}")

    def chunk_count_estimate(self, path: Path, chunk_size: int) -> int | None:
        if chunk_size <= 0:
            return None

        from bist_signal_bot.data_import.preview import ImportPreviewBuilder
        preview_builder = ImportPreviewBuilder(self.settings, None) # base_dir not needed here
        row_count = preview_builder.estimate_row_count(path)
        if row_count is None:
            return None

        import math
        return math.ceil(row_count / chunk_size)

    def normalize_chunks(self, path: Path, mapping: SchemaMapping, dataset_type: ImportDatasetType, chunk_size: int) -> Iterable[tuple[pd.DataFrame, dict[str, Any]]]:
        for chunk in self.read_in_chunks(path, chunk_size):
             df_norm, stats = self.normalizer.normalize_dataframe(chunk, mapping, dataset_type)
             yield df_norm, stats

    def combine_chunk_summaries(self, summaries: list[dict[str, Any]]) -> dict[str, Any]:
        combined = {
            "duplicate_rows_removed": 0,
            "invalid_rows_removed": 0
        }
        for s in summaries:
             combined["duplicate_rows_removed"] += s.get("duplicate_rows_removed", 0)
             combined["invalid_rows_removed"] += s.get("invalid_rows_removed", 0)
        return combined
