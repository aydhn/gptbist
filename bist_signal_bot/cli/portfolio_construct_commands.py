import json
import logging
import uuid
import pandas as pd
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.app.portfolio_construction_app import create_portfolio_construction_engine, create_portfolio_construction_store
from bist_signal_bot.portfolio_construction.models import PortfolioConstructionRequest, PortfolioWeightingMethod
from bist_signal_bot.portfolio_construction.reporting import (
    format_portfolio_construction_text, format_rebalance_simulation_text,
    format_constraints_text, format_risk_budget_text,
    construction_result_to_dict, rebalance_to_dict
)

logger = logging.getLogger(__name__)

def handle_portfolio_construct_command(args: Any, settings: Settings) -> None:
    if not settings.ENABLE_PORTFOLIO_CONSTRUCTION:
        print("Portfolio Construction is disabled in settings.")
        return

    engine = create_portfolio_construction_engine(settings)
    store = create_portfolio_construction_store(settings)

    if args.pc_command == "build":
        method = PortfolioWeightingMethod(args.method)
        req = PortfolioConstructionRequest(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            symbols=args.symbols,
            strategy_names=["auto"],
            weighting_method=method,
            max_positions=args.max_positions,
            portfolio_notional=args.notional,
            current_weights={}
        )
        res = engine.construct(req)

        if getattr(args, "json", False):
            print(json.dumps(construction_result_to_dict(res), indent=2))
        else:
            print(format_portfolio_construction_text(res))

    elif args.pc_command == "compare":
        methods = [PortfolioWeightingMethod(m) for m in args.methods]
        req = PortfolioConstructionRequest(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            symbols=args.symbols,
            strategy_names=["auto"],
            weighting_method=PortfolioWeightingMethod.EQUAL_WEIGHT,
            max_positions=10,
            portfolio_notional=100000.0,
            current_weights={}
        )
        results = engine.compare_methods(req, methods)

        if getattr(args, "json", False):
            print(json.dumps([construction_result_to_dict(r) for r in results], indent=2))
        else:
            for r in results:
                print(format_portfolio_construction_text(r))
                print("-" * 50)

    elif args.pc_command == "rebalance":
        if getattr(args, "latest", False):
            sim = store.load_latest_rebalance()
            if not sim:
                print("No latest rebalance simulation found.")
                return
            if getattr(args, "json", False):
                print(json.dumps(rebalance_to_dict(sim), indent=2))
            else:
                print(format_rebalance_simulation_text(sim))
        else:
            print("Only --latest is supported in this mock CLI implementation for rebalance.")

    elif args.pc_command == "constraints":
        if getattr(args, "latest", False):
            res = store.load_latest_result()
            if not res:
                print("No latest result found.")
                return
            if getattr(args, "json", False):
                print(json.dumps([v.model_dump() for v in res.violations], indent=2))
            else:
                print(format_constraints_text(res.violations))

    elif args.pc_command == "risk-budget":
        if getattr(args, "latest", False):
            res = store.load_latest_result()
            if not res:
                print("No latest result found.")
                return
            if getattr(args, "json", False):
                print(json.dumps([i.model_dump() for i in res.risk_budget], indent=2))
            else:
                print(format_risk_budget_text(res.risk_budget))

    elif args.pc_command == "report":
        if getattr(args, "latest", False):
            res = store.load_latest_result()
            if not res:
                print("No latest result found.")
                return
            if getattr(args, "json", False):
                print(json.dumps(construction_result_to_dict(res), indent=2))
            else:
                print(format_portfolio_construction_text(res))

    elif args.pc_command == "recent":
        recents = store.list_recent_results(limit=args.limit)
        if getattr(args, "json", False):
            print(json.dumps(recents, indent=2))
        else:
            if not recents:
                print("No recent portfolio constructions found.")
            for r in recents:
                print(f"{r['generated_at']} - {r['weighting_method']} - Score: {r['portfolio_score']}")

    elif args.pc_command == "config":
        data = {k: getattr(settings, k) for k in dir(settings) if k.startswith("PORTFOLIO_CONSTRUCTION_") or k.startswith("PORTFOLIO_")}
        if getattr(args, "json", False):
            print(json.dumps(data, indent=2))
        else:
            print("Portfolio Construction Configuration:")
            for k, v in data.items():
                print(f"{k}: {v}")
