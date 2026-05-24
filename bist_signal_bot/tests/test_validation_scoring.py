import pytest
from bist_signal_bot.validation.scoring import StrategyValidationScorer
from bist_signal_bot.validation.models import WalkForwardResult, ValidationStatus

def test_score_walk_forward():
    scorer = StrategyValidationScorer()
    res = WalkForwardResult(walk_forward_id="1", strategy_name="MA", status=ValidationStatus.PASS)
    assert scorer.score_walk_forward(res) == 80.0
    res.status = ValidationStatus.FAIL
    assert scorer.score_walk_forward(res) == 20.0

def test_derive_status():
    scorer = StrategyValidationScorer()
    status, sev = scorer.derive_status(85.0, [])
    assert status.value == "PASS"
    assert sev.value == "LOW"

    status, sev = scorer.derive_status(30.0, [])
    assert status.value == "FAIL"
    assert sev.value == "CRITICAL"
