from bist_signal_bot.feature_store.registry import FeatureRegistry

def test_feature_registry_default_sets():
    registry = FeatureRegistry()
    sets = registry.default_feature_sets()
    assert any(s.name == "scanner_core_v1" for s in sets)
