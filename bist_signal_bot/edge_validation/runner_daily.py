"""Daily cross-sectional family runner: ScoreFamily -> portfolio events -> ledger (EVERY trial) -> best trial by
in-sample net Sharpe -> CandidateGate under both cost scenarios. Research/paper only; no real order is sent.

How the gate sees overlapping positions (IMPORTANT):
  * Baskets never overlap (rebalance_every >= horizon). Each basket = up to top_n events that share t0 and t1.
  * ``gate.daily_series`` buckets events by their EXIT day t1 and takes the MEAN per-event return that day, zero on
    all other days. So the gate's "daily" series is sparse (one non-zero day per basket, ~1/horizon of days); its
    Sharpe is NOT the portfolio's NAV Sharpe. The ledger stores this same series (so DSR's trial-Sharpe variance
    and the strategy Sharpe are on the same scale). The report adds the portfolio-level NAV Sharpe (daily NAV
    returns, idle cash earning the cash rate, costs deducted at exit) as an independent cross-check.
  * Common evaluation window: starts at the latest first-rebalance among all trials (so long-lookback trials are
    not penalised by warm-up zeros); events before it are discarded for every trial.
  * Candidacy verdict = placeholder_commission scenario. zero_commission is upside information only.
  * The ledger counts each (params, horizon) trial ONCE (never per scenario).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation import stats as st
from bist_signal_bot.edge_validation.cash_benchmark import alpha_over_cash
from bist_signal_bot.edge_validation.costs_daily import SCENARIOS, DailyCostModel
from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
from bist_signal_bot.edge_validation.gate import CandidateGate, GateConfig, GateReport, _day, daily_series
from bist_signal_bot.edge_validation.runner import expand_grid
from bist_signal_bot.edge_validation.xsection import (NO_ORDER, SURVIVORSHIP_WARNING, DailyContext,
                                                      build_portfolio_events, nav_returns)

INTERVAL_LABEL = "1d"
PRIMARY = "placeholder_commission"
ANN = 252.0


@dataclass
class DailyRunResult:
    family: str
    ledger_family: str
    selected_trial_id: Optional[str]
    reports: Dict[str, GateReport]
    trials: List[dict] = field(default_factory=list)
    report: dict = field(default_factory=dict)
    report_path: Optional[str] = None
    placebo: bool = False

    @property
    def verdict(self) -> str:
        return self.reports[self.report["candidacy_scenario"]].verdict


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return float(o) if math.isfinite(float(o)) else None
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


def _ann_sharpe(r: pd.Series) -> Optional[float]:
    r = r.dropna()
    sd = r.std(ddof=1) if len(r) > 2 else float("nan")
    return float(r.mean() / sd * math.sqrt(ANN)) if sd and sd > 0 else None


def _nav_stats(r: pd.Series, bench: pd.DataFrame) -> dict:
    nav = (1.0 + r).cumprod()
    n = len(r)
    cagr = float(nav.iloc[-1] ** (ANN / n) - 1.0) if n > 1 and nav.iloc[-1] > 0 else None
    dd = float((nav / nav.cummax() - 1.0).min()) if n else None
    out = {"n_days": n, "total_return": float(nav.iloc[-1] - 1.0) if n else None, "cagr": cagr,
           "max_drawdown": dd, "sharpe_annual": _ann_sharpe(r)}
    for name, key in (("cash", "alpha_vs_cash"), ("xu100", "alpha_vs_xu100"), ("ew_universe", "alpha_vs_ew_universe")):
        if name in bench:
            b = bench[name].reindex(r.index)
            out[key] = alpha_over_cash(r, b.fillna(0.0) if name != "xu100" else b.dropna())
            out[key + "_cagr"] = (None if cagr is None else
                                  cagr - float((1 + b.fillna(0.0)).prod() ** (ANN / n) - 1.0))
    return out


def _setting(settings, key, default):
    try:
        v = getattr(settings, key)
        return default if v is None else v
    except AttributeError:
        return default


def run_family_daily(family, ctx: DailyContext, horizons: Sequence[int], param_grid=None, top_n: int = 8,
                     ledger=None, gate: Optional[CandidateGate] = None,
                     scenarios: Sequence[str] = ("placeholder_commission", "zero_commission"),
                     placebo: bool = False, seed: int = 0, settings=None,
                     regime_scale: Optional[pd.Series] = None, save_report: bool = True,
                     report_dir=None, cost_models: Optional[Dict[str, DailyCostModel]] = None) -> DailyRunResult:
    fam = DAILY_FAMILIES[family] if isinstance(family, str) else family
    if isinstance(family, str) and family not in DAILY_FAMILIES:
        raise ValueError(f"unknown daily family {family!r}; choose from {sorted(DAILY_FAMILIES)}")
    scenarios = tuple(scenarios)
    for s in scenarios:
        if s not in SCENARIOS:
            raise ValueError(f"scenario must be in {SCENARIOS}, got {s!r}")
    if not scenarios or ledger is None:
        raise ValueError("need >=1 scenario and a TrialLedger (every trial must be recorded)")
    if settings is None:
        from bist_signal_bot.config.settings import get_settings
        settings = get_settings()
    cfg = gate.config if gate is not None else GateConfig.from_settings(settings)
    primary = PRIMARY if PRIMARY in scenarios else scenarios[0]
    cms = {s: (cost_models or {}).get(s) or DailyCostModel.from_settings(settings, scenario=s) for s in scenarios}
    gates = {s: CandidateGate(cfg, settings=settings, cost_model=cms[s], save=False) for s in scenarios}
    lfam = fam.name + "_daily" + ("__placebo" if placebo else "")
    rs_tag = "rs" if regime_scale is not None else "nors"
    grid_params = [p for p in expand_grid(param_grid if param_grid is not None else fam.default_grid)
                   if fam.valid(p)]

    # 1) build every trial's events (nothing is skipped silently: all combos go to the ledger)
    trials: List[dict] = []
    score_cache: Dict[int, pd.DataFrame] = {}
    mask_cache: Dict[int, Optional[pd.Series]] = {}
    for pi, p in enumerate(grid_params):
        for h in horizons:
            tid = (f"{lfam}|{INTERVAL_LABEL}|u{len(ctx.symbols)}|h{int(h)}|top{int(top_n)}|{rs_tag}|"
                   f"{json.dumps(p, sort_keys=True)}|s{seed if placebo else 0}")
            info = {"trial_id": tid, "params": p, "horizon": int(h), "events": None, "n_events": 0, "error": None}
            try:
                if pi not in score_cache:
                    sc = fam.score(ctx, p).reindex(index=ctx.index, columns=ctx.symbols)
                    if placebo:  # random scores, same eligibility pattern as the real family
                        rng = np.random.default_rng([int(seed), pi])
                        S = sc.to_numpy(float)
                        sc = pd.DataFrame(np.where(np.isfinite(S), rng.random(S.shape), np.nan),
                                          index=sc.index, columns=sc.columns)
                    score_cache[pi] = sc
                    mfn = getattr(fam, "rebalance_mask", None)  # optional timing mask (calendar families)
                    mask_cache[pi] = mfn(ctx, p) if callable(mfn) else None
                pr = build_portfolio_events(ctx, score_cache[pi], int(h), top_n, regime_scale=regime_scale,
                                            rebalance_mask=mask_cache[pi])
                info["events"], info["n_events"] = pr.events, len(pr.events)
            except Exception as exc:  # recorded as a failed trial, still counts toward N
                info["error"] = f"{type(exc).__name__}: {exc}"
            trials.append(info)

    # 2) common window
    firsts = [pd.Timestamp(t["events"]["t0"].min()) for t in trials if t["n_events"]]
    lasts = [pd.Timestamp(t["events"]["t1"].max()) for t in trials if t["n_events"]]
    if firsts:
        start, end = max(firsts), max(lasts)
        win = ctx.index[(ctx.index >= start) & (ctx.index <= end)]
    else:
        win = ctx.index
    gdays = _day(win)

    # 3) per-trial net series (primary scenario), ledger, selection
    events_by_trial: Dict[str, pd.DataFrame] = {}
    best, best_sr, most, most_n = None, -np.inf, None, -1
    for t in trials:
        ev = t["events"]
        if ev is not None and len(ev):
            ev = ev[ev["t0"] >= win[0]].reset_index(drop=True) if len(win) else ev
        else:
            ev = pd.DataFrame(columns=["t0", "t1", "symbol", "gross_ret", "price", "order_value", "bar_value_try"])
        t["events"], t["n_events"] = ev, len(ev)
        events_by_trial[t["trial_id"]] = ev
        if t["n_events"] > most_n:
            most, most_n = t["trial_id"], t["n_events"]
        net = gates[primary]._net(ev).dropna(subset=["net_ret"]) if len(ev) else ev
        daily = daily_series(net, "net_ret", gdays) if len(net) and len(gdays) else None
        if daily is not None:
            sr = float(st.sharpe(daily.to_numpy()))
            t["net_sharpe_period"] = sr if np.isfinite(sr) else None
        too_few = t["n_events"] < cfg.min_events
        ok = daily is not None and not too_few and t["error"] is None
        t["status"] = "ok" if ok else "failed"
        ledger.record_trial(t["trial_id"], fam.name, t["params"], INTERVAL_LABEL,
                            f"daily_panel[{len(ctx.symbols)}]|h{t['horizon']}|top{top_n}|{rs_tag}",
                            daily if ok else None, lfam, t["status"])
        if ok and t.get("net_sharpe_period") is not None and t["net_sharpe_period"] > best_sr:
            best, best_sr = t["trial_id"], t["net_sharpe_period"]
    selected = best if best is not None else most

    # 4) gate under every scenario (same selected trial, same ledger count)
    reports = {s: gates[s].evaluate(lfam, selected, events_by_trial, ledger, INTERVAL_LABEL, trading_days=win)
               for s in scenarios}

    # 5) portfolio-level metrics for the selected trial
    sel = next((t for t in trials if t["trial_id"] == selected), None)
    bench = ctx.benchmarks().reindex(win) if len(win) else ctx.benchmarks()
    scen_out: Dict[str, dict] = {}
    for s in scenarios:
        rep = reports[s]
        d = {"verdict": rep.verdict, "failed_criteria": rep.failed_criteria,
             "gate_net_sharpe_annual": rep.net_sharpe_annual, "gate_gross_sharpe_annual": rep.gross_sharpe_annual,
             "dsr": rep.dsr, "pbo": rep.pbo, "reality_check_p": rep.reality_check_p,
             "selected_p_bh": rep.selected_p_bh, "positive_path_fraction": rep.positive_path_fraction,
             "n_events": rep.n_events, "n_events_disallowed": rep.n_events_disallowed}
        if sel is not None and sel["n_events"]:
            ev = sel["events"]
            netev = gates[s]._net(ev)
            valid = netev.dropna(subset=["net_ret"])
            navn = nav_returns(ctx, ev, cms[s]).reindex(win)
            navg = nav_returns(ctx, ev, None).reindex(win)
            ns, gs = _nav_stats(navn["ret"], bench), _nav_stats(navg["ret"], bench)
            years = max(len(win) / ANN, 1e-9)
            d.update({
                "nav_net": ns, "nav_gross": gs,
                "nav_net_sharpe_annual": ns["sharpe_annual"], "nav_gross_sharpe_annual": gs["sharpe_annual"],
                "net_cagr": ns["cagr"], "gross_cagr": gs["cagr"], "max_drawdown": ns["max_drawdown"],
                "cost_drag_bps_per_year": (None if ns["cagr"] is None or gs["cagr"] is None
                                           else (gs["cagr"] - ns["cagr"]) * 1e4),
                "avg_round_trip_cost_bps": float((valid["gross_ret"] - valid["net_ret"]).mean() * 1e4)
                if len(valid) else None,
                "turnover_two_way_per_year": float(2.0 * valid["order_value"].sum() / ctx.capital / years),
                "avg_holdings": float(navn["holdings"].mean()),
                "avg_invested_fraction": float(navn["invested_frac"].mean()),
                "alpha_vs_cash": ns.get("alpha_vs_cash"), "alpha_vs_xu100": ns.get("alpha_vs_xu100"),
                "alpha_vs_ew_universe": ns.get("alpha_vs_ew_universe"),
            })
        scen_out[s] = d

    cand = scen_out[primary]
    report = reports[primary].model_dump(mode="json")
    report.update({
        "family": lfam, "interval": INTERVAL_LABEL,
        "candidacy_scenario": primary, "scenarios": scen_out,
        "zero_commission_is_upside_only": True,
        "selected_params": sel["params"] if sel else None, "selected_horizon": sel["horizon"] if sel else None,
        "top_n": top_n, "capital_try": ctx.capital, "long_only": True, "regime_scale": regime_scale is not None,
        "placebo": placebo, "seed": seed, "n_trials_ledger": ledger.n_trials(lfam),
        "window": [str(win[0].date()), str(win[-1].date())] if len(win) else None,
        "n_symbols": len(ctx.symbols),
        "benchmark_returns_total": {k: float((1 + bench[k].fillna(0.0)).prod() - 1.0) for k in bench},
        "cash_rate_annual": ctx.cash_rate,
        "trials": [{k: t.get(k) for k in ("trial_id", "params", "horizon", "n_events", "status",
                                          "net_sharpe_period", "error")} for t in trials],
        "survivorship_warning": SURVIVORSHIP_WARNING,
        "overlap_note": ("Gate daily series = mean event return per exit day t1 (sparse, baskets do not overlap); "
                         "nav_* fields are the portfolio-level daily NAV cross-check. Window starts at the latest "
                         "first rebalance among trials."),
        "no_order": NO_ORDER,
    })
    report = _clean(report)
    path = None
    if save_report:
        if report_dir is None:
            from bist_signal_bot.storage.paths import get_edge_validation_dir
            report_dir = get_edge_validation_dir(settings) / "reports"
        report_dir = __import__("pathlib").Path(report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        path = report_dir / f"{lfam}_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.json"
        report["report_path"] = str(path)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for t in trials:
        t.pop("events", None)
    return DailyRunResult(fam.name, lfam, selected, reports, trials, report, str(path) if path else None, placebo)
