import pytest
from bist_signal_bot.performance.resources import ResourceMonitor
from bist_signal_bot.performance.models import ResourceLevel, ResourceSnapshot
from datetime import datetime, timezone

def test_resource_monitor_fallback():
    # Force psutil unavailable if we want to test fallback, or just snapshot
    monitor = ResourceMonitor()
    snap = monitor.snapshot()
    assert snap.timestamp is not None
    assert snap.cpu_count is not None
    assert snap.disk_percent is not None
    assert isinstance(snap.gpu_detected, bool)

def test_memory_classification():
    monitor = ResourceMonitor()
    snap = ResourceSnapshot(timestamp=datetime.now(timezone.utc), memory_percent=85.0)
    level = monitor.classify_memory_level(snap)
    assert level == ResourceLevel.HIGH

    snap.memory_percent = 95.0
    level = monitor.classify_memory_level(snap)
    assert level == ResourceLevel.CRITICAL

    snap.memory_percent = 40.0
    level = monitor.classify_memory_level(snap)
    assert level == ResourceLevel.LOW

def test_disk_classification():
    monitor = ResourceMonitor()
    snap = ResourceSnapshot(timestamp=datetime.now(timezone.utc), disk_percent=88.0)
    level = monitor.classify_disk_level(snap)
    assert level == ResourceLevel.HIGH
