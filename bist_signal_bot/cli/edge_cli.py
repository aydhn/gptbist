"""`edge` CLI: validate research baselines with the CandidateGate. Research/paper only."""

import argparse
import json

from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.intraday.archive import BarArchive
from bist_signal_bot.intraday.models import normalize_interval

NO_ORDER = "No real order sent."
FAMILIES = ["sma_trend", "rsi_meanrev", "breakout"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="edge", description="Edge validation gate (local, research only).")
    sub = p.add_subparsers(dest="edge_command", required=True)
    r = sub.add_parser("run", help="Run a strategy family through the candidate gate")
    r.add_argument("--family", required=True, choices=FAMILIES)
    r.add_argument("--interval", default="1h")
    g = r.add_mutually_exclusive_group()
    g.add_argument("--symbols", nargs="+")
    g.add_argument("--all-archived", action="store_true", help="All symbols present in the archive")
    r.add_argument("--placebo", action="store_true", help="Shuffle signal timing (noise control)")
    r.add_argument("--horizon-bars", type=int, default=4)
    r.add_argument("--label", choices=["forward", "triple_barrier"], default="forward")
    r.add_argument("--seed", type=int, default=0)
    d = sub.add_parser("run-daily", help="Cross-sectional daily family (long-only top-N) through the gate")
    d.add_argument("--family", required=True)
    d.add_argument("--horizons", default="5,10", help="comma-separated trading-day horizons")
    d.add_argument("--top-n", type=int, default=None, help="max positions (default DAILY_TOP_N=8)")
    d.add_argument("--placebo", action="store_true", help="random scores (must be REJECTED)")
    d.add_argument("--scenarios", choices=["both", "placeholder", "zero"], default="both")
    d.add_argument("--regime-scale", action="store_true", help="regime-dependent exposure (optional switch)")
    d.add_argument("--symbols", nargs="+", default=None)
    d.add_argument("--max-symbols", type=int, default=None, help="smoke runs: most liquid N symbols only")
    d.add_argument("--seed", type=int, default=0)
    d.add_argument("--benchmark", choices=["ew_universe", "cash", "none"], default="ew_universe",
                   help="evaluated stream: excess over EW universe (default, primary), over cash, or absolute")
    d.add_argument("--survivor-check", action="store_true", help="append survivorship sensitivity diagnostic")
    d.add_argument("--ledger-path", default=None,
                   help="trial ledger sqlite (default: the REAL ledger; use a temp path for smoke runs)")
    d.add_argument("--report-dir", default=None, help="report output dir (default data/edge_validation/reports)")
    d.add_argument("--grid-json", default=None,
                   help="override grid as JSON object of lists (creates NEW ledger trials!)")
    a = sub.add_parser("run-daily-all", help="Every registered daily family x horizons (placebo once per family)")
    a.add_argument("--horizons", default="3,5,10,15")
    a.add_argument("--families", default="all", help="comma-separated names or 'all'")
    a.add_argument("--top-n", type=int, default=None)
    a.add_argument("--regime-scale", action="store_true")
    a.add_argument("--scenarios", choices=["both", "placeholder", "zero"], default="both")
    a.add_argument("--symbols", nargs="+", default=None)
    a.add_argument("--max-symbols", type=int, default=None)
    a.add_argument("--seed", type=int, default=0)
    a.add_argument("--benchmark", choices=["ew_universe", "cash", "none"], default="ew_universe")
    a.add_argument("--survivor-check", action="store_true", help="append survivorship sensitivity diagnostic")
    a.add_argument("--ledger-path", default=None)
    a.add_argument("--report-dir", default=None)
    sub.add_parser("list-daily-families", help="Registered daily cross-sectional families")
    rp = sub.add_parser("report", help="Show a saved gate report")
    rp.add_argument("--latest", action="store_true", default=True)
    return p


def _print_report(d: dict) -> None:
    def fmt(x, n=4):
        return "n/a" if x is None else (f"{x:.{n}f}" if isinstance(x, float) else str(x))

    print(f"family={d['family']} interval={d['interval']} verdict={d['verdict']}")
    print(f"selected={d.get('selected_trial_id')}")
    print(f"{'metric':<26}{'value':>14}")
    rows = [("events / active_days", f"{d['n_events']} / {d['active_days']}"),
            ("trials (ledger/run)", f"{d['n_trials_ledger']} / {d['n_trials_evaluated']}"),
            ("net Sharpe (annual)", fmt(d.get("net_sharpe_annual"), 2)),
            ("gross Sharpe (annual)", fmt(d.get("gross_sharpe_annual"), 2)),
            ("DSR", fmt(d.get("dsr"), 3)), ("PBO", fmt(d.get("pbo"), 3)),
            ("BH-adj p (selected)", fmt(d.get("selected_p_bh"), 4)),
            ("reality-check p", fmt(d.get("reality_check_p"), 4)),
            ("positive path frac", fmt(d.get("positive_path_fraction"), 2))]
    for k, v in rows:
        print(f"{k:<26}{v:>14}")
    if d.get("failed_criteria"):
        print("failed: " + ", ".join(d["failed_criteria"]))
    if d.get("report_path"):
        print(f"report: {d['report_path']}")
    print(d["disclaimer"])


