with open("bist_signal_bot/tests/test_factor_library.py", "w") as f:
    f.write("""
from bist_signal_bot.factors.library import FactorLibrary
def test_factor_library():
    l = FactorLibrary()
    factors = l.supported_factors()
    assert len(factors) > 0
""")
