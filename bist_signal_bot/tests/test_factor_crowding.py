
from bist_signal_bot.factors.crowding import FactorCrowdingAnalyzer
from bist_signal_bot.factors.exposure import FactorExposureEngine
def test_crowding():
    c = FactorCrowdingAnalyzer()
    e = FactorExposureEngine()
    exp = e.exposure_for_symbol("ASELS")
    # inject high concentration
    exp.factor_concentration_score = 85.0
    res = c.assess_crowding(exp)
    assert res.crowding_risk_level == "HIGH"
    assert any("High concentration warning" in w for w in res.warnings)
