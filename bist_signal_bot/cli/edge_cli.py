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
