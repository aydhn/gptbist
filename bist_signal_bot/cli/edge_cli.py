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


def _run_daily(args, settings) -> int:
    from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
    from bist_signal_bot.edge_validation.ledger import TrialLedger
    from bist_signal_bot.edge_validation.runner_daily import run_family_daily
    from bist_signal_bot.edge_validation.xsection import DailyContext

    if args.family not in DAILY_FAMILIES:
        print(f"unknown daily family {args.family!r}; see: edge list-daily-families")
        return 1
    horizons = [int(x) for x in args.horizons.split(",") if x.strip()]
    top_n = args.top_n or int(getattr(settings, "DAILY_TOP_N", 8))
    scen = {"both": ("placeholder_commission", "zero_commission"), "placeholder": ("placeholder_commission",),
            "zero": ("zero_commission",)}[args.scenarios]
    archive = BarArchive(settings=settings)
    try:
        ctx = DailyContext.from_archive(archive, args.symbols, settings)
        if args.max_symbols and args.max_symbols < len(ctx.symbols):
            keep = ctx.value.tail(250).mean().nlargest(args.max_symbols).index.tolist()
            panel_syms = sorted(keep)
            ctx = DailyContext.from_archive(archive, panel_syms, settings)
        rs = None
        if args.regime_scale:
            from bist_signal_bot.edge_validation.regime_labels import label_regimes
            base = ctx.benchmark.dropna() if ctx.benchmark is not None else None
            if base is None or len(base) == 0:
                print("regime scale needs XU100 in the daily archive (daily archive-update).")
                return 1
            lab = label_regimes(base)
            rs = lab.set_index("date")["exposure_scale"]
        res = run_family_daily(args.family, ctx, horizons, None, top_n, TrialLedger(settings=settings),
                               scenarios=scen, placebo=args.placebo, seed=args.seed, settings=settings,
                               regime_scale=rs)
    finally:
        archive.close()
    r = res.report
    print(f"family={r['family']} symbols={r['n_symbols']} window={r['window']} trials_ledger={r['n_trials_ledger']}")
    print(f"selected={res.selected_trial_id}")
    for s, d in r["scenarios"].items():
        tag = "CANDIDACY" if s == r["candidacy_scenario"] else "upside-only"
        f = lambda x, n=3: "n/a" if x is None else f"{x:.{n}f}"  # noqa: E731
        print(f"[{s}] ({tag}) verdict={d['verdict']} failed={','.join(d['failed_criteria']) or '-'}")
        print(f"   gate netSR={f(d.get('gate_net_sharpe_annual'), 2)} NAV netSR={f(d.get('nav_net_sharpe_annual'), 2)} "
              f"CAGR={f(d.get('net_cagr'))} maxDD={f(d.get('max_drawdown'))} "
              f"cost_drag_bps/yr={f(d.get('cost_drag_bps_per_year'), 0)} turnover/yr={f(d.get('turnover_two_way_per_year'), 1)}")
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
