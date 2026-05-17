import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.release.storage import ReleaseStore
from bist_signal_bot.release.models import ReleaseReadinessConfig, ReleaseStage, ReleaseProfile, ReleaseReadinessReport, ReleaseStatus

def test_release_store_save_readiness(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    store = ReleaseStore(s)

    cfg = ReleaseReadinessConfig(stage=ReleaseStage.RELEASE_CANDIDATE, profile=ReleaseProfile.FULL_SAFE_LOCAL, version="1")
    rep = ReleaseReadinessReport(readiness_id="r1", config=cfg, status=ReleaseStatus.READY, readiness_score=100)

    paths = store.save_readiness_report(rep)
    assert "json" in paths
    assert paths["json"].exists()
    assert "markdown" in paths
    assert paths["markdown"].exists()
