from bist_signal_bot.monitoring.decay import PerformanceDecayDetector
from bist_signal_bot.monitoring.models import MonitoringMetric, MonitoringObjectType, MonitoringWindow, MonitoringStatus
from datetime import datetime

def test_decay_detector_no_baseline():
    det = PerformanceDecayDetector()
    metric = MonitoringMetric(
        metric_id="1", object_type=MonitoringObjectType.STRATEGY, object_id="S1",
        metric_name="win_rate", window=MonitoringWindow.SHORT,
        value=0.5, status=MonitoringStatus.PASS, as_of=datetime.now()
    )
    res = det.detect_metric_decay(metric)
    assert res is None

def test_decay_detector_finds_decay():
    det = PerformanceDecayDetector()
    metric = MonitoringMetric(
        metric_id="1", object_type=MonitoringObjectType.STRATEGY, object_id="S1",
        metric_name="win_rate", window=MonitoringWindow.SHORT,
        value=0.4, baseline_value=0.6, sample_count=50,
        status=MonitoringStatus.PASS, as_of=datetime.now()
    )
    res = det.detect_metric_decay(metric)
    assert res is not None
    assert res.status == MonitoringStatus.DEGRADED
