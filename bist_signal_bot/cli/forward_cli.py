"""`forward` CLI: shadow (forward out-of-sample) paper trading. Simulation only; no real order is ever sent."""

import argparse
import json
from datetime import datetime

NO_ORDER = "No real order sent."


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="forward", description="Forward shadow paper trading (local, simulated).")
    p.add_argument("--forward-dir", default=None, help="override data/forward (tests / dry runs)")
    p.add_argument("--archive-path", default=None, help="override daily bar archive sqlite")
    p.add_argument("--ledger-path", default=None, help="override trial ledger sqlite (portfolio selection)")
    sub = p.add_subparsers(dest="forward_command", required=True)
    r = sub.add_parser("run-daily", help="Refresh data, decide, settle, mark-to-market (idempotent)")
    r.add_argument("--no-fetch", action="store_true", help="skip the yfinance refresh (use the archive as is)")
    r.add_argument("--now", default=None, help="ISO Istanbul time override for the freshness gate (testing)")
    fz = sub.add_parser("freeze", help="Create data/forward/portfolios.json once (never re-selected)")
    fz.add_argument("--force-new-version", action="store_true",
                    help="write the NEXT frozen version (portfolios.v2.json ...); older versions stay untouched")
    sub.add_parser("report", help="Per-portfolio forward stats and verdicts").add_argument("--json", action="store_true")
    for name in ("status", "health"):
        h = sub.add_parser(name, help="Daily health report (saved under data/forward/health/)")
        h.add_argument("--notify", action="store_true", help="send via the Telegram notifier (respects its dry-run)")
        h.add_argument("--dry-run", action="store_true", help="only print the Telegram text")
        h.add_argument("--json", action="store_true")
    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    from bist_signal_bot.forward import health as H
    from bist_signal_bot.forward import report as R
    from bist_signal_bot.forward import shadow as S
    from bist_signal_bot.forward.config import ForwardConfig, freeze_portfolios
    cfg = ForwardConfig.from_settings(None, args.forward_dir, args.archive_path, args.ledger_path)
    cmd = args.forward_command
    rc = 0
    if cmd == "freeze":
        doc = freeze_portfolios(cfg, force_new_version=args.force_new_version)
        print(f"portfolios frozen: v{doc.get('freeze_version')} n={doc['n_portfolios']} "
              f"candidates={doc.get('n_candidates')} watch={doc.get('n_watch')} (source {doc['source']}) hash={doc['content_hash'][:12]}")
        for p in doc["portfolios"]:
            print(f"  [{p.get('tier')}/{p.get('role')}] {p['id']} sharpe={p['ledger_sharpe']} "
                  f"v2={p.get('v2_verdict')} robust={p.get('v2_robust')}")
    elif cmd == "run-daily":
        now = datetime.fromisoformat(args.now) if args.now else None
        res = S.run_daily(cfg, now=now, fetch=not args.no_fetch, now_override=bool(args.now))
        print(f"status={res['status']} as_of={res.get('as_of')} gate={res.get('freshness_gate')} "
              f"decisions={res['decisions_written']} entries={res['entries_written']} exits={res['exits_written']} "
              f"portfolios={res.get('portfolios_frozen')} alerts={res.get('alerts_new')} "
              f"elapsed_s={res.get('elapsed_s')} timings_s={res.get('timings_s')}")
        for e in res["errors"][:5]:
            print(f"error: {e}")
        rc = 0 if res["status"] in ("OK", "STALE", "KILL_SWITCH") else 1
    elif cmd == "report":
        rep = R.build_report(cfg)
        R.save_report(cfg, rep)
        print(json.dumps(rep, indent=2, default=str) if args.json else R.format_report(rep))
    else:
        h = H.build_health(cfg)
        path = H.save_health(cfg, h)
        print(json.dumps(h, indent=2, default=str) if args.json else H.format_health(h))
        if args.notify or args.dry_run:
            r = H.notify_telegram(cfg, h, dry_run=args.dry_run or not args.notify)
            print(f"telegram: sent={r['sent']} dry_run={r['dry_run']}")
        print(f"saved: {path}")
    print(NO_ORDER)
    return rc
