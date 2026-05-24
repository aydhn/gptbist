import pytest
from bist_signal_bot.instruments.master import InstrumentMaster
from bist_signal_bot.instruments.universe import InstrumentUniverseBuilder
from bist_signal_bot.instruments.models import InstrumentRecord, InstrumentStatus, InstrumentType

def test_universe_builder_active_equity():
    master = InstrumentMaster()
    master.upsert_instrument(InstrumentRecord(symbol="A", name="A", instrument_type=InstrumentType.EQUITY, status=InstrumentStatus.ACTIVE))
    master.upsert_instrument(InstrumentRecord(symbol="B", name="B", instrument_type=InstrumentType.EQUITY, status=InstrumentStatus.DELISTED))

    builder = InstrumentUniverseBuilder(master)
    u = builder.default_bist_equity_universe()
    assert "A" in u.symbols
    assert "B" not in u.symbols
