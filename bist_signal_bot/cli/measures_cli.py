"""`measures` CLI: BIST VBTS measure history (KAP). Research only; no real order is ever sent."""
import argparse
from datetime import date

NO_ORDER = "No real order sent."


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="measures", description="BIST VBTS measures history (KAP).")
    p.add_argument("--measures-dir", default=None, help="override data/measures (tests)")
    sub = p.add_subparsers(dest="measures_command", required=True)
    s = sub.add_parser("sync", help="Fetch KAP announcements (slow, >=2.5 s/request, restartable)")
    s.add_argument("--since", default="2018-01-01", help="YYYY-MM-DD")
    s.add_argument("--max-bodies", type=int, default=None, help="max NEW bodies to download this run")
    sub.add_parser("status", help="Coverage summary of data/measures/measures.csv")
    c = sub.add_parser("check", help="Is SYMBOL under a measure on DATE?")
    c.add_argument("symbol")
    c.add_argument("date", help="YYYY-MM-DD")
    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    from bist_signal_bot.measures.store import MeasureStore
    store = MeasureStore(directory=args.measures_dir)
    if args.measures_command == "status":
        cov = store.coverage()
        for k, v in cov.items():
            print(f"{k}: {v}")
        if not cov["rows"]:
            print("no measures stored (run: measures sync); the daily measure rule is NOT applicable without coverage.")
        print(NO_ORDER)
        return 0
    if args.measures_command == "check":
        d = date.fromisoformat(args.date)
        cs = store.coverage_start()
        df = store.load()
        hit = df[(df["symbol"] == args.symbol.upper()) & (df["start"] <= d.isoformat()) & (df["end"] >= d.isoformat())]
        print(f"{args.symbol.upper()} {d}: {'RESTRICTED' if len(hit) else 'not restricted'}"
              + (f" ({', '.join(sorted(hit['type']))})" if len(hit) else ""))
        if cs is None or d < cs:
            print("warning: date is outside the announcement coverage -> answer is not reliable.")
        print(NO_ORDER)
        return 0
    from bist_signal_bot.measures.fetcher import FetcherDependencyError, MeasureFetcher
    try:
        res = MeasureFetcher(store).sync(date.fromisoformat(args.since), args.max_bodies)
    except FetcherDependencyError as exc:
        print(f"error: {exc}")
        return 2
    for k, v in res.items():
        print(f"{k}: {v}")
    print(NO_ORDER)
    return 0
