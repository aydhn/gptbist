"""`edge real-report`: recompute a daily family's NAV (read-only, no ledger writes) and print the real-return
report with and without the exposure overlay. Research only. No real order sent."""
from __future__ import annotations

import json

NO_ORDER = "No real order sent."


def add_parser(sub) -> None:
    p = sub.add_parser("real-report", help="Real (CPI-adjusted) report for a daily family, with/without overlay")
    p.add_argument("--family", required=True)
    p.add_argument("--horizon", type=int, required=True)
    p.add_argument("--params-json", default="{}", help='family params, e.g. {"lookback":20}')
    p.add_argument("--top-n", type=int, default=None)
    p.add_argument("--scenarios", choices=["both", "placeholder", "zero"], default="both")
    p.add_argument("--symbols", nargs="+", default=None)
    p.add_argument("--max-symbols", type=int, default=None)
    p.add_argument("--no-regime", action="store_true", help="overlay without XU100 regime scale")
    p.add_argument("--cpi-mode", choices=["interpolate", "causal"], default="interpolate")
    p.add_argument("--no-fetch", action="store_true", help="do not download CPI (local CSV/cache only)")
    p.add_argument("--json", action="store_true", help="print full JSON")


def compute_reports(args, settings) -> dict:
    from bist_signal_bot.daily.macro import CPIUnavailable, load_cpi
    from bist_signal_bot.edge_validation.costs_daily import DailyCostModel
    from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
    from bist_signal_bot.edge_validation.real_returns import report_for_nav
    from bist_signal_bot.edge_validation.regime_labels import label_regimes
    from bist_signal_bot.edge_validation.xsection import DailyContext, build_portfolio_events, nav_returns
    from bist_signal_bot.intraday.archive import BarArchive

    if args.family not in DAILY_FAMILIES:
        raise ValueError(f"unknown daily family {args.family!r}")
    fam = DAILY_FAMILIES[args.family]
    params = json.loads(args.params_json)
    if not isinstance(params, dict) or not fam.valid(params):
        raise ValueError(f"invalid params for {args.family}: {params}")
    archive = BarArchive(settings=settings)
    try:
        ctx = DailyContext.from_archive(archive, args.symbols, settings)
        if args.max_symbols and args.max_symbols < len(ctx.symbols):
            keep = ctx.value.tail(250).mean().nlargest(args.max_symbols).index.tolist()
            ctx = DailyContext.from_archive(archive, sorted(keep), settings)
    finally:
        archive.close()
    top_n = args.top_n or int(getattr(settings, "DAILY_TOP_N", 8))
    rs = None
    if not args.no_regime and ctx.benchmark is not None and ctx.benchmark.notna().any():
        rs = label_regimes(ctx.benchmark.dropna()).set_index("date")["exposure_scale"]
    try:
        cpi, src = load_cpi(settings, allow_fetch=not args.no_fetch)
    except CPIUnavailable as exc:
        cpi, src = None, None
        print(f"WARNING: {exc}")
    scores = fam.score(ctx, params).reindex(index=ctx.index, columns=ctx.symbols)
    mfn = getattr(fam, "rebalance_mask", None)
    mask = mfn(ctx, params) if callable(mfn) else None
    pr = build_portfolio_events(ctx, scores, args.horizon, top_n, rebalance_mask=mask)
    if not len(pr.events):
        raise ValueError("no portfolio events produced")
    start = pd_ts(pr.events["t_entry"].min())
    scen = {"both": ("zero_commission", "placeholder_commission"), "placeholder": ("placeholder_commission",),
            "zero": ("zero_commission",)}[args.scenarios]
    out = {"family": args.family, "horizon": args.horizon, "params": params, "top_n": top_n,
           "n_symbols": len(ctx.symbols), "cpi_source": src, "scenarios": {}}
    for s in scen:
        nav = nav_returns(ctx, pr.events, DailyCostModel.from_settings(settings, scenario=s))
        out["scenarios"][s] = report_for_nav(nav, ctx, cpi=cpi, regime_scale=rs, settings=settings,
                                             cpi_mode=args.cpi_mode, load_cpi_if_missing=False, start=start)
    return out


def pd_ts(x):
    import pandas as pd
    return pd.Timestamp(x)


def _f(x, pct=True):
    if x is None or (isinstance(x, float) and x != x):
        return "n/a"
    return f"{x:.1%}" if pct else f"{x:.2f}"


def print_report(res: dict) -> None:
    print(f"family={res['family']} h={res['horizon']} params={res['params']} top_n={res['top_n']} "
          f"symbols={res['n_symbols']} cpi={res['cpi_source']}")
    for s, rep in res["scenarios"].items():
        for key in ("base", "overlay"):
            r = rep.get(key)
            if not r:
                continue
            c = r["comparators"]
            print(f"[{s}/{r['label']}] {r['window'][0]}..{r['window'][1]} ({r['years']:.1f}y) "
                  f"nominalCAGR={_f(r['nominal_cagr'])} realCAGR={_f(r['real_cagr'])} infl={_f(r['inflation_cagr'])} "
                  f"maxDD={_f(r['max_drawdown'])} worst12m(nom/real)={_f(r['worst_12m_nominal'])}/{_f(r['worst_12m_real'])} "
                  f"%12m_real>=target={_f(r['pct_12m_real_ge_target'])}")
            print(f"    vs XU100 {_f(c.get('xu100', {}).get('excess_cagr'))} | cash(gross) {_f(c['cash_gross']['excess_cagr'])} | "
                  f"deposit(after stopaj {c['deposit_net_stopaj']['withholding']:.0%}) {_f(c['deposit_net_stopaj']['excess_cagr'])} | "
                  f"USDTRY {_f(c.get('usdtry', {}).get('excess_cagr'))} | USD CAGR {_f(r.get('usd_cagr'))}")
            print(f"    {r['target_statement']}")
            for w in r["warnings"][:3]:
                print(f"    note: {w}")
        if "overlay_summary" in rep:
            o = rep["overlay_summary"]
            print(f"    overlay: avg_exposure={o['avg_exposure']:.2f} halts={o['n_halts']} reentries={o['n_reentries']} "
                  f"flat_days={o['pct_days_flat']:.1%} maxDD_cfg={o['max_dd_cfg']:.0%}")
    print(NO_ORDER)


def run(args, settings) -> int:
    try:
        res = compute_reports(args, settings)
    except Exception as exc:
        print(f"real-report failed: {type(exc).__name__}: {exc}")
        return 1
    if args.json:
        print(json.dumps(res, indent=1, default=str))
    else:
        print_report(res)
    return 0
