import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.patterns.engine import PatternRegistry, PatternEngine
from bist_signal_bot.patterns.models import PatternRequest, PatternStatus

@pytest.fixture
def sample_data():
    np.random.seed(42)
    return pd.DataFrame({
        "open": np.random.uniform(100, 110, 50),
        "high": np.random.uniform(105, 115, 50),
        "low": np.random.uniform(95, 105, 50),
        "close": np.random.uniform(100, 110, 50),
        "volume": np.random.uniform(1000, 5000, 50)
    })

def test_pattern_registry():
    registry = PatternRegistry.create_default_pattern_registry()
    assert registry.exists("price_breakout")
    assert registry.exists("doji")

    with pytest.raises(ValueError):
        # Register duplicate
        registry.register(registry.get("doji"))

def test_pattern_engine_detect(sample_data):
    engine = PatternEngine()
    req = PatternRequest(name="price_breakout", params={"window": 10})
    df, res = engine.detect(sample_data, req)

    assert res.status == PatternStatus.SUCCESS
    assert "price_breakout_up_10" in df.columns
    assert "price_breakout_up_10" in res.output_columns

def test_pattern_engine_detect_many(sample_data):
    engine = PatternEngine()
    reqs = [
        PatternRequest(name="price_breakout", params={"window": 10}),
        PatternRequest(name="doji")
    ]
    batch_res = engine.detect_many(sample_data, reqs)

    assert batch_res.success_count == 2
    assert "price_breakout_up_10" in batch_res.output_data.columns
    assert "candle_doji_0.1" in batch_res.output_data.columns

def test_parse_requests():
    engine = PatternEngine()
    reqs = engine.parse_requests(["price_breakout:window=20", "doji"])
    assert len(reqs) == 2
    assert reqs[0].name == "price_breakout"
    assert reqs[0].params["window"] == 20
    assert reqs[1].name == "doji"
