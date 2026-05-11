import pytest
import pandas as pd
from datetime import datetime, timezone
from bist_signal_bot.ml.feature_store import FeatureStore
from bist_signal_bot.ml.models import MLDatasetResult, MLDatasetRequest, MLDatasetStatus, MLDatasetSchema, FeatureStoreFormat
from bist_signal_bot.config.settings import Settings

def test_feature_store_csv_fallback(tmp_path):
    settings = Settings()
    store = FeatureStore(settings, base_dir=tmp_path)

    # Mock result
    req = MLDatasetRequest(symbols=["A"], source="mock", timeframe="1d", task_type="CLASSIFICATION", label_config={"label_type": "FORWARD_RETURN", "horizon_bars": 1}, feature_config={"feature_set_level": "BASIC"}, preprocessing_config={}, split_mode="NONE")
    schema = MLDatasetSchema(symbol_col="symbol", timestamp_col="timestamp", feature_cols=["feat_1"], label_cols=["label_1"], metadata_cols=[], excluded_cols=[], generated_at=datetime.now(timezone.utc))

    result = MLDatasetResult(
        request=req,
        status=MLDatasetStatus.SUCCESS,
        data=pd.DataFrame({"symbol": ["A"], "timestamp": [1], "feat_1": [1], "label_1": [1]}),
        schema_=schema,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc)
    )

    # Force CSV only
    out = store.save_dataset(result, formats=[FeatureStoreFormat.CSV])
    assert "dataset.csv" in out

def test_feature_store_save_schema(tmp_path):
    settings = Settings()
    store = FeatureStore(settings, base_dir=tmp_path)
    schema = MLDatasetSchema(symbol_col="symbol", timestamp_col="timestamp", feature_cols=["feat_1"], label_cols=["label_1"], metadata_cols=[], excluded_cols=[], generated_at=datetime.now(timezone.utc))

    path = store.save_schema(schema, tmp_path)
    assert path.exists()
    assert "dataset_schema.json" in str(path)
