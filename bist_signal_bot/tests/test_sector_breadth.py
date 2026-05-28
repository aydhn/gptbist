import pytest
from datetime import datetime
from bist_signal_bot.breadth.models import BreadthInputRow
from bist_signal_bot.breadth.sector_breadth import SectorBreadthAnalyzer
from bist_signal_bot.config.settings import Settings

def test_sector_breadth_analyzer_basic():
    settings = Settings()
    settings.BREADTH_SECTOR_MIN_SYMBOLS = 2
    analyzer = SectorBreadthAnalyzer(settings=settings)

    inputs = [
        BreadthInputRow(row_id="1", symbol="A", as_of=datetime.now(), sector="TECH", close=110, previous_close=100, ma_50=100, return_1d_pct=10.0),
        BreadthInputRow(row_id="2", symbol="B", as_of=datetime.now(), sector="TECH", close=90, previous_close=100, ma_50=100, return_1d_pct=-10.0),
        BreadthInputRow(row_id="3", symbol="C", as_of=datetime.now(), sector="BANK", close=100, previous_close=100, ma_50=90, return_1d_pct=0.0),
    ]

    summaries = analyzer.analyze_by_sector(inputs)
    assert len(summaries) == 2

    tech = next(s for s in summaries if s.sector == "TECH")
    assert tech.symbols_count == 2
    assert tech.advance_percent == 50.0
    assert tech.above_ma_50_pct == 50.0
    assert "A" in tech.leading_symbols
    assert "B" in tech.lagging_symbols

    bank = next(s for s in summaries if s.sector == "BANK")
    assert bank.symbols_count == 1
    assert "Sector BANK has too few symbols" in bank.warnings[0]
