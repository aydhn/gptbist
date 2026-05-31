from bist_signal_bot.monitoring.champion_challenger import ChampionChallengerEngine
from bist_signal_bot.monitoring.models import MonitoringMetric, MonitoringObjectType, MonitoringWindow, MonitoringStatus
from datetime import datetime

def test_cc_low_sample():
    eng = ChampionChallengerEngine()
    m1 = MonitoringMetric(
        metric_id="1", object_type=MonitoringObjectType.STRATEGY, object_id="S1",
        metric_name="win_rate", window=MonitoringWindow.SHORT,
        value=0.5, baseline_value=0.6, sample_count=10,
        status=MonitoringStatus.PASS, as_of=datetime.now()
    )
    dec = eng.decision_from_metrics([m1], [m1])
    assert dec == "NEEDS_MORE_DATA"

def test_cc_promote():
    eng = ChampionChallengerEngine()
    m1 = MonitoringMetric(
        metric_id="1", object_type=MonitoringObjectType.STRATEGY, object_id="S1",
        metric_name="win_rate", window=MonitoringWindow.SHORT,
        value=0.5, baseline_value=0.6, sample_count=50,
        status=MonitoringStatus.PASS, as_of=datetime.now()
    )
    m2 = MonitoringMetric(
        metric_id="2", object_type=MonitoringObjectType.STRATEGY, object_id="S2",
        metric_name="win_rate", window=MonitoringWindow.SHORT,
        value=0.7, baseline_value=0.6, sample_count=50,
        status=MonitoringStatus.PASS, as_of=datetime.now()
    )
    dec = eng.decision_from_metrics([m1], [m2])
    # The dummy logic sets score to 10.0, so PROMOTE_CHALLENGER_RESEARCH
    assert dec == "PROMOTE_CHALLENGER_RESEARCH"
