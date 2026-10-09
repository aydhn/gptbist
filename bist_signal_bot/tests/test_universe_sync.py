from datetime import UTC, datetime, timedelta

import pytest

from bist_signal_bot.data.symbol_universe import DEFAULT_SEED_SYMBOLS_STR
from bist_signal_bot.data.universe_store import UniverseStore
from bist_signal_bot.data.universe_sync import fetch_ist_listing, sync_if_stale, sync_universe

NOW = datetime(2026, 10, 9, tzinfo=UTC)


def _q(sym, days_ago=3000, qt="EQUITY"):
    ms = int((NOW - timedelta(days=days_ago)).timestamp() * 1000)
    return {"symbol": f"{sym}.IS", "quoteType": qt, "longName": sym, "firstTradeDateMilliseconds": ms}


def _base(n=320):
    qs = [_q(s) for s in DEFAULT_SEED_SYMBOLS_STR]
    qs += [_q(f"AAA{i:03d}") for i in range(n - len(qs))]
    return qs


@pytest.fixture
def settings(settings_factory):
    return settings_factory(INTRADAY_UNIVERSE_DELIST_MISSES=2)


def test_new_ipo_added_and_flagged(settings):
    r = sync_universe(settings, fetch=lambda: _base() + [_q("NEWIPO", days_ago=10)], now=NOW)
    assert "NEWIPO" in r.added and "NEWIPO" in r.new_ipos
    assert UniverseStore(settings).load_universe().contains("NEWIPO")
    assert "AAA001" not in r.new_ipos


def test_missing_deactivated_only_after_n_misses(settings):
    sync_universe(settings, fetch=lambda: _base(), now=NOW)
    short = [q for q in _base() if q["symbol"] != "AAA005.IS"]
    r1 = sync_universe(settings, fetch=lambda: short, now=NOW)
    assert r1.deactivated == []
    assert UniverseStore(settings).load_universe().require("AAA005").is_active
    r2 = sync_universe(settings, fetch=lambda: short, now=NOW)
    assert r2.deactivated == ["AAA005"]
    uni = UniverseStore(settings).load_universe()
    assert uni.contains("AAA005") and not uni.require("AAA005").is_active
    r3 = sync_universe(settings, fetch=lambda: _base(), now=NOW)
    assert "AAA005" in r3.reactivated


def test_tiny_listing_refused(settings):
    r = sync_universe(settings, fetch=lambda: _base()[:50], now=NOW)
    assert r.skipped_reason and not UniverseStore(settings).exists()


def test_fetch_failure_fail_closed(settings):
    def boom():
        raise RuntimeError("net down")

    r = sync_universe(settings, fetch=boom)
    assert "fetch failed" in r.skipped_reason and not UniverseStore(settings).exists()


def test_seeds_protected(settings):
    sync_universe(settings, fetch=lambda: _base(), now=NOW)
    no_seed = [q for q in _base() if q["symbol"][:-3] not in DEFAULT_SEED_SYMBOLS_STR]
    for _ in range(4):
        sync_universe(settings, fetch=lambda: no_seed, now=NOW)
    uni = UniverseStore(settings).load_universe()
    assert all(uni.require(s).is_active for s in DEFAULT_SEED_SYMBOLS_STR)


def test_dry_run_changes_nothing(settings):
    r = sync_universe(settings, fetch=lambda: _base(), dry_run=True, now=NOW)
    assert r.added and not UniverseStore(settings).exists()
    assert sync_if_stale(settings, fetch=lambda: _base()) is not None  # no state written by dry-run


def test_non_equity_and_bad_symbols_filtered():
    rows = fetch_ist_listing(lambda: [_q("GOOD"), _q("ETFX", qt="ETF"), _q("BAD-X"), _q("OK2")])
    assert sorted(r["symbol"] for r in rows) == ["GOOD", "OK2"]
    assert rows[0]["first_trade_date"]


def test_warrant_etf_fund_rights_index_names_filtered():
    def n(sym, name, **kw):
        q = _q(sym)
        q["longName"] = name
        q.update(kw)
        return q

    rows = fetch_ist_listing(lambda: [
        n("REAL1", "Real Sanayi A.S."),
        n("WARR1", "Foo Bank Warrant"),
        n("ETF1", "Bar BIST30 Borsa Yatirim Fonu"),
        n("FND1", "Baz Yatirim Fonu"),
        n("RGT1", "Qux Rights"),
        n("IDX1", "BIST 100 Index"),
        n("TYP1", "Plain Name", typeDisp="ETF"),
    ])
    assert [r["symbol"] for r in rows] == ["REAL1"]


def test_seed_symbols_never_filtered_as_non_equity():
    seed = DEFAULT_SEED_SYMBOLS_STR[0]
    q = _q(seed)
    q["longName"] = "Some Index Fund Warrant"
    q["typeDisp"] = "ETF"
    assert [r["symbol"] for r in fetch_ist_listing(lambda: [q])] == [seed]


def test_auto_sync_throttled(settings):
    sync_universe(settings, fetch=lambda: _base(), now=datetime.now(UTC))
    assert sync_if_stale(settings, fetch=lambda: _base()) is None
