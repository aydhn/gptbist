from bist_signal_bot.cli_ux.cli_parser import add_cli_ux_subparser, handle_cli_ux


import sys

from bist_signal_bot.app.bootstrap import bootstrap_app
from bist_signal_bot.cli.parsers import parse_args
from bist_signal_bot.cli.commands import (

    cmd_patterns_list,
    cmd_patterns_detect,
    cmd_pattern_features,
    cmd_momentum_features,
    cmd_trend_features,
    cmd_healthcheck,
    cmd_config,
    cmd_symbols,
    cmd_validate_symbol,
    cmd_provider_status,
    cmd_storage_status,
    cmd_calendar_status,
    cmd_telegram_test,
    cmd_mock_data,
    cmd_quality_demo,
    cmd_version,
    cmd_diagnose,
    cmd_download_data,
    cmd_universe,
    cmd_clean_data,
    cmd_normalize_data,
    cmd_corporate_actions,
    cmd_adjust_data,
    cmd_indicators,
    cmd_volatility_features,
    cmd_volume_features,
    cmd_divergence_detect,
)
from bist_signal_bot.core.logging_setup import get_logger

logger = get_logger("bist_signal_bot.cli")

def cmd_instruments(args, app_context):
    import sys
    from bist_signal_bot.cli.commands import instruments
    # Strip everything before 'instruments'
    idx = sys.argv.index('instruments')
    instruments.main(args=sys.argv[idx+1:])

def cmd_corporate_actions_wrap(args, app_context):
    import sys
    from bist_signal_bot.cli.commands import corporate_actions
    idx = sys.argv.index('corporate-actions')
    corporate_actions.main(args=sys.argv[idx+1:])

def cmd_data_quality_wrap(args, app_context):
    import sys
    from bist_signal_bot.cli.commands import data_quality
    idx = sys.argv.index('data-quality')
    data_quality.main(args=sys.argv[idx+1:])



def dispatch_strategies(args, ctx) -> int:
    from bist_signal_bot.cli.commands import cmd_strategies_list, cmd_strategies_run, cmd_strategies_batch
    if args.strategies_cmd == "list":
        return cmd_strategies_list(args, ctx)
    elif args.strategies_cmd == "run":
        return cmd_strategies_run(args, ctx)
    elif args.strategies_cmd == "batch":
        return cmd_strategies_batch(args, ctx)
    return 1




def dispatch_validate_backtest(args, ctx) -> int:
    from bist_signal_bot.cli.commands import handle_validate_backtest
    handle_validate_backtest(args)
    return 0

def dispatch_backtest(args, ctx) -> int:
    from bist_signal_bot.cli.commands_backtest import handle_backtest_command
    return handle_backtest_command(args, ctx)

def dispatch_costs(args, ctx) -> int:


    from bist_signal_bot.cli.commands import handle_costs_command
    handle_costs_command(args, ctx.settings)
    return 0

def dispatch_security(args, ctx) -> int:
    from bist_signal_bot.cli.commands import handle_security_command
    handle_security_command(args, ctx.settings)
    return 0

def dispatch_quality(args, ctx) -> int:
    from bist_signal_bot.cli.commands import handle_quality_command
    handle_quality_command(args, ctx.settings)
    return 0

def dispatch_benchmarks(args, ctx) -> int:
    from bist_signal_bot.cli.commands import cmd_benchmarks_list, cmd_benchmarks_run, cmd_benchmarks_batch, cmd_benchmarks_default
    if args.benchmarks_cmd == "list":
        return cmd_benchmarks_list(args, ctx)
    elif args.benchmarks_cmd == "run":
        return cmd_benchmarks_run(args, ctx)
    elif args.benchmarks_cmd == "batch":
        return cmd_benchmarks_batch(args, ctx)
    elif args.benchmarks_cmd == "default":
        return cmd_benchmarks_default(args, ctx)
    return 1


def dispatch_risk(args, ctx) -> int:
    from bist_signal_bot.cli.commands import handle_risk_commands
    ctx.logger = logger
    return handle_risk_commands(args, ctx)

