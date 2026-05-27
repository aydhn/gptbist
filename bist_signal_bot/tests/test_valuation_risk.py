from bist_signal_bot.valuation.risk import ValuationRiskEngine
from bist_signal_bot.valuation.models import ValuationRiskLevel

def test_risk_level_assignment():
    engine = ValuationRiskEngine()

    assert engine.risk_level(80.0, ["PE is historically EXTREME_EXPENSIVE"]) == ValuationRiskLevel.EXTREME
    assert engine.risk_level(80.0, []) == ValuationRiskLevel.HIGH

    assert engine.risk_level(20.0, [], {"score": 80}) == ValuationRiskLevel.LOW
    assert engine.risk_level(20.0, [], {"score": 30}) == ValuationRiskLevel.HIGH # Value trap

    assert engine.risk_level(50.0, []) == ValuationRiskLevel.MEDIUM
