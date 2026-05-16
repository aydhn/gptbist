import json
import logging
from argparse import Namespace

from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.app.adaptive_app import create_adaptive_engine

logger = logging.getLogger(__name__)

def handle_adaptive_commands(args: Namespace) -> None:
    engine = create_adaptive_engine()
    settings = get_settings()

    if args.adaptive_command == "recommend":
        symbols = args.symbols or []
        strategies = args.strategies or settings.ADAPTIVE_DEFAULT_STRATEGIES.split(",")
        top_n = args.top or settings.ADAPTIVE_DEFAULT_TOP_N

        result = engine.recommend(symbols, strategies, top_n=top_n, save_report=args.save_report)
        if args.json:
            print(json.dumps(result.safe_public_dict(), indent=2))
        else:
            from bist_signal_bot.adaptive.reporting import format_adaptive_recommendation_text
            print(format_adaptive_recommendation_text(result))

    elif args.adaptive_command == "symbol":
        strategies = args.strategies or settings.ADAPTIVE_DEFAULT_STRATEGIES.split(",")
        result = engine.recommend_for_symbol(args.symbol, strategies)
        if args.json:
            print(json.dumps(result.safe_public_dict(), indent=2))
        else:
            from bist_signal_bot.adaptive.reporting import format_adaptive_recommendation_text
            print(format_adaptive_recommendation_text(result))

    elif args.adaptive_command == "refresh-plan":
        symbols = args.symbols or []
        strategies = settings.ADAPTIVE_DEFAULT_STRATEGIES.split(",")
        result = engine.recommend(symbols, strategies, save_report=False)
        if args.json:
            print(json.dumps(result.refresh_plan.model_dump(mode='json') if result.refresh_plan else {}, indent=2))
        else:
            if result.refresh_plan:
                from bist_signal_bot.adaptive.reporting import format_refresh_plan_text
                print(format_refresh_plan_text(result.refresh_plan))
            else:
                print("No refresh plan generated.")

    elif args.adaptive_command == "model-refresh":
        symbols = []
        strategies = ["ml_filter"]
        result = engine.recommend(symbols, strategies, save_report=False)
        if args.json:
            print(json.dumps([m.model_dump(mode='json') for m in result.model_refresh_recommendations], indent=2))
        else:
            print(f"Model Refresh Recommendations: {len(result.model_refresh_recommendations)}")
            for m in result.model_refresh_recommendations:
                print(f"- Model: {m.model_id or 'unknown'} | Retrain: {m.should_retrain} | Reason: {m.reason}")
                if m.recommended_command:
                    print(f"  Command: {' '.join(m.recommended_command)}")

    elif args.adaptive_command == "params":
        params = engine.parameter_store.load_active_parameters()
        if args.strategy:
            params = [p for p in params if p.strategy_name == args.strategy]

        if args.json:
            print(json.dumps([p.model_dump(mode='json') for p in params], indent=2))
        else:
            print(f"Active Parameter Sets: {len(params)}")
            for p in params:
                print(f"- {p.strategy_name} | {p.symbol or 'ALL'} | ID: {p.parameter_set_id}")

    elif args.adaptive_command == "apply-params":
        if not args.confirm:
            print("Error: --confirm flag is required to apply parameters permanently.")
            return

        if args.from_latest:
            # Simplistic application for CLI demonstration
            # In a real scenario, would load the latest recommendation from store
            print("Applying latest adaptive parameters...")
            print("Note: In this version, manual extraction is recommended for safety.")
        else:
            print("Specify parameter source (e.g. --from-latest).")

    elif args.adaptive_command == "policy":
        policy = engine.policy_manager.load_policy()
        if args.json:
            print(json.dumps(policy.model_dump(mode='json'), indent=2))
        else:
            print(f"Adaptive Policy (Mode: {policy.mode.value})")
            print(f"- Min Evidence: {policy.min_evidence_count}")
            print(f"- Max Model Age: {policy.max_model_age_days} days")
            print(f"- Require Regime Match: {policy.require_regime_match}")

    elif args.adaptive_command == "recent":
        recent = engine.storage.list_recent_recommendations(args.limit)
        if args.json:
            print(json.dumps(recent, indent=2))
        else:
            print(f"Recent Recommendations ({len(recent)}):")
            for r in recent:
                print(f"- {r.get('id')} | {r.get('date')} | Status: {r.get('status')} | Candidates: {r.get('candidates')}")

    elif args.adaptive_command == "config":
        cfg = {
            "enabled": settings.ENABLE_ADAPTIVE_ENGINE,
            "mode": settings.ADAPTIVE_MODE,
            "default_strategies": settings.ADAPTIVE_DEFAULT_STRATEGIES,
            "runtime_use_adaptive": settings.RUNTIME_USE_ADAPTIVE,
            "scanner_use_adaptive_params": settings.SCANNER_USE_ADAPTIVE_PARAMS
        }
        if args.json:
            print(json.dumps(cfg, indent=2))
        else:
            print("Adaptive Engine Configuration:")
            for k, v in cfg.items():
                print(f"  {k}: {v}")
