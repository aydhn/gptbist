from datetime import datetime
import pytest

from bist_signal_bot.release.models import (
    ReleaseReadinessConfig, ReleaseStage, ReleaseProfile, ReleaseReadinessReport, ReleaseStatus,
    ReleaseCandidateManifest, ReleaseNotes, ReleaseCheckResult, ReleaseCheckCategory, ReleaseCheckStatus, ReleaseBlockerSeverity
)

def test_release_readiness_config_validation():
    with pytest.raises(ValueError, match="version cannot be empty"):
        ReleaseReadinessConfig(stage=ReleaseStage.RELEASE_CANDIDATE, profile=ReleaseProfile.FULL_SAFE_LOCAL, version="")

    cfg = ReleaseReadinessConfig(stage=ReleaseStage.RELEASE_CANDIDATE, profile=ReleaseProfile.FULL_SAFE_LOCAL, version="0.1.0")
    assert cfg.version == "0.1.0"
    assert cfg.run_healthcheck is True

def test_release_check_result_summary():
    res = ReleaseCheckResult("c1", "Check 1", ReleaseCheckCategory.IMPORTS, ReleaseCheckStatus.PASS, ReleaseBlockerSeverity.LOW, "Passed")
    s = res.summary()
    assert s["check_id"] == "c1"
    assert s["status"] == "PASS"

def test_release_readiness_report_passed():
    cfg = ReleaseReadinessConfig(stage=ReleaseStage.RELEASE_CANDIDATE, profile=ReleaseProfile.FULL_SAFE_LOCAL, version="0.1.0")
    rep = ReleaseReadinessReport(readiness_id="r1", config=cfg, status=ReleaseStatus.READY, readiness_score=95.0)
    assert rep.passed() is True

    rep.status = ReleaseStatus.BLOCKED
    assert rep.passed() is False

def test_release_candidate_manifest_no_real_order():
    m = ReleaseCandidateManifest(candidate_id="c1", version="0.1.0", stage=ReleaseStage.RELEASE_CANDIDATE)
    assert m.no_real_order_sent is True

def test_release_notes():
    n = ReleaseNotes(version="0.1.0", stage=ReleaseStage.RELEASE_CANDIDATE, title="Test", summary="Sum")
    assert n.version == "0.1.0"
    assert "Not investment advice" in n.disclaimer
