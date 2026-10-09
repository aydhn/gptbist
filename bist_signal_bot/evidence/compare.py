"""Paper-replay vs backtest divergence measurement (research only).

Measured evidence; not a profit guarantee. No real order sent.

ALIGNMENT (what is made equal) and RESIDUAL ASSUMPTION DIFFERENCES (what cannot be) are listed in
``ASSUMPTIONS`` and written into every report.
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from bist_signal_bot.evidence.replay import ReplayResult, _as_date, load_local_frames, replay_paper

NO_ORDER = "No real order sent."
DISCLAIMER = "Ölçülmüş kanıt; kazanç garantisi değildir. No real order sent."
MIN_TRADES = 5
LOOKBACK_ROWS = 200  # PaperTradingEngine._load_frame default window; backtest strategy sees the same window

ASSUMPTIONS = [
    "Backtest runs one independent portfolio per symbol (each with the full initial capital) and the report sums "
    "their P&L onto one initial capital; paper uses ONE shared cash account, so concurrent entries can hit "
    "'Insufficient cash' in paper but never in the backtest.",
    "Sizing: paper (risk off) buys PAPER_INITIAL_CASH*10% / price (fixed notional, fractional); backtest buys "
    "10% of that symbol-portfolio's CURRENT equity (compounds per symbol), fractional shares forced on.",
    "Costs: both use TransactionCostEngine.from_settings (COMMISSION_*/SLIPPAGE_*/SPREAD_* keys; the BACKTEST_COMMISSION_RATE/"
    "BACKTEST_SLIPPAGE_RATE keys are NOT read by that engine) with no ADV/volatility input; backtest cost scenario "
    "comes from BACKTEST_COST_SCENARIO.",
    "Signals: both use StrategyEngine.run_strategy_on_data on the last 200 bars (BacktestEngine now uses that path natively; "
    "its default status filter is ACTIVE+CANDIDATE) and the backtest only trades on/after the start date (earlier bars are warm-up).",
    "Exits: PaperTradingEngine.run_once only opens positions; the replay closes via close_position when the strategy "
    "returns a non-LONG signal on an open position (same rule as the backtest's close_on_flat/opposite). Open positions "
    "are force-closed on the last day in both.",
    "Paper NEXT_OPEN_SIMULATED fills at the SAME bar's open and NEXT_CLOSE_SIMULATED at the same bar's close "
    "(engine simplification), not the following bar; backtest NEXT_OPEN/NEXT_CLOSE use the following bar.",
    "Risk engines (trade/portfolio/decision layer) are OFF in the aligned comparison unless use_risk=True; the backtest "
    "has no risk layer at all.",
    "Equity curves are compared on trading dates present in both; paper marks stale symbols at their last close.",
    "Idle-cash interest: both sides credit interest per calendar-day gap with paper.cash_interest.accrue_cash_interest "
    "(PAPER_CASH_INTEREST_ANNUAL/WITHHOLDING). The backtest runs per-symbol portfolios WITHOUT interest and credits interest "
    "once on the aggregated shared idle cash (initial cash + summed per-symbol cash deltas), mirroring paper's single account.",
]


class DivergenceReport(BaseModel):
    strategy: str
    symbols: list[str]
    start: str
    end: str
    generated_at: str
    paper_execution_mode: str
    backtest_execution_mode: str
    initial_cash: float
    use_risk: bool
    use_decision_layer: bool
    paper_trades: int
    backtest_trades: int
    matched_trades: int
    unmatched_paper: int
    unmatched_backtest: int
    entry_date_aligned_pct: Optional[float] = None
    exit_date_aligned_pct: Optional[float] = None
    entry_fill_diff_bps_mean: Optional[float] = None
    entry_fill_diff_bps_mean_abs: Optional[float] = None
    exit_fill_diff_bps_mean: Optional[float] = None
    exit_fill_diff_bps_mean_abs: Optional[float] = None
    paper_total_return_pct: float
    backtest_total_return_pct: float
    return_diff_pct_points: float
    paper_net_pnl: float
    backtest_net_pnl: float
    tracking_error_annualized_pct: Optional[float] = None
    max_equity_divergence: float
    max_equity_divergence_pct_of_capital: float
    paper_total_cost: float
    backtest_total_cost: float
    cost_diff: float
    paper_max_drawdown_pct: float
    backtest_max_drawdown_pct: float
    drawdown_diff_pct_points: float
    cash_interest_enabled: bool = False
    paper_cash_interest_total: float = 0.0
    backtest_cash_interest_total: float = 0.0
    cash_interest_diff: float = 0.0
    cash_benchmark_return_pct: float = 0.0
    paper_excess_over_cash_pct: float = 0.0
    backtest_excess_over_cash_pct: float = 0.0
    paper_return_ex_cash_pct: float = 0.0
    backtest_return_ex_cash_pct: float = 0.0
    return_diff_ex_cash_pct_points: float = 0.0
    paper_rejections: int
    paper_rejection_breakdown: dict[str, int] = Field(default_factory=dict)
    insufficient_trades: bool
    notes: list[str] = Field(default_factory=list)
    attribution: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=lambda: list(ASSUMPTIONS))
    data_gaps: list[str] = Field(default_factory=list)
    disclaimer: str = DISCLAIMER
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None


def _max_dd(eq: pd.Series) -> float:
    if eq.empty:
        return 0.0
    peak = eq.cummax()
    return float(((eq / peak) - 1).min() * 100)


def _bps(a: float, b: float) -> float:
    return (a - b) / b * 1e4 if b else float("nan")


def _stats(v: list[float]) -> tuple[Optional[float], Optional[float]]:
    v = [x for x in v if x == x]
    if not v:
        return None, None
    return float(np.mean(v)), float(np.mean(np.abs(v)))


def run_backtest_aligned(strategy: str, frames: dict[str, pd.DataFrame], start: date, end: date, settings: Any,
                         cash0: float, bt_mode: str = "SAME_CLOSE_FOR_RESEARCH_ONLY", size_pct: float = 0.10,
                         cash_interest: Optional[bool] = None, extras: Optional[dict] = None):
    """Per-symbol backtests -> (aggregate equity Series by date, trades list, total cost, issues).

    Per-symbol portfolios run with interest OFF; interest is then credited once on the aggregated shared idle cash
    (so N symbols do not earn N x interest). ``extras`` (if given) receives cash_interest_total, equity_ex_cash,
    cash_benchmark."""
    from bist_signal_bot.backtesting.cash import CashAccrual, CashParams, cash_benchmark_curve
    from bist_signal_bot.backtesting.engine import BacktestEngine
    from bist_signal_bot.backtesting.models import ExecutionPriceMode
    from bist_signal_bot.costs.engine import TransactionCostEngine
    from bist_signal_bot.strategies.engine import StrategyEngine

    se = StrategyEngine(settings=settings)
    if not se.registry.get(strategy):
        raise ValueError(f"Strategy {strategy} not found")
    eng = BacktestEngine(se, TransactionCostEngine.from_settings(settings), settings)
    eng.signal_lookback_rows = LOOKBACK_ROWS  # same window as the paper engine
    eng.trade_from = start  # bars before the evaluation window are warm-up only
    cparams = CashParams(enabled=bool(getattr(settings, "BACKTEST_CASH_INTEREST_ENABLED", True)) if cash_interest is None else bool(cash_interest),
                         annual=float(getattr(settings, "PAPER_CASH_INTEREST_ANNUAL", 0.0)),
                         withholding=float(getattr(settings, "PAPER_CASH_INTEREST_WITHHOLDING", 0.0)))
    eng.cash_interest_enabled = False  # aggregate-level accrual below
    cfg = eng.build_default_config()
    cfg.initial_capital = cash0
    cfg.execution_price_mode = ExecutionPriceMode(bt_mode)
    cfg.max_position_size_pct = size_pct
    cfg.use_fractional_shares = True
    cfg.close_open_positions_at_end = True
    cfg.close_on_flat_signal = True
    cfg.close_on_opposite_signal = True
    cfg.one_position_per_symbol = True
    cfg.min_trade_notional = 0.0

    trades, issues, total_cost, curves, cash_curves = [], [], 0.0, [], []
    prev_rl = getattr(settings, "RESEARCH_AUTO_LOG_BACKTEST", False)
    settings.RESEARCH_AUTO_LOG_BACKTEST = False  # no research-ledger side effects from evidence runs
    for sym, df in frames.items():
        d = df.loc[[i for i in df.index if pd.Timestamp(i).date() <= end]]
        pos = [k for k, i in enumerate(d.index) if pd.Timestamp(i).date() >= start]
        if not pos:
            issues.append(f"{sym}: no bars in period")
            continue
        d = d.iloc[max(0, pos[0] - LOOKBACK_ROWS):]
        try:
            r = eng.run_single_symbol(strategy, sym, d, config=cfg)
        except Exception as e:
            issues.append(f"{sym}: backtest failed: {e}")
            continue
        trades.extend(r.trades)
        issues.extend(f"{sym}: {m}" for m in r.issues)
        total_cost += float(sum(f.total_cost for f in r.fills))
        if not r.equity_curve.empty:
            eq = r.equity_curve["equity"].copy()
            eq.index = [pd.Timestamp(i).date() for i in eq.index]
            eq = eq[~eq.index.duplicated(keep="last")]
            curves.append(eq - cash0)
            ce = r.equity_curve["cash"].copy()
            ce.index = [pd.Timestamp(i).date() for i in ce.index]
            cash_curves.append(ce[~ce.index.duplicated(keep="last")] - cash0)
    settings.RESEARCH_AUTO_LOG_BACKTEST = prev_rl
    if curves:
        pnl = pd.concat(curves, axis=1).sort_index().ffill().fillna(0.0).sum(axis=1)
        cash_delta = pd.concat(cash_curves, axis=1).sort_index().ffill().fillna(0.0).sum(axis=1)
        cum, ex_cash = pd.Series(0.0, index=pnl.index), cash0 + pnl
        total_int = 0.0
        if cparams.enabled:
            acc = CashAccrual(cparams, start_date=start)
            shim = SimpleNamespace(cash=cash0)
            for d_ in pnl.index:
                shim.cash = cash0 + float(cash_delta.loc[d_]) + acc.total  # shared idle cash incl. interest so far
                acc.step(shim, d_)
                cum.loc[d_] = acc.total
            total_int = acc.total
        agg = ex_cash + cum
        if extras is not None:
            extras.update(cash_interest_total=total_int, equity_ex_cash=ex_cash,
                          cash_benchmark=cash_benchmark_curve(list(pnl.index), cash0, cparams), enabled=cparams.enabled)
    else:
        agg = pd.Series(dtype=float)
        if extras is not None:
            extras.update(cash_interest_total=0.0, equity_ex_cash=agg, cash_benchmark=pd.Series(dtype=float), enabled=cparams.enabled)
    return agg, trades, total_cost, issues


def _pair(paper: list, bt: list, tol_days: int = 0):
    """Greedy per-symbol matching of trades by entry date (|delta| <= tol_days trading-calendar days)."""
    bt_by = {}
    for t in bt:
        bt_by.setdefault(t.symbol, []).append(t)
    pairs, un_p = [], []
    used = set()
    for p in paper:
        best = None
        for k, b in enumerate(bt_by.get(p.symbol, [])):
            if (p.symbol, k) in used:
                continue
            dd = abs((_as_date(b.entry_time) - p.entry_date).days)
            if dd <= tol_days and (best is None or dd < best[0]):
                best = (dd, k, b)
        if best:
            used.add((p.symbol, best[1]))
            pairs.append((p, best[2]))
        else:
            un_p.append(p)
    un_b = [b for s, lst in bt_by.items() for k, b in enumerate(lst) if (s, k) not in used]
    return pairs, un_p, un_b


def compare_paper_backtest(
    strategy: str,
    symbols: list[str],
    start: Any,
    end: Any,
    settings: Any = None,
    paper_settings: Any = None,
    use_risk: bool = False,
    use_decision_layer: bool = False,
    execution_mode: Any = None,
    backtest_execution_mode: str = "SAME_CLOSE_FOR_RESEARCH_ONLY",
    frames: Optional[dict[str, pd.DataFrame]] = None,
    save: bool = True,
    out_dir: Optional[Path] = None,
    match_tolerance_days: int = 0,
    cash_interest: Optional[bool] = None,
) -> DivergenceReport:
    """Replay paper and run the backtest on the same symbols/period/strategy/capital; report the divergence."""
    from bist_signal_bot.config.settings import Settings
    from bist_signal_bot.paper.models import PaperExecutionMode
    from bist_signal_bot.storage.paths import get_data_dir

    settings = settings or Settings()
    paper_settings = paper_settings or settings
    execution_mode = execution_mode or PaperExecutionMode.LATEST_CLOSE_RESEARCH
    if isinstance(execution_mode, str):
        execution_mode = PaperExecutionMode(execution_mode)
    symbols = [s.upper() for s in symbols]
    start_d, end_d = _as_date(start), _as_date(end)
    frames = frames if frames is not None else load_local_frames(settings, symbols)
    frames = {s: frames[s] for s in symbols if s in frames}
    cash0 = float(paper_settings.PAPER_INITIAL_CASH)

    ci = cash_interest if cash_interest is not None else bool(getattr(settings, "BACKTEST_CASH_INTEREST_ENABLED", True))
    rep: ReplayResult = replay_paper(
        strategy, symbols, start_d, end_d, settings=paper_settings, use_decision_layer=use_decision_layer,
        execution_mode=execution_mode, frames=frames, use_trade_risk=use_risk, use_portfolio_risk=use_risk,
        close_open_at_end=True, cash_interest=ci)
    bt_extras: dict = {}
    bt_eq, bt_trades, bt_cost, bt_issues = run_backtest_aligned(
        strategy, frames, start_d, end_d, settings, cash0, backtest_execution_mode, cash_interest=ci, extras=bt_extras)

    pairs, un_p, un_b = _pair(rep.trades, bt_trades, match_tolerance_days)
    ent_bps, ex_bps, ex_ok = [], [], 0
    for p, b in pairs:
        ent_bps.append(_bps(p.entry_price, float(b.entry_price)))
        if p.closed and b.exit_time is not None:
            ex_bps.append(_bps(p.exit_price, float(b.exit_price)))
            ex_ok += int(p.exit_date == _as_date(b.exit_time))
    ent_m, ent_a = _stats(ent_bps)
    ex_m, ex_a = _stats(ex_bps)

    pe = rep.equity_curve["equity"] if not rep.equity_curve.empty else pd.Series(dtype=float)
    pe = pe.copy()
    common = sorted(set(pe.index) & set(bt_eq.index))
    te = None
    maxdiv = 0.0
    if len(common) > 2:
        a, b = pe.loc[common], bt_eq.loc[common]
        maxdiv = float((a - b).abs().max())
        dr = a.pct_change().dropna() - b.pct_change().dropna()
        te = float(dr.std(ddof=1) * math.sqrt(252) * 100) if len(dr) > 1 else None
    p_final = float(pe.iloc[-1]) if len(pe) else cash0
    b_final = float(bt_eq.iloc[-1]) if len(bt_eq) else cash0
    p_ret, b_ret = (p_final / cash0 - 1) * 100, (b_final / cash0 - 1) * 100
    p_dd, b_dd = _max_dd(pe), _max_dd(bt_eq)
    p_int, b_int = float(rep.cash_interest_total), float(bt_extras.get("cash_interest_total", 0.0))
    bench = rep.cash_benchmark if len(rep.cash_benchmark) else bt_extras.get("cash_benchmark", pd.Series(dtype=float))
    bench_ret = (float(bench.iloc[-1]) / cash0 - 1) * 100 if len(bench) else 0.0
    p_ex, b_ex = p_ret - p_int / cash0 * 100, b_ret - b_int / cash0 * 100

    breakdown: dict[str, int] = {}
    for r in rep.rejections:
        breakdown[r["stage"]] = breakdown.get(r["stage"], 0) + 1

    insufficient = len(rep.trades) < MIN_TRADES and len(bt_trades) < MIN_TRADES
    notes, attr = [], []
    if insufficient:
        notes.append("insufficient trades for a meaningful comparison")
    notes.extend(f"backtest: {m}" for m in bt_issues[:5])
    notes.extend(rep.issues[:5])
    if rep.execution_mode != "LATEST_CLOSE_RESEARCH" or backtest_execution_mode != "SAME_CLOSE_FOR_RESEARCH_ONLY":
        attr.append(f"execution price mode: paper={rep.execution_mode} vs backtest={backtest_execution_mode}")
    if ci:
        attr.append(f"cash interest: paper {p_int:.2f} vs backtest {b_int:.2f} (diff {p_int - b_int:+.2f} = {(p_int - b_int) / cash0 * 100:+.4f} pp of capital; "
                    f"cash-only benchmark {bench_ret:.2f}%, alpha over cash paper {p_ret - bench_ret:+.2f} pp / backtest {b_ret - bench_ret:+.2f} pp); "
                    f"return diff ex-cash {p_ex - b_ex:+.2f} pp")
    else:
        attr.append("cash interest OFF on both sides (idle cash earns nothing)")
    if abs(rep.total_costs - bt_cost) > max(1.0, 0.02 * max(bt_cost, 1.0)):
        attr.append(f"costs: paper {rep.total_costs:.2f} vs backtest {bt_cost:.2f} (cost settings/scenario differ)")
    if breakdown.get("execution"):
        attr.append(f"sizing/cash: {breakdown['execution']} paper entries rejected at execution (shared-cash account; backtest has per-symbol capital)")
    if breakdown.get("risk_engine_error") or use_risk:
        attr.append(f"risk filters: use_risk={use_risk}; {breakdown.get('risk_engine_error', 0)} risk-engine errors, "
                    f"{breakdown.get('trade_risk', 0)} trade-risk and {breakdown.get('portfolio_risk', 0)} portfolio rejections")
    if use_decision_layer:
        attr.append(f"decision layer ON ({breakdown.get('decision_layer', 0)} blocked entries); backtest has no such layer")
    if un_p or un_b:
        attr.append(f"unmatched trades: {len(un_p)} paper-only, {len(un_b)} backtest-only (signal/universe/timing differences)")
    miss = [s for s in symbols if s not in frames]
    gaps = [f"no local data: {', '.join(miss)}"] if miss else []
    if gaps:
        attr.append("universe/data gaps: " + gaps[0])
    attr.append("structural (always present): per-symbol backtest capital vs shared paper cash; compounding vs fixed-notional sizing; see assumptions")

    n = len(pairs)
    rpt = DivergenceReport(
        strategy=strategy, symbols=symbols, start=str(start_d), end=str(end_d), generated_at=datetime.now().isoformat(timespec="seconds"),
        paper_execution_mode=rep.execution_mode, backtest_execution_mode=backtest_execution_mode, initial_cash=cash0,
        use_risk=use_risk, use_decision_layer=use_decision_layer,
        paper_trades=len(rep.trades), backtest_trades=len(bt_trades), matched_trades=n,
        unmatched_paper=len(un_p), unmatched_backtest=len(un_b),
        entry_date_aligned_pct=(100.0 * n / max(len(rep.trades), len(bt_trades))) if (rep.trades or bt_trades) else None,
        exit_date_aligned_pct=(100.0 * ex_ok / n) if n else None,
        entry_fill_diff_bps_mean=ent_m, entry_fill_diff_bps_mean_abs=ent_a,
        exit_fill_diff_bps_mean=ex_m, exit_fill_diff_bps_mean_abs=ex_a,
        paper_total_return_pct=p_ret, backtest_total_return_pct=b_ret, return_diff_pct_points=p_ret - b_ret,
        paper_net_pnl=p_final - cash0, backtest_net_pnl=b_final - cash0,
        tracking_error_annualized_pct=te, max_equity_divergence=maxdiv,
        max_equity_divergence_pct_of_capital=maxdiv / cash0 * 100,
        paper_total_cost=rep.total_costs, backtest_total_cost=bt_cost, cost_diff=rep.total_costs - bt_cost,
        paper_max_drawdown_pct=p_dd, backtest_max_drawdown_pct=b_dd, drawdown_diff_pct_points=p_dd - b_dd,
        cash_interest_enabled=bool(ci), paper_cash_interest_total=p_int, backtest_cash_interest_total=b_int,
        cash_interest_diff=p_int - b_int, cash_benchmark_return_pct=bench_ret,
        paper_excess_over_cash_pct=p_ret - bench_ret, backtest_excess_over_cash_pct=b_ret - bench_ret,
        paper_return_ex_cash_pct=p_ex, backtest_return_ex_cash_pct=b_ex, return_diff_ex_cash_pct_points=p_ex - b_ex,
        paper_rejections=len(rep.rejections), paper_rejection_breakdown=breakdown,
        insufficient_trades=insufficient, notes=notes, attribution=attr, data_gaps=gaps)
    if save:
        save_report(rpt, out_dir or (get_data_dir(settings) / "evidence"))
    return rpt


def save_report(rpt: DivergenceReport, out_dir: Path) -> DivergenceReport:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    jp, mp = out_dir / f"divergence_{ts}.json", out_dir / f"divergence_{ts}.md"
    rpt.json_path, rpt.markdown_path = str(jp), str(mp)
    jp.write_text(json.dumps(rpt.model_dump(), indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    mp.write_text(to_markdown(rpt), encoding="utf-8")
    return rpt


def _f(x: Any, nd: int = 2) -> str:
    return "n/a" if x is None else f"{x:.{nd}f}"


def to_markdown(r: DivergenceReport) -> str:
    L = [f"# Paper vs Backtest divergence: {r.strategy}", "",
         f"Period {r.start} .. {r.end}; {len(r.symbols)} symbols; paper mode {r.paper_execution_mode}; backtest mode {r.backtest_execution_mode}; "
         f"risk={'on' if r.use_risk else 'off'}; decision layer={'on' if r.use_decision_layer else 'off'}", ""]
    if r.insufficient_trades:
        L += ["**insufficient trades for a meaningful comparison** (both sides < 5 trades)", ""]
    L += ["| metric | paper | backtest | diff |", "|---|---|---|---|",
          f"| trades | {r.paper_trades} | {r.backtest_trades} | matched {r.matched_trades} |",
          f"| total return % | {_f(r.paper_total_return_pct)} | {_f(r.backtest_total_return_pct)} | {_f(r.return_diff_pct_points)} pp |",
          f"| net P&L | {_f(r.paper_net_pnl)} | {_f(r.backtest_net_pnl)} | {_f(r.paper_net_pnl - r.backtest_net_pnl)} |",
          f"| total cost | {_f(r.paper_total_cost)} | {_f(r.backtest_total_cost)} | {_f(r.cost_diff)} |",
          f"| max drawdown % | {_f(r.paper_max_drawdown_pct)} | {_f(r.backtest_max_drawdown_pct)} | {_f(r.drawdown_diff_pct_points)} pp |",
          f"| cash interest | {_f(r.paper_cash_interest_total)} | {_f(r.backtest_cash_interest_total)} | {_f(r.cash_interest_diff)} |",
          f"| return ex-cash % | {_f(r.paper_return_ex_cash_pct)} | {_f(r.backtest_return_ex_cash_pct)} | {_f(r.return_diff_ex_cash_pct_points)} pp |",
          f"| alpha over cash (pp) | {_f(r.paper_excess_over_cash_pct)} | {_f(r.backtest_excess_over_cash_pct)} | cash benchmark {_f(r.cash_benchmark_return_pct)}% |",
          "", f"- entry date aligned: {_f(r.entry_date_aligned_pct, 1)}%; exit date aligned (of matched): {_f(r.exit_date_aligned_pct, 1)}%",
          f"- fill diff bps (paper-backtest) entry mean {_f(r.entry_fill_diff_bps_mean)} / abs {_f(r.entry_fill_diff_bps_mean_abs)}; "
          f"exit mean {_f(r.exit_fill_diff_bps_mean)} / abs {_f(r.exit_fill_diff_bps_mean_abs)}",
          f"- tracking error (annualized) {_f(r.tracking_error_annualized_pct)}%; max equity divergence {_f(r.max_equity_divergence)} "
          f"({_f(r.max_equity_divergence_pct_of_capital)}% of capital)",
          f"- paper rejections {r.paper_rejections} {r.paper_rejection_breakdown}", "", "## Attribution"]
    L += [f"- {a}" for a in r.attribution] + ["", "## Notes"] + [f"- {n}" for n in r.notes]
    L += ["", "## Residual assumption differences"] + [f"- {a}" for a in r.assumptions] + ["", r.disclaimer, ""]
    return "\n".join(L)
