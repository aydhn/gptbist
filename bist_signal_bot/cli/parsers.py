import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bist_signal_bot",
        description="BIST Signal Bot - Command Line Interface"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # healthcheck
    healthcheck_parser = subparsers.add_parser("healthcheck", help="System health check summary")
    healthcheck_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    healthcheck_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # config
    config_parser = subparsers.add_parser("config", help="Safe configuration summary")
    config_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # symbols
    symbols_parser = subparsers.add_parser("symbols", help="List default BIST seed symbol universe")
    symbols_parser.add_argument("--yfinance", action="store_true", help="List in yfinance format")
    symbols_parser.add_argument("--group", type=str, help="Filter by symbol group")
    symbols_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # validate-symbol
    validate_parser = subparsers.add_parser("validate-symbol", help="Normalize and validate a symbol")
    validate_parser.add_argument("symbol", type=str, help="Symbol to validate")
    validate_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # provider-status
    provider_parser = subparsers.add_parser("provider-status", help="Show data provider status")
    provider_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # storage-status
    storage_parser = subparsers.add_parser("storage-status", help="Show local storage status")
    storage_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # calendar-status
    calendar_parser = subparsers.add_parser("calendar-status", help="Show BIST market calendar and session status")
    calendar_parser.add_argument("--at", type=str, help="ISO format datetime to check (default: now)")
    calendar_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # telegram-test
    telegram_parser = subparsers.add_parser("telegram-test", help="Test Telegram configuration (dry-run by default)")
    telegram_parser.add_argument("--message", type=str, default="BIST Bot test mesajı", help="Message to send")

    # mock-data
    mock_parser = subparsers.add_parser("mock-data", help="Generate deterministic mock data for a symbol")
    mock_parser.add_argument("symbol", type=str, help="Symbol to generate mock data for")
    mock_parser.add_argument("--rows", type=int, default=252, help="Number of rows to generate")
    mock_parser.add_argument("--save", action="store_true", help="Save to local store")
    mock_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # quality-demo
    quality_parser = subparsers.add_parser("quality-demo", help="Run DataQualityChecker on mock data")
    quality_parser.add_argument("symbol", type=str, help="Symbol to run quality demo for")
    quality_parser.add_argument("--rows", type=int, default=252, help="Number of rows")
    quality_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # version
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # diagnose
    diagnose_parser = subparsers.add_parser("diagnose", help="Show detailed diagnostic output")
    diagnose_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    return parser

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        args.command = "healthcheck"
        args.json = False
        args.verbose = False
    return args
