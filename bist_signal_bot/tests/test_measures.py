"""VBTS measures: parser (fixtures copied from real KAP sentences), store, fetcher (injected providers),
and the daily fill rule (on/off/no-table). Offline."""
from datetime import date

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.fills_daily import (DailySemantics, get_fills, measure_report,
                                                         resolve_window)
from bist_signal_bot.edge_validation.xsection import DailyContext
from bist_signal_bot.measures.fetcher import MeasureFetcher
from bist_signal_bot.measures.parser import GROSS_SETTLEMENT, ORDER_PACKAGE, SINGLE_PRICE, Measure, parse_measure_body
from bist_signal_bot.measures.store import MeasureStore

HEAD = ("Sermaye Piyasası Kurulu kararı uyarınca devreye alınan Volatilite Bazlı Tedbir Sistemi (VBTS) kapsamında, ")
B_ATLAS = ("<div><div><div class=\"text-block-value\"><div>" + HEAD +
           "ATLAS.E, paylarında 13/12/2018 tarihli işlemlerden (seans başından) 27/12/2018 tarihli işlemlere "
           "(seans sonuna) kadar brüt takas uygulanacaktır.</div></div></div></div>")
B_MARKA = ("<div>" + HEAD + "MARKA.E payları 01/02/2024 tarihli işlemlerden (seans başından) 29/02/2024 tarihli "
           "işlemlere (seans sonuna) kadar tek fiyat işlem yöntemi ile işlem görecektir.</div>")
B_NIBAS = (HEAD + "NIBAS.E paylarında 25/02/2026 tarihli işlemlerden (seans başından) 24/03/2026 tarihli işlemlere "
           "(seans sonuna) kadar brüt takas uygulanacaktır. RUBNS.E paylarında 25/02/2026 tarihli işlemlerden "
           "(seans başından) 24/03/2026 tarihli işlemlere (seans sonuna) kadar emir paketi tedbiri uygulanacaktır.")
B_NOISE = HEAD + "LUKSK.E. Piyasa yapıcılı sürekli işlem yöntemiyle işlem gören paylarda tedbir nedeniyle tek fiyat işlem yöntemi uygulandığı süre boyunca piyasa yapıcılık faaliyeti yapılmaz."


def test_parse_single_gross():
    m = parse_measure_body(B_ATLAS, "12.12.2018 18:31:50", 724402)
    assert m == [Measure("ATLAS", GROSS_SETTLEMENT, date(2018, 12, 13), date(2018, 12, 27), "724402", date(2018, 12, 12))]


def test_parse_single_price_html_entities():
    m = parse_measure_body(B_MARKA.replace("işlem", "i&#351;lem").replace("tek fiyat", "tek&nbsp;fiyat"), "31.01.2024 18:37:57", 1245150)
    assert [(x.symbol, x.type, x.start, x.end) for x in m] == [("MARKA", SINGLE_PRICE, date(2024, 2, 1), date(2024, 2, 29))]


def test_parse_multi_symbol_multi_type():
    m = parse_measure_body(B_NIBAS, date(2026, 2, 24), 1561041)
    assert {(x.symbol, x.type) for x in m} == {("NIBAS", GROSS_SETTLEMENT), ("RUBNS", ORDER_PACKAGE)}


def test_parse_shared_sentence_and_bad_input(caplog):
    t = HEAD + "AAAA.E, BBBB.E ve CCCC.E paylarında 01/03/2024 tarihli işlemlerden (seans başından) 05/03/2024 tarihli işlemlere (seans sonuna) kadar brüt takas uygulanacaktır."
    assert {x.symbol for x in parse_measure_body(t, None, 1)} == {"AAAA", "BBBB", "CCCC"}
    for bad in ("", None, 123, "<p>hello</p>", B_NOISE, "X.E 99/99/2024 tarihli işlemlerden a 01/01/2024 tarihli işlemlere kadar brüt takas",
                "ABC.E 05/03/2024 tarihli işlemlerden a 01/03/2024 tarihli işlemlere kadar brüt takas"):
        assert parse_measure_body(bad, None, 9) == []


def test_store_upsert_idempotent_and_lookup(tmp_path):
    st = MeasureStore(tmp_path / "m")
    ms = parse_measure_body(B_ATLAS, "12.12.2018 18:31:50", 724402) + parse_measure_body(B_NIBAS, "24.02.2026", 1561041)
    assert st.upsert(ms) == 3
    assert st.upsert(ms) == 0
    cov = st.coverage()
    assert cov["rows"] == 3 and cov["oldest_publish"] == "2018-12-12" and cov["newest_publish"] == "2026-02-24"
    assert st.load()["source"].iloc[0] == "KAP/Borsa Istanbul A.S. duyurulari"
    assert st.is_restricted("ATLAS", "2018-12-13") and st.is_restricted("ATLAS", "2018-12-27")
    assert not st.is_restricted("ATLAS", "2018-12-28") and not st.is_restricted("ATLAS", "2018-12-12")
    assert not st.is_restricted("ATLAS", "2018-12-20", kinds=[SINGLE_PRICE])
    mk = st.restricted_mask(["ATLAS", "ZZZZ"], pd.bdate_range("2018-12-10", "2018-12-31"))
    assert int(mk["ATLAS"].sum()) == 11 and not mk["ZZZZ"].any()


