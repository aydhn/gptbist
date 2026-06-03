import pytest
from bist_signal_bot.markets.registry import MarketRegistry
from bist_signal_bot.markets.instruments import InstrumentRegistry
from bist_signal_bot.markets.symbols import SymbolNormalizer
from bist_signal_bot.markets.calendar import MarketCalendarProvider
from bist_signal_bot.markets.sessions import MarketSessionProvider
from bist_signal_bot.markets.currencies import CurrencyRegistry
from bist_signal_bot.markets.asset_classes import AssetClassRegistry
from bist_signal_bot.markets.normalization import MarketDataNormalizer
from bist_signal_bot.markets.validation import MarketValidationEngine
from bist_signal_bot.markets.universe import MarketUniverseBuilder
from bist_signal_bot.markets.governance import MarketGovernanceEngine

def test_market_registry():
    r = MarketRegistry()
    assert len(r.list_markets()) >= 7
    m = r.get_market("BIST_EQUITY")
    assert m is not None
    assert m.default_currency == "TRY"

def test_instrument_registry():
    ir = InstrumentRegistry()
    bist_insts = ir.default_instruments("BIST_EQUITY")
    assert len(bist_insts) == 5
    assert any(i.symbol == "ASELS" for i in bist_insts)

    us_insts = ir.default_instruments("US_EQUITY_RESEARCH")
    assert len(us_insts) == 3

def test_symbol_normalizer():
    sn = SymbolNormalizer()
    assert sn.strip_exchange_suffix("ASELS.IS") == "ASELS"
    assert sn.detect_market("ASELS.IS") == "BIST_EQUITY"

    canon = sn.canonicalize("ASELS.IS")
    assert canon.canonical_symbol == "BIST:ASELS"
    assert canon.market_id == "BIST_EQUITY"

def test_calendar_provider():
    cp = MarketCalendarProvider()
    days = cp.default_calendar("BIST_EQUITY", "2024-01-01", "2024-01-07")
    assert len(days) == 7
    crypto_days = cp.default_calendar("CRYPTO_RESEARCH", "2024-01-01", "2024-01-01")
    assert "24/7 crypto research fixture" in crypto_days[0].warnings[0]

def test_currency_registry():
    cr = CurrencyRegistry()
    c = cr.get_currency("TRY")
    assert c is not None
    assert c.precision == 2

def test_asset_class_registry():
    ac = AssetClassRegistry()
    assert ac.asset_class_for_market("BIST_EQUITY") == "EQUITY"
    assert ac.asset_class_for_market("FX_RESEARCH") == "CURRENCY_PAIR"

def test_market_data_normalizer():
    sn = SymbolNormalizer()
    mdn = MarketDataNormalizer(sn)
    res = mdn.normalize_dataset([{"symbol": "ASELS.IS"}, {"val": 10}], "BIST_EQUITY")
    assert res.input_rows == 2
    assert res.output_rows == 1
    assert res.rejected_rows == 1

def test_validation_engine():
    sn = SymbolNormalizer()
    cr = CurrencyRegistry()
    ir = InstrumentRegistry()
    ve = MarketValidationEngine(sn, cr, ir)
    res = ve.validate_market_dataset([{"symbol": "ASELS", "currency": "INVALID"}], "BIST_EQUITY")
    assert "FAIL" in res.status or "WATCH" in res.status

def test_universe_builder():
    sn = SymbolNormalizer()
    ir = InstrumentRegistry()
    ub = MarketUniverseBuilder(ir, sn)
    uns = ub.default_universes()
    assert len(uns) == 6

def test_governance_engine():
    mr = MarketRegistry()
    ir = InstrumentRegistry()
    cp = MarketCalendarProvider()
    ge = MarketGovernanceEngine(mr, ir, cp)
    ass = ge.assess_market("BIST_EQUITY")
    assert ass.registry_complete is True

    findings = ge.unsafe_language_findings("this is trade ready and guaranteed")
    assert len(findings) == 2
