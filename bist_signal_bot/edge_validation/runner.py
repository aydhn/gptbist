"""Family runner: signals -> events -> ledger (every trial) -> best trial by net Sharpe -> gate."""
from __future__ import annotations

import itertools
import json
import zlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.costs import IntradayCostModel, liquidity_ok
from bist_signal_bot.edge_validation.gate import CandidateGate, GateReport, _day, daily_series
from bist_signal_bot.edge_validation.labels import forward_return_labels, triple_barrier_labels
from bist_signal_bot.edge_validation.signals import DEFAULT_GRIDS, SIGNAL_FUNCS
from bist_signal_bot.edge_validation import stats as st

NO_ORDER = "No real order sent."


@dataclass
class RunResult:
    family: str
    ledger_family: str
    report: GateReport
    trials: List[dict] = field(default_factory=list)
    skipped_illiquid: List[str] = field(default_factory=list)
    placebo: bool = False


def expand_grid(grid) -> List[dict]:
    if isinstance(grid, (list, tuple)):
        return [dict(g) for g in grid]
    keys = list(grid)
    return [dict(zip(keys, v)) for v in itertools.product(*[grid[k] for k in keys])]


def _valid(family: str, p: dict) -> bool:
    return not (family == "sma_trend" and p.get("fast", 0) >= p.get("slow", 1))


def _setting(settings, key, default):
    try:
        v = getattr(settings, key)
        return default if v is None else v
    except AttributeError:
        return default


def build_events(bars: pd.DataFrame, signal: np.ndarray, symbol: str, horizon_bars: int,
                 label: str, notional: float, tb_params: Optional[dict] = None) -> pd.DataFrame:
    """Decision bar (signal True) -> next-open entry events, non-overlapping per symbol."""
    cols = ["t0", "t1", "symbol", "gross_ret", "price", "order_value", "bar_value_try"]
    if label == "triple_barrier":
        tb = {"pt_mult": 2.0, "sl_mult": 2.0, "vol_window": 20, **(tb_params or {})}
        lab = triple_barrier_labels(bars, tb["pt_mult"], tb["sl_mult"], tb["vol_window"], horizon_bars)
    elif label == "forward":
        lab = forward_return_labels(bars, horizon_bars)
    else:
        raise ValueError("label must be 'forward' or 'triple_barrier'")
    if len(lab) == 0:
        return pd.DataFrame(columns=cols)
    pos = bars.index.get_indexer(lab["t0"])
    keep = signal[pos]
    lab, pos = lab[keep].reset_index(drop=True), pos[keep]
    if len(lab) == 0:
        return pd.DataFrame(columns=cols)
    # greedy non-overlap: next entry no earlier than the previous exit
    sel, last = [], None
    for i, (a, b) in enumerate(zip(lab["t0"], lab["t1"])):
        if last is None or a >= last:
            sel.append(i)
            last = b
    lab, pos = lab.iloc[sel].reset_index(drop=True), pos[sel]
    entry = bars["open"].to_numpy(float)[pos + 1]
    bar_value = bars["close"].to_numpy(float)[pos] * bars["volume"].to_numpy(float)[pos]
    return pd.DataFrame({"t0": lab["t0"], "t1": lab["t1"], "symbol": symbol,
                         "gross_ret": lab["ret"].to_numpy(float), "price": entry,
                         "order_value": float(notional), "bar_value_try": bar_value})


def _avg_daily_value(bars: pd.DataFrame) -> float:
    if len(bars) == 0:
        return float("nan")
    v = bars["close"] * bars["volume"]
    return float(v.groupby(_day(bars.index)).sum().mean())


