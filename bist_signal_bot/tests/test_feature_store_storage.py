from bist_signal_bot.feature_store.storage import FeatureStore
from bist_signal_bot.feature_store.contracts import FeatureContractRegistry

def test_feature_store_storage(tmp_path):
    store = FeatureStore(base_dir=tmp_path)
    registry = FeatureContractRegistry()
    contracts = registry.default_contracts()
    store.save_contracts(contracts)
    loaded = store.load_contracts()
    assert len(loaded) == len(contracts)
