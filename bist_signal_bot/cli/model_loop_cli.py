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
