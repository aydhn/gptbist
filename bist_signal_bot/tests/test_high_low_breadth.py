import pytest
from datetime import datetime
from bist_signal_bot.breadth.models import BreadthInputRow, BreadthScope
from bist_signal_bot.breadth.high_low import HighLowBreadthAnalyzer

def test_high_low_analyzer_basic():
    analyzer = HighLowBreadthAnalyzer()
    inputs = [
        BreadthInputRow(row_id="1", symbol="A", as_of=datetime.now(), close=110, high_20d=110, low_20d=100, high_252d=110, low_252d=50),
        BreadthInputRow(row_id="2", symbol="B", as_of=datetime.now(), close=90, high_20d=100, low_20d=90, high_252d=120, low_252d=90),
        BreadthInputRow(row_id="3", symbol="C", as_of=datetime.now(), close=100, high_20d=110, low_20d=90, high_252d=110, low_252d=80),
    ]
    summary = analyzer.analyze(inputs, BreadthScope.MARKET, "TEST")

    assert summary.new_high_20d_count == 1 # A
    assert summary.new_low_20d_count == 1  # B
    assert summary.new_high_52w_count == 1 # A
    assert summary.new_low_52w_count == 1  # B
    assert summary.high_low_spread == 0
