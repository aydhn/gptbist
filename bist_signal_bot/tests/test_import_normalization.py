import pytest
import pandas as pd
from bist_signal_bot.data_import.normalization import ImportNormalizer
from bist_signal_bot.data_import.schema_mapping import SchemaMappingEngine
from bist_signal_bot.data_import.models import ImportDatasetType
from bist_signal_bot.config.settings import Settings

def test_normalize_symbol():
    normalizer = ImportNormalizer(Settings())
    assert normalizer.normalize_symbol("thyao ") == "THYAO"
    assert normalizer.normalize_symbol("garan.is") == "GARAN.IS"
    assert normalizer.normalize_symbol(None) is None

def test_normalize_numeric_comma():
    normalizer = ImportNormalizer(Settings())
    assert normalizer.normalize_numeric("1.234,56") == 1234.56
    assert normalizer.normalize_numeric("1,23") == 1.23
    assert normalizer.normalize_numeric("1000") == 1000.0
    assert normalizer.normalize_numeric(1.5) == 1.5

def test_normalize_date():
    normalizer = ImportNormalizer(Settings())
    assert normalizer.normalize_date("2024-01-01 10:00:00") == "2024-01-01"
    assert normalizer.normalize_date("01/02/2024") == "2024-01-02"

def test_normalize_dataframe():
    normalizer = ImportNormalizer(Settings())
    engine = SchemaMappingEngine(Settings())

    df = pd.DataFrame({
        "symbol": ["thyao ", "THYAO "],
        "date": ["2024-01-01", "2024-01-01"], # duplicate
        "close": ["1.234,56", "1.234,56"]
    })
    mapping = engine.infer_mapping(["symbol", "date", "close"], ImportDatasetType.OHLCV)

    df_norm, stats = normalizer.normalize_dataframe(df, mapping, ImportDatasetType.OHLCV)

    assert len(df_norm) == 1 # duplicate removed
    assert stats["duplicate_rows_removed"] == 1
    assert df_norm.iloc[0]["symbol"] == "THYAO"
    assert df_norm.iloc[0]["close"] == 1234.56
