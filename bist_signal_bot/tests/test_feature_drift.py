from bist_signal_bot.feature_store.drift import FeatureDriftDetector

def test_drift_detector():
    detector = FeatureDriftDetector()
    ms = detector.mean_shift("test", [1.0]*30, [100.0]*30)
    assert ms is not None
