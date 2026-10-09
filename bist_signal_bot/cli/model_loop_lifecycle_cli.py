"""`model-loop` lifecycle subcommands: evaluate / promote / rollback / status.

Research/paper only. No real order sent. Promotion and rollback are dry runs
unless --confirm is given. Wiring into `main.py` is done by the owner of
cli/model_loop_cli.py via `build_lifecycle_parser` / `handle_lifecycle`.
"""
from __future__ import annotations

import argparse

NO_ORDER = "No real order sent."


def build_lifecycle_parser(subparsers) -> None:
    e = subparsers.add_parser("evaluate", help="Run drift check and (if warranted) train a challenger")
    e.add_argument("--as-of", default=None, help="YYYY-MM-DD; default today")
    e.add_argument("--force", action="store_true", help="Treat as drift detected (still respects kill switch and min days)")
    e.add_argument("--interval", default="1h")
    p = subparsers.add_parser("promote", help="Promote a CANDIDATE challenger (dry run unless --confirm)")
    p.add_argument("model_id")
    p.add_argument("--confirm", action="store_true")
    r = subparsers.add_parser("rollback", help="Demote the champion to the previous one (dry run unless --confirm)")
    r.add_argument("--confirm", action="store_true")
    subparsers.add_parser("status", help="Show champion / challengers / last retrain")


def build_lifecycle(settings=None, interval: str = "1h", with_trainer: bool = False):
    from bist_signal_bot.config.settings import get_settings
    from bist_signal_bot.core.audit import AuditLogger
    from bist_signal_bot.model_loop.drift_monitor import DriftMonitor
    from bist_signal_bot.model_loop.lifecycle import ModelLifecycle
    from bist_signal_bot.model_loop.training import IntradayModelTrainer, make_registry
    from bist_signal_bot.security.kill_switch import KillSwitchManager
    from bist_signal_bot.security.preflight import SecurityPreflightRunner
    from bist_signal_bot.storage.paths import get_data_dir

    settings = settings or get_settings()
    registry = make_registry(settings)
    kill = KillSwitchManager(settings, get_data_dir(settings))
    trainer = None
    if with_trainer:
        from bist_signal_bot.intraday.archive import BarArchive
        archive = BarArchive(settings)
        symbols = list(archive.symbols(interval))
        trainer = IntradayModelTrainer(archive, symbols, interval, settings, registry=registry)
    return ModelLifecycle(registry, trainer, DriftMonitor(settings), AuditLogger(settings),
                          SecurityPreflightRunner(settings, kill_switch=kill), kill, settings)


def handle_lifecycle(args: argparse.Namespace, lifecycle=None) -> int:
    cmd = args.model_loop_command
    if lifecycle is None:
        lifecycle = build_lifecycle(interval=getattr(args, "interval", "1h"), with_trainer=(cmd == "evaluate"))
    if cmd == "status":
        s = lifecycle.status()
        print(f"champion: {s['champion_id']}")
        print(f"last_retrain: {s['last_retrain']}  kill_switch_active: {s['kill_switch_active']}")
        for mid, st in s["challengers"]:
            print(f"  challenger {mid}: {st}")
    elif cmd == "evaluate":
        import pandas as pd
        as_of = args.as_of or pd.Timestamp.now().strftime("%Y-%m-%d")
        rep = lifecycle.evaluate(as_of, force=getattr(args, "force", False))
        print(f"as_of={rep.as_of} trained={rep.trained} challenger={rep.challenger_id} "
              f"recommended={rep.promotion_recommended}")
        if rep.drift:
            print(f"drift severity={rep.drift.severity} retrain={rep.drift.retrain} reasons={rep.drift.reasons}")
        if rep.skipped_reason:
            print(f"skipped: {rep.skipped_reason}")
        if rep.comparison:
            print(f"comparison: better={rep.comparison.get('better')} reasons={rep.comparison.get('reasons')}")
    elif cmd in ("promote", "rollback"):
        res = lifecycle.promote(args.model_id, args.confirm) if cmd == "promote" else lifecycle.rollback(args.confirm)
        print(f"{cmd}: {res.status} model={res.model_id} dry_run={res.dry_run} reasons={res.reasons}")
    else:
        print(f"unknown model-loop lifecycle command: {cmd}")
        return 2
    print(NO_ORDER)
    return 0
