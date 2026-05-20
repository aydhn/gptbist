import pytest
import pandas as pd
from bist_signal_bot.stress.returns import ReturnSeriesBuilder
from bist_signal_bot.stress.models import StressInputType

def test_return_series_from_price_data():
    df = pd.DataFrame({"Close": [100.0, 101.0, 102.0, float('nan'), 104.0]})
    rs = ReturnSeriesBuilder.from_price_data("TEST", df)
    assert rs.source_type == StressInputType.CUSTOM_RETURNS
    assert len(rs.returns) > 0
    assert len(rs.warnings) > 0 # Less than 30 points

def test_return_series_from_portfolio_snapshot():
    class DummyItem:
        def __init__(self, sym, w):
            self.symbol = sym
            self.weight_pct = w

    class DummySnapshot:
        def __init__(self):
            self.items = [DummyItem("A", 60.0), DummyItem("B", 40.0)]

    df_A = pd.DataFrame({"Close": [100.0, 101.0, 102.0]})
    df_B = pd.DataFrame({"Close": [50.0, 49.0, 51.0]})

    data_by_sym = {"A": df_A, "B": df_B}
    rs = ReturnSeriesBuilder.from_portfolio_snapshot(DummySnapshot(), data_by_sym)

    assert len(rs.returns) == 2 # 3 prices -> 2 returns
    assert rs.source_type == StressInputType.PORTFOLIO_RESEARCH_SNAPSHOT
