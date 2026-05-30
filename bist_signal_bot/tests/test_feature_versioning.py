from bist_signal_bot.feature_store.versioning import FeatureVersionManager
from bist_signal_bot.feature_store.models import FeatureDefinition, FeatureKind
from datetime import datetime, timezone

def test_versioning():
    manager = FeatureVersionManager()
    fd = FeatureDefinition(feature_id="f1", feature_name="test_feat", feature_kind=FeatureKind.TECHNICAL, created_at=datetime.now(timezone.utc))
    v1 = manager.create_version(fd)
    assert v1.version == "1.0"
    v2 = manager.create_version(fd)
    assert v2.version == "1.1"
