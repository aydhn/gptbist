import pytest
from bist_signal_bot.drift.strategy_decay import StrategyDecayAnalyzer
from bist_signal_bot.drift.models import DriftStatus, DriftSeverity
from bist_signal_bot.config.settings import Settings

def test_strategy_decay_insufficient():
    sda = StrategyDecayAnalyzer(Settings())
    res = sda.analyze("s1", [], [])
    assert res.status == DriftStatus.INSUFFICIENT_DATA

def test_strategy_decay_drop():
    s = Settings()
    s.DRIFT_STRATEGY_DECAY_SCORE_FAIL = 70.0
    sda = StrategyDecayAnalyzer(s)

    ref = [{"profit_factor": 2.0, "max_drawdown": 10.0}]
    cur = [{"profit_factor": 0.5, "max_drawdown": 40.0}] # -75% PF, +30 DD
    # PF Drop (-75%) -> score += 30
    # DD inc (+30) -> score += 40
    # total score ~ 70
    res = sda.analyze("s1", ref, cur)
    assert res.status == DriftStatus.DRIFTING
    assert res.severity == DriftSeverity.HIGH