def _build_ctx(args, settings, archive):
    """(ctx, regime_scale) from the daily archive (USDTRY/XU100 included); (None, None) + message on failure."""
    from bist_signal_bot.edge_validation.xsection import DailyContext
    ctx = DailyContext.from_archive(archive, args.symbols, settings)
    if args.max_symbols and args.max_symbols < len(ctx.symbols):
        keep = ctx.value.tail(250).mean().nlargest(args.max_symbols).index.tolist()
        ctx = DailyContext.from_archive(archive, sorted(keep), settings)
    rs = None
    if args.regime_scale:
        from bist_signal_bot.edge_validation.regime_labels import label_regimes
        base = ctx.benchmark.dropna() if ctx.benchmark is not None else None
        if base is None or len(base) == 0:
            print("regime scale needs XU100 in the daily archive (daily archive-update).")
            return None, None
        rs = label_regimes(base).set_index("date")["exposure_scale"]
    return ctx, rs


def _scen(args):
    return {"both": ("placeholder_commission", "zero_commission"), "placeholder": ("placeholder_commission",),
            "zero": ("zero_commission",)}[args.scenarios]


def _run_daily_all(args, settings) -> int:
    from datetime import datetime
    from pathlib import Path

    from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
    from bist_signal_bot.edge_validation.ledger import TrialLedger
    from bist_signal_bot.edge_validation.run_all_daily import format_markdown, format_table, run_all_daily

    fams = (sorted(DAILY_FAMILIES) if args.families.strip().lower() == "all"
            else [x.strip() for x in args.families.split(",") if x.strip()])
    bad = [f for f in fams if f not in DAILY_FAMILIES]
    if bad:
        print(f"unknown daily families {bad}; see: edge list-daily-families")
        return 1
    horizons = [int(x) for x in args.horizons.split(",") if x.strip()]
    top_n = args.top_n or int(getattr(settings, "DAILY_TOP_N", 8))
    if args.report_dir:
        rdir = Path(args.report_dir)
    else:
        from bist_signal_bot.storage.paths import get_edge_validation_dir
        rdir = get_edge_validation_dir(settings) / "reports"
    ledger = TrialLedger(path=args.ledger_path, settings=settings)
    archive = BarArchive(settings=settings)
    try:
        ctx, rs = _build_ctx(args, settings, archive)
        if ctx is None:
            return 1
        print(f"run-daily-all: {len(fams)} families, horizons={horizons}, symbols={len(ctx.symbols)}, "
              f"ledger={ledger.path}", flush=True)

        def _progress(r):
            print(f"  done {r['family']} h={r['horizon']}{' placebo' if r['placebo'] else ''} "
                  f"{r.get('error') or r['verdicts']} ({r['seconds']}s)", flush=True)

        rows = run_all_daily(ctx, fams, horizons, top_n, ledger, scenarios=_scen(args), regime_scale=rs,
                             settings=settings, report_dir=rdir, seed=args.seed, progress=_progress,
                             benchmark=args.benchmark, survivor_check=args.survivor_check)
        n_sym = len(ctx.symbols)
    finally:
        archive.close()
    print(format_table(rows))
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    rdir.mkdir(parents=True, exist_ok=True)
    meta = {"generated": ts, "n_symbols": n_sym, "horizons": horizons, "top_n": top_n,
            "regime_scale": bool(args.regime_scale), "benchmark": args.benchmark, "ledger_path": str(ledger.path), "no_order": NO_ORDER}
    jp = rdir / f"daily_all_{ts}.json"
    jp.write_text(json.dumps({"meta": meta, "rows": rows}, ensure_ascii=False, indent=2, default=str),
                  encoding="utf-8")
    (rdir / f"daily_all_{ts}.md").write_text(format_markdown(rows, meta), encoding="utf-8")
    print(f"report: {jp}")
    print(NO_ORDER)
    return 0 if not any(r.get("error") for r in rows) else 2


