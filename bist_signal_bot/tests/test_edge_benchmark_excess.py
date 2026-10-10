"""Excess-return (benchmark) evaluation modes: placebo / pure-beta must be REJECTED in a drifting market, planted
alpha must be CANDIDATE-able. All runs use TEMP ledgers (the real ledger is append-only and never touched)."""
import json

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.cli.edge_cli import build_parser
from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
from bist_signal_bot.edge_validation.gate import CandidateGate, GateConfig
from bist_signal_bot.edge_validation.ledger import TrialLedger
from bist_signal_bot.edge_validation.run_all_daily import format_markdown, format_table
from bist_signal_bot.edge_validation.runner_daily import run_family_daily, survivor_robustness
from bist_signal_bot.edge_validation.xsection import (DailyContext, apply_benchmark, benchmark_event_returns,
                                                      build_portfolio_events)

GRID = {"lookback": [20, 60, 120], "skip": [0, 5]}


def drift_panel(seed, n_sym=40, days=1100, alpha=0.0, drift=0.0012, sigma=0.015, persist=0.985):
    """Market drift ~35%/yr nominal (inflation-like). ``alpha``>0 adds persistent idiosyncratic drift (planted
    momentum alpha); alpha=0 is a pure-beta world (every stock = market + noise)."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2019-01-01", periods=days)
    common = rng.normal(drift, 0.008, days)
    panel = {}
    for k in range(n_sym):
        a = np.zeros(days)
        e = rng.normal(0, 1, days) * alpha * np.sqrt(1 - persist ** 2)
        for t in range(1, days):
            a[t] = persist * a[t - 1] + e[t]
        r = common + a + rng.normal(0, sigma, days)
        c = 50.0 * np.exp(np.cumsum(r))
        o = np.concatenate([[50.0], c[:-1]]) * (1 + rng.normal(0, 0.002, days))
        v = rng.uniform(0.8, 1.2, days) * 2e6
        panel[f"S{k:02d}"] = pd.DataFrame({"open": o, "high": np.maximum(o, c), "low": np.minimum(o, c),
                                           "close": c, "volume": v}, index=idx)
    return panel


@pytest.fixture(scope="module")
def beta_ctx():
    return DailyContext.from_panel(drift_panel(11), min_adv=5e6)


@pytest.fixture(scope="module")
def alpha_ctx():
    return DailyContext.from_panel(drift_panel(12, alpha=0.004), min_adv=5e6)


def _run(fam, ctx, tmp, bm="ew_universe", placebo=False, seed=0, **kw):
    return run_family_daily(fam, ctx, (5,), GRID, 8, TrialLedger(tmp / "t.sqlite"),
                            CandidateGate(GateConfig(), save=False), placebo=placebo, seed=seed, save_report=False,
                            benchmark=bm, **kw)


def test_event_benchmark_is_window_matched_and_scaled(beta_ctx):
    ctx = beta_ctx
    sc = DAILY_FAMILIES["xs_momentum"].score(ctx, {"lookback": 60, "skip": 0})
    rs = pd.Series(0.5, index=ctx.index)
    for scale in (None, rs):
        ev = build_portfolio_events(ctx, sc, 5, 8, regime_scale=scale).events
        b = benchmark_event_returns(ctx, ev, "ew_universe")
        k = len(ev) // 2
        r = ev.iloc[k]
        i, e, x = (ctx.index.get_loc(r.t0), ctx.index.get_loc(r.t_entry), ctx.index.get_loc(r.t1))
        raw = ctx.close.iloc[x] / ctx.open.iloc[e] - 1.0
        ok = ctx.universe_mask.iloc[i] & ctx.open.iloc[e].notna() & raw.notna() & (ctx.volume.iloc[e] > 0)
        s = r.exposure_scale
        cash_hold = float(np.prod(1.0 + ctx.cash_ret.iloc[e:x + 1].to_numpy()) - 1.0)
        assert b[k] == pytest.approx(s * raw[ok].mean() + (1 - s) * cash_hold)
        exc = apply_benchmark(ctx, ev, "ew_universe")
        assert exc["gross_ret"].iloc[k] == pytest.approx(r.gross_ret - b[k])
        if scale is not None:  # excess = scale*(raw - ew_raw)
            assert exc["gross_ret"].iloc[k] == pytest.approx(s * (r.raw_ret - raw[ok].mean()))
    cash = benchmark_event_returns(ctx, ev, "cash")
    assert np.allclose(cash, [np.prod(1.0 + ctx.cash_ret.iloc[ctx.index.get_loc(a):ctx.index.get_loc(c) + 1]) - 1.0
                              for a, c in zip(ev["t_entry"], ev["t1"])])
    assert apply_benchmark(ctx, ev, "none") is ev


def test_placebo_rejected_in_excess_mode_but_wins_in_absolute_mode(beta_ctx, tmp_path):
    for sd in (0, 1, 2):
        pl = _run("xs_momentum", beta_ctx, tmp_path / f"p{sd}", placebo=True, seed=sd)
        assert pl.ledger_family == "xs_momentum_daily_xs_ew__placebo"
        assert pl.reports["placeholder_commission"].verdict == "REJECTED", sd
        assert pl.verdict == "REJECTED"
    ab = _run("xs_momentum", beta_ctx, tmp_path / "abs", bm="none", placebo=True, seed=0)
    # the market drifts up: a random long-only basket earns a large positive nominal return (the bug being fixed)
    assert ab.report["scenarios"]["zero_commission"]["gross_cagr"] > 0.15


def test_pure_beta_rejected_planted_alpha_candidate_in_excess_mode(beta_ctx, alpha_ctx, tmp_path):
    beta = _run("xs_momentum", beta_ctx, tmp_path / "b")
    assert beta.reports["placeholder_commission"].verdict == "REJECTED"
    assert beta.reports["zero_commission"].verdict == "REJECTED"
    al = _run("xs_momentum", alpha_ctx, tmp_path / "a")
    z = al.reports["zero_commission"]
    assert z.gross_sharpe_annual and z.gross_sharpe_annual > 0.5
    assert z.verdict == "CANDIDATE", z.failed_criteria
    d = al.report["scenarios"]["zero_commission"]
    assert d["excess_sharpe_vs_ew"] > 0 and d["excess_cagr_vs_ew"] > 0 and d["cash_alpha_ok"] is True
    assert al.report["benchmark"] == "ew_universe"


def test_candidate_requires_positive_cash_alpha_invariant(tmp_path):
    ctx = DailyContext.from_panel(drift_panel(13, alpha=0.004, drift=-0.002), min_adv=5e6)
    r = _run("xs_momentum", ctx, tmp_path)
    for s, d in r.report["scenarios"].items():
        if d["verdict"] == "CANDIDATE":
            assert d["cash_alpha_ok"] is True
        else:
            assert d["verdict"] in ("REJECTED", "INSUFFICIENT_DATA")
    # excess over EW is positive (alpha) while the absolute NAV loses vs cash -> must not be a candidate
    d = r.report["scenarios"]["placeholder_commission"]
    if d["alpha_vs_cash_cagr"] is not None and d["alpha_vs_cash_cagr"] <= 0:
        assert d["verdict"] == "REJECTED"


def test_ledger_family_separation_and_excess_returns(alpha_ctx, tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    kw = dict(gate=CandidateGate(GateConfig(), save=False), save_report=False)
    run_family_daily("xs_momentum", alpha_ctx, (5,), GRID, 8, led, benchmark="none", **kw)
    run_family_daily("xs_momentum", alpha_ctx, (5,), GRID, 8, led, benchmark="ew_universe", **kw)
    run_family_daily("xs_momentum", alpha_ctx, (5,), GRID, 8, led, benchmark="cash", **kw)
    assert led.n_trials("xs_momentum_daily") == 6
    assert led.n_trials("xs_momentum_daily_xs_ew") == 6
    assert led.n_trials("xs_momentum_daily_xs_cash") == 6
    run_family_daily("xs_momentum", alpha_ctx, (5,), GRID, 8, led, benchmark="ew_universe", **kw)  # idempotent
    assert led.n_trials("xs_momentum_daily_xs_ew") == 6
    m_abs, m_ew = led.returns_matrix("xs_momentum_daily"), led.returns_matrix("xs_momentum_daily_xs_ew")
    assert m_abs.shape[1] == m_ew.shape[1] == 6
    assert m_abs.to_numpy().sum() > m_ew.to_numpy().sum() + 0.5  # drift removed from the evaluated stream


def test_survivor_robustness_and_report_fields(alpha_ctx, tmp_path):
    res = run_family_daily("xs_momentum", alpha_ctx, (5,), GRID, 8, TrialLedger(tmp_path / "t.sqlite"),
                           CandidateGate(GateConfig(), save=False), survivor_check=True, report_dir=tmp_path)
    sv = res.report["survivor_robustness"]
    assert "currently" in sv["warning"] and "optimistic" in sv["warning"]
    for k in ("full", "old_survivors", "ex_top_k_winners"):
        assert k in sv
    assert sv["ex_top_k_winners"]["n_symbols"] == len(alpha_ctx.symbols) - sv["top_k"]
    assert sv["full"]["excess_cagr_vs_ew"] is not None
    saved = json.loads(open(res.report_path, encoding="utf-8").read())
    assert saved["benchmark"] == "ew_universe" and "survivor_robustness" in saved
    d = saved["scenarios"]["placeholder_commission"]
    for k in ("excess_sharpe_vs_ew", "excess_cagr_vs_ew", "alpha_vs_cash_cagr", "alpha_vs_cash", "nav_net_sharpe_annual",
              "net_cagr"):
        assert k in d
    # direct call
    p = res.report["selected_params"]
    from bist_signal_bot.config.settings import get_settings
    from bist_signal_bot.edge_validation.costs_daily import DailyCostModel
    cm = DailyCostModel.from_settings(get_settings(), scenario="zero_commission")
    out = survivor_robustness(alpha_ctx, "xs_momentum", p, res.report["selected_horizon"], 8, cm, top_k=3)
    assert out["top_k"] == 3



def test_table_and_markdown_have_excess_columns():
    row = {"family": "f", "horizon": 5, "placebo": False, "error": None, "seconds": 1.0, "n_trials_ledger": 3,
           "verdicts": {"placeholder_commission": "REJECTED"}, "nav_net_sharpe": 1.0, "net_cagr": 0.3,
           "max_drawdown": -0.2, "alpha_vs_cash": 0.01, "excess_sharpe_vs_ew": 0.4, "excess_cagr_vs_ew": 0.05,
           "cash_alpha_ok": True}
    t = format_table([row])
    assert "xsSRew" in t and "0.40" in t and "aCash" in t
    md = format_markdown([row], {"benchmark": "ew_universe"})
    assert "excess Sharpe vs EW" in md and "alpha vs cash" in md


def test_cli_benchmark_flags():
    p = build_parser()
    assert p.parse_args(["run-daily", "--family", "x"]).benchmark == "ew_universe"
    assert p.parse_args(["run-daily", "--family", "x", "--benchmark", "cash"]).benchmark == "cash"
    assert p.parse_args(["run-daily-all", "--benchmark", "none", "--survivor-check"]).benchmark == "none"
    with pytest.raises(SystemExit):
        p.parse_args(["run-daily", "--family", "x", "--benchmark", "bogus"])
    with pytest.raises(ValueError):
        run_family_daily("xs_momentum", None, (5,), None, 8, None, benchmark="bogus")
