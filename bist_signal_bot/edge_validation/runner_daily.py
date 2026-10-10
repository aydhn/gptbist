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

Benchmark modes (``benchmark=``), the statistic the gate evaluates:
  * 'ew_universe' (DEFAULT, primary candidacy): event return minus the equal-weight raw return of the same
    point-in-time eligible universe over the identical t_entry(open)..t1(close) window (scaled with the event's regime
    exposure; remainder at cash). A candidate must ALSO beat cash at NAV level (alpha_vs_cash_cagr > 0) else REJECTED
    with failed criterion ``cash_alpha_nav``.
  * 'cash': event return minus cash accrued over the same window.
  * 'none': absolute return vs zero (legacy; NOT credible evidence in a high-inflation market: random long-only picks
    earn positive nominal returns).
  Costs are applied on top of the excess return (strategy leg only); the benchmark leg is frictionless, which is
  conservative for the strategy. Excess trials are recorded under a separate ledger family
  (``<fam>_daily_xs_ew`` / ``_xs_cash``) with the excess daily series as trial returns, so DSR/PBO/N refer to the same
  statistic that is evaluated. Existing ledger rows are never touched.

Robust (v2) mode (``robust=True``, DEFAULT, only with benchmark 'ew_universe'): the selected trial must ALSO pass
``robustness.robustness_report`` (top-event trim, top-symbol drop, calendar-year stability, 2x cost stress, event cap,
gating global-multiplicity DSR; top-20 breadth informational) under each cost scenario, else verdict REJECTED with
failed criteria ``robust:<name>``. v2 trials go to a NEW ledger family (``<fam>`` + ``LEDGER_SUFFIX_V2``,
``_daily_xs_ew2``) so rows of the old statistic are never conflated; ML trial ids carry FEATURES_VERSION.
``robust=False`` reproduces the legacy behaviour exactly. The gate itself is never loosened.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from bist_signal_bot.core.logging_setup import get_logger
from bist_signal_bot.edge_validation import stats as st
from bist_signal_bot.edge_validation import xsection as _xs
from bist_signal_bot.edge_validation.cash_benchmark import alpha_over_cash
from bist_signal_bot.edge_validation.costs_daily import SCENARIOS, DailyCostModel
from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
from bist_signal_bot.edge_validation.gate import CandidateGate, GateConfig, GateReport, _day, daily_series
from bist_signal_bot.edge_validation.runner import expand_grid
from bist_signal_bot.edge_validation.xsection import (LEDGER_SUFFIX, NO_ORDER, SURVIVORSHIP_WARNING, DailyContext,
                                                      apply_benchmark, build_portfolio_events,
                                                      check_benchmark_mode, nav_returns, subset_ctx)

