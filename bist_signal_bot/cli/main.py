import sys

from bist_signal_bot.app.bootstrap import bootstrap_app
from bist_signal_bot.cli.parsers import parse_args
from bist_signal_bot.cli.commands import (
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
    cmd_indicators
)
from bist_signal_bot.core.logging_setup import get_logger

logger = get_logger("bist_signal_bot.cli")

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
        "trend-features": cmd_trend_features
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
