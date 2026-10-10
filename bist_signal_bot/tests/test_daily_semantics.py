"""Daily execution semantics: date-dependent price limits, bar health, entry fillability, locked-limit exit deferral,
NaN-exit carry, identical semantics across events / benchmark / labels, spread proxy, capacity. Offline, seeded."""
from datetime import date

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.capacity_daily import capacity_report
from bist_signal_bot.edge_validation.costs_daily import DailyCostModel
from bist_signal_bot.edge_validation.fills_daily import (DailySemantics, bar_health, bar_health_flags,
                                                         bar_health_report)
from bist_signal_bot.edge_validation.gate import CandidateGate, GateConfig
from bist_signal_bot.edge_validation.xsection import (EVENT_COLS, LEDGER_SUFFIX_V2, DailyContext, apply_benchmark,
                                                      benchmark_event_returns, build_portfolio_events,
                                                      ledger_family_name, nav_returns)
from bist_signal_bot.intraday import sessions as S
from bist_signal_bot.model_loop.daily_training import build_labels
from bist_signal_bot.tests.test_xsection_daily import make_panel

LEGACY = DailySemantics.legacy_semantics()


def _panel(seed=3, n_sym=30, days=700):
    p = make_panel(seed, n_sym=n_sym, days=days)
    for d in p.values():  # shift into the 10% era (>= 2020-03) so limits are the current ones
        d.index = d.index + pd.DateOffset(years=2)
    return p


def _scores(ctx):
    # S00 best ... S29 worst, constant over time (deterministic ranking)
    s = pd.DataFrame(np.tile(-np.arange(len(ctx.symbols), dtype=float), (len(ctx.index), 1)),
                     index=ctx.index, columns=ctx.symbols)
    return s


def _events(panel, semantics=None, h=5, top_n=3, policy=None, scores=None):
    kw = {}
    if semantics is not None:
        kw["semantics"] = semantics
    elif policy:
        kw["semantics"] = DailySemantics(entry_policy=policy)
    ctx = DailyContext.from_panel(panel, min_adv=5e6, **kw)
    return ctx, build_portfolio_events(ctx, _scores(ctx) if scores is None else scores(ctx), h, top_n)


def _second_basket(panel, h=5, top_n=3):
    ctx, res = _events(panel, h=h, top_n=top_n)
    ev = res.events
    t0 = sorted(ev["t0"].unique())[3]
    r = ev[ev["t0"] == t0]
    return ctx, r.iloc[0]["t0"], r.iloc[0]["t_entry"], r.iloc[0]["t1"]


# ------------------------------------------------------------------ price limits
def test_price_limit_schedule_is_date_dependent_and_backward_compatible():
    assert S.daily_price_limits(10.0) == (9.0, 11.0)  # no date -> current 10%
    assert S.daily_price_limits(10.0, date(2021, 5, 3)) == (9.0, 11.0)
    assert S.daily_price_limits(10.0, date(2019, 5, 3)) == (8.0, 12.0)  # UNVERIFIED pre-2020 band
    assert S.daily_price_limits(15.37, tick_table=False) == (13.83, 16.91)
    assert S.daily_price_limits(15.37, False) == (13.83, 16.91)  # legacy positional tick_table
    sched = S.parse_price_limit_schedule("1900-01-01:0.10")
    assert S.daily_price_limits(10.0, date(2019, 5, 3), schedule=sched) == (9.0, 11.0)
    assert S.PRICE_LIMIT_TRANSITION_DATE == date(2020, 3, 13)  # verified vs official BIST notice (2020-03-13)


def test_vectorised_limits_match_scalar():
    pcs = np.array([3.37, 15.37, 49.99, 51.3, 123.45, 777.7])
    lo, hi = S.daily_price_limits_array(pcs, 0.10)
    for p, a, b in zip(pcs, lo, hi):
        sl, sh = S.daily_price_limits(float(p))
        assert a == pytest.approx(sl) and b == pytest.approx(sh)


