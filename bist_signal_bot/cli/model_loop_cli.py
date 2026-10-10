"""`model-loop` CLI: train intraday models and show registry status. Research/paper only."""

import argparse

from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.intraday.archive import BarArchive
from bist_signal_bot.intraday.models import normalize_interval

NO_ORDER = "No real order sent."


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="model-loop", description="Intraday model loop (local, research only).")
    sub = p.add_subparsers(dest="model_loop_command", required=True)
    t = sub.add_parser("train", help="Train + CPCV-evaluate + gate + register a model (never auto-promoted)")
    t.add_argument("--interval", default="1h")
    g = t.add_mutually_exclusive_group()
    g.add_argument("--symbols", nargs="+")
    g.add_argument("--all-archived", action="store_true")
    t.add_argument("--kind", choices=["hgb", "logreg"], default=None)
    t.add_argument("--as-of", default=None, help="YYYY-MM-DD (inclusive); default = all archived data")
    t.add_argument("--horizon-bars", type=int, default=None)
    sub.add_parser("models", help="List registered model-loop models")
    d = sub.add_parser("daily-train", help="Multi-day ML: walk-forward train + SAME excess CandidateGate + register "
                                           "(non-CANDIDATE -> WATCH, never champion)")
    d.add_argument("--kind", choices=["logit", "hgb", "meta"], default="logit")
    d.add_argument("--horizon", type=int, default=10)
    d.add_argument("--retrain-every", type=int, default=None)
    d.add_argument("--symbols", nargs="+")
    d.add_argument("--max-symbols", type=int, default=None)
    d.add_argument("--as-of", default=None, help="YYYY-MM-DD; default = last archived session")
    d.add_argument("--ledger-path", default=None, help="trial ledger sqlite (default: the REAL append-only ledger)")
    d.add_argument("--cpcv", action="store_true", help="also report CPCV (purged) AUC/Brier/IC")
    d.add_argument("--only-if-due", action="store_true", help="skip unless the weekly retrain schedule is due")
    d.add_argument("--retrain-days", type=int, default=7)
    from bist_signal_bot.cli.model_loop_lifecycle_cli import build_lifecycle_parser
    build_lifecycle_parser(sub)  # evaluate | promote | rollback | status (champion + model list)
    return p


def _fmt(x, n=4):
    return "n/a" if x is None else (f"{x:.{n}f}" if isinstance(x, float) else str(x))


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    from bist_signal_bot.model_loop.training import make_registry, train_model
    registry = make_registry(settings)
    if args.model_loop_command == "daily-train":
        return _daily_train(args, settings, registry)
    if args.model_loop_command in ("evaluate", "promote", "rollback", "status"):
        from bist_signal_bot.cli.model_loop_lifecycle_cli import handle_lifecycle
        rc = handle_lifecycle(args)
        if args.model_loop_command != "status":
            return rc
    if args.model_loop_command in ("status", "models"):
        models = [m for m in registry.list_models() if m.owner_module == "model_loop"]
        if not models:
            print("No model-loop models yet. Run: model-loop train --interval 1h --all-archived")
        for m in models:
            md = m.metadata
            om = md.get("oos_metrics", {})
            print(f"{m.model_id} status={m.status.value} verdict={md.get('gate_verdict')} "
                  f"through={md.get('trained_through')} AUC={_fmt(om.get('auc'))} "
                  f"netSharpe={_fmt(md.get('oos_net_sharpe_annual'), 2)}")
        print(NO_ORDER)
        return 0
    interval = normalize_interval(args.interval)
    archive = BarArchive(settings=settings)
    try:
        symbols = args.symbols if args.symbols else archive.symbols(interval)
        if not symbols:
            print("No symbols: pass --symbols or fill the archive (intraday archive-update).")
            print(NO_ORDER)
            return 1
        if args.as_of:
            as_of = args.as_of
        else:
            last = max(archive.last_ts(s, interval) for s in symbols)
            as_of = last
        try:
            info = train_model(archive, symbols, interval, as_of, settings, horizon_bars=args.horizon_bars,
                               model_kind=args.kind, registry=registry)
        except ValueError as exc:
            print(f"train failed: {exc}")
            print(NO_ORDER)
            return 1
        print(f"model_id={info.model_id} kind={info.kind} interval={info.interval} events={info.n_events}")
        print(f"trained_through={info.trained_through} status={info.registry_status}")
        for k, v in info.oos_metrics.items():
            print(f"  oos.{k} = {_fmt(v) if not isinstance(v, (list, dict)) else v}")
        print(f"gate_verdict={info.gate_verdict}")
        for w in info.warnings:
            print(f"WARNING: {w}")
        print(f"artifact: {info.artifact_path}")
        print(NO_ORDER)
        return 0
    finally:
        archive.close()


def _daily_train(args, settings, registry) -> int:
    import pandas as pd

    from bist_signal_bot.edge_validation.ledger import TrialLedger
    from bist_signal_bot.edge_validation.xsection import DailyContext
    from bist_signal_bot.model_loop.daily_lifecycle import (DEFAULT_PARAMS, DailyModelTrainer, due_for_retrain)
    from bist_signal_bot.model_loop.training import models_dir
    if args.only_if_due:
        due, why = due_for_retrain(registry, args.as_of or pd.Timestamp.now(), args.retrain_days)
        print(f"retrain schedule: due={due} ({why})")
        if not due:
            print(NO_ORDER)
            return 0
    archive = BarArchive(settings=settings)
    try:
        ctx = DailyContext.from_archive(archive, args.symbols, settings)
        if args.max_symbols and args.max_symbols < len(ctx.symbols):
            keep = ctx.value.tail(250).mean().nlargest(args.max_symbols).index.tolist()
            ctx = DailyContext.from_archive(archive, sorted(keep), settings)
    finally:
        archive.close()
    params = dict(DEFAULT_PARAMS[args.kind])
    if args.retrain_every:
        params["retrain_every"] = args.retrain_every
    ledger = TrialLedger(path=args.ledger_path, settings=settings)
    print(f"daily-train kind={args.kind} h={args.horizon} symbols={len(ctx.symbols)} "
          f"ledger={args.ledger_path or 'REAL ledger'}")
    trainer = DailyModelTrainer(ctx, ledger, args.kind, args.horizon, settings, registry, params,
                                models_dir=models_dir(settings), cpcv=args.cpcv)
    try:
        info = trainer.train(args.as_of or ctx.index[-1])
    except ValueError as exc:
        print(f"daily-train failed: {exc}")
        print(NO_ORDER)
        return 1
    print(f"model_id={info.model_id} status={info.registry_status} trained_through={info.trained_through}")
    for k, v in info.oos_metrics.items():
        print(f"  oos.{k} = {_fmt(v) if not isinstance(v, (list, dict)) else v}")
    print(f"gate_verdict={info.gate_verdict}")
    for w in info.warnings:
        print(f"WARNING: {w}")
    print(NO_ORDER)
    return 0
