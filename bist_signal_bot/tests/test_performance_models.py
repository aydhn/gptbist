import pytest
from datetime import datetime, UTC
import uuid

from bist_signal_bot.performance.models import (
    PerformanceStatus,
    ResourceKind,
    TimingMeasurement,
    ResourceMeasurement,
)

def test_timing_measurement_validation():
    t = TimingMeasurement(
        timing_id="test-1",
        name="test-timing",
        started_at=datetime.now(UTC),
        status=PerformanceStatus.PASS
    )
    assert t.status == PerformanceStatus.PASS
    assert t.elapsed_seconds is None

def test_resource_measurement_validation():
    r = ResourceMeasurement(
        measurement_id="res-1",
        resource_kind=ResourceKind.CPU,
        module_name="test_mod",
        value=42.0,
        unit="pct",
        status=PerformanceStatus.PASS,
        measured_at=datetime.now(UTC)
    )
    assert r.value == 42.0
    assert r.unit == "pct"

