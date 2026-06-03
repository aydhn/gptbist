import pytest
from bist_signal_bot.release_policy.freeze import ReleaseBranchFreezeManager, FinalPostReleaseClosureBuilder
from bist_signal_bot.release_policy.governance import ReleasePolicyGovernanceEngine
from bist_signal_bot.release_policy.models import ReleasePolicyStatus

def test_freeze_manager():
    manager = ReleaseBranchFreezeManager()
    manifest = manager.create_freeze("release/v1.0.0", "1.0.0", confirm=False)
    assert manifest.frozen is False
    assert "without confirm" in manifest.warnings[0]

    manifest2 = manager.create_freeze("release/v1.0.0", "1.0.0", confirm=True)
    assert manifest2.frozen is True

def test_closure_builder():
    builder = FinalPostReleaseClosureBuilder()
    manifest = builder.build_closure_manifest(confirm=True)
    assert manifest.no_real_order_sent is True
    assert "config" in manifest.modules_closed
    assert len(manifest.accepted_limitations) > 0

def test_governance_engine():
    engine = ReleasePolicyGovernanceEngine()
    findings = engine.unsafe_language_findings("trade ready and al/sat")
    assert len(findings) == 2

    status = engine.status_from_parts([ReleasePolicyStatus.PASS, ReleasePolicyStatus.BLOCKED], [])
    assert status == ReleasePolicyStatus.BLOCKED
