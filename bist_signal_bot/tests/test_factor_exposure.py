
from bist_signal_bot.factors.exposure import FactorExposureEngine
def test_exposure():
    e = FactorExposureEngine()
    exp = e.exposure_for_symbol("ASELS")
    assert exp.symbol == "ASELS"
    assert exp.aggregate_factor_score is not None
