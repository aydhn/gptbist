from bist_signal_bot.feature_store.contracts import FeatureContractRegistry

def test_feature_contract_registry_defaults():
    registry = FeatureContractRegistry()
    defaults = registry.default_contracts()
    assert len(defaults) > 0
    assert any(c.feature_name == "momentum_20d" for c in defaults)
