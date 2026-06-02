import pytest
from bist_signal_bot.data_import.schema_mapping import SchemaMappingEngine
from bist_signal_bot.data_import.models import ImportDatasetType, ImportStatus
from bist_signal_bot.config.settings import Settings
import pandas as pd

def test_infer_mapping_ohlcv():
    engine = SchemaMappingEngine(Settings())
    cols = ["Sembol", "Tarih", "Açılış", "Yüksek", "Düşük", "Kapanış", "Hacim", "Other"]
    mapping = engine.infer_mapping(cols, ImportDatasetType.OHLCV)

    assert mapping.status == ImportStatus.PASS
    assert len(mapping.missing_required_targets) == 0
    assert "Other" in mapping.unmapped_columns

def test_infer_mapping_missing_required():
    engine = SchemaMappingEngine(Settings())
    cols = ["symbol", "open", "close"] # missing date, high, low, volume
    mapping = engine.infer_mapping(cols, ImportDatasetType.OHLCV)

    assert mapping.status == ImportStatus.FAIL
    assert "date" in mapping.missing_required_targets

def test_apply_mapping():
    engine = SchemaMappingEngine(Settings())
    df = pd.DataFrame({"Sembol": ["THYAO"], "Kapanış": [100.5]})
    mapping = engine.infer_mapping(["Sembol", "Kapanış"], ImportDatasetType.OHLCV)

    mapped_df = engine.apply_mapping(df, mapping)
    assert "symbol" in mapped_df.columns
    assert "close" in mapped_df.columns
    assert mapped_df["symbol"].iloc[0] == "THYAO"
