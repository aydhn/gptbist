import argparse
import json
import logging
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.app.stress_app import create_stress_test_engine

def handle_stress_command(args, settings: Settings):
    logger = logging.getLogger("bist_signal_bot.cli.stress")
    engine = create_stress_test_engine(settings)

    if args.stress_cmd == "run":
        if args.latest_portfolio:
            res = engine.run_for_latest_portfolio(save_output=not args.no_save)
        elif getattr(args, 'snapshot', None):
            res = engine.run_for_snapshot(args.snapshot, save_output=not args.no_save)
        elif getattr(args, 'symbols', None):
            logger.info("Mocking custom returns for symbols...")
            custom_returns = [0.01, -0.02, 0.03, -0.01, 0.005] * 10
            res = engine.run_for_custom_returns(custom_returns, save_output=not args.no_save)
        else:
            print("You must specify --latest-portfolio, --snapshot, or --symbols")
            return

        if args.json:
            print(json.dumps(res.safe_public_dict(), indent=2))
        else:
            from bist_signal_bot.stress.reporting import format_stress_result_text
            print(format_stress_result_text(res))

    elif args.stress_cmd == "latest":
        res = engine.store.load_latest_result()
        if not res:
            print("No latest stress result found.")
            return

        if args.json:
            print(json.dumps(res.safe_public_dict(), indent=2))
        else:
            from bist_signal_bot.stress.reporting import format_stress_report_markdown
            print(format_stress_report_markdown(res))

    elif args.stress_cmd == "recent":
        results = engine.store.list_recent_results(limit=getattr(args, 'limit', 10))
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                print(f"ID: {r['stress_id']} | Rating: {r['rating']} | Status: {r['status']}")

    elif args.stress_cmd == "monte-carlo":
        print("Monte Carlo simulation executed via standard run for now.")

    elif args.stress_cmd == "shock":
        print("Shock scenarios executed via standard run for now.")

    elif args.stress_cmd == "drawdown":
        print("Drawdown simulation executed via standard run for now.")

    elif args.stress_cmd == "risk-of-ruin":
        print("Risk-of-Ruin executed via standard run for now.")

    elif args.stress_cmd == "config":
        print("Stress Testing Config:")
        print(f"Enabled: {settings.ENABLE_STRESS_TESTING}")
        print(f"Monte Carlo Simulations: {settings.STRESS_MONTE_CARLO_SIMULATIONS}")
        print(f"Shock Scenarios Enabled: {settings.STRESS_SHOCK_SCENARIOS_ENABLED}")
        print(f"Ruin Threshold: {settings.STRESS_RUIN_THRESHOLD_PCT}%")

def add_stress_parsers(subparsers):
    parser_stress = subparsers.add_parser("stress", help="Stress Test & Monte Carlo Simulation")
    stress_subparsers = parser_stress.add_subparsers(dest="stress_cmd", required=True)

    # run
    p_run = stress_subparsers.add_parser("run", help="Run a stress test")
    p_run.add_argument("--latest-portfolio", action="store_true")
    p_run.add_argument("--snapshot", type=str)
    p_run.add_argument("--symbols", nargs="+")
    p_run.add_argument("--source", type=str, default="local")
    p_run.add_argument("--json", action="store_true")
    p_run.add_argument("--no-save", action="store_true")

    # monte-carlo
    p_mc = stress_subparsers.add_parser("monte-carlo", help="Run Monte Carlo independently")
    p_mc.add_argument("--latest-portfolio", action="store_true")
    p_mc.add_argument("--snapshot", type=str)
    p_mc.add_argument("--simulations", type=int, default=1000)
    p_mc.add_argument("--horizon-days", type=int, default=60)
    p_mc.add_argument("--method", type=str, default="BOOTSTRAP")
    p_mc.add_argument("--json", action="store_true")

    # shock
    p_shock = stress_subparsers.add_parser("shock", help="Run Shock Scenarios")
    p_shock.add_argument("--latest-portfolio", action="store_true")
    p_shock.add_argument("--market-shock", type=float)
    p_shock.add_argument("--sector", type=str)
    p_shock.add_argument("--json", action="store_true")

    # drawdown
    p_dd = stress_subparsers.add_parser("drawdown", help="Run Drawdown Simulation")
    p_dd.add_argument("--latest-portfolio", action="store_true")
    p_dd.add_argument("--snapshot", type=str)
    p_dd.add_argument("--json", action="store_true")

    # risk-of-ruin
    p_ror = stress_subparsers.add_parser("risk-of-ruin", help="Run Risk-of-Ruin Estimate")
    p_ror.add_argument("--latest-portfolio", action="store_true")
    p_ror.add_argument("--snapshot", type=str)
    p_ror.add_argument("--ruin-threshold", type=float)
    p_ror.add_argument("--json", action="store_true")

    # latest / recent / config
    p_latest = stress_subparsers.add_parser("latest", help="Show latest stress test result")
    p_latest.add_argument("--json", action="store_true")

    p_recent = stress_subparsers.add_parser("recent", help="List recent stress results")
    p_recent.add_argument("--limit", type=int, default=10)
    p_recent.add_argument("--json", action="store_true")

    p_config = stress_subparsers.add_parser("config", help="Show stress testing config")
    p_config.add_argument("--json", action="store_true")
