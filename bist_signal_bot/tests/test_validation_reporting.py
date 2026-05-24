import pytest
from bist_signal_bot.validation.reporting import format_validation_report_markdown, walk_forward_to_dict
from bist_signal_bot.validation.models import StrategyValidationResult, StrategyValidationRequest, WalkForwardResult, ValidationStatus

def test_format_validation_report_markdown():
    req = StrategyValidationRequest(strategy_name="MA", symbols=["ASELS"])
    res = StrategyValidationResult(validation_id="123", request=req, status=ValidationStatus.PASS, aggregate_score=85.0)
    md = format_validation_report_markdown(res)
    assert "Strategy Validation Report: MA" in md
    assert "PASS" in md
    assert "85.0" in md

def test_walk_forward_to_dict():
    res = WalkForwardResult(walk_forward_id="1", strategy_name="MA")
    d = walk_forward_to_dict(res)
    assert d["walk_forward_id"] == "1"
    assert d["strategy_name"] == "MA"