# ------------------------------------------------------------------ bar health
def test_bar_health_flags_bad_bars_and_is_causal():
    panel = _panel()
    idx = panel["S00"].index
    t = idx[300]
    panel["S01"].loc[t, "close"] *= 1.30                      # > limit + tol close-to-close
    panel["S02"].loc[idx[301], "volume"] = 0.0                # zero volume
    panel["S03"].iloc[303] = panel["S03"].iloc[302]           # copied bar
    panel["S04"].loc[idx[305], ["close", "high"]] *= 1.12     # spike ...
    panel["S04"].loc[idx[306], ["close", "low", "open"]] = panel["S04"].loc[idx[304], "close"]  # ... and revert
    panel["S05"].loc[idx[307], "open"] *= 1.5                 # gap beyond limit
    ctx = DailyContext.from_panel(panel, min_adv=5e6)
    fl = bar_health_flags(ctx)
    assert fl["c2c_limit"].loc[t, "S01"]
    assert fl["zero_volume"].loc[idx[301], "S02"]
    assert fl["copy_bar"].loc[idx[303], "S03"]
    assert fl["spike_revert"].loc[idx[306], "S04"]
    assert fl["gap_limit"].loc[idx[307], "S05"]
    h = bar_health(ctx)
    assert not h.loc[t, "S01"] and not h.loc[idx[303], "S03"]
    assert not ctx.universe_mask.loc[t, "S01"] and ctx.universe_mask.loc[t, "S00"]
    rep = bar_health_report(ctx)
    assert rep["n_flagged_bars"] >= 5 and rep["rules"]["c2c_limit"] >= 1 and rep["examples"]
    # causality: truncating the future never changes earlier flags
    k = 304
    part = bar_health(ctx.truncate(k))
    assert part.equals(h.iloc[:k])
    # switchable off / legacy
    off = DailyContext.from_panel(panel, min_adv=5e6, semantics=LEGACY)
    assert off.healthy.all().all() and off.universe_mask.loc[t, "S01"]


# ------------------------------------------------------------------ entry fillability
def _limit_up_open(panel, sym, te, i_prev_close):
    hi = S.daily_price_limits(float(i_prev_close), te)[1]
    d = panel[sym]
    d.loc[te, "open"] = hi
    d.loc[te, "high"] = hi
    d.loc[te, "low"] = hi * 0.97
    d.loc[te, "close"] = hi * 0.98


def test_entry_policies_cash_next_ranked_flag_and_legacy():
    panel = _panel()
    ctx0, t0, te, t1 = _second_basket(panel)
    prev_close = panel["S00"].loc[t0, "close"]
    _limit_up_open(panel, "S00", te, prev_close)
    top_n = 3
    _, cash = _events(panel, policy="cash")
    _, nxt = _events(panel, policy="next_ranked")
    _, flag = _events(panel, policy="flag")
    _, leg = _events(panel, semantics=LEGACY)
    pick = lambda r, c: set(r.events[r.events["t0"] == t0][c])  # noqa: E731
    assert pick(cash, "symbol") == {"S01", "S02"} and cash.n_unfillable_entry >= 1
    assert pick(nxt, "symbol") == {"S01", "S02", "S03"} and len(pick(nxt, "symbol")) == top_n
    assert pick(flag, "symbol") == {"S00", "S01", "S02"}
    fe = flag.events[flag.events["t0"] == t0]
    assert fe.loc[fe["symbol"] == "S00", "price_limit_flag"].iloc[0] and not fe["price_limit_flag"].iloc[1:].any()
    assert pick(leg, "symbol") == {"S00", "S01", "S02"}
    # the flagged event is disallowed by the cost model (NaN net) and excluded from NAV exactly like the gate does
    cm = DailyCostModel(0.0, 0.05, 0.3, 0.5, 0.05, 0.0)
    net = CandidateGate(GateConfig(), cost_model=cm, save=False)._net(flag.events)
    assert net.loc[net["price_limit_flag"], "net_ret"].isna().all()
    assert net.loc[~net["price_limit_flag"], "net_ret"].notna().all()
    assert np.isfinite(nav_returns(ctx0, flag.events, cm)["ret"]).all()


def test_locked_bar_and_zero_volume_entries_not_fillable():
    panel = _panel()
    _, t0, te, _ = _second_basket(panel)
    d = panel["S00"]
    d.loc[te, ["open", "high", "low", "close"]] = d.loc[t0, "close"]  # H == L locked
    panel["S01"].loc[te, "volume"] = 0.0
    _, res = _events(panel, policy="cash")
    assert set(res.events[res.events["t0"] == t0]["symbol"]) == {"S02"}
    _, leg = _events(panel, semantics=LEGACY)
    assert "S00" in set(leg.events[leg.events["t0"] == t0]["symbol"])
    assert "S01" not in set(leg.events[leg.events["t0"] == t0]["symbol"])  # volume==0 was already dropped before


