import pytest
from bist_signal_bot.data_import.preview import ImportPreviewBuilder
from bist_signal_bot.data_import.models import ImportDatasetType
from bist_signal_bot.config.settings import Settings

def test_infer_types():
    builder = ImportPreviewBuilder(Settings())
    rows = [{"a": 1, "b": 1.5, "c": "test", "d": True}]
    types = builder.infer_types(rows)
    assert types["a"] == "integer"
    assert types["b"] == "float"
    assert types["c"] == "string"
    assert types["d"] == "boolean"

def test_sanitize_rows():
    builder = ImportPreviewBuilder(Settings())
    import math
    rows = [{"a": float('nan'), "b": 1}]
    sanitized = builder.sanitize_sample_rows(rows)
    assert sanitized[0]["a"] is None
    assert sanitized[0]["b"] == 1