def test_fetcher_restartable_and_rate_floor(tmp_path):
    st = MeasureStore(tmp_path / "m")
    listing = [{"disclosureIndex": 724402, "publishDate": "12.12.2018 18:31:50", "summary": "Pay Piyasasında Volatilite Bazlı Tedbir Sistemi"},
               {"disclosureIndex": 5, "publishDate": "12.12.2018 18:31:50", "summary": "Yatırımcı bazlı"}]
    calls, sleeps = [], []

    def body(i):
        calls.append(i)
        return B_ATLAS

    f = MeasureFetcher(st, lambda a, b: listing if a.year == 2018 and a.month == 7 else [], body, interval=0.1,
                       sleep=sleeps.append, today=date(2019, 1, 31))
    r = f.sync(date(2018, 1, 1))
    assert r["new_rows"] == 1 and r["fetched"] == 1 and calls == ["724402"]
    assert min(sleeps) >= 2.5
    r2 = MeasureFetcher(st, lambda a, b: [], lambda i: 1 / 0, sleep=lambda s: None, today=date(2019, 1, 31)).sync(date(2018, 1, 1))
    assert r2["fetched"] == 0 and r2["cached"] == 1 and r2["new_rows"] == 0
    # --max-bodies
    f3 = MeasureFetcher(MeasureStore(tmp_path / "n"), lambda a, b: listing if a.month == 7 else [], body, sleep=lambda s: None,
                        today=date(2019, 1, 31))
    assert f3.sync(date(2018, 1, 1), max_bodies=0)["remaining_bodies"] == 1


# ------------------------------------------------------------------ daily rule
def _ctx(sem, n=40):
    idx = pd.bdate_range("2024-01-02", periods=n)
    px = pd.DataFrame({"AAA": np.linspace(10, 12, n), "BBB": np.linspace(20, 22, n)}, index=idx)
    vol = pd.DataFrame(1e6, index=idx, columns=px.columns)
    return DailyContext(px, px, vol, semantics=sem), idx


def _table(path, idx):
    st = MeasureStore(path)
    st.upsert([Measure("AAA", GROSS_SETTLEMENT, idx[10].date(), idx[14].date(), "1", idx[8].date())])
    return st


def test_rule_on_blocks_entry_and_defers_exit(tmp_path):
    ctx0, idx = _ctx(DailySemantics())
    _table(tmp_path / "m", idx)
    ctx, _ = _ctx(DailySemantics(measure_rule=True, measure_dir=str(tmp_path / "m")))
    f = get_fills(ctx)
    assert not f.entry_ok[10:15, 0].any() and f.entry_ok[9, 0] and f.entry_ok[15, 0]
    assert f.entry_ok[:, 1].all()
    assert f.exit_next[12, 0] == 15  # deferred to first unrestricted session
    w = resolve_window(ctx, 9, 11, 13)
    assert not w.entry_ok[0] and w.entry_ok[1]
    rep = measure_report(ctx)
    assert rep["applied"] and rep["n_blocked_cells"] == 5 and rep["share_dates_covered"] < 1.0 and "warning" in rep
    assert f.exit_next[12, 0] != get_fills(ctx0).exit_next[12, 0]


def test_rule_off_or_no_table_is_identical(tmp_path):
    base, idx = _ctx(DailySemantics())
    _table(tmp_path / "m", idx)
    off, _ = _ctx(DailySemantics(measure_rule=False, measure_dir=str(tmp_path / "m")))
    none, _ = _ctx(DailySemantics(measure_rule=True, measure_dir=str(tmp_path / "empty")))
    fb = get_fills(base)
    for c in (off, none):
        f = get_fills(c)
        assert (f.entry_ok == fb.entry_ok).all() and (f.exit_next == fb.exit_next).all()
    assert measure_report(off)["reason"] == "disabled" and measure_report(none)["reason"] == "no_table"


def test_from_settings_key():
    class S:
        DAILY_MEASURE_RULE_ENABLED = True
    assert DailySemantics.from_settings(S()).measure_rule is True
    assert DailySemantics.from_settings(None).measure_rule is False
    assert DailySemantics.legacy_semantics().measure_rule is False


def test_measure_rule_matches_yahoo_suffixed_symbols(tmp_path):
    ctx0, idx = _ctx(DailySemantics())
    _table(tmp_path / "m", idx)
    sem = DailySemantics(measure_rule=True, measure_dir=str(tmp_path / "m"))
    n = len(idx)
    px = pd.DataFrame({"AAA.IS": np.linspace(10, 12, n), "BBB.IS": np.linspace(20, 22, n)}, index=idx)
    ctx = DailyContext(px, px, pd.DataFrame(1e6, index=idx, columns=px.columns), semantics=sem)
    f = get_fills(ctx)
    assert not f.entry_ok[10:15, 0].any() and f.entry_ok[:, 1].all()
    assert measure_report(ctx)["n_blocked_cells"] == 5
