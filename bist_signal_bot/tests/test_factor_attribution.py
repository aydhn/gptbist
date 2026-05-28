
from bist_signal_bot.factors.attribution import FactorAttributionEngine
from bist_signal_bot.factors.exposure import FactorExposureEngine
def test_attribution():
    a = FactorAttributionEngine()
    e = FactorExposureEngine().exposure_for_symbol("ASELS")
    res = a.attribute_portfolio_return({}, e)
    assert len(res) == 1
    assert "Momentum" in res[0].message
