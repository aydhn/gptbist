import pandas as pd
from datetime import datetime
from bist_signal_bot.breadth.relative_strength import RelativeStrengthCalculator

def test_relative_strength_calculator():
    calc = RelativeStrengthCalculator()

    dates = pd.date_range("2024-01-01", periods=250)
    df1 = pd.DataFrame({"date": dates, "close": range(1, 251)})

    # 20 periods ago close was 230, now 250 -> (250-230)/230 = 20/230 ~ 8.7%
    ret = calc.relative_return(df1, None, 20, datetime(2024, 9, 6)) # 250th day is 2024-09-06
    assert ret is not None
    assert ret > 0

    scores = calc.calculate_scores({"SYM1": df1}, None, None, datetime(2024, 9, 6))
    assert len(scores) == 1
    assert scores[0].rs_20 is not None
