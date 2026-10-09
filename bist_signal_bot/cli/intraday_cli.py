"""`intraday` CLI: archive update, gap report, archive status. Research/paper only."""

import argparse
from datetime import timedelta

from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.core.logging_setup import get_logger
from bist_signal_bot.core.time_utils import istanbul_now
from bist_signal_bot.intraday.archive import BarArchive
from bist_signal_bot.intraday.fetcher import ArchiveUpdater, RateLimitedFetcher
from bist_signal_bot.intraday.gaps import detect_gaps_range
from bist_signal_bot.intraday.models import interval_minutes, normalize_interval

logger = get_logger(__name__)
NO_ORDER = "No real order sent."


def _universe_symbols(settings) -> list[str]:
    from bist_signal_bot.data.universe_store import UniverseStore

    return UniverseStore(settings).load_universe().list_symbols(active_only=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="intraday", description="Intraday bar archive (free data, local).")
    sub = p.add_subparsers(dest="intraday_command", required=True)
    u = sub.add_parser("archive-update", help="Fetch new bars into the local archive")
    u.add_argument("--interval", default="1h")
    g = u.add_mutually_exclusive_group()
    g.add_argument("--symbols", nargs="+")
    g.add_argument("--all-active", action="store_true", help="All active symbols in the universe")
    gp = sub.add_parser("gaps", help="Gap/halt report from the archive")
    gp.add_argument("symbol")
    gp.add_argument("--interval", default="1h")
    gp.add_argument("--days", type=int, default=20)
    sub.add_parser("status", help="Archive row counts and survivorship report")
    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    archive = BarArchive(settings=settings)
    try:
        if args.intraday_command == "archive-update":
            if args.all_active and not args.symbols:
                from bist_signal_bot.data.universe_sync import sync_if_stale

                sres = sync_if_stale(settings)
                if sres is not None:
                    print(f"universe auto-sync: added={len(sres.added)} deactivated={len(sres.deactivated)} "
                          f"new_ipos={len(sres.new_ipos)} skipped={sres.skipped_reason}")
            symbols = args.symbols if args.symbols else _universe_symbols(settings)
            if not symbols:
                print("No symbols: pass --symbols or load a universe (python -m bist_signal_bot universe init/import).")
                return 1
            now = istanbul_now()
            report = ArchiveUpdater(archive, RateLimitedFetcher(settings=settings, archive=archive), settings=settings).update(
                symbols, normalize_interval(args.interval), now
            )
            archive.snapshot_universe(now.date(), symbols)
            print(f"interval={report.interval} symbols={len(symbols)} inserted={report.inserted} "
                  f"updated={report.updated} unchanged={report.unchanged} failures={len(report.failures)} "
                  f"clamped={report.clamped}")
            for n in report.notes[:5]:
                print(f"note: {n}")
            for sym, why in list(report.failures.items())[:10]:
                print(f"fail: {sym}: {why}")
        elif args.intraday_command == "gaps":
            iv = normalize_interval(args.interval)
            df = archive.read_bars(args.symbol, iv)
            end = istanbul_now().date() - timedelta(days=1)
            reps = detect_gaps_range(df.index, end - timedelta(days=args.days), end, interval_minutes(iv))
            for r in reps:
                if r.coverage < 1.0:
                    print(f"{r.day} expected={r.expected_count} present={r.present_count} "
                          f"coverage={r.coverage:.3f} halt_runs={len(r.suspected_halt_runs)}")
            print(f"{args.symbol} {iv}: {len(reps)} trading days checked")
        else:
            print(f"archive rows: {archive.count()}")
            print(archive.survivorship_report())
        print(NO_ORDER)
        return 0
    finally:
        archive.close()
