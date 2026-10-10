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
            "benchmark": r.get("benchmark"),
            "excess_sharpe_vs_ew": prim.get("excess_sharpe_vs_ew"), "excess_cagr_vs_ew": prim.get("excess_cagr_vs_ew"),
            "alpha_vs_cash_cagr": prim.get("alpha_vs_cash_cagr"), "cash_alpha_ok": prim.get("cash_alpha_ok"),
            "survivor_robustness": r.get("survivor_robustness"),
            "failed_criteria": prim.get("failed_criteria"), "report_path": res.report_path,
            "robust_mode": r.get("robust_mode"), "robust": prim.get("robust"),
            "robust_failed": ((prim.get("robustness") or {}).get("failed")),
            "robust_criteria": {k: v.get("pass") for k, v in ((prim.get("robustness") or {}).get("criteria") or {}).items()},
            "ledger_family": r.get("family")}


def run_all_daily(ctx, families: Sequence[str], horizons: Sequence[int], top_n: int, ledger, *, scenarios=None,
                  regime_scale=None, settings=None, report_dir=None, seed: int = 0, param_grids: Optional[Dict] = None,
                  progress=None, benchmark: str = "ew_universe", survivor_check: bool = False,
                  robust: bool = True) -> List[dict]:
    from bist_signal_bot.edge_validation.runner_daily import run_family_daily
    scenarios = tuple(scenarios or ("placeholder_commission", "zero_commission"))
    rows: List[dict] = []
    for item in plan_runs(families, horizons):
        t0 = time.perf_counter()
        try:
            res = run_family_daily(item["family"], ctx, [item["horizon"]], (param_grids or {}).get(item["family"]),
                                   top_n, ledger, scenarios=scenarios, placebo=item["placebo"], seed=seed,
                                   settings=settings, regime_scale=regime_scale, report_dir=report_dir,
                                   benchmark=benchmark, survivor_check=survivor_check, robust=robust)
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


def _rtag(r: dict) -> str:
    """'Y' robust, 'N' not robust, '-' robust layer off/unavailable."""
    v = r.get("robust")
    return "-" if v is None else ("Y" if v else "N")


def _rfail(r: dict) -> str:
    f = r.get("robust_failed")
    return "" if not f else ",".join(f)


def format_table(rows: List[dict]) -> str:
    head = (f"{'family':<26}{'h':>3} {'plc':<3} {'verdicts':<40}{'navSR':>7}{'CAGR':>8}{'maxDD':>8}{'aCash':>8}"
            f"{'xsSRew':>8}{'xsCAGRew':>9}{'rob':>4}{'trials':>7}{'sec':>7}  robust_failed")
    out = [head, "-" * len(head)]
    for r in rows:
        if r.get("error"):
            out.append(f"{r['family']:<26}{r['horizon']:>3} {'P' if r['placebo'] else '':<3} "
                       f"ERROR {r['error'][:60]}")
            continue
        out.append(f"{r['family']:<26}{r['horizon']:>3} {'P' if r['placebo'] else '':<3} "
                   f"{_vtag(r['verdicts']):<40}{_f(r['nav_net_sharpe']):>7}{_f(r['net_cagr'], 3):>8}"
                   f"{_f(r['max_drawdown'], 3):>8}{_f(r['alpha_vs_cash'], 3):>8}"
                   f"{_f(r.get('excess_sharpe_vs_ew')):>8}{_f(r.get('excess_cagr_vs_ew'), 3):>9}"
                   f"{_rtag(r):>4}{str(r['n_trials_ledger']):>7}{r['seconds']:>7.1f}  {_rfail(r)}")
    return "\n".join(out)


def format_markdown(rows: List[dict], meta: dict) -> str:
    L = ["# Daily all-family run", "", f"- generated: {meta.get('generated')}", f"- symbols: {meta.get('n_symbols')}",
         f"- horizons: {meta.get('horizons')} top_n={meta.get('top_n')} regime_scale={meta.get('regime_scale')}",
         f"- ledger: {meta.get('ledger_path')}",
         "- note: cal_turn_of_month always runs at horizon 5; placebo once per family at the middle horizon (P rows).",
         f"- {NO_ORDER}", "",
         f"- robust (v2) mode: {meta.get('robust')} (candidacy additionally needs the robustness layer; ledger suffix "
         f"{meta.get('ledger_suffix')})",
         f"- benchmark mode: {meta.get('benchmark')} (candidacy = excess over EW universe AND positive NAV alpha vs cash)",
         "| family | h | placebo | verdicts | NAV net Sharpe | CAGR | maxDD | alpha vs cash (CAGR) | "
         "excess Sharpe vs EW | excess CAGR vs EW | cash alpha NAV ok | robust | failed robustness criteria | "
         "trials | error |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['family']} | {r['horizon']} | {'yes' if r['placebo'] else ''} | {_vtag(r.get('verdicts'))} | "
                 f"{_f(r.get('nav_net_sharpe'))} | {_f(r.get('net_cagr'), 3)} | {_f(r.get('max_drawdown'), 3)} | "
                 f"{_f(r.get('alpha_vs_cash'), 3)} | {_f(r.get('excess_sharpe_vs_ew'))} | "
                 f"{_f(r.get('excess_cagr_vs_ew'), 3)} | {r.get('cash_alpha_ok')} | "
                 f"{_rtag(r)} | {_rfail(r)} | {r.get('n_trials_ledger', '')} | {r.get('error') or ''} |")
    sv = [r for r in rows if r.get("survivor_robustness")]
    if sv:
        L += ["", "## Survivorship sensitivity (diagnostic)", "",
              "WARNING: universe = currently listed names (delisted missing); all results are optimistic.", "",
              "| family | h | placebo | full xs CAGR vs EW | old survivors | frac kept | ex top-K winners | frac kept |",
              "|---|---|---|---|---|---|---|---|"]
        for r in sv:
            s = r["survivor_robustness"]
            if "full" not in s:
                continue
            o, t = s.get("old_survivors", {}), s.get("ex_top_k_winners", {})
            L.append(f"| {r['family']} | {r['horizon']} | {'yes' if r['placebo'] else ''} | "
                     f"{_f(s['full'].get('excess_cagr_vs_ew'), 3)} | {_f(o.get('excess_cagr_vs_ew'), 3)} | "
                     f"{_f(o.get('excess_cagr_remaining_fraction'))} | {_f(t.get('excess_cagr_vs_ew'), 3)} | "
                     f"{_f(t.get('excess_cagr_remaining_fraction'))} |")
    rb = [r for r in rows if r.get("robust_criteria")]
    if rb:
        names = ["trim_top_events", "drop_top_symbols", "year_stability", "cost_stress", "event_cap", "breadth_topk",
                 "global_dsr"]
        L += ["", "## Robustness criteria (primary scenario; pass=Y, fail=N, n/a=not evaluated; breadth is "
              "informational)", "", "| family | h | placebo | " + " | ".join(names) + " |",
              "|---|---|---|" + "---|" * len(names)]
        for r in rb:
            c = r["robust_criteria"]
            L.append(f"| {r['family']} | {r['horizon']} | {'yes' if r['placebo'] else ''} | " +
                     " | ".join({True: "Y", False: "N", None: "n/a"}[c.get(k)] for k in names) + " |")
    L += ["", "Survivorship: universe = currently active symbols; results are optimistic."]
    return "\n".join(L)
