"""Batch driver: every registered daily family x every horizon through ``run_family_daily``. Research only.

No real order is sent. Handling rules (documented, deterministic):
  * One ``run_family_daily`` call per (family, horizon): each gets its own gate verdict and report; the ledger
    counts every (params, horizon) trial once and ``n_trials_ledger`` accumulates across horizons (conservative DSR).
  * Placebo (random scores, separate ``<family>_daily__placebo`` ledger family) runs ONCE per family at the middle
    horizon (``sorted(horizons)[len//2]``).
  * ``cal_turn_of_month`` is only defined for a 5-session hold (2 last + 3 first sessions of the month), so it is
    ALWAYS run at horizon 5 only, regardless of ``--horizons`` (placebo also at 5).
  * A failing family/horizon is recorded (``error``) and the batch continues.
"""
from __future__ import annotations

import time
import traceback
from typing import Dict, List, Optional, Sequence

NO_ORDER = "No real order sent."
FIXED_HORIZON = {"cal_turn_of_month": 5}


def plan_runs(families: Sequence[str], horizons: Sequence[int]) -> List[dict]:
    hs = sorted(set(int(h) for h in horizons))
    if not hs:
        raise ValueError("need at least one horizon")
    mid = hs[len(hs) // 2]
    plan: List[dict] = []
    for f in families:
        fh = [FIXED_HORIZON[f]] if f in FIXED_HORIZON else hs
        pmid = FIXED_HORIZON.get(f, mid)
        for h in fh:
            plan.append({"family": f, "horizon": h, "placebo": False})
        plan.append({"family": f, "horizon": pmid, "placebo": True})
    return plan


def _row(item: dict, res, secs: float) -> dict:
    r = res.report
    scen = r["scenarios"]
    prim = scen[r["candidacy_scenario"]]
    return {**item, "error": None, "seconds": round(secs, 2), "n_trials_ledger": r.get("n_trials_ledger"),
            "selected_params": r.get("selected_params"), "window": r.get("window"),
            "verdicts": {s: d["verdict"] for s, d in scen.items()},
            "nav_net_sharpe": prim.get("nav_net_sharpe_annual"), "net_cagr": prim.get("net_cagr"),
            "max_drawdown": prim.get("max_drawdown"), "alpha_vs_cash": (prim.get("nav_net") or {}).get("alpha_vs_cash_cagr"),  # CAGR minus cash CAGR
            "alpha_vs_cash_detail": prim.get("alpha_vs_cash"),
            "failed_criteria": prim.get("failed_criteria"), "report_path": res.report_path}


def run_all_daily(ctx, families: Sequence[str], horizons: Sequence[int], top_n: int, ledger, *, scenarios=None,
                  regime_scale=None, settings=None, report_dir=None, seed: int = 0, param_grids: Optional[Dict] = None,
                  progress=None) -> List[dict]:
    from bist_signal_bot.edge_validation.runner_daily import run_family_daily
    scenarios = tuple(scenarios or ("placeholder_commission", "zero_commission"))
    rows: List[dict] = []
    for item in plan_runs(families, horizons):
        t0 = time.perf_counter()
        try:
            res = run_family_daily(item["family"], ctx, [item["horizon"]], (param_grids or {}).get(item["family"]),
                                   top_n, ledger, scenarios=scenarios, placebo=item["placebo"], seed=seed,
                                   settings=settings, regime_scale=regime_scale, report_dir=report_dir)
            row = _row(item, res, time.perf_counter() - t0)
        except Exception as exc:  # recorded, batch continues
            row = {**item, "error": f"{type(exc).__name__}: {exc}", "seconds": round(time.perf_counter() - t0, 2),
                   "traceback": traceback.format_exc(limit=3), "verdicts": {}}
        rows.append(row)
        if progress:
            progress(row)
    return rows


def _f(x, n=2):
    return "n/a" if x is None else f"{x:.{n}f}"


def _vtag(v: Optional[dict]) -> str:
    if not v:
        return "-"
    return "/".join(f"{k.split('_')[0][:5]}={x}" for k, x in v.items())


def format_table(rows: List[dict]) -> str:
    head = (f"{'family':<26}{'h':>3} {'plc':<3} {'verdicts':<40}{'navSR':>7}{'CAGR':>8}{'maxDD':>8}{'aCash':>8}"
            f"{'trials':>7}{'sec':>7}")
    out = [head, "-" * len(head)]
    for r in rows:
        if r.get("error"):
            out.append(f"{r['family']:<26}{r['horizon']:>3} {'P' if r['placebo'] else '':<3} "
                       f"ERROR {r['error'][:60]}")
            continue
        out.append(f"{r['family']:<26}{r['horizon']:>3} {'P' if r['placebo'] else '':<3} "
                   f"{_vtag(r['verdicts']):<40}{_f(r['nav_net_sharpe']):>7}{_f(r['net_cagr'], 3):>8}"
                   f"{_f(r['max_drawdown'], 3):>8}{_f(r['alpha_vs_cash'], 3):>8}"
                   f"{str(r['n_trials_ledger']):>7}{r['seconds']:>7.1f}")
    return "\n".join(out)


def format_markdown(rows: List[dict], meta: dict) -> str:
    L = ["# Daily all-family run", "", f"- generated: {meta.get('generated')}", f"- symbols: {meta.get('n_symbols')}",
         f"- horizons: {meta.get('horizons')} top_n={meta.get('top_n')} regime_scale={meta.get('regime_scale')}",
         f"- ledger: {meta.get('ledger_path')}",
         "- note: cal_turn_of_month always runs at horizon 5; placebo once per family at the middle horizon (P rows).",
         f"- {NO_ORDER}", "",
         "| family | h | placebo | verdicts | NAV net Sharpe | CAGR | maxDD | alpha vs cash | trials | error |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['family']} | {r['horizon']} | {'yes' if r['placebo'] else ''} | {_vtag(r.get('verdicts'))} | "
                 f"{_f(r.get('nav_net_sharpe'))} | {_f(r.get('net_cagr'), 3)} | {_f(r.get('max_drawdown'), 3)} | "
                 f"{_f(r.get('alpha_vs_cash'), 3)} | {r.get('n_trials_ledger', '')} | {r.get('error') or ''} |")
    L += ["", "Survivorship: universe = currently active symbols; results are optimistic."]
    return "\n".join(L)
