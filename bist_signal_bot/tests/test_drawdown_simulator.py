import pytest
from bist_signal_bot.stress.drawdown import DrawdownSimulator
from bist_signal_bot.stress.models import ReturnSeries, StressInputType

def test_drawdown_simulation():
    series = ReturnSeries(
        series_id="test",
        source_type=StressInputType.CUSTOM_RETURNS,
        returns=[0.10, -0.20, 0.10],
        frequency="1D"
    )
    sim = DrawdownSimulator()
    res = sim.analyze(series, initial_value=100.0)

    assert round(res.max_drawdown_pct, 2) == -20.0
    assert res.longest_drawdown_days == 2
