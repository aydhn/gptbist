import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.resources import ResourceSampler

def test_resource_sampler_snapshot():
    settings = Settings(PERFORMANCE_USE_GPU_SAMPLING=False)
    sampler = ResourceSampler(settings)
    snap = sampler.snapshot()
    assert snap.snapshot_id is not None
    assert snap.gpu_available is False

def test_resource_sampler_no_psutil():
    settings = Settings()
    sampler = ResourceSampler(settings)
    sampler._use_psutil = False

    assert sampler.cpu_percent() is None
    assert sampler.memory_rss_mb() is None

    snap = sampler.snapshot()
    assert len(snap.warnings) > 0
