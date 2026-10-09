"""Evidence replay/compare tests. Offline, synthetic bars. Paper only. No real order sent."""
import json
from datetime import date
from types import SimpleNamespace

import numpy as np
import pandas as pd

from bist_signal_bot.evidence.compare import compare_paper_backtest
from bist_signal_bot.evidence.replay import replay_paper

START, END = date(2024, 9, 2), date(2025, 3, 31)


def _frame(seed=0, n=420, flat=False):
    idx = pd.bdate_range("2023-06-01", periods=n)
    t = np.arange(n)
    close = np.full(n, 100.0) if flat else 100 + 0.08 * t + 12 * np.sin(t / 14 + seed)
    return pd.DataFrame({"open": np.r_[close[0], close[:-1]], "high": close + 1, "low": close - 1,
                         "close": close, "volume": np.full(n, 1e6)}, index=idx)


def _frames(flat=False):
    return {"AAA": _frame(0, flat=flat), "BBB": _frame(1.5, flat=flat)}


def test_replay_point_in_time_future_mutation_irrelevant(settings_factory):
    s = settings_factory()
    base = _frames()
    mut = {k: v.copy() for k, v in base.items()}
    for v in mut.values():
        v.loc[v.index > pd.Timestamp(END), ["open", "high", "low", "close"]] *= 7.0
    a = replay_paper("moving_average_trend", ["AAA", "BBB"], START, END, settings=s, frames=base, use_trade_risk=False, use_portfolio_risk=False)
    b = replay_paper("moving_average_trend", ["AAA", "BBB"], START, END, settings=s, frames=mut, use_trade_risk=False, use_portfolio_risk=False)
    assert len(a.trades) > 0
    pd.testing.assert_frame_equal(a.equity_curve, b.equity_curve)
    assert [(t.symbol, t.entry_date, t.entry_price) for t in a.trades] == [(t.symbol, t.entry_date, t.entry_price) for t in b.trades]
    assert a.disclaimer == "No real order sent."


def test_replay_isolated_and_deterministic(settings_factory, tmp_data_dir):
    s = settings_factory()
    kw = dict(settings=s, frames=_frames(), use_trade_risk=False, use_portfolio_risk=False)
    a = replay_paper("moving_average_trend", ["AAA", "BBB"], START, END, **kw)
    b = replay_paper("moving_average_trend", ["AAA", "BBB"], START, END, **kw)
    pd.testing.assert_frame_equal(a.equity_curve, b.equity_curve)
    assert a.equity_curve["equity"].iloc[0] > 0 and abs(a.initial_cash - float(s.PAPER_INITIAL_CASH)) < 1e-9
    assert not list(tmp_data_dir.rglob("ledger.json"))  # ledger lived in a temp dir


def test_compare_aligned_matches_and_saves_json(settings_factory, tmp_data_dir):
    s = settings_factory()
    r = compare_paper_backtest("moving_average_trend", ["AAA", "BBB"], START, END, settings=s, frames=_frames())
    assert r.paper_trades >= 1 and r.matched_trades >= 1
    assert r.entry_date_aligned_pct and r.entry_date_aligned_pct > 50
    assert abs(r.entry_fill_diff_bps_mean_abs or 0) < 1e-6
    assert abs(r.cost_diff) < 0.05 * max(r.backtest_total_cost, 1)
    assert r.tracking_error_annualized_pct is not None and r.tracking_error_annualized_pct < 2.0
    assert "kazanç garantisi değildir" in r.disclaimer and "No real order sent." in r.disclaimer
    p = tmp_data_dir / "evidence"
    js = list(p.glob("divergence_*.json"))
    assert js and list(p.glob("divergence_*.md"))
    assert json.loads(js[0].read_text(encoding="utf-8"))["strategy"] == "moving_average_trend"


def test_compare_shows_divergence_for_other_mode_and_higher_costs(settings_factory):
    s = settings_factory()
    fr = {"AAA": _frame(0)}
    base = compare_paper_backtest("moving_average_trend", ["AAA"], START, END, settings=s, frames=fr, save=False)
    mode = compare_paper_backtest("moving_average_trend", ["AAA"], START, END, settings=s, frames=fr, save=False,
                                  execution_mode="NEXT_OPEN_SIMULATED")
    assert (mode.entry_fill_diff_bps_mean_abs or 0) > 1.0
    assert any("execution price mode" in a for a in mode.attribution)
    costly = compare_paper_backtest("moving_average_trend", ["AAA"], START, END, settings=s, frames=fr, save=False,
                                    paper_settings=settings_factory(COMMISSION_BPS=80.0))
    assert costly.cost_diff > base.cost_diff + 1.0
    assert costly.return_diff_pct_points < base.return_diff_pct_points


def test_compare_insufficient_trades(settings_factory):
    r = compare_paper_backtest("moving_average_trend", ["AAA"], START, END, settings=settings_factory(),
                               frames={"AAA": _frame(0, flat=True)}, save=False)
    assert r.insufficient_trades and "insufficient trades for a meaningful comparison" in r.notes


def test_as_of_default_off_equivalence(settings_factory):
    from bist_signal_bot.paper.engine import PaperTradingDependencies, PaperTradingEngine
    from bist_signal_bot.paper.models import PaperRunRequest
    df = _frame(0)
    svc = SimpleNamespace(get_data=lambda sym, src, tf, rows=200: df.tail(rows))
    eng = PaperTradingEngine(PaperTradingDependencies(ledger_store=SimpleNamespace(), strategy_engine=SimpleNamespace(),
                                                      data_service=svc, settings=settings_factory()))
    req = PaperRunRequest(account_id="x", symbols=["AAA"], strategy_name="s", source="local", timeframe="1d")
    pd.testing.assert_frame_equal(eng._load_frame("AAA", req), eng._load_frame_raw("AAA", req))
    eng.as_of = pd.Timestamp("2024-06-03 23:59:59")
    cut = eng._load_frame("AAA", req)
    assert cut.index[-1] <= pd.Timestamp("2024-06-03") and len(cut) <= 200