logger = get_logger(__name__)
LEDGER_SUFFIX_V2 = getattr(_xs, "LEDGER_SUFFIX_V2", "_daily_xs_ew2")  # new ledger family of the robust statistic
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
                     report_dir=None, cost_models: Optional[Dict[str, DailyCostModel]] = None,
                     benchmark: str = "ew_universe", survivor_check: bool = False,
                     robust: bool = True, robust_config=None, global_gate: str = "live",
                     snapshot_rowid: Optional[int] = None, min_adv: Optional[float] = None,
                     fixed_primary: Optional[dict] = None, grid_tag: Optional[str] = None) -> DailyRunResult:
    """``min_adv`` (TRY, None = ctx default/unchanged behaviour) sets the point-in-time eligibility ADV threshold
    (liquid-universe trials). It is encoded in the ledger family (``<fam>_adv5e+07_daily_xs_ew2``: still ends with the
    v2 suffix so the trials count toward the global pool N), the trial ids and the ``universe`` string."""
    fam = DAILY_FAMILIES[family] if isinstance(family, str) else family
    adv_tag = ""
    if min_adv is not None:
        min_adv = float(min_adv)
        adv_tag = f"adv{min_adv:.0e}"
        if float(ctx.min_adv) != min_adv:  # shallow copy: shares price matrices, own (lazily rebuilt) eligibility mask
            import copy
            ctx = copy.copy(ctx)
            ctx.min_adv = min_adv
            ctx._mask = None
    if isinstance(family, str) and family not in DAILY_FAMILIES:
        raise ValueError(f"unknown daily family {family!r}; choose from {sorted(DAILY_FAMILIES)}")
    check_benchmark_mode(benchmark)
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
    if global_gate not in ("live", "deferred"):
        raise ValueError("global_gate must be 'live' or 'deferred'")
    min_univ = int(_setting(settings, "GLOBAL_POOL_MIN_UNIVERSE", 100) or 0)
    robust_on = bool(robust) and benchmark == "ew_universe"  # robustness is defined for the excess-vs-EW statistic
    lfam = (fam.name + (f"_{adv_tag}" if adv_tag else "")
            + (LEDGER_SUFFIX_V2 if robust_on else "_daily" + LEDGER_SUFFIX[benchmark])
            + ("__placebo" if placebo else ""))
    fv_tag = ""
    if getattr(fam, "needs_horizon", False):  # ML families depend on the feature set: keep ledger rows apart
        from bist_signal_bot.model_loop.daily_features import FEATURES_VERSION
        fv_tag = f"|fv{FEATURES_VERSION}"
    rs_tag = "rs" if regime_scale is not None else "nors"
    grid_params = [p for p in expand_grid(param_grid if param_grid is not None else fam.default_grid)
                   if fam.valid(p)]

    n_sym = len(ctx.symbols)
    univ_tag = f"daily_panel[{n_sym}]" + (f"|{adv_tag}" if adv_tag else "")
    if n_sym < min_univ and not getattr(ledger, "smoke", False):
        univ_tag += "|SMALL_UNIVERSE"  # excluded from the global pool; marked so it can be audited
        logger.warning("writing %d-symbol trials (< GLOBAL_POOL_MIN_UNIVERSE=%d) to the non-smoke ledger %s; "
                       "use the smoke ledger for dev runs", n_sym, min_univ, getattr(ledger, "path", "?"))

    # 1) build every trial's events (nothing is skipped silently: all combos go to the ledger)
    trials: List[dict] = []
    score_cache: Dict[int, pd.DataFrame] = {}
    mask_cache: Dict[int, Optional[pd.Series]] = {}
    for pi, p in enumerate(grid_params):
        for h in horizons:
            tid = (f"{lfam}|{INTERVAL_LABEL}|u{len(ctx.symbols)}|h{int(h)}|top{int(top_n)}|{rs_tag}|"
                   f"{json.dumps(p, sort_keys=True)}|s{seed if placebo else 0}{fv_tag}"
                   f"{'|' + adv_tag if adv_tag else ''}")
            info = {"trial_id": tid, "params": p, "horizon": int(h), "events": None, "n_events": 0, "error": None,
                    "skey": None}
            try:
                skey = (pi, int(h)) if getattr(fam, "needs_horizon", False) else pi  # ML families label at h
                info["skey"] = skey
                if skey not in score_cache:
                    sp = {**p, "label_h": int(h)} if getattr(fam, "needs_horizon", False) else p
                    sc = fam.score(ctx, sp).reindex(index=ctx.index, columns=ctx.symbols)
                    if placebo:  # random scores, same eligibility pattern as the real family
                        rng = np.random.default_rng([int(seed), pi])
                        S = sc.to_numpy(float)
                        sc = pd.DataFrame(np.where(np.isfinite(S), rng.random(S.shape), np.nan),
                                          index=sc.index, columns=sc.columns)
                    score_cache[skey] = sc
                    mfn = getattr(fam, "rebalance_mask", None)  # optional timing mask (calendar families)
                    mask_cache[skey] = mfn(ctx, p) if callable(mfn) else None
                pr = build_portfolio_events(ctx, score_cache[skey], int(h), top_n, regime_scale=regime_scale,
                                            rebalance_mask=mask_cache[skey])
                ev0 = apply_benchmark(ctx, pr.events, benchmark)
                info["events"], info["n_events"] = ev0, len(ev0)
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
        rec_params = {**t["params"], "grid_tag": grid_tag} if grid_tag else t["params"]  # metadata only (trial_id unchanged)
        ledger.record_trial(t["trial_id"], fam.name, rec_params, INTERVAL_LABEL,
                            f"{univ_tag}|h{t['horizon']}|top{top_n}|{rs_tag}",
                            daily if ok else None, lfam, t["status"])
        if ok and t.get("net_sharpe_period") is not None and t["net_sharpe_period"] > best_sr:
            best, best_sr = t["trial_id"], t["net_sharpe_period"]
    selected = best if best is not None else most
    if fixed_primary is not None:  # pre-declared primary (e.g. grid centre): neighbours only feed PBO, never the selection
        fx = next((t for t in trials if t["params"] == fixed_primary), None)
        if fx is None:
            raise ValueError("fixed_primary is not part of the parameter grid")
        selected = fx["trial_id"]

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
            matched = _matched_ew(navn, bench, win)
            ex = _nav_stats(navn["ret"] - matched, {}) if matched is not None else {}
            d.update({
                "excess_sharpe_vs_ew": ex.get("sharpe_annual"),
                "excess_cagr_vs_ew": (None if matched is None or ns["cagr"] is None else
                                      ns["cagr"] - float((1 + matched).prod() ** (ANN / len(win)) - 1.0)),
                "alpha_vs_cash_cagr": ns.get("alpha_vs_cash_cagr"),
                "event_excess_net_mean_bps": float(valid["net_ret"].mean() * 1e4) if len(valid) else None,
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

    # candidacy needs positive NAV-level alpha over cash as well (ew_universe mode)
    for s in scenarios:
        d = scen_out[s]
        d["benchmark_mode"] = benchmark
        if benchmark == "ew_universe" and d.get("nav_net"):
            ac = d.get("alpha_vs_cash_cagr")
            d["cash_alpha_ok"] = bool(ac is not None and ac > 0)
            if reports[s].verdict == "CANDIDATE" and not d["cash_alpha_ok"]:
                reports[s].failed_criteria = list(reports[s].failed_criteria) + ["cash_alpha_nav"]
                reports[s].verdict = "REJECTED"
                d["verdict"], d["failed_criteria"] = "REJECTED", reports[s].failed_criteria
    # robust (v2) layer: stacked on top of the gate, tightening only
    rob_cfg = None
    if robust_on:
        from bist_signal_bot.edge_validation.global_multiplicity import global_dsr_robust
        from bist_signal_bot.edge_validation.robustness import RobustnessConfig, robustness_report
        rob_cfg = robust_config or RobustnessConfig.from_settings(settings)
        gdsr = None
        if sel is not None and sel["n_events"]:
            try:
                if global_gate == "deferred":  # batch driver re-evaluates against the final snapshot
                    gdsr = {"dsr_global": 1.0, "n_global": None, "deferred": True}
                else:
                    gdsr = global_dsr_robust(ledger, lfam, LEDGER_SUFFIX_V2, trial_id=selected, dsr_min=cfg.dsr_min,
                                             mad_k=rob_cfg.global_mad_k, snapshot_rowid=snapshot_rowid,
                                             min_universe=min_univ)
            except Exception as exc:  # fail closed (criterion g -> fail)
                gdsr = {"dsr_global": None, "error": f"{type(exc).__name__}: {exc}"}
        breadth_cache: Dict[str, Optional[dict]] = {}
        for s in scenarios:
            d = scen_out[s]
            if sel is None or not sel["n_events"]:
                continue
            netev = gates[s]._net(sel["events"])
            navn = nav_returns(ctx, sel["events"], cms[s]).reindex(win)
            matched = _matched_ew(navn, bench, win)
            nav_ex = None if matched is None else (navn["ret"] - matched)
            breadth = None
            if top_n < rob_cfg.breadth_top_k:
                try:
                    pr20 = build_portfolio_events(ctx, score_cache[sel["skey"]], int(sel["horizon"]),
                                                  rob_cfg.breadth_top_k, regime_scale=regime_scale,
                                                  rebalance_mask=mask_cache.get(sel["skey"]))
                    e20 = apply_benchmark(ctx, pr20.events, benchmark)
                    e20 = e20[e20["t0"] >= win[0]] if len(win) and len(e20) else e20
                    n20 = gates[s]._net(e20).dropna(subset=["net_ret"]) if len(e20) else e20
                    from bist_signal_bot.edge_validation.robustness import _ann_sharpe_daily
                    breadth = {"top_k": int(rob_cfg.breadth_top_k), "n_events": int(len(n20)),
                               "mean_net_bps": float(n20["net_ret"].mean() * 1e4) if len(n20) else None,
                               "sharpe_annual": _ann_sharpe_daily(n20, "net_ret", gdays) if len(n20) else None}
                except Exception as exc:  # informational only
                    breadth = {"top_k": int(rob_cfg.breadth_top_k), "error": f"{type(exc).__name__}: {exc}"}
            rr = robustness_report(netev, nav_ex, grid=gdays, cfg=rob_cfg, global_dsr=gdsr or {"dsr_global": None},
                                   family_dsr=reports[s].dsr, breadth=breadth, dsr_min=cfg.dsr_min)
            if gdsr and gdsr.get("deferred"):
                rr["criteria"]["global_dsr"]["deferred"] = True
            elif gdsr:
                d["global_dsr_detail"] = {k: gdsr.get(k) for k in (
                    "n_global", "n_effective", "small_universe_count", "dsr_global", "dsr_global_neff",
                    "snapshot_rowid", "min_universe", "variance_trimmed", "error")}
            d["robustness"] = rr
            d["robust"] = bool(rr["robust"])
            if reports[s].verdict == "CANDIDATE" and not rr["robust"]:
                reports[s].failed_criteria = list(reports[s].failed_criteria) + [f"robust:{k}" for k in rr["failed"]]
                reports[s].verdict = "REJECTED"
                d["verdict"], d["failed_criteria"] = "REJECTED", reports[s].failed_criteria
    deferred = bool(robust_on and global_gate == "deferred")
    if deferred:  # global-multiplicity criterion is applied later by the batch driver against one final snapshot
        for d in scen_out.values():
            if d["verdict"] == "CANDIDATE":
                d["verdict"] = "PENDING_GLOBAL"
    cand = scen_out[primary]
    report = reports[primary].model_dump(mode="json")
    if deferred and report.get("verdict") == "CANDIDATE":
        report["verdict"] = "PENDING_GLOBAL"
    report["provisional"] = deferred
    report.update({
        "family": lfam, "interval": INTERVAL_LABEL,
        "candidacy_scenario": primary, "scenarios": scen_out,
        "zero_commission_is_upside_only": True,
        "selected_params": sel["params"] if sel else None, "selected_horizon": sel["horizon"] if sel else None,
        "top_n": top_n, "capital_try": ctx.capital, "long_only": True, "regime_scale": regime_scale is not None,
        "benchmark": benchmark, "robust_mode": robust_on,
        "robust_config": None if rob_cfg is None else rob_cfg.model_dump(),
        "robust_note": ("v2 candidacy requires the robustness layer on top of the gate (ledger family "
                        f"{lfam}); legacy (robust=False) rows live in separate ledger families." if robust_on
                        else "robust layer OFF (legacy/diagnostic mode)."),
        "benchmark_note": ("Gate stream = event return minus benchmark over the identical window; costs on the "
                           "strategy leg only, benchmark leg frictionless (conservative). 'excess_*_vs_ew' NAV fields "
                           "compare against an exposure-matched EW (cash when flat)."),
        "selected_trial_id": selected, "global_gate": global_gate, "global_pool_min_universe": min_univ,
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
    if survivor_check and sel is not None and sel["n_events"]:
        try:
            report["survivor_robustness"] = survivor_robustness(
                ctx, fam, sel["params"], sel["horizon"], top_n, cms[primary], benchmark=benchmark,
                placebo=placebo, seed=seed, regime_scale=regime_scale, win_start=win[0] if len(win) else None)
        except Exception as exc:  # diagnostic only
            report["survivor_robustness"] = {"error": f"{type(exc).__name__}: {exc}",
                                             "warning": SURVIVORSHIP_WARNING}
    try:  # always present; cheap sensitivity only (no refits); NOT a survivorship correction
        from bist_signal_bot.edge_validation import survivorship as _sv
        _ev = None
        if sel is not None and sel["n_events"]:
            _ev = gates[primary]._net(sel["events"])
        report["survivorship"] = _sv.optimism_bound(
            ctx, _ev, full_weight_days=int(_setting(settings, "SURVIVORSHIP_AGE_FULL_WEIGHT_DAYS",
                                                    _sv.AGE_FULL_WEIGHT_DAYS_DEFAULT)),
            horizon=None if sel is None else int(sel["horizon"]))
    except Exception as exc:
        report["survivorship"] = {"statement": _sv.HONESTY_STATEMENT if "_sv" in dir() else None,
                                  "error": f"{type(exc).__name__}: {exc}"}
    report["min_adv"] = min_adv
    report["effective_min_adv"] = float(ctx.min_adv)
    try:  # informational: entry at close of t0+1 instead of the model's open
        from bist_signal_bot.edge_validation.entry_delay import delayed_entry_report
        report["entry_delay"] = (delayed_entry_report(ctx, sel["events"], 1, cms[primary])
                                 if sel is not None and sel["n_events"] else None)
    except Exception as exc:
        report["entry_delay"] = {"error": f"{type(exc).__name__}: {exc}"}
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
        t.pop("skey", None)
    return DailyRunResult(fam.name, lfam, selected, reports, trials, report, str(path) if path else None, placebo)


def _matched_ew(navn: pd.DataFrame, bench: pd.DataFrame, win) -> Optional[pd.Series]:
    """Exposure-matched EW benchmark: cash + invested_frac*(ew - cash) per day (cash when flat), frictionless."""
    if "ew_universe" not in bench or "cash" not in bench:
        return None
    ew, cs = bench["ew_universe"].reindex(win).fillna(0.0), bench["cash"].reindex(win).fillna(0.0)
    inv = navn["invested_frac"].reindex(win).fillna(0.0)
    return cs + inv * (ew - cs)


def _survivor_stats(ctx_s, ctx_b, fam, params, horizon, top_n, cm, benchmark, placebo, seed, regime_scale,
                    start) -> dict:
    sc = fam.score(ctx_s, params).reindex(index=ctx_s.index, columns=ctx_s.symbols)
    if placebo:
        S = sc.to_numpy(float)
        rng = np.random.default_rng([int(seed), 0])
        sc = pd.DataFrame(np.where(np.isfinite(S), rng.random(S.shape), np.nan), index=sc.index, columns=sc.columns)
    mfn = getattr(fam, "rebalance_mask", None)
    pr = build_portfolio_events(ctx_s, sc, int(horizon), top_n, regime_scale=regime_scale,
                                rebalance_mask=mfn(ctx_s, params) if callable(mfn) else None)
    ev = pr.events
    if start is not None and len(ev):
        ev = ev[ev["t0"] >= start].reset_index(drop=True)
    if len(ev) == 0:
        return {"n_symbols": len(ctx_s.symbols), "n_events": 0}
    evx = apply_benchmark(ctx_s, ev, benchmark, bench_ctx=ctx_b)
    gate = CandidateGate(GateConfig(), cost_model=cm, save=False)
    net = gate._net(evx).dropna(subset=["net_ret"])
    win = ctx_s.index[(ctx_s.index >= ev["t0"].min()) & (ctx_s.index <= ev["t1"].max())]
    daily = daily_series(net, "net_ret", _day(win)) if len(net) else None
    navn = nav_returns(ctx_s, ev, cm).reindex(win)
    matched = _matched_ew(navn, ctx_b.benchmarks().reindex(win), win)
    cagr = _nav_stats(navn["ret"], {})["cagr"]
    mcagr = float((1 + matched).prod() ** (ANN / len(win)) - 1.0) if matched is not None and len(win) else None
    exc = None if cagr is None or mcagr is None else cagr - mcagr
    return {"n_symbols": len(ctx_s.symbols), "n_events": int(len(net)),
            "excess_sharpe_gate": None if daily is None else float(st.sharpe(daily.to_numpy()) * math.sqrt(ANN)),
            "mean_event_excess_net_bps": float(net["net_ret"].mean() * 1e4) if len(net) else None,
            "nav_net_cagr": cagr, "excess_cagr_vs_ew": exc}


def survivor_robustness(ctx: DailyContext, family, params: dict, horizon: int, top_n: int, cost_model,
                        benchmark: str = "ew_universe", placebo: bool = False, seed: int = 0,
                        regime_scale=None, win_start=None, min_years: float = 3.0,
                        top_k: Optional[int] = None) -> dict:
    """DIAGNOSTIC ONLY. Re-evaluates the selected trial on symbol subsets and reports how much excess return is left:
      (a) 'old_survivors': symbols whose first valid close is >= ``min_years`` before the window start;
      (b) 'ex_top_k_winners': the ``top_k`` (default 10% of symbols) best ex-post total-return symbols are removed
          from the PICKABLE universe while the benchmark stays the full-universe EW (harsh stress).
    WARNING: universe = currently listed names (delisted missing), so every result here is optimistic."""
    fam = DAILY_FAMILIES[family] if isinstance(family, str) else family
    start = pd.Timestamp(win_start) if win_start is not None else ctx.index[0]
    args = (fam, params, horizon, top_n, cost_model, benchmark, placebo, seed, regime_scale, win_start)
    full = _survivor_stats(ctx, ctx, *args)
    first = ctx.close.apply(lambda c: c.first_valid_index())
    cutoff = start - pd.Timedelta(days=int(365.25 * min_years))
    old = [s for s in ctx.symbols if pd.notna(first[s]) and first[s] <= cutoff]
    tot = (ctx.close.ffill().iloc[-1] / ctx.close.bfill().iloc[0] - 1.0).dropna()
    k = int(top_k if top_k is not None else max(1, round(0.1 * len(ctx.symbols))))
    drop = set(tot.nlargest(k).index)
    keep = [s for s in ctx.symbols if s not in drop]
    out = {"full": full, "min_years": min_years, "top_k": k, "benchmark": benchmark,
           "warning": SURVIVORSHIP_WARNING + " Diagnostic only; not part of the gate verdict."}
    for name, syms, bctx in (("old_survivors", old, None), ("ex_top_k_winners", keep, ctx)):
        if len(syms) < max(top_n, 2):
            out[name] = {"n_symbols": len(syms), "note": "too few symbols"}
            continue
        sub = subset_ctx(ctx, syms)
        r = _survivor_stats(sub, bctx or sub, *args)
        fe, se = full.get("excess_cagr_vs_ew"), r.get("excess_cagr_vs_ew")
        r["excess_cagr_remaining_fraction"] = (None if fe is None or se is None or fe <= 0.01 else float(se / fe))
        out[name] = r
    return out
