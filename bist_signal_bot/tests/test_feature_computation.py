from bist_signal_bot.feature_store.computation import FeatureComputationEngine

def test_pct_change():
    engine = FeatureComputationEngine()
    res = engine.safe_pct_change([100.0, 110.0], 1)
    assert res == 0.1

def test_rolling_std():
    engine = FeatureComputationEngine()
    res = engine.safe_rolling_std([1.0, 2.0, 3.0], 3)
    assert res == 1.0

def test_zscore():
    engine = FeatureComputationEngine()
    res = engine.safe_zscore([1.0, 2.0, 3.0], 3)
    assert res == 1.0 # (3-2)/1
