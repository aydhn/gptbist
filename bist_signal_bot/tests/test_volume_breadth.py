import pytest
from datetime import datetime
from bist_signal_bot.breadth.models import BreadthInputRow, BreadthScope
from bist_signal_bot.breadth.volume_breadth import VolumeBreadthAnalyzer

def test_volume_breadth_analyzer_basic():
    analyzer = VolumeBreadthAnalyzer()
    inputs = [
        BreadthInputRow(row_id="1", symbol="A", as_of=datetime.now(), close=110, previous_close=100, volume=1000),
        BreadthInputRow(row_id="2", symbol="B", as_of=datetime.now(), close=90, previous_close=100, volume=500),
        BreadthInputRow(row_id="3", symbol="C", as_of=datetime.now(), close=100, previous_close=100, volume=200),
    ]
    summary = analyzer.analyze(inputs, BreadthScope.MARKET, "TEST")

    assert summary.up_volume == 1000
    assert summary.down_volume == 500
    assert summary.unchanged_volume == 200
    # ratio of up vs down: up = 1000 / 1500
    assert summary.up_volume_ratio == round((1000/1500)*100, 2)
    assert summary.down_volume_ratio == round((500/1500)*100, 2)
