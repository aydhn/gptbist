import pytest
from bist_signal_bot.data.providers_v2.health import ProviderHealthTracker
from bist_signal_bot.data.providers_v2.models import ProviderHealthSnapshot, ProviderType, ProviderStatus
from bist_signal_bot.config.settings import Settings

def test_health_tracker(tmp_path):
    settings = Settings(DATA_DIR=str(tmp_path))
    tracker = ProviderHealthTracker(settings)

    snap = ProviderHealthSnapshot(
        provider_type=ProviderType.LOCAL_FILE,
        provider_name="local",
        status=ProviderStatus.HEALTHY,
        success_count=10
    )

    tracker.record_snapshot(snap)
    recent = tracker.load_recent()
    assert len(recent) == 1
    assert recent[0].success_count == 10

    summary = tracker.summarize_health()
    assert ProviderType.LOCAL_FILE.value in summary
    assert summary[ProviderType.LOCAL_FILE.value]["score"] == 100.0