# ------------------------------------------------------------------ exits
def test_locked_limit_down_exit_is_deferred_and_nan_exit_carried():
    panel = _panel()
    ctx0, t0, te, t1 = _second_basket(panel)
    pos = {d: k for k, d in enumerate(ctx0.index)}
    x = pos[t1]
    nxt_close = panel["S00"].iloc[x + 1]["close"]
    prev = panel["S00"].iloc[x - 1]["close"]
    lo = S.daily_price_limits(float(prev), t1)[0]
    d = panel["S00"]
    d.iloc[x, d.columns.get_loc("close")] = lo
    d.iloc[x, d.columns.get_loc("low")] = lo
    d.iloc[x, d.columns.get_loc("open")] = lo * 1.0
    d.iloc[x, d.columns.get_loc("high")] = lo * 1.002
    panel["S01"].iloc[x, panel["S01"].columns.get_loc("close")] = np.nan
    nan_next = panel["S01"].iloc[x + 1]["close"]
    ctx, res = _events(panel, policy="cash")
    e = res.events[res.events["t0"] == t0].set_index("symbol")
    assert e.loc["S00", "t_exit"] == ctx.index[x + 1] and e.loc["S00", "exit_deferred"] == 1
    assert e.loc["S00", "exit_price"] == pytest.approx(nxt_close)
    assert e.loc["S00", "raw_ret"] == pytest.approx(nxt_close / e.loc["S00", "price"] - 1.0)
    assert e.loc["S01", "exit_price"] == pytest.approx(nan_next)  # carried, not dropped
    assert res.n_exit_deferred >= 2 and res.n_exit_carried >= 1
    _, leg = _events(panel, semantics=LEGACY)
    le = leg.events[leg.events["t0"] == t0].set_index("symbol")
    assert le.loc["S00", "raw_ret"] == pytest.approx(lo / le.loc["S00", "price"] - 1.0)  # legacy: exits at lock
    assert "S01" not in le.index  # legacy dropped the NaN-exit name
    # NAV books the realised (deferred) exit price at t1 and stays finite
    assert np.isfinite(res.nav_gross["ret"]).all()


# ------------------------------------------------------------------ identical semantics across events / benchmark / labels
def test_events_benchmark_and_labels_use_identical_entry_exit_semantics():
    panel = _panel(seed=4, n_sym=30, days=700)
    ctx0 = DailyContext.from_panel(panel, min_adv=5e6)
    rng = np.random.default_rng(0)
    scores = pd.DataFrame(rng.random(ctx0.close.shape), index=ctx0.index, columns=ctx0.symbols)
    base = build_portfolio_events(ctx0, scores, 5, 8).events
    t0 = [t for t in sorted(base["t0"].unique()) if t > ctx0.index[480]][0]
    syms = list(base[base["t0"] == t0]["symbol"])
    pos = {d: k for k, d in enumerate(ctx0.index)}
    i = pos[t0]
    e_, x_ = i + 1, i + 5
    a, b, c = syms[0], syms[1], syms[2]
    _limit_up_open(panel, a, ctx0.index[e_], panel[a].iloc[i]["close"])
    lo = S.daily_price_limits(float(panel[b].iloc[x_ - 1]["close"]), ctx0.index[x_])[0]
    pb = panel[b]
    for col, v in (("close", lo), ("low", lo), ("open", lo), ("high", lo * 1.002)):
        pb.iloc[x_, pb.columns.get_loc(col)] = v
    panel[c].iloc[x_, panel[c].columns.get_loc("close")] = np.nan
    ctx = DailyContext.from_panel(panel, min_adv=5e6)
    ev = apply_benchmark(ctx, build_portfolio_events(ctx, scores, 5, 8).events, "ew_universe")
    lp = build_labels(ctx, 5)
    col = {s: k for k, s in enumerate(ctx.symbols)}
    sel = ev[ev["t0"] == t0]
    assert a not in set(sel["symbol"]) and {b, c} <= set(sel["symbol"])
    assert (sel["exit_deferred"] > 0).sum() >= 2
    m = lp.pos == i
    assert m.any() and not (lp.j[m] == col[a]).any()  # blocked entry absent from labels too
    ew_lab = float(lp.ew[m][0])
    assert np.allclose(sel["bench_ret"].to_numpy(float), ew_lab, atol=1e-12)  # benchmark == label EW
    key = {(int(p), int(j)): (ex, ew) for p, j, ex, ew in zip(lp.pos, lp.j, lp.excess, lp.ew)}
    for _, r in sel.iterrows():
        ex, ew = key[(i, col[r["symbol"]])]
        assert ex + ew == pytest.approx(r["raw_ret"], abs=1e-12)  # label raw == event raw (deferred/carried exits too)
    # legacy semantics differ (blocked name is bought, NaN-exit dropped)
    ctx_l = DailyContext.from_panel(panel, min_adv=5e6, semantics=LEGACY)
    leg = build_portfolio_events(ctx_l, scores, 5, 8).events
    ls = set(leg[leg["t0"] == t0]["symbol"])
    assert a in ls and c not in ls
    # direct call equals apply_benchmark column
    bm = benchmark_event_returns(ctx, ev, "ew_universe")
    assert np.allclose(bm, ev["bench_ret"].to_numpy(float))


