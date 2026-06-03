import pytest
from bist_signal_bot.notifications.formatter import (
    format_plugin_manifest, format_plugin_validation, format_plugin_governance
)
from bist_signal_bot.plugins.models import PluginManifest, PluginKind, PluginValidationResult, PluginStatus, PluginGovernanceAssessment
from datetime import datetime

def test_notification_formatter():
    m = PluginManifest(plugin_id="p1", name="p", version="1", kind=PluginKind.STRATEGY, description="d")
    out = format_plugin_manifest(m)
    assert "Yatırım tavsiyesi değildir." in out

    v = PluginValidationResult(
        validation_id="v1", plugin_id="p1", created_at=datetime.now(),
        status=PluginStatus.VALIDATED, manifest_valid=True, contract_valid=True,
        capabilities_valid=True, hooks_valid=True, sandbox_valid=True
    )
    out_v = format_plugin_validation(v)
    assert "Yatırım tavsiyesi değildir." in out_v

    g = PluginGovernanceAssessment(
        governance_id="g1", plugin_id="p1", created_at=datetime.now(),
        status=PluginStatus.VALIDATED, manifest_status=PluginStatus.VALIDATED,
        capability_status=PluginStatus.VALIDATED, validation_status=PluginStatus.VALIDATED
    )
    out_g = format_plugin_governance(g)
    assert "Yatırım tavsiyesi değildir." in out_g
