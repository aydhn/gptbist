import pytest
from datetime import datetime
from bist_signal_bot.breadth.models import BreadthInputRow, BreadthScope, BreadthStatus
from bist_signal_bot.breadth.advance_decline import AdvanceDeclineCalculator
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def calc():
    settings = Settings()
    settings.BREADTH_MIN_UNIVERSE_SIZE = 2
    return AdvanceDeclineCalculator(settings=settings)

def test_advance_decline_basic(calc):
    inputs = [
        BreadthInputRow(row_id="1", symbol="A", as_of=datetime.now(), close=110, previous_close=100),
        BreadthInputRow(row_id="2", symbol="B", as_of=datetime.now(), close=90, previous_close=100),
        BreadthInputRow(row_id="3", symbol="C", as_of=datetime.now(), close=100, previous_close=100),
        BreadthInputRow(row_id="4", symbol="D", as_of=datetime.now(), close=105, previous_close=100),
    ]
    summary = calc.calculate(inputs, BreadthScope.MARKET, "TEST")

    assert summary.advances == 2
    assert summary.declines == 1
    assert summary.unchanged == 1
    assert summary.net_advances == 1
    assert summary.advance_decline_ratio == 2.0
    assert summary.advance_percent == 50.0
    assert summary.status == BreadthStatus.STRONG

def test_advance_decline_zero_declines(calc):
    inputs = [
        BreadthInputRow(row_id="1", symbol="A", as_of=datetime.now(), close=110, previous_close=100),
        BreadthInputRow(row_id="2", symbol="B", as_of=datetime.now(), close=105, previous_close=100),
    ]
    summary = calc.calculate(inputs, BreadthScope.MARKET, "TEST")

    assert summary.advances == 2
    assert summary.declines == 0
    assert summary.advance_decline_ratio == 2.0

def test_advance_decline_insufficient_data():
    settings = Settings()
    settings.BREADTH_MIN_UNIVERSE_SIZE = 10
    calc = AdvanceDeclineCalculator(settings=settings)
    inputs = [
        BreadthInputRow(row_id="1", symbol="A", as_of=datetime.now(), close=110, previous_close=100),
    ]
    summary = calc.calculate(inputs, BreadthScope.MARKET, "TEST")

    assert summary.status == BreadthStatus.INSUFFICIENT_DATA