# ------------------------------------------------------------------ costs
def test_spread_proxy_adv_dependent_and_legacy_off():
    cm = DailyCostModel(0.0, 0.05, 0.3, 0.5, 0.05, 0.0, spread_base_bps=1.0, spread_k_bps=3.0)
    thin = cm.breakdown(500.0, 1000.0, 2e6).half_spread_bps
    thick = cm.breakdown(500.0, 1000.0, 2e9).half_spread_bps
    assert thin > thick > 0 and thin == pytest.approx(1.0 + 3.0 / np.sqrt(2.0), rel=1e-6)
    zero = DailyCostModel(0.0, 0.05, 0.3, 0.5, 0.05, 0.0)
    assert zero.breakdown(500.0, 1000.0, 2e6).half_spread_bps == pytest.approx(0.5 * 0.10 / 500.0 * 1e4)  # tick floor only
    # price_limit_flags disallow entries
    out = cm.apply_costs(np.zeros(2), np.full(2, 50.0), np.full(2, 1e4), np.full(2, 1e8),
                         price_limit_flags=np.array([True, False]))
    assert np.isnan(out[0]) and np.isfinite(out[1])

    class _Cfg:
        DAILY_COST_COMMISSION_PLACEHOLDER_BPS = 5.0
        DAILY_COST_BSMV_RATE = 0.05
        DAILY_COST_EXCHANGE_FEE_BPS = 0.3
        DAILY_COST_IMPACT_COEF = 0.5
        DAILY_COST_MAX_PARTICIPATION = 0.05
        CASH_BENCHMARK_ANNUAL_RATE = 0.37
        CASH_BENCHMARK_WITHHOLDING = 0.0
        DAILY_LEGACY_SEMANTICS = False

    assert DailyCostModel.from_settings(_Cfg()).spread_k_bps > 0
    _Cfg.DAILY_LEGACY_SEMANTICS = True
    leg = DailyCostModel.from_settings(_Cfg())
    assert leg.spread_k_bps == 0 and leg.spread_base_bps == 0


# ------------------------------------------------------------------ capacity / misc
def test_capacity_report_scales_with_capital():
    ctx, res = _events(_panel(), policy="cash")
    rep = capacity_report(res.events, ctx, capitals=(1e5, 1e6, 1e8), cost_model=DailyCostModel(0, 0.05, 0.3, 0.5, 0.05, 0.0))
    p = [rep[c]["median_participation"] for c in (1e5, 1e6, 1e8)]
    assert p[0] < p[1] < p[2]
    assert rep[1e5]["share_over_cap"] <= rep[1e6]["share_over_cap"] <= rep[1e8]["share_over_cap"]
    assert rep[1e8]["share_over_cap"] > 0.5 and rep[1e5]["n_orders"] == len(res.events)
    assert rep[1e6]["cost_uplift_bps"] >= -1e-9
    assert capacity_report(res.events.iloc[0:0], ctx)[1e5]["n_orders"] == 0


def test_event_columns_ledger_suffix_and_semantics_from_settings():
    ctx, res = _events(_panel(), policy="cash")
    assert list(res.events.columns) == EVENT_COLS and not res.events["price_limit_flag"].any()
    assert LEDGER_SUFFIX_V2 == "_daily_xs_ew2"
    assert ledger_family_name("xs_momentum", "ew_universe") == "xs_momentum_daily_xs_ew2"
    assert ledger_family_name("xs_momentum", "ew_universe", v2=False) == "xs_momentum_daily_xs_ew"
    assert ledger_family_name("f", "cash", placebo=True) == "f_daily_xs_cash2__placebo"

    class _St:
        DAILY_LEGACY_SEMANTICS = True

    assert DailySemantics.from_settings(_St()).legacy and not DailySemantics.from_settings(None).legacy
    with pytest.raises(ValueError):
        DailySemantics(entry_policy="bogus")
