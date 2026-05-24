import pytest
from unittest.mock import MagicMock
from bist_signal_bot.config_registry.models import (
    ConfigDefinition, ConfigModule, ConfigValueRecord, ConfigSafetyLevel, ConfigValueType,
    FeatureFlagState, RuntimeProfileType
)
from bist_signal_bot.config_registry.schema import ConfigSchemaBuilder
from bist_signal_bot.config_registry.registry import ConfigRegistry
from bist_signal_bot.config_registry.flags import FeatureFlagManager
from bist_signal_bot.config_registry.profiles import RuntimeProfileManager
from bist_signal_bot.config_registry.validator import ConfigValidator
from bist_signal_bot.config_registry.snapshot import ConfigSnapshotManager
from bist_signal_bot.config_registry.diff import ConfigDiffEngine
from bist_signal_bot.config_registry.drift import ConfigDriftDetector
from bist_signal_bot.config_registry.gate import ConfigGate


@pytest.fixture
def test_settings():
    class MockSettings:
        ENABLE_CONFIG_REGISTRY = True
        TELEGRAM_BOT_TOKEN = "secret-token-123"
        BROKER_ENABLED = False
    return MockSettings()

def test_config_definition_validation():
    # Should raise error for FORBIDDEN with unsafe default
    with pytest.raises(ValueError, match="FORBIDDEN safety level configs must default to safe"):
        ConfigDefinition(
            key="BAD_CONFIG",
            module=ConfigModule.CORE,
            value_type=ConfigValueType.BOOLEAN,
            default_value=True,
            description="Bad forbidden config",
            safety_level=ConfigSafetyLevel.FORBIDDEN
        )

def test_secret_safety_level():
    # Should raise error if secret is not SENSITIVE+
    with pytest.raises(ValueError, match="Secret configs must have at least SENSITIVE"):
        ConfigDefinition(
            key="BAD_SECRET",
            module=ConfigModule.CORE,
            value_type=ConfigValueType.SECRET,
            default_value="",
            description="Bad secret config",
            safety_level=ConfigSafetyLevel.SAFE,
            secret=True
        )

def test_runtime_profile_validation():
    with pytest.raises(ValueError, match="broker_enabled must be false"):
        from bist_signal_bot.config_registry.models import RuntimeProfile
        RuntimeProfile(
            profile_id="1",
            profile_type=RuntimeProfileType.CUSTOM,
            name="Bad Profile",
            description="",
            broker_enabled=True
        )

def test_schema_builder_default_schema():
    builder = ConfigSchemaBuilder()
    schema = builder.build_default_schema()

    # Check forbidden configs
    forbidden_keys = ["BROKER_ENABLED", "REAL_ORDER_ENABLED", "ALLOW_HTML_SCRAPING"]
    for k in forbidden_keys:
        d = builder.definition_for_key(k)
        assert d is not None
        assert d.safety_level == ConfigSafetyLevel.FORBIDDEN
        assert d.default_value is False

def test_registry_load_and_redact(test_settings):
    builder = ConfigSchemaBuilder()
    registry = ConfigRegistry(schema_builder=builder, settings=test_settings)

    records = registry.load_records()
    tele_rec = registry.get_record("TELEGRAM_BOT_TOKEN")

    assert tele_rec is not None
    assert tele_rec.value == "secret-token-123"
    assert "secret-token-123" not in tele_rec.value_redacted
    assert "REDACTED" in tele_rec.value_redacted or "***" in tele_rec.value_redacted

def test_registry_show_summary(test_settings):
    builder = ConfigSchemaBuilder()
    registry = ConfigRegistry(schema_builder=builder, settings=test_settings)

    summary = registry.redacted_summary()
    assert "TELEGRAM_BOT_TOKEN" in summary
    assert "secret-token-123" not in summary["TELEGRAM_BOT_TOKEN"]

def test_feature_flag_manager():
    manager = FeatureFlagManager()
    flags = manager.default_flags()
    assert len(flags) > 0

    # Try forbidden change
    with pytest.raises(ValueError, match="requires confirmation"):
        manager.set_flag("ENABLE_TELEGRAM_CENTER", FeatureFlagState.ENABLED)

    manager.set_flag("ENABLE_TELEGRAM_CENTER", FeatureFlagState.ENABLED, confirm=True)
    f = manager.get_flag("ENABLE_TELEGRAM_CENTER")
    assert f.state == FeatureFlagState.ENABLED