def _run_daily(args, settings) -> int:
    from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
    from bist_signal_bot.edge_validation.ledger import TrialLedger
    from bist_signal_bot.edge_validation.runner_daily import run_family_daily

    if args.family not in DAILY_FAMILIES:
        print(f"unknown daily family {args.family!r}; see: edge list-daily-families")
        return 1
    grid = None
    if args.grid_json:
        try:
            grid = json.loads(args.grid_json)
            assert isinstance(grid, dict) and all(isinstance(v, list) for v in grid.values())
        except Exception:
            print("--grid-json must be a JSON object of lists, e.g. {\"lookback\":[60,120]}")
            return 1
        print("WARNING: --grid-json overrides the default grid; every combination x horizon is a NEW ledger trial "
              f"(ledger: {args.ledger_path or 'REAL ledger'}).")
    horizons = [int(x) for x in args.horizons.split(",") if x.strip()]
    top_n = args.top_n or int(getattr(settings, "DAILY_TOP_N", 8))
    scen = _scen(args)
    archive = BarArchive(settings=settings)
    try:
        ctx, rs = _build_ctx(args, settings, archive)
        if ctx is None:
            return 1
        res = run_family_daily(args.family, ctx, horizons, grid, top_n,
                               TrialLedger(path=args.ledger_path, settings=settings),
                               scenarios=scen, placebo=args.placebo, seed=args.seed, settings=settings,
                               regime_scale=rs, report_dir=args.report_dir, benchmark=args.benchmark,
                               survivor_check=args.survivor_check)
    finally:
        archive.close()
    r = res.report
    print(f"benchmark={r['benchmark']} (candidacy stream = {'excess over EW universe' if r['benchmark'] == 'ew_universe' else r['benchmark']})")
    print(f"family={r['family']} symbols={r['n_symbols']} window={r['window']} trials_ledger={r['n_trials_ledger']}")
    print(f"selected={res.selected_trial_id}")
    for s, d in r["scenarios"].items():
        tag = "CANDIDACY" if s == r["candidacy_scenario"] else "upside-only"
        f = lambda x, n=3: "n/a" if x is None else f"{x:.{n}f}"  # noqa: E731
        print(f"[{s}] ({tag}) verdict={d['verdict']} failed={','.join(d['failed_criteria']) or '-'}")
        print(f"   excessSR_vs_EW={f(d.get('excess_sharpe_vs_ew'), 2)} excessCAGR_vs_EW={f(d.get('excess_cagr_vs_ew'))} "
              f"alpha_vs_cash_CAGR={f(d.get('alpha_vs_cash_cagr'))} cash_alpha_ok={d.get('cash_alpha_ok')}")
        print(f"   gate netSR={f(d.get('gate_net_sharpe_annual'), 2)} NAV netSR={f(d.get('nav_net_sharpe_annual'), 2)} "
              f"CAGR={f(d.get('net_cagr'))} maxDD={f(d.get('max_drawdown'))} "
              f"cost_drag_bps/yr={f(d.get('cost_drag_bps_per_year'), 0)} turnover/yr={f(d.get('turnover_two_way_per_year'), 1)}")
    sv = r.get("survivor_robustness")
    if sv and "full" in sv:
        for k in ("full", "old_survivors", "ex_top_k_winners"):
            x = sv.get(k, {})
            print(f"   survivor[{k}] n_sym={x.get('n_symbols')} excessCAGR={x.get('excess_cagr_vs_ew')} "
                  f"kept={x.get('excess_cagr_remaining_fraction')}")
    print(r["survivorship_warning"])
    if res.report_path:
        print(f"report: {res.report_path}")
    print(NO_ORDER)
    return 0


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    if args.edge_command == "report":
        from bist_signal_bot.storage.paths import get_edge_validation_dir
        files = sorted((get_edge_validation_dir(settings) / "reports").glob("*.json"),
                       key=lambda f: f.stat().st_mtime)
        if not files:
            print("No edge reports yet. Run: edge run --family breakout --symbols ...")
            print(NO_ORDER)
            return 1
        _print_report(json.loads(files[-1].read_text(encoding="utf-8")))
        print(NO_ORDER)
        return 0
    if args.edge_command == "list-daily-families":
        from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
        for n, f in sorted(DAILY_FAMILIES.items()):
            print(f"{n}: grid={f.default_grid}")
        print(NO_ORDER)
        return 0
    if args.edge_command == "run-daily":
        return _run_daily(args, settings)
    if args.edge_command == "run-daily-all":
        return _run_daily_all(args, settings)
    from bist_signal_bot.edge_validation.ledger import TrialLedger
    from bist_signal_bot.edge_validation.runner import run_family

    interval = normalize_interval(args.interval)
    archive = BarArchive(settings=settings)
    try:
        symbols = args.symbols if args.symbols else archive.symbols(interval)
        if not symbols:
            print("No symbols: pass --symbols or fill the archive (intraday archive-update).")
            print(NO_ORDER)
            return 1
        res = run_family(args.family, symbols, interval, None, archive, TrialLedger(settings=settings),
                         horizon_bars=args.horizon_bars, label=args.label, placebo=args.placebo,
                         seed=args.seed, settings=settings)
        if res.skipped_illiquid:
            print(f"skipped (illiquid): {', '.join(res.skipped_illiquid)}")
        _print_report(res.report.model_dump(mode="json"))
        print(NO_ORDER)
        return 0
    finally:
        archive.close()