def run_cli(argv: list[str] | None = None) -> int:
    """Top-level CLI entry point."""
    import sys
    args_list = list(sys.argv[1:]) if argv is None else list(argv)
    first = args_list[0] if args_list else None

    if first == 'cli-ux':
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_cli_ux_subparser(subparsers)
        args, _ = parser.parse_known_args(args_list)
        handle_cli_ux(args)
        return 0
    if first == 'ops':
        import argparse
        from bist_signal_bot.cli.ops_commands import add_ops_subparsers, handle_ops_command
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_cli_ux_subparser(subparsers)
        add_ops_subparsers(subparsers)
        args, _ = parser.parse_known_args(args_list)
        handle_ops_command(args)
        return 0
    if first == 'factors':
        from bist_signal_bot.cli.factors_commands import factors_cli

        sys.argv = [sys.argv[0]] + args_list[1:]
        factors_cli()
        return 0
    if first == 'bootstrap':
        return _run_bootstrap_command(args_list[1:])

    import sys
    args_to_parse = args_list





    if args_to_parse and args_to_parse[0] == 'calibration':
        from bist_signal_bot.cli.routers.dispatchers import route_calibration
        return route_calibration(args_to_parse)


    if args_to_parse and args_to_parse[0] == 'portfolio-construct':
        from bist_signal_bot.cli.routers.dispatchers import route_portfolio_construct
        return route_portfolio_construct(args_to_parse)

    if args_to_parse and args_to_parse[0] == 'review':
        from bist_signal_bot.cli.commands import review
        import sys
        sys.argv = [sys.argv[0]] + args_to_parse[1:]
        review()
        return 0


    if args_to_parse and args_to_parse[0] == 'strategy-registry':
        from bist_signal_bot.cli.routers.dispatchers import route_strategy_registry
        return route_strategy_registry(args_to_parse)

    if args_to_parse and args_to_parse[0] == 'config-registry':
        from bist_signal_bot.cli.routers.dispatchers import route_config_registry
        return route_config_registry(args_to_parse)

    if args_to_parse and args_to_parse[0] == 'governance':
        from bist_signal_bot.cli.routers.dispatchers import route_governance
        return route_governance(args_to_parse)

    if args_to_parse and args_to_parse[0] == "event-calendar":
        from bist_signal_bot.cli.routers.dispatchers import route_event_calendar
        return route_event_calendar(args_to_parse)

    if args_to_parse and args_to_parse[0] == 'maintenance':
        from bist_signal_bot.cli.commands_maintenance import run_maintenance_cli
        import sys
        sys.argv = [sys.argv[0]] + args_to_parse[1:]
        run_maintenance_cli()
        return 0

    if args_to_parse and args_to_parse[0] == 'scenario':
        from bist_signal_bot.cli.commands_scenarios import scenario_cli
        import sys
        sys.argv = [sys.argv[0]] + args_to_parse[1:]
        scenario_cli()
        return 0






    if args_to_parse and args_to_parse[0] == 'valuation':
        from bist_signal_bot.cli.routers.dispatchers import route_valuation
        return route_valuation(args_to_parse)

    if args_to_parse and args_to_parse[0] == 'what-if':
        from bist_signal_bot.cli.routers.dispatchers import route_what_if
        return route_what_if(args_to_parse)

    if args_to_parse and args_to_parse[0] == 'explain':
        from bist_signal_bot.cli.routers.dispatchers import route_explain
        return route_explain(args_to_parse)

    if args_to_parse and args_to_parse[0] == 'validation':
        from bist_signal_bot.cli.validation_commands import app
        import sys
        sys.argv = [sys.argv[0]] + args_to_parse[1:]
        app()
        return 0

    if args_to_parse and args_to_parse[0] == 'docs':
        from bist_signal_bot.cli.commands import docs_app
        import sys
        sys.argv = [sys.argv[0]] + args_to_parse[1:]
        docs_app()
        return 0


    if args_to_parse and args_to_parse[0] == 'instruments':
        from bist_signal_bot.cli.commands import instruments
        import sys
        sys.argv = [sys.argv[0]] + args_to_parse[1:]
        instruments()
        return 0

    if args_to_parse and args_to_parse[0] == 'corporate-actions':
        from bist_signal_bot.cli.commands import corporate_actions
        import sys
        sys.argv = [sys.argv[0]] + args_to_parse[1:]
        corporate_actions()
        return 0

    if args_to_parse and args_to_parse[0] == 'data-quality':
        from bist_signal_bot.cli.commands import data_quality
        import sys
        sys.argv = [sys.argv[0]] + args_to_parse[1:]
        data_quality()
        return 0


    if args_to_parse and args_to_parse[0] == 'qa':
        from bist_signal_bot.cli.routers.dispatchers import route_qa
        return route_qa(args_to_parse)

    args = parse_args(argv)


    try:
        app_context = bootstrap_app()
    except Exception as e:
        logger.exception(f"Bootstrap failed: {e}")
        return 1

    # Audit log
    commands = {
        'cli-ux': handle_cli_ux,
        'scheduler': lambda args, ctx: __import__('bist_signal_bot.cli.scheduler_cli', fromlist=['']).handle_scheduler(args),
        "healthcheck": cmd_healthcheck,
        "config": cmd_config,
        "symbols": cmd_symbols,
        "validate-symbol": cmd_validate_symbol,
        "provider-status": cmd_provider_status,
        "storage-status": cmd_storage_status,
        "calendar-status": cmd_calendar_status,
        "telegram-test": cmd_telegram_test,
        "mock-data": cmd_mock_data,
        "quality-demo": cmd_quality_demo,
        "version": cmd_version,
        "diagnose": cmd_diagnose,
        "download-data": cmd_download_data,
        "universe": cmd_universe,
        "clean-data": cmd_clean_data,
        "normalize-data": cmd_normalize_data,
        "corporate-actions": cmd_corporate_actions,
        "adjust-data": cmd_adjust_data,
        "indicators": cmd_indicators,
        "trend-features": cmd_trend_features,
        "momentum-features": cmd_momentum_features,
        "volatility-features": cmd_volatility_features,
        "volume-features": cmd_volume_features,
        "patterns": lambda a, c: cmd_patterns_list(a, c) if a.patterns_command == 'list' else cmd_patterns_detect(a, c),
        "pattern-features": cmd_pattern_features,
        "divergence": lambda a, c: cmd_divergence_detect(a, c) if getattr(a, "subcommand", None) == "detect" else 1,
        "strategies": dispatch_strategies,
        "benchmarks": dispatch_benchmarks,
        "costs": dispatch_costs,
        "backtest": dispatch_backtest,
        "security": dispatch_security,
        "quality": dispatch_quality,
        "validate-backtest": dispatch_validate_backtest,
        "risk": dispatch_risk,
        "optimize": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["cmd_optimize"]).cmd_optimize(a, c),
        "ml-dataset": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["handle_ml_dataset_command"]).handle_ml_dataset_command(a, c.settings),
        "runtime": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["cmd_runtime"]).cmd_runtime(a, c.settings),
        "monitor": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["cmd_monitor"]).cmd_monitor(a, c.settings),
        "package": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["run_package_command"]).run_package_command(a, c.settings),
        "performance": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["handle_performance_command"]).handle_performance_command(a, c.settings),
        "perf": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["handle_performance_command"]).handle_performance_command(a, c.settings),
        "docs": lambda a, c: __import__("typer").run(__import__("bist_signal_bot.cli.commands", fromlist=["docs_app"]).docs_app(), sys.argv[2:]),
        "adaptive": lambda a, c: __import__("bist_signal_bot.cli.adaptive_commands", fromlist=["handle_adaptive_commands"]).handle_adaptive_commands(a),
        "scan": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["cmd_scan"]).cmd_scan(a, c.settings),

        "scenario": lambda a, c: __import__("bist_signal_bot.cli.commands").cli(sys.argv[1:], prog_name="bist_signal_bot"),


                "qa": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["handle_qa_command"]).handle_qa_command(a, c.settings),
        "research": lambda a, c: __import__("bist_signal_bot.cli.commands_research", fromlist=["handle_research_commands"]).handle_research_commands(a, c.settings),
        "breadth": lambda a, c: __import__("bist_signal_bot.cli.commands_breadth", fromlist=["handle_breadth_commands"]).handle_breadth_commands(a, c.settings),
    }

    cmd_func = commands.get(args.command)
    if not cmd_func:
        logger.error(f"Unknown command: {args.command}")
        return 1

    try:
        return cmd_func(args, app_context)
    except Exception as e:
        app_context.error_handler.handle_exception(e, context={"command": args.command})
        if getattr(args, "json", False):
            from bist_signal_bot.cli.formatting import print_output
            print_output({"error": str(e), "command": args.command}, as_json=True)
        else:
            from bist_signal_bot.cli.formatting import format_error
            print(format_error(str(e)))
        return 1

if __name__ == "__main__":
    sys.exit(run_cli())



# Registering factors cli via click syntax directly to the main click group

# Normally we would attach to the root click group here



def _run_bootstrap_command(rest: list[str]) -> int:
    """Handle ``bootstrap demo`` — run the offline capability demo (best-effort)."""
    sub = rest[0] if rest else "demo"
    if sub == "demo":
        from bist_signal_bot.bootstrap.demo import OfflineDemoRunner
        runner = OfflineDemoRunner()
        run = runner.run_demo(save=("--save" in rest))
        for line in runner.demo_summary(run):
            print(line)
        return 0  # best-effort; the summary reports per-command status
    print(f"Unknown bootstrap subcommand: {sub!r} (expected: demo)")
    return 1


