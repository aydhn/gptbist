from bist_signal_bot.feature_store.serving import FeatureServingEngine

def test_serve_scanner():
    serving = FeatureServingEngine()
    frame = serving.serve_for_scanner(["ASELS"])
    assert frame.feature_set_id == "fs_scanner_core_v1"
    assert frame.point_in_time_safe is True
