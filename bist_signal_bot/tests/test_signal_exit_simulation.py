import pandas as pd
from datetime import datetime, timezone, timedelta
from bist_signal_bot.signals.exit_simulation import ResearchExitSimulator
from bist_signal_bot.signals.models import TrackedSignal, ResearchExitRule, ResearchExitRuleType, SignalOutcomeState

def test_simulate_fixed_target():
    sim = ResearchExitSimulator()
    now = datetime.now(timezone.utc)
    signal = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now - timedelta(days=2), updated_at=now, direction="LONG")

    df = pd.DataFrame({
        'Close': [100.0, 105.0, 110.0]
    }, index=[now - timedelta(days=2), now - timedelta(days=1), now])

    rules = [ResearchExitRule(rule_id="r1", rule_type=ResearchExitRuleType.FIXED_PERCENT_TARGET, value=5.0)]

    result = sim.simulate(signal, df, rules)
    assert result.outcome_state == SignalOutcomeState.HIT_RESEARCH_TARGET
    assert result.simulated_return_pct == 10.0

def test_simulate_time_stop():
    sim = ResearchExitSimulator()
    now = datetime.now(timezone.utc)
    signal = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now - timedelta(days=5), updated_at=now, direction="LONG")

    df = pd.DataFrame({
        'Close': [100.0, 101.0]
    }, index=[now - timedelta(days=5), now])

    rules = [ResearchExitRule(rule_id="r1", rule_type=ResearchExitRuleType.TIME_STOP, value=3)]

    result = sim.simulate(signal, df, rules)
    assert result.outcome_state == SignalOutcomeState.TIME_EXPIRED
