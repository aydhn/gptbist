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
    args = parse_args(argv)

    try:
        app_context = bootstrap_app()
    except Exception as e:
        logger.exception(f"Bootstrap failed: {e}")
        return 1

    # Audit log
    if app_context.audit_logger:
        safe_args = vars(args).copy()
        from bist_signal_bot.core.audit import AuditEvent, AuditEventType
        app_context.audit_logger.log_event(AuditEvent(
            event_type=AuditEventType.CLI_COMMAND,
            message=f"Executed CLI command: {args.command}",
            run_id=app_context.runtime_context.run_id,
            metadata={
                "command": args.command,
                "args": safe_args
            }
        ))

    commands = {
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

        "ml-dataset": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["handle_ml_dataset_command"]).handle_ml_dataset_command(a, c.settings),
        "runtime": lambda a, c: __import__("bist_signal_bot.cli.commands", fromlist=["cmd_runtime"]).cmd_runtime(a, c.settings),


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
