import pytest
import math
from datetime import datetime
from bist_signal_bot.monitoring.models import (
    MonitoringMetric, MonitoringSnapshot, MonitoringStatus, MonitoringObjectType, MonitoringWindow,
    PerformanceDecayFinding, DecayType, ChampionChallengerComparison, ChampionChallengerDecision,
    MonitoringAlert, MonitoringAlertType
)
from bist_signal_bot.monitoring.metrics import MonitoringMetricCalculator
from bist_signal_bot.monitoring.decay import PerformanceDecayDetector
from bist_signal_bot.monitoring.champion_challenger import ChampionChallengerEngine
from bist_signal_bot.monitoring.health import MonitoringHealthEngine
from bist_signal_bot.monitoring.alerts import MonitoringAlertRouter
from bist_signal_bot.monitoring.escalation import MonitoringEscalationEngine
from bist_signal_bot.monitoring.watchlist import MonitoringWatchlistManager
from bist_signal_bot.notifications.formatter import format_monitoring_summary

class MockOutcome:
    def __init__(self, ret):
        self.return_pct = ret

def test_monitoring_models_disclaimer():
    snap = MonitoringSnapshot(
        snapshot_id="1", object_type=MonitoringObjectType.STRATEGY, object_id="s1",
        as_of=datetime.now(), status=MonitoringStatus.PASS
    )
    assert "not investment advice" in snap.disclaimer

def test_metric_calculator_win_rate():
    calc = MonitoringMetricCalculator()
    outcomes = [MockOutcome(0.1), MockOutcome(-0.05), MockOutcome(0.02)]
    wr = calc.win_rate(outcomes)
    assert math.isclose(wr, 2/3)

def test_metric_calculator_expectancy():
    calc = MonitoringMetricCalculator()
    outcomes = [MockOutcome(0.1), MockOutcome(-0.05)]
    ex = calc.expectancy(outcomes)
    # (1/2 * 0.1) - (1/2 * 0.05) = 0.05 - 0.025 = 0.025
    assert math.isclose(ex, 0.025)

def test_metric_calculator_insufficient_data():
    calc = MonitoringMetricCalculator()
    status = calc.status_from_metric("win_rate", 0.5, 0.6, 10)
    assert status == MonitoringStatus.INSUFFICIENT_DATA

def test_performance_decay_detector_no_baseline():
    det = PerformanceDecayDetector()
    snap = MonitoringSnapshot(
        snapshot_id="1", object_type=MonitoringObjectType.STRATEGY, object_id="s1",
        as_of=datetime.now(), status=MonitoringStatus.PASS,
        metrics=[
            MonitoringMetric(
                metric_id="m1", object_type=MonitoringObjectType.STRATEGY, object_id="s1",
                metric_name="win_rate", window=MonitoringWindow.SHORT, value=0.5,
                as_of=datetime.now(), status=MonitoringStatus.PASS, sample_count=50
            )
        ]
    )
    findings = det.detect_decay(snap)
    assert findings[0].status == MonitoringStatus.INSUFFICIENT_DATA

def test_performance_decay_detector_decay():
    det = PerformanceDecayDetector()
    snap = MonitoringSnapshot(
        snapshot_id="1", object_type=MonitoringObjectType.STRATEGY, object_id="s1",
        as_of=datetime.now(), status=MonitoringStatus.PASS,
        metrics=[
            MonitoringMetric(
                metric_id="m1", object_type=MonitoringObjectType.STRATEGY, object_id="s1",
                metric_name="win_rate", window=MonitoringWindow.SHORT, value=0.4,
                baseline_value=0.6, as_of=datetime.now(), status=MonitoringStatus.PASS, sample_count=50
            )
        ]
    )
    findings = det.detect_decay(snap)
    assert findings[0].status == MonitoringStatus.DEGRADED
    assert findings[0].decay_type == DecayType.WIN_RATE_DECAY

def test_champion_challenger_low_sample():
    eng = ChampionChallengerEngine(min_sample=50)
    comp = eng.compare(MonitoringObjectType.STRATEGY, "c1", "c2")
    assert comp.decision == ChampionChallengerDecision.NEEDS_MORE_DATA
    assert len(comp.warnings) > 0

def test_health_engine():
    eng = MonitoringHealthEngine()
    score = eng.health_score([])
    assert score is None

    # Degraded decay drops score by 20
    decay = PerformanceDecayFinding(
        decay_id="d1", object_type=MonitoringObjectType.STRATEGY, object_id="s1",
        decay_type=DecayType.PERFORMANCE_DECAY, metric_name="wr", status=MonitoringStatus.DEGRADED, message="x"
    )
    score2 = eng.health_score([], [decay])
    assert score2 == 80.0

def test_alert_router():
    router = MonitoringAlertRouter()
    decay = PerformanceDecayFinding(
        decay_id="d1", object_type=MonitoringObjectType.STRATEGY, object_id="s1",
        decay_type=DecayType.WIN_RATE_DECAY, metric_name="wr", status=MonitoringStatus.DEGRADED, message="x"
    )
    alert = router.alert_from_decay(decay)
    assert alert.severity == "HIGH"

def test_escalation():
    eng = MonitoringEscalationEngine()
    alert = MonitoringAlert(
        alert_id="a1", alert_type=MonitoringAlertType.STRATEGY_DEGRADED,
        object_type=MonitoringObjectType.STRATEGY, object_id="s1",
        severity="CRITICAL", status=MonitoringStatus.DEGRADED,
        created_at=datetime.now(), title="t", message="m"
    )
    escalated = eng.escalate_if_needed([alert], save=True)
    assert len(escalated) == 1
    assert escalated[0].review_case_id is not None

def test_watchlist():
    wm = MonitoringWatchlistManager()
    snap = MonitoringSnapshot(
        snapshot_id="1", object_type=MonitoringObjectType.STRATEGY, object_id="s1",
        as_of=datetime.now(), status=MonitoringStatus.DEGRADED
    )
    item = wm.update_from_snapshot(snap)
    assert item is not None
    assert item.status == MonitoringStatus.WATCH

def test_notification_formatter():
    text = format_monitoring_summary("s1", "WATCH", 62.0, 1, 1, True)
    assert "Yatırım tavsiyesi değildir" in text
    assert "WATCH" in text
    assert "62.0" in text
