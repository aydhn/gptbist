import pandas as pd
from datetime import datetime
from bist_signal_bot.breadth.calculator import BreadthCalculator
from bist_signal_bot.breadth.models import BreadthAnalysisRequest

def test_breadth_calculator():
    calc = BreadthCalculator()

    dates = pd.date_range("2024-01-01", periods=250)
    df1 = pd.DataFrame({"date": dates, "close": range(1, 251), "volume": 100})
    df2 = pd.DataFrame({"date": dates, "close": range(250, 0, -1), "volume": 50})

    data = {"SYM1": df1, "SYM2": df2}

    adv_dec = calc.calculate_advance_decline(data, datetime(2024, 8, 1))
    assert adv_dec["advance"] == 1
    assert adv_dec["decline"] == 1

    pct20 = calc.percent_above_ma(data, 20, datetime(2024, 8, 1))
    assert pct20 == 50.0  # sym1 above, sym2 below

    h, l = calc.new_high_low_counts(data, 20, datetime(2024, 8, 1))
    assert h == 1 # sym1 new high
    assert l == 1 # sym2 new low

    vb = calc.volume_breadth(data, datetime(2024, 8, 1))
    assert vb is not None

    mb = calc.momentum_breadth(data, 20, datetime(2024, 8, 1))
    assert mb == 50.0
