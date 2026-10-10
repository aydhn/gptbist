"""`macro` CLI: EVDS sync of CPI and cash rate. Research only; no real order is ever sent."""

import argparse

NO_ORDER = "No real order sent."


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="macro", description="Macro data (TCMB EVDS3).")
    sub = p.add_subparsers(dest="macro_command", required=True)
    e = sub.add_parser("evds-sync", help="Fetch CPI (spliced) + TLREF/AOFM cash rate into data/macro/")
    e.add_argument("--only", choices=["cpi", "cash", "all"], default="all")
    e.add_argument("--macro-dir", default=None, help="override data/macro (tests)")
    return p


def main(argv: list[str]) -> int:
    if argv[:1] == ["fred-sync"]:
        from bist_signal_bot.cli.fred_cli import fred_sync_main
        return fred_sync_main(argv[1:])
    args = build_parser().parse_args(argv)
    from bist_signal_bot.data_sources.evds_client import EVDSClient, EVDSError, get_api_key, mask
    try:
        get_api_key()
    except EVDSError as exc:
        print(f"error: {exc}")
        return 2
    cl = EVDSClient(directory=args.macro_dir)
    rc = 0
    for name, fn, label in (("cpi", cl.build_cpi, "cpi_tr.csv"), ("cash", cl.build_cash_rate, "tlref.csv")):
        if args.only not in ("all", name):
            continue
        try:
            s = fn()
            print(f"{name}: {len(s)} rows {s.index[0].date()}..{s.index[-1].date()} -> {cl.dir / label}")
        except Exception as exc:
            print(f"error[{name}]: {mask(exc, cl.key)}")
            rc = 1
    print(NO_ORDER)
    return rc
