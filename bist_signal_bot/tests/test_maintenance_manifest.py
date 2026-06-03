import pytest
from bist_signal_bot.maintenance_automation.models import MaintenanceRunManifest
from bist_signal_bot.maintenance_automation.manifest import MaintenanceManifestBuilder
from datetime import datetime, timezone

def test_manifest_no_real_order_true():
    manifest = MaintenanceRunManifest(
        manifest_id="1",
        run_id="2",
        plan_id="3",
        created_at=datetime.now(timezone.utc),
        action_result_ids=[],
        no_real_order_sent=True
    )
    builder = MaintenanceManifestBuilder()
    errors = builder.validate_manifest(manifest)
    assert not any("no real order" in e.lower() for e in errors)
