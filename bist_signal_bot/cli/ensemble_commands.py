import argparse
from typing import Optional
from pathlib import Path
import json
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.app.ensemble_app import create_ensemble_engine, create_weight_manager, create_ensemble_store
from bist_signal_bot.ensemble.models import EnsembleMode

def setup_ensemble_parser(subparsers):
    parser = subparsers.add_parser("ensemble", help="Ensemble consensus commands")
    sub = parser.add_subparsers(dest="ensemble_command", required=True)

    run_p = sub.add_parser("run", help="Run ensemble consensus on symbols")
    run_p.add_argument("--symbols", nargs="+", required=True, help="Symbols to analyze")
    run_p.add_argument("--strategies", nargs="+", help="Strategies to use")
    run_p.add_argument("--source", default="local", help="Data source")
    run_p.add_argument("--mode", default="METADATA_ONLY", help="Ensemble mode")
    run_p.add_argument("--save-output", action="store_true", help="Save output to disk")
    run_p.add_argument("--json", action="store_true", help="Output JSON")

    exp_p = sub.add_parser("explain", help="Explain consensus for a single symbol")
    exp_p.add_argument("symbol", help="Symbol to explain")
    exp_p.add_argument("--strategies", nargs="+", help="Strategies to use")
    exp_p.add_argument("--source", default="local", help="Data source")
    exp_p.add_argument("--json", action="store_true", help="Output JSON")

    w_p = sub.add_parser("weights", help="Manage ensemble weights")
    w_p.add_argument("--save", action="store_true", help="Save weights")
    w_p.add_argument("--confirm", action="store_true", help="Confirm save")
    w_p.add_argument("--json", action="store_true", help="Output JSON")

    rec_p = sub.add_parser("recent", help="List recent ensemble runs")
    rec_p.add_argument("--limit", type=int, default=10, help="Number of results")
    rec_p.add_argument("--json", action="store_true", help="Output JSON")

    cfg_p = sub.add_parser("config", help="Show ensemble config")
    cfg_p.add_argument("--json", action="store_true", help="Output JSON")

def handle_ensemble_command(args: argparse.Namespace):
    settings = Settings()

    if args.ensemble_command == "run":
        engine = create_ensemble_engine(settings)
        req = engine.build_request_from_settings(args.symbols)
        req.source = args.source
        if args.strategies:
            req.strategy_names = args.strategies
        req.mode = EnsembleMode(args.mode)
        req.save_output = args.save_output

        res = engine.run(req)

        if args.json:
            print(json.dumps(res.summary(), indent=2))
        else:
            from bist_signal_bot.ensemble.reporting import format_ensemble_result_text
            print(format_ensemble_result_text(res))

    elif args.ensemble_command == "explain":
        engine = create_ensemble_engine(settings)
        req = engine.build_request_from_settings([args.symbol])
        req.source = args.source
        if args.strategies:
            req.strategy_names = args.strategies

        expl = engine.explain(args.symbol, req)

        if args.json:
            print(json.dumps(expl.model_dump(), indent=2))
        else:
            from bist_signal_bot.ensemble.reporting import format_explanation_text
            print(format_explanation_text(expl))

    elif args.ensemble_command == "weights":
        wm = create_weight_manager(settings)

        if args.save:
            if not args.confirm:
                print("Error: --confirm is required to save weights")
                return
            w = wm.default_weights()
            wm.save_weights(w, confirm=True)
            print("Weights saved successfully")
        else:
            w = wm.load_weights() or wm.default_weights()
            if args.json:
                print(json.dumps(w.model_dump(), indent=2))
            else:
                for k, v in w.model_dump().items():
                    print(f"{k}: {v}")

    elif args.ensemble_command == "recent":
        store = create_ensemble_store(settings)
        recs = store.list_recent_results(args.limit)

        if args.json:
            print(json.dumps(recs, indent=2))
        else:
            print(f"=== Recent Ensemble Runs (last {args.limit}) ===")
            for r in recs:
                print(f"[{r['date']}] {r['id']} - Mode: {r['mode']} - Symbols: {r['symbols']} - Consensus: {r['consensus_count']}")

    elif args.ensemble_command == "config":
        data = {
            "enabled": settings.ENABLE_ENSEMBLE_ENGINE,
            "mode": getattr(settings, "ENSEMBLE_DEFAULT_MODE", "METADATA_ONLY"),
            "strategies": getattr(settings, "ENSEMBLE_DEFAULT_STRATEGIES", ""),
            "thresholds": {
                "min_score": getattr(settings, "ENSEMBLE_MIN_APPROVED_SCORE", 70.0),
                "min_conf": getattr(settings, "ENSEMBLE_MIN_APPROVED_CONFIDENCE", 55.0),
                "min_agr": getattr(settings, "ENSEMBLE_MIN_AGREEMENT_RATIO", 0.6),
                "max_conf_score": getattr(settings, "ENSEMBLE_MAX_CONFLICT_SCORE", 35.0),
                "high_conf_score": getattr(settings, "ENSEMBLE_HIGH_CONFLICT_SCORE", 60.0)
            }
        }
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            for k, v in data.items():
                print(f"{k}: {v}")
