"""Cross-sectional daily layer tests: offline, seeded synthetic panels."""
import json

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.cli.edge_cli import build_parser
from bist_signal_bot.edge_validation.costs_daily import DailyCostModel
from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES, XSMomentum, register_family
from bist_signal_bot.edge_validation.gate import CandidateGate, GateConfig
from bist_signal_bot.edge_validation.labels_daily import forward_return_labels_daily
from bist_signal_bot.edge_validation.ledger import TrialLedger
from bist_signal_bot.edge_validation.runner_daily import run_family_daily
from bist_signal_bot.edge_validation.xsection import (EVENT_COLS, DailyContext, build_portfolio_events,
                                                      check_score_causality, nav_returns)


def make_panel(seed=0, n_sym=40, days=1100, momentum=0.0, sigma=0.015, persist=0.985):
    """Random-walk panel; momentum>0 adds a persistent per-stock drift component (planted signal)."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2019-01-01", periods=days)
    common = rng.normal(0.0003, 0.008, days)
    panel = {}
    for k in range(n_sym):
        a = np.zeros(days)
        e = rng.normal(0, 1, days) * momentum * np.sqrt(1 - persist ** 2)
        for t in range(1, days):
            a[t] = persist * a[t - 1] + e[t]
        r = common + a + rng.normal(0, sigma, days)
        c = 50.0 * np.exp(np.cumsum(r))
        o = np.concatenate([[50.0], c[:-1]]) * (1 + rng.normal(0, 0.002, days))
        v = rng.uniform(0.8, 1.2, days) * 2e6  # ~1e8 TRY/day
        panel[f"S{k:02d}"] = pd.DataFrame({"open": o, "high": np.maximum(o, c), "low": np.minimum(o, c),
                                           "close": c, "volume": v}, index=idx)
    return panel


@pytest.fixture(scope="module")
def noise_ctx():
    return DailyContext.from_panel(make_panel(1), min_adv=5e6)


@pytest.fixture(scope="module")
def mom_ctx():
    return DailyContext.from_panel(make_panel(2, momentum=0.004), min_adv=5e6)


def _gate():
    return CandidateGate(GateConfig(), save=False)


def _run(fam, ctx, tmp_path, horizons=(5,), grid=None, placebo=False, seed=0, **kw):
    grid = grid or {"lookback": [20, 60, 120], "skip": [0, 5]}
    return run_family_daily(fam, ctx, horizons, grid, 8, TrialLedger(tmp_path / "t.sqlite"), _gate(),
                            placebo=placebo, seed=seed, save_report=False, **kw)


# ---------------------------------------------------------------- causality
def test_momentum_scores_are_causal(mom_ctx):
    fam = DAILY_FAMILIES["xs_momentum"]
    for p in ({"lookback": 20, "skip": 0}, {"lookback": 120, "skip": 5}):
        check_score_causality(fam, mom_ctx, p)


def test_causality_check_detects_lookahead(noise_ctx):
    class Leaky:
        name, default_grid = "leaky", {}

        def valid(self, p):
            return True

        def score(self, ctx, p):
            return ctx.close.shift(-3) / ctx.close - 1.0  # uses the future

    with pytest.raises(AssertionError):
        check_score_causality(Leaky(), noise_ctx, {})


def test_universe_mask_and_derived_data_are_causal(noise_ctx):
    k = 700
    full = noise_ctx.universe_mask.iloc[:k]
    part = noise_ctx.truncate(k).universe_mask
    assert (full.to_numpy() == part.to_numpy()).all()
    assert (noise_ctx.adv.iloc[:k].fillna(-1).to_numpy() == noise_ctx.truncate(k).adv.fillna(-1).to_numpy()).all()
    with pytest.raises(ValueError):
        noise_ctx.lag(noise_ctx.close, -1)


def test_registry_has_momentum_and_rejects_duplicates():
    assert "xs_momentum" in DAILY_FAMILIES
    with pytest.raises(ValueError):
        register_family(XSMomentum())


# ---------------------------------------------------------------- universe mask
def test_universe_mask_filters_illiquid_zero_volume_short_history():
    p = make_panel(3, n_sym=4, days=300)
    p["S00"]["volume"] = 100.0  # illiquid (ADV ~5e3 TRY)
    p["S01"].loc[p["S01"].index[150], "volume"] = 0.0  # halted day
    p["S02"] = p["S02"].iloc[200:]  # short history
    ctx = DailyContext.from_panel(p, min_adv=5e6, min_history=60)
    m = ctx.universe_mask
    assert not m["S00"].any()
    assert not m["S01"].iloc[150]
    assert m["S01"].iloc[140]
    assert not m["S02"].iloc[:259].any() and m["S02"].iloc[-1]  # needs 60 bars of history (+ADV20 window)
    assert m["S03"].iloc[-1]
    ctx2 = DailyContext.from_panel(p, min_adv=5e6, min_price=1e9)
    assert not ctx2.universe_mask.to_numpy().any()


# ---------------------------------------------------------------- events frame
def test_events_schema_and_semantics(noise_ctx):
    sc = DAILY_FAMILIES["xs_momentum"].score(noise_ctx, {"lookback": 60, "skip": 5})
    pr = build_portfolio_events(noise_ctx, sc, horizon=5, top_n=8)
    ev = pr.events
    assert list(ev.columns) == EVENT_COLS and len(ev) > 300
    assert (ev["t0"] < ev["t_entry"]).all() and (ev["t_entry"] < ev["t1"]).all()
    assert ev.groupby("rebalance_date").size().max() <= 8
    assert np.allclose(ev["order_value"], noise_ctx.capital / 8)
    assert ev["rank"].min() == 1 and ev["gross_ret"].notna().all() and ev["bar_value_try"].gt(5e6).all()
    # no overlap between baskets: next basket enters after previous exit
    b = ev.groupby("rebalance_date").agg(e=("t_entry", "first"), x=("t1", "first")).sort_index()
    assert (b["e"].iloc[1:].to_numpy() > b["x"].iloc[:-1].to_numpy()).all()
    # top-N by score, long-only: selected scores >= every other eligible score at that date
    d = ev["rebalance_date"].iloc[len(ev) // 2]
    g = ev[ev["rebalance_date"] == d]
    elig = noise_ctx.universe_mask.loc[d] & sc.loc[d].notna()
    assert g["score"].min() >= sc.loc[d][elig].drop(g["symbol"]).max()
    # same return semantics as labels_daily
    row = g.iloc[0]
    lab = forward_return_labels_daily(noise_ctx.close.join(noise_ctx.open, rsuffix="_o")[[]].assign(
        open=noise_ctx.open[row["symbol"]], close=noise_ctx.close[row["symbol"]]), 5)
    assert lab.set_index("t0").loc[row["t0"], "ret"] == pytest.approx(row["raw_ret"])


def test_events_deterministic_ties(noise_ctx):
    sc = pd.DataFrame(1.0, index=noise_ctx.index, columns=noise_ctx.symbols)  # all tied
    a = build_portfolio_events(noise_ctx, sc, 5, 8).events
    b = build_portfolio_events(noise_ctx, sc, 5, 8).events
    pd.testing.assert_frame_equal(a, b)
    assert list(a[a["rebalance_date"] == a["rebalance_date"].iloc[0]]["symbol"]) == noise_ctx.symbols[:8]


def test_regime_scale_reduces_exposure(noise_ctx):
    sc = DAILY_FAMILIES["xs_momentum"].score(noise_ctx, {"lookback": 20, "skip": 0})
    half = pd.Series(0.5, index=noise_ctx.index)
    full = build_portfolio_events(noise_ctx, sc, 5, 8).events
    red = build_portfolio_events(noise_ctx, sc, 5, 8, regime_scale=half).events
    assert np.allclose(red["order_value"], full["order_value"] * 0.5)
    assert (red["gross_ret"] - (0.5 * red["raw_ret"])).abs().max() < 0.05  # remainder = small cash return
    assert red["gross_ret"].abs().mean() < full["gross_ret"].abs().mean()


# ---------------------------------------------------------------- NAV / cash
def test_nav_idle_is_cash_and_remainder_earns_cash(noise_ctx):
    empty = pd.DataFrame(columns=EVENT_COLS)
    n = nav_returns(noise_ctx, empty, None)
    assert np.allclose(n["ret"], noise_ctx.cash_ret) and n["holdings"].sum() == 0
    # 3 symbols in a 8-slot book -> 5/8 of capital stays in cash
    sc = pd.DataFrame(np.nan, index=noise_ctx.index, columns=noise_ctx.symbols)
    sc.iloc[:, :3] = [3.0, 2.0, 1.0]
    pr = build_portfolio_events(noise_ctx, sc, 5, 8)
    ev = pr.events
    assert ev.groupby("rebalance_date").size().eq(3).all()
    g = ev[ev["rebalance_date"] == ev["rebalance_date"].iloc[0]]
    e, x = noise_ctx.index.get_loc(g["t_entry"].iloc[0]), noise_ctx.index.get_loc(g["t1"].iloc[0])
    cash = noise_ctx.cash_ret.to_numpy()[e:x + 1]
    w = 1 / 8
    pos = sum(w * noise_ctx.close[s].iloc[x] / noise_ctx.open[s].iloc[e] for s in g["symbol"])
    expected = pos + (1 - 3 * w) * np.prod(1 + cash)
    got = (1 + pr.nav_gross["ret"].iloc[e:x + 1]).prod()
    assert got == pytest.approx(expected, rel=1e-9)
    assert pr.nav_gross["invested_frac"].iloc[e] == pytest.approx(3 / 8)
    # costs reduce NAV
    net = pr.nav_net(DailyCostModel(commission_bps=5.0))
    assert net["nav"].iloc[-1] < pr.nav_gross["nav"].iloc[-1]


# ---------------------------------------------------------------- gate behaviour
def test_planted_momentum_is_candidate_before_costs_and_report(mom_ctx, tmp_path):
    res = run_family_daily("xs_momentum", mom_ctx, (5,), {"lookback": [20, 60, 120], "skip": [0, 5]}, 8,
                           TrialLedger(tmp_path / "t.sqlite"), _gate(), save_report=True, report_dir=tmp_path)
    zero = res.reports["zero_commission"]
    assert zero.gross_sharpe_annual and zero.gross_sharpe_annual > 0.5
    assert zero.verdict == "CANDIDATE", zero.failed_criteria
    r = json.loads((tmp_path / res.report_path.split("\\")[-1].split("/")[-1]).read_text(encoding="utf-8"))
    assert r["candidacy_scenario"] == "placeholder_commission"
    for s in ("placeholder_commission", "zero_commission"):
        d = r["scenarios"][s]
        for k in ("verdict", "nav_net_sharpe_annual", "net_cagr", "max_drawdown", "turnover_two_way_per_year",
                  "avg_holdings", "alpha_vs_cash", "alpha_vs_ew_universe",
                  "cost_drag_bps_per_year"):
            assert k in d
    assert r["n_trials_ledger"] == 6 and "Survivorship" in r["survivorship_warning"]
    assert r["no_order"] == "No real order sent."


def test_both_scenarios_differ_and_ledger_counted_once(mom_ctx, tmp_path):
    res = _run("xs_momentum", mom_ctx, tmp_path)
    z, p = res.report["scenarios"]["zero_commission"], res.report["scenarios"]["placeholder_commission"]
    assert z["nav_net"]["cagr"] > p["nav_net"]["cagr"]
    assert z["cost_drag_bps_per_year"] < p["cost_drag_bps_per_year"]
    assert res.reports["zero_commission"].n_trials_ledger == res.reports["placeholder_commission"].n_trials_ledger == 6
    assert res.report["n_trials_ledger"] == 6
    # idempotent: re-running the same trials does not inflate N
    res2 = _run("xs_momentum", mom_ctx, tmp_path)
    assert res2.report["n_trials_ledger"] == 6


def test_noise_and_placebo_rejected(noise_ctx, tmp_path):
    real = _run("xs_momentum", noise_ctx, tmp_path / "a")
    assert real.reports["placeholder_commission"].verdict != "CANDIDATE"
    for sd in (0, 1):
        pl = _run("xs_momentum", noise_ctx, tmp_path / f"p{sd}", placebo=True, seed=sd)
        assert pl.ledger_family.endswith("_xs_ew2__placebo")
        assert pl.reports["placeholder_commission"].verdict == "REJECTED"
    # placebo on a panel WITH planted momentum is still rejected (scores are random)
    mc = DailyContext.from_panel(make_panel(2, momentum=0.004), min_adv=5e6)
    pl = _run("xs_momentum", mc, tmp_path / "pm", placebo=True, seed=3)
    assert pl.reports["placeholder_commission"].verdict == "REJECTED"


def test_trials_all_recorded_including_failed(noise_ctx, tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    run_family_daily("xs_momentum", noise_ctx, (5, 10), {"lookback": [20, 250], "skip": [0]}, 8, led, _gate(),
                     save_report=False)
    assert led.n_trials("xs_momentum_daily_xs_ew2") == 4


# ---------------------------------------------------------------- CLI
def test_cli_parser_run_daily():
    a = build_parser().parse_args(["run-daily", "--family", "xs_momentum", "--horizons", "5,10", "--top-n", "8",
                                   "--placebo", "--scenarios", "both", "--regime-scale"])
    assert a.edge_command == "run-daily" and a.placebo and a.regime_scale and a.horizons == "5,10"
    assert build_parser().parse_args(["list-daily-families"]).edge_command == "list-daily-families"
