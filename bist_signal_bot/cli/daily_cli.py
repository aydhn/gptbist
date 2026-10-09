"""`daily` CLI: daily bar archive update and status. Research/paper only."""

import argparse

from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.core.time_utils import istanbul_now
from bist_signal_bot.daily.fetch import BENCHMARKS, INTERVAL, DailyFetcher, DailyUpdater
from bist_signal_bot.intraday.archive import BarArchive

NO_ORDER = "No real order sent."


def _universe_symbols(settings) -> list[str]:
    from bist_signal_bot.data.universe_store import UniverseStore

    return UniverseStore(settings).load_universe().list_symbols(active_only=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="daily", description="Daily bar archive (free yfinance data, local).")
    sub = p.add_subparsers(dest="daily_command", required=True)
    u = sub.add_parser("archive-update", help="Fetch daily bars (adjusted) into the local archive")
    g = u.add_mutually_exclusive_group()
    g.add_argument("--symbols", nargs="+")
    g.add_argument("--all-active", action="store_true", help="All active universe symbols (no auto-sync)")
    u.add_argument("--period", default=None, help="History for new symbols (default DAILY_HISTORY_PERIOD=10y)")
    u.add_argument("--full", action="store_true", help="Re-pull full history even for existing symbols")
    u.add_argument("--no-benchmarks", action="store_true", help="Skip XU100 / USDTRY")
    u.add_argument("--dry-run", action="store_true", help="Show plan only; no network, no writes")
    s = sub.add_parser("status", help="Per-symbol rows, first/last date, staleness")
    s.add_argument("--limit", type=int, default=20, help="Max symbol lines to print")
    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    archive = BarArchive(settings=settings)
    try:
        if args.daily_command == "archive-update":
            symbols = args.symbols if args.symbols else _universe_symbols(settings)
            if not symbols:
                print("No symbols: pass --symbols or load a universe (python -m bist_signal_bot universe init/import).")
                return 1
            period = args.period or str(getattr(settings, "DAILY_HISTORY_PERIOD", "10y"))
            if args.dry_run:
                have = sum(1 for s in symbols if archive.last_ts(s, INTERVAL) is not None)
                print(f"dry-run: symbols={len(symbols)} already_archived={have} period={period} "
                      f"benchmarks={'no' if args.no_benchmarks else ','.join(BENCHMARKS)}")
            else:
                rep = DailyUpdater(archive, DailyFetcher(settings=settings, archive=archive)).update(
                    symbols, period=period, include_benchmarks=not args.no_benchmarks, full=args.full)
                print(f"interval={INTERVAL} symbols={len(symbols)} inserted={rep.inserted} updated={rep.updated} "
                      f"unchanged={rep.unchanged} failures={len(rep.failures)}")
                for sym, why in list(rep.failures.items())[:10]:
                    print(f"fail: {sym}: {why}")
        else:
            today = istanbul_now().date()
            stale_days = int(getattr(settings, "DAILY_STALE_DAYS", 5) or 5)
            syms = archive.symbols(INTERVAL)
            total, stale, shown = 0, 0, 0
            for s in syms:
                n = archive.count(s, INTERVAL)
                first, last = archive.first_ts(s, INTERVAL), archive.last_ts(s, INTERVAL)
                age = (today - last.date()).days
                total += n
                is_stale = age > stale_days
                stale += int(is_stale)
                if shown < args.limit or s in BENCHMARKS:
                    print(f"{s}: rows={n} first={first.date()} last={last.date()} age_days={age}"
                          f"{' STALE' if is_stale else ''}")
                    shown += 1
            print(f"daily symbols={len(syms)} rows={total} stale={stale} (> {stale_days} calendar days)")
        print(NO_ORDER)
        return 0
    finally:
        archive.close()
