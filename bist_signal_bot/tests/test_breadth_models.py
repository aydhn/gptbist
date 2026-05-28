import pytest
from datetime import datetime
from bist_signal_bot.breadth.models import (
    BreadthUniverseSnapshot, BreadthScope, BreadthInputRow
)

def test_breadth_universe_snapshot_normalizes_symbols():
    snapshot = BreadthUniverseSnapshot(
        universe_id="123",
        name="TEST",
        as_of=datetime.now(),
        scope=BreadthScope.MARKET,
        symbols=["asels", "Thyao"],
        sectors={},
        active_count=2
    )
    assert snapshot.symbols == ["ASELS", "THYAO"]

def test_breadth_universe_snapshot_negative_active_count():
    snapshot = BreadthUniverseSnapshot(
        universe_id="123",
        name="TEST",
        as_of=datetime.now(),
        scope=BreadthScope.MARKET,
        symbols=[],
        sectors={},
        active_count=-5
    )
    assert snapshot.active_count == 0
    assert "Empty universe" in snapshot.warnings

def test_breadth_input_row_negative_close():
    row = BreadthInputRow(
        row_id="123",
        symbol="asels",
        as_of=datetime.now(),
        close=-10.0,
        volume=-100.0
    )
    assert row.symbol == "ASELS"
    assert "Negative close price for ASELS" in row.warnings
    assert "Negative volume for ASELS" in row.warnings
