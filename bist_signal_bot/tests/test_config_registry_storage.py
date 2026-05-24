import pytest
from unittest.mock import MagicMock
from datetime import datetime, UTC
import uuid

from bist_signal_bot.config_registry.models import (
    ConfigSnapshot, ConfigValueRecord, FeatureFlag,
    ConfigModule, ConfigSafetyLevel, ConfigValueType, FeatureFlagState
)
from bist_signal_bot.config_registry.storage import ConfigRegistryStore

def test_config_registry_storage_snapshot_save_load(tmp_path):
    store = ConfigRegistryStore(settings=MagicMock(), base_dir=tmp_path)

    rec = ConfigValueRecord(
        key="TEST_KEY",
        value="test_val",
        value_redacted="test_val",
        source="TEST",
        module=ConfigModule.CORE,
        value_type=ConfigValueType.STRING,
        safety_level=ConfigSafetyLevel.SAFE,
        is_default=True,
        is_secret=False,
        valid=True
    )
    flag = FeatureFlag(
        flag_id="f1",
        key="TEST_FLAG",
        module=ConfigModule.CORE,
        state=FeatureFlagState.ENABLED,
        default_state=FeatureFlagState.ENABLED,
        safety_level=ConfigSafetyLevel.SAFE,
        description="Test flag"
    )

    snap = ConfigSnapshot(
        snapshot_id=str(uuid.uuid4()),
        created_at=datetime.now(UTC),
        records=[rec],
        flags=[flag],
        redacted=True,
        checksum_sha256="test_checksum"
    )

    store.save_snapshot(snap)

    loaded = store.load_snapshot(snap.snapshot_id)
    assert loaded is not None
    assert loaded.snapshot_id == snap.snapshot_id
    assert len(loaded.records) == 1
    assert loaded.records[0].key == "TEST_KEY"
    assert loaded.records[0].module == ConfigModule.CORE
    assert len(loaded.flags) == 1
    assert loaded.flags[0].state == FeatureFlagState.ENABLED

def test_config_registry_storage_latest_snapshot(tmp_path):
    store = ConfigRegistryStore(settings=MagicMock(), base_dir=tmp_path)

    snap1 = ConfigSnapshot(
        snapshot_id="1",
        created_at=datetime(2023, 1, 1, tzinfo=UTC),
        records=[],
        flags=[],
        redacted=True
    )

    snap2 = ConfigSnapshot(
        snapshot_id="2",
        created_at=datetime(2023, 2, 1, tzinfo=UTC),
        records=[],
        flags=[],
        redacted=True
    )

    store.save_snapshot(snap1)
    store.save_snapshot(snap2)

    latest = store.load_latest_snapshot()
    assert latest is not None
    assert latest.snapshot_id == "2"
