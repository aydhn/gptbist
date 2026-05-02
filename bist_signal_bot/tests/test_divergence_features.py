import pytest
import pandas as pd
from datetime import datetime, timedelta
from bist_signal_bot.features.divergence_features import DivergenceFeatureBuilder

@pytest.fixture
def test_data():
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(100)]
    df = pd.DataFrame(index=dates)
    df['close'] = [100 + i for i in range(100)]
    df['high'] = df['close'] + 2
    df['low'] = df['close'] - 2
    df['open'] = df['close']
    df['volume'] = [1000] * 100
    return df

def test_divergence_feature_builder_levels(test_data):
    builder = DivergenceFeatureBuilder()

    # Basic
    res_basic = builder.build_basic_divergence_features(test_data)
    assert set(res_basic.result.requested_indicators) == {"rsi", "macd_hist", "obv"}

    # Advanced
    res_adv = builder.build_advanced_divergence_features(test_data)
    assert set(res_adv.result.requested_indicators) == {"mfi", "stoch_k", "ppo_hist", "cmf", "momentum"}

    # Full
    res_full = builder.build_full_divergence_features(test_data)
    assert len(res_full.result.requested_indicators) == 8

def test_divergence_feature_builder_invalid_level():
    builder = DivergenceFeatureBuilder()
    with pytest.raises(ValueError):
        builder.default_divergence_indicators("unknown_level")