def run_family(family: str, symbols: Sequence[str], interval: str, param_grid=None, archive=None,
               ledger=None, cost_model: Optional[IntradayCostModel] = None, horizon_bars: int = 4,
               label: str = "forward", placebo: bool = False, seed: int = 0, settings=None,
               gate: Optional[CandidateGate] = None, tb_params: Optional[dict] = None) -> RunResult:
    if family not in SIGNAL_FUNCS:
        raise ValueError(f"unknown family {family!r}; choose from {sorted(SIGNAL_FUNCS)}")
    if settings is None:
        from bist_signal_bot.config.settings import get_settings
        settings = get_settings()
    cost_model = cost_model or IntradayCostModel.from_settings(settings)
    if gate is None:
        from bist_signal_bot.edge_validation.gate import GateConfig
        gate = CandidateGate(GateConfig.from_settings(settings), settings=settings, cost_model=cost_model)
    notional = float(_setting(settings, "EDGE_NOTIONAL_TRY", 10000.0))
    min_adv = float(_setting(settings, "EDGE_MIN_AVG_DAILY_VALUE_TRY", 5e6))
    grid = expand_grid(param_grid if param_grid is not None else DEFAULT_GRIDS[family])
    grid = [p for p in grid if _valid(family, p)]
    lfam = family + "__placebo" if placebo else family
    fn = SIGNAL_FUNCS[family]

    bars_by_sym: Dict[str, pd.DataFrame] = {}
    skipped: List[str] = []
    for s in symbols:
        b = archive.read_bars(s, interval)
        if len(b) < 2:
            continue
        if not liquidity_ok(_avg_daily_value(b), min_adv):
            skipped.append(s)
            continue
        bars_by_sym[s] = b
    days = pd.DatetimeIndex(sorted(set().union(*[set(_day(b.index)) for b in bars_by_sym.values()]))) \
        if bars_by_sym else pd.DatetimeIndex([])

    events_by_trial: Dict[str, pd.DataFrame] = {}
    summaries: List[dict] = []
    best, best_sr = None, -np.inf
    most, most_n = None, -1
    for pi, p in enumerate(grid):
        tid = f"{lfam}|{interval}|{label}|h{horizon_bars}|{json.dumps(p, sort_keys=True)}|s{seed if placebo else 0}"
        frames = []
        for si, (sym, bars) in enumerate(bars_by_sym.items()):
            try:
                sig = np.asarray(fn(bars, **p), dtype=bool)
            except Exception:
                continue
            if placebo:  # same number of signals, random timing (seeded, stable per symbol/param)
                rng = np.random.default_rng([seed, pi, zlib.crc32(sym.encode())])
                sig = rng.permutation(sig)
            ev = build_events(bars, sig, sym, horizon_bars, label, notional, tb_params)
            if len(ev):
                frames.append(ev)
        ev = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
            columns=["t0", "t1", "symbol", "gross_ret", "price", "order_value", "bar_value_try"])
        n_ev = len(ev)
        info = {"trial_id": tid, "params": p, "n_events": n_ev}
        if n_ev > most_n:
            most, most_n = tid, n_ev
        events_by_trial[tid] = ev
        too_few = n_ev < gate.config.min_events
        net = gate._net(ev).dropna(subset=["net_ret"]) if n_ev else ev
        daily = daily_series(net, "net_ret", days) if len(net) and len(days) else None
        if daily is not None:
            sr = float(st.sharpe(daily.to_numpy()))
            info["net_sharpe_period"] = sr if np.isfinite(sr) else None
        if too_few or daily is None:
            info["status"] = "failed"
            ledger.record_trial(tid, family, p, interval, ",".join(bars_by_sym), None, lfam, "failed")
        else:
            info["status"] = "ok"
            ledger.record_trial(tid, family, p, interval, ",".join(bars_by_sym), daily, lfam, "ok")
            if info.get("net_sharpe_period") is not None and info["net_sharpe_period"] > best_sr:
                best, best_sr = tid, info["net_sharpe_period"]
        summaries.append(info)
    selected = best if best is not None else most
    report = gate.evaluate(lfam, selected, events_by_trial, ledger, interval, trading_days=days)
    return RunResult(family, lfam, report, summaries, skipped, placebo)