def test_runtime_profile_manager():
    manager = RuntimeProfileManager()
    profiles = manager.default_profiles()
    assert len(profiles) > 0

    with pytest.raises(ValueError, match="requires confirmation"):
        manager.apply_profile(RuntimeProfileType.RESEARCH_ONLY)

    p = manager.apply_profile(RuntimeProfileType.RESEARCH_ONLY, confirm=True)
    assert p.force_research_only is True

def test_config_validator_forbidden(test_settings):
    builder = ConfigSchemaBuilder()
    registry = ConfigRegistry(schema_builder=builder, settings=test_settings)
    validator = ConfigValidator(test_settings)

    # Mock a forbidden value
    registry.load_records() # need to init first
    # Just force set a mocked record
    rec = ConfigValueRecord(key="BROKER_ENABLED", value=True, value_redacted=True, source="TEST", module=ConfigModule.CORE, value_type=ConfigValueType.BOOLEAN, safety_level=ConfigSafetyLevel.FORBIDDEN, is_default=False, is_secret=False, valid=True)
    records = [rec]

    res = validator.validate_all(records)
    assert res.blocked_count > 0
    assert res.status.name == "FAIL"

def test_snapshot_creation(test_settings):
    builder = ConfigSchemaBuilder()
    registry = ConfigRegistry(schema_builder=builder, settings=test_settings)
    flags = FeatureFlagManager()
    manager = ConfigSnapshotManager(registry=registry, flag_manager=flags, store=None)

    snapshot = manager.create_snapshot(save=False)
    assert snapshot.redacted is True
    assert snapshot.checksum_sha256 is not None

    # Ensure raw secret is not in snapshot
    for r in snapshot.records:
        if r.key == "TELEGRAM_BOT_TOKEN":
            assert r.value == r.value_redacted

def test_diff_engine(test_settings):
    builder = ConfigSchemaBuilder()
    registry = ConfigRegistry(schema_builder=builder, settings=test_settings)
    flags = FeatureFlagManager()
    manager = ConfigSnapshotManager(registry=registry, flag_manager=flags, store=None)

    s1 = manager.create_snapshot(save=False)
    registry._records["RESEARCH_LAB_MAX_JOBS"] = ConfigValueRecord(key="RESEARCH_LAB_MAX_JOBS", value=5, value_redacted=5, source="TEST", module=ConfigModule.CORE, value_type=ConfigValueType.INTEGER, safety_level=ConfigSafetyLevel.CAUTION, is_default=False, is_secret=False, valid=True)
    s2 = manager.create_snapshot(save=False)

    engine = ConfigDiffEngine(schema_builder=builder, store=None)
    diff = engine.diff_snapshots(s1, s2)

    assert diff.changed_count >= 1

def test_drift_detector(test_settings):
    builder = ConfigSchemaBuilder()
    registry = ConfigRegistry(schema_builder=builder, settings=test_settings)
    flags = FeatureFlagManager()
    manager = ConfigSnapshotManager(registry=registry, flag_manager=flags, store=None)

    s1 = manager.create_snapshot(save=False)
    flags.set_flag("ENABLE_TELEGRAM_CENTER", FeatureFlagState.ENABLED, confirm=True)
    s2 = manager.create_snapshot(save=False)

    engine = ConfigDiffEngine(schema_builder=builder, store=None)
    detector = ConfigDriftDetector(diff_engine=engine, store=None)

    drift = detector.detect_drift(s2, s1)
    assert "ENABLE_TELEGRAM_CENTER" in drift.unexpected_enabled_flags

def test_config_gate(test_settings):
    builder = ConfigSchemaBuilder()
    registry = ConfigRegistry(schema_builder=builder, settings=test_settings)
    validator = ConfigValidator(test_settings)
    gate = ConfigGate(registry=registry, validator=validator, store=None)

    res = gate.runtime_gate(profile_type=RuntimeProfileType.RESEARCH_ONLY)
    assert res.blocked is False
    assert res.status.name in ["PASS", "WARN"]

    # Introduce forbidden setting
    registry._records["REAL_ORDER_ENABLED"] = ConfigValueRecord(key="REAL_ORDER_ENABLED", value=True, value_redacted=True, source="TEST", module=ConfigModule.CORE, value_type=ConfigValueType.BOOLEAN, safety_level=ConfigSafetyLevel.FORBIDDEN, is_default=False, is_secret=False, valid=True)

    res2 = gate.runtime_gate()
    assert res2.blocked is True
