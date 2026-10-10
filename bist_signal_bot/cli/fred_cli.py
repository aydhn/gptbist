"""`macro fred-sync` command (separate file; EVDS agent owns `macro evds-sync`)."""
import argparse

from bist_signal_bot.data_sources.fred_client import DEFAULT_SERIES, NO_ORDER, FredClient


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="macro fred-sync", description="Sync FRED series into data/macro/fred_cache/")
    p.add_argument("--series", nargs="+", default=list(DEFAULT_SERIES))
    p.add_argument("--start", default=None, help="observation_start YYYY-MM-DD (not cached when set)")
    p.add_argument("--info", action="store_true", help="Only print series metadata")
    return p


def fred_sync_main(argv: list[str], client: FredClient | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = client or FredClient()
    rc = 0
    if args.info:
        for sid in args.series:
            try:
                print(client.series_info(sid))
            except Exception as e:
                print(f"{sid}: ERROR {e}")
                rc = 1
    else:
        for sid, res in client.sync(args.series, start=args.start).items():
            print(f"{sid}: {res}")
            rc = rc or int("error" in res)
    print(NO_ORDER)
    return rc
