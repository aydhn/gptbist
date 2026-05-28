import pytest
from datetime import datetime
from bist_signal_bot.breadth.models import BreadthInputRow, BreadthScope
from bist_signal_bot.breadth.participation import ParticipationAnalyzer
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def analyzer():
    settings = Settings()
    settings.BREADTH_MIN_UNIVERSE_SIZE = 2
    return ParticipationAnalyzer(settings=settings)

def test_participation_analyzer_basic(analyzer):
    inputs = [
        BreadthInputRow(row_id="1", symbol="A", as_of=datetime.now(), close=110, ma_20=100, ma_50=90, ma_200=80, return_1d_pct=2.0),
        BreadthInputRow(row_id="2", symbol="B", as_of=datetime.now(), close=95, ma_20=100, ma_50=90, ma_200=80, return_1d_pct=-1.0),
        BreadthInputRow(row_id="3", symbol="C", as_of=datetime.now(), close=85, ma_20=100, ma_50=90, ma_200=100, return_1d_pct=-2.0),
        BreadthInputRow(row_id="4", symbol="D", as_of=datetime.now(), close=105, ma_20=100, ma_50=100, ma_200=100, return_1d_pct=1.5),
    ]
    summary = analyzer.analyze(inputs, BreadthScope.MARKET, "TEST")

    assert summary.above_ma_20_pct == 50.0  # A, D > 20MA
    assert summary.above_ma_50_pct == 75.0  # A, B, D > 50MA
    assert summary.above_ma_200_pct == 75.0 # A, B, D > 200MA
    assert summary.positive_return_pct == 50.0 # A, D positive return
    assert summary.breadth_thrust_score == 50.0 # A, D return > 1.0%

def test_participation_analyzer_missing_ma(analyzer):
    inputs = [
        BreadthInputRow(row_id="1", symbol="A", as_of=datetime.now(), close=110)
    ]
    summary = analyzer.analyze(inputs, BreadthScope.MARKET, "TEST")
    assert summary.above_ma_20_pct is None
    assert "No moving average data available" in summary.warnings[0]
