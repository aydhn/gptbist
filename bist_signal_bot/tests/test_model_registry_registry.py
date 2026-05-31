import pytest
from datetime import datetime, timezone
from bist_signal_bot.model_registry.registry import LocalModelRegistry
from bist_signal_bot.model_registry.models import ModelRecord, ModelKind, ModelRegistryStatus
from bist_signal_bot.config.settings import Settings

class DummyStore:
    def __init__(self):
        self.models = []
    def append_model(self, model):
        self.models.append(model)
    def load_models(self, status=None, limit=1000):
        res = self.models
        if status:
            res = [m for m in res if m.status == status]
        return res[:limit]
    def get_model(self, model_id_or_name):
        return next((m for m in self.models if m.model_id == model_id_or_name or m.model_name == model_id_or_name), None)

def test_registry_register_dry_run():
    store = DummyStore()
    registry = LocalModelRegistry(store=store)
    m = ModelRecord(model_id="m1", model_name="m1", version="1.0", model_kind=ModelKind.CLASSIFIER, status=ModelRegistryStatus.STAGING, created_at=datetime.now(timezone.utc))

    registry.register_model(m, confirm=False)
    assert len(store.models) == 0

def test_registry_register_confirm():
    store = DummyStore()
    registry = LocalModelRegistry(store=store)
    m = ModelRecord(model_id="m1", model_name="m1", version="1.0", model_kind=ModelKind.CLASSIFIER, status=ModelRegistryStatus.STAGING, created_at=datetime.now(timezone.utc))

    registry.register_model(m, confirm=True)
    assert len(store.models) == 1
    assert store.models[0].model_id == "m1"

def test_registry_active_research_validation():
    store = DummyStore()
    settings = Settings()
    # Ensure properties exist on settings in our dummy test
    settings.MODEL_REGISTRY_REQUIRE_VALIDATION = True
    settings.MODEL_REGISTRY_REQUIRE_CALIBRATION = True
    settings.MODEL_REGISTRY_REQUIRE_FEATURE_SET_VERSION = True

    registry = LocalModelRegistry(settings=settings, store=store)
    m = ModelRecord(model_id="m1", model_name="m1", version="1.0", model_kind=ModelKind.CLASSIFIER, status=ModelRegistryStatus.ACTIVE_RESEARCH, created_at=datetime.now(timezone.utc))

    issues = registry.validate_model_record(m)
    assert len(issues) == 3
    assert "ACTIVE_RESEARCH model requires validation metadata" in issues
    assert "ACTIVE_RESEARCH model requires calibration metadata" in issues
    assert "ACTIVE_RESEARCH model requires feature_set_version" in issues

def test_registry_archive_model():
    store = DummyStore()
    registry = LocalModelRegistry(store=store)
    m = ModelRecord(model_id="m1", model_name="m1", version="1.0", model_kind=ModelKind.CLASSIFIER, status=ModelRegistryStatus.STAGING, created_at=datetime.now(timezone.utc))
    store.append_model(m)

    registry.archive_model("m1", confirm=True)
    assert store.models[-1].status == ModelRegistryStatus.ARCHIVED
