import pytest
from datetime import datetime
from bist_signal_bot.instruments.models import InstrumentRecord, InstrumentStatus, InstrumentType
from bist_signal_bot.instruments.master import InstrumentMaster
from bist_signal_bot.core.exceptions import *

def test_instrument_record_validation():
    # Should normalize symbol
    rec = InstrumentRecord(symbol=" asels ", name="Aselsan", instrument_type=InstrumentType.EQUITY, status=InstrumentStatus.ACTIVE)
    assert rec.symbol == "ASELS"
    assert rec.currency == "TRY"

def test_instrument_record_delisted_warning():
    rec = InstrumentRecord(symbol="YAZIC", name="Yazicilar", instrument_type=InstrumentType.EQUITY, status=InstrumentStatus.DELISTED)
    assert any("DELISTED" in w for w in rec.warnings)

def test_instrument_master_upsert_get():
    master = InstrumentMaster()
    rec = InstrumentRecord(symbol="ASELS", name="Aselsan", instrument_type=InstrumentType.EQUITY, status=InstrumentStatus.ACTIVE)
    master.upsert_instrument(rec)
    assert master.get("ASELS") is not None
    assert master.get("ASELS").name == "Aselsan"

def test_instrument_master_alias_resolve():
    master = InstrumentMaster()
    rec = InstrumentRecord(symbol="TUPRS", name="Tupras", aliases=["TUPRAS"], instrument_type=InstrumentType.EQUITY, status=InstrumentStatus.ACTIVE)
    master.upsert_instrument(rec)
    assert master.resolve_symbol("TUPRAS") == "TUPRS"
