
from bist_signal_bot.factors.inputs import FactorInputBuilder
def test_factor_input_builder():
    b = FactorInputBuilder()
    snap = b.build_input("GARAN")
    assert snap.symbol == "GARAN"
    assert snap.price_return_20d_pct is not None
