import argparse
import json
from pathlib import Path

from bist_signal_bot.app.portfolio_ledger_app import (
    create_research_portfolio_ledger,
    create_portfolio_lifecycle_manager,
    create_portfolio_valuation_engine,
    create_portfolio_attribution_engine,
    create_portfolio_outcome_evaluator,
    create_portfolio_nav_builder
)
from bist_signal_bot.portfolio_ledger.models import ResearchPortfolioStatus, AttributionType
from bist_signal_bot.portfolio_ledger.reporting import (
    format_research_portfolio_text,
    format_valuation_snapshot_text,
    format_attribution_result_text,
    format_portfolio_outcome_text,
    research_portfolio_to_dict,
    valuation_snapshot_to_dict,
    attribution_result_to_dict,
    portfolio_outcome_to_dict
)
from bist_signal_bot.config.settings import Settings

def setup_portfolio_ledger_parser(subparsers):
    parser = subparsers.add_parser("portfolio-ledger", help="Manage Research Portfolio Ledger")
    sub = parser.add_subparsers(dest="ledger_command")

    # create
    create_parser = sub.add_parser("create", help="Create a research portfolio")
    create_parser.add_argument("--name", type=str, help="Name of the portfolio")
    create_parser.add_argument("--from-construction", type=str, help="Create from a construction result ID")
    create_parser.add_argument("--notional", type=float, default=100000.0, help="Initial notional value")
    create_parser.add_argument("--confirm", action="store_true", help="Confirm creation")

    # list
    list_parser = sub.add_parser("list", help="List portfolios")
    list_parser.add_argument("--status", type=str, help="Filter by status")
    list_parser.add_argument("--json", action="store_true", help="Output JSON")

    # show
    show_parser = sub.add_parser("show", help="Show portfolio details")
    show_parser.add_argument("portfolio_id", type=str, help="Portfolio ID")
    show_parser.add_argument("--json", action="store_true", help="Output JSON")

    # value
    value_parser = sub.add_parser("value", help="Value a portfolio")
    value_parser.add_argument("portfolio_id", type=str, help="Portfolio ID")
    value_parser.add_argument("--json", action="store_true", help="Output JSON")

    # attribution
    attr_parser = sub.add_parser("attribution", help="Calculate portfolio attribution")
    attr_parser.add_argument("portfolio_id", type=str, help="Portfolio ID")
    attr_parser.add_argument("--by", type=str, default="symbol", choices=["symbol", "sector", "strategy", "cost"], help="Attribution grouping")
    attr_parser.add_argument("--json", action="store_true", help="Output JSON")

    # outcome
    out_parser = sub.add_parser("outcome", help="Evaluate portfolio outcome")
    out_parser.add_argument("portfolio_id", type=str, help="Portfolio ID")
    out_parser.add_argument("--horizon-days", type=int, default=5, help="Evaluation horizon in days")
    out_parser.add_argument("--json", action="store_true", help="Output JSON")

    # close
    close_parser = sub.add_parser("close", help="Close a research portfolio")
    close_parser.add_argument("portfolio_id", type=str, help="Portfolio ID")
    close_parser.add_argument("--reason", type=str, default="Manual close", help="Reason for closing")
    close_parser.add_argument("--confirm", action="store_true", help="Confirm closing")

    # To be added: nav, events, rebalance-track, recent, config, report. (Stubs below if needed)

def handle_portfolio_ledger_command(args, settings=None):
    if not settings:
        settings = Settings()

    ledger = create_research_portfolio_ledger(settings)

    cmd = args.ledger_command
    if not cmd:
        print("Usage: python -m bist_signal_bot portfolio-ledger [command] --help")
        return

    if cmd == "create":
        if not args.confirm:
            print("Error: Creating a portfolio requires confirmation (--confirm).")
            return

        if args.from_construction:
            # Mock construction result
            class MockConstructionResult:
                result_id = args.from_construction
                allocations = []
            res = ledger.create_from_construction_result(MockConstructionResult(), name=args.name, confirm=True)
            print(f"Created portfolio from construction result: {res.portfolio_id}")
        else:
            if not args.name:
                print("Error: Portfolio name is required.")
                return
            res = ledger.create_portfolio(name=args.name, initial_notional=args.notional, confirm=True)
            print(f"Created portfolio: {res.portfolio_id}")

    elif cmd == "list":
        status_filter = None
        if args.status:
            try:
                status_filter = ResearchPortfolioStatus(args.status.upper())
            except ValueError:
                print(f"Invalid status: {args.status}")
                return

        portfolios = ledger.list_portfolios(status=status_filter)
        if args.json:
            print(json.dumps([research_portfolio_to_dict(p) for p in portfolios], indent=2, default=str))
        else:
            for p in portfolios:
                print(f"- {p.portfolio_id}: {p.name} [{p.status.value}]")

    elif cmd == "show":
        p = ledger.get_portfolio(args.portfolio_id)
        if not p:
            print(f"Portfolio not found: {args.portfolio_id}")
            return
        if args.json:
            print(json.dumps(research_portfolio_to_dict(p), indent=2, default=str))
        else:
            print(format_research_portfolio_text(p))

    elif cmd == "value":
        p = ledger.get_portfolio(args.portfolio_id)
        if not p:
            print(f"Portfolio not found: {args.portfolio_id}")
            return

        val_engine = create_portfolio_valuation_engine(settings)
        snapshot = val_engine.value_portfolio(p)
        # In a real system, you would store this snapshot.
        if args.json:
            print(json.dumps(valuation_snapshot_to_dict(snapshot), indent=2, default=str))
        else:
            print(format_valuation_snapshot_text(snapshot))

    elif cmd == "attribution":
        p = ledger.get_portfolio(args.portfolio_id)
        if not p:
            print(f"Portfolio not found: {args.portfolio_id}")
            return

        val_engine = create_portfolio_valuation_engine(settings)
        snapshot = val_engine.value_portfolio(p)

        attr_engine = create_portfolio_attribution_engine(settings)
        attr_type = AttributionType(args.by.upper())
        result = attr_engine.calculate_attribution(snapshot, by=attr_type)

        if args.json:
            print(json.dumps(attribution_result_to_dict(result), indent=2, default=str))
        else:
            print(format_attribution_result_text(result))

    elif cmd == "outcome":
        p = ledger.get_portfolio(args.portfolio_id)
        if not p:
            print(f"Portfolio not found: {args.portfolio_id}")
            return

        out_evaluator = create_portfolio_outcome_evaluator(settings)
        result = out_evaluator.evaluate_outcome(p, horizon_days=args.horizon_days)

        if args.json:
            print(json.dumps(portfolio_outcome_to_dict(result), indent=2, default=str))
        else:
            print(format_portfolio_outcome_text(result))

    elif cmd == "close":
        if not args.confirm:
            print("Error: Closing a portfolio requires confirmation (--confirm).")
            return
        evt = ledger.close_portfolio(args.portfolio_id, reason=args.reason, confirm=True)
        print(f"Portfolio closed. Event ID: {evt.event_id}")

    else:
        print(f"Command not implemented yet: {cmd}")
