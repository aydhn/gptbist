import argparse

def add_costs_parser(subparsers):
    costs_parser = subparsers.add_parser(
        "costs",
        help="Estimate transaction costs, slippage, and spread."
    )
    costs_subparsers = costs_parser.add_subparsers(dest="costs_command", required=True)

    estimate_parser = costs_subparsers.add_parser("estimate", help="Estimate transaction cost for a single trade.")
    estimate_parser.add_argument("symbol", type=str, help="Symbol to estimate cost for (e.g. ASELS)")
    estimate_parser.add_argument("--side", type=str, required=True, choices=["BUY", "SELL"], help="Order side")
    estimate_parser.add_argument("--quantity", type=float, required=True, help="Quantity of shares")
    estimate_parser.add_argument("--price", type=float, required=True, help="Price per share")
    estimate_parser.add_argument("--avg-daily-volume", type=float, dest="avg_daily_volume", help="Average daily volume for slippage calculation")
    estimate_parser.add_argument("--avg-daily-turnover", type=float, dest="avg_daily_turnover", help="Average daily turnover for spread bucket calculation")
    estimate_parser.add_argument("--volatility", type=float, help="Volatility for slippage calculation")
    estimate_parser.add_argument("--scenario", type=str, choices=["OPTIMISTIC", "BASE", "CONSERVATIVE", "STRESS"], help="Cost scenario to use")
    estimate_parser.add_argument("--json", action="store_true", help="Output result as JSON")

    round_trip_parser = costs_subparsers.add_parser("round-trip", help="Estimate total round trip cost for an entry and exit.")
    round_trip_parser.add_argument("symbol", type=str, help="Symbol to estimate cost for (e.g. ASELS)")
    round_trip_parser.add_argument("--side", type=str, required=True, choices=["BUY", "SELL"], help="Entry order side")
    round_trip_parser.add_argument("--quantity", type=float, required=True, help="Quantity of shares")
    round_trip_parser.add_argument("--entry-price", type=float, dest="entry_price", required=True, help="Entry price per share")
    round_trip_parser.add_argument("--exit-price", type=float, dest="exit_price", required=True, help="Exit price per share")
    round_trip_parser.add_argument("--scenario", type=str, choices=["OPTIMISTIC", "BASE", "CONSERVATIVE", "STRESS"], help="Cost scenario to use")
    round_trip_parser.add_argument("--json", action="store_true", help="Output result as JSON")

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", None) is None:
        args.command = "healthcheck"
        args.json = False
        args.verbose = False
    return args

def add_backtest_parser(subparsers):
    parser_backtest = subparsers.add_parser("backtest", help="Backtest engine operations")
    backtest_subparsers = parser_backtest.add_subparsers(dest="backtest_cmd", required=True)

    # backtest run
    run_parser = backtest_subparsers.add_parser("run", help="Run backtest on a single symbol")
    run_parser.add_argument("symbol", type=str, help="Symbol to run backtest for")
    run_parser.add_argument("--strategy", type=str, required=True, help="Strategy name")
    run_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    run_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g., 1d)")
    run_parser.add_argument("--period", type=str, help="History period")
    run_parser.add_argument("--rows", type=int, help="Rows for mock data")
    run_parser.add_argument("--param", type=str, action="append", help="Strategy parameters")
    run_parser.add_argument("--initial-capital", type=float, help="Initial capital")
    run_parser.add_argument("--execution", type=str, choices=["NEXT_OPEN", "NEXT_CLOSE", "SAME_CLOSE_FOR_RESEARCH_ONLY"], help="Execution mode")
    run_parser.add_argument("--cost-scenario", type=str, choices=["OPTIMISTIC", "BASE", "CONSERVATIVE", "STRESS"], help="Cost scenario")
    run_parser.add_argument("--max-position-size-pct", type=float, help="Max position size percentage")
    run_parser.add_argument("--allow-short", action="store_true", help="Allow short trades")
    run_parser.add_argument("--no-costs", action="store_true", help="Disable commission and slippage")
    run_parser.add_argument("--save-results", action="store_true", help="Save backtest results")
    run_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # backtest batch
    batch_parser = backtest_subparsers.add_parser("batch", help="Run backtest on multiple symbols")
    batch_parser.add_argument("--strategy", type=str, required=True, help="Strategy name")

    group = batch_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbols", type=str, nargs="+", help="List of symbols")
    group.add_argument("--all", action="store_true", help="Run on all symbols")
    group.add_argument("--group", type=str, help="Run on symbol group")

    batch_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    batch_parser.add_argument("--param", type=str, action="append", help="Strategy parameters")
    batch_parser.add_argument("--initial-capital", type=float, help="Initial capital")
    batch_parser.add_argument("--execution", type=str, choices=["NEXT_OPEN", "NEXT_CLOSE", "SAME_CLOSE_FOR_RESEARCH_ONLY"], help="Execution mode")
    batch_parser.add_argument("--cost-scenario", type=str, choices=["OPTIMISTIC", "BASE", "CONSERVATIVE", "STRESS"], help="Cost scenario")
    batch_parser.add_argument("--max-position-size-pct", type=float, help="Max position size percentage")
    batch_parser.add_argument("--allow-short", action="store_true", help="Allow short trades")
    batch_parser.add_argument("--no-costs", action="store_true", help="Disable commission and slippage")
    batch_parser.add_argument("--save-results", action="store_true", help="Save backtest results")
    batch_parser.add_argument("--json", action="store_true", help="Output in JSON format")

def add_validate_backtest_parser(subparsers):
    validate_parser = subparsers.add_parser("validate-backtest", help="Walk-forward analysis, robustness, and out-of-sample testing")
    validate_subparsers = validate_parser.add_subparsers(dest="validate_command", required=True)

    # train-test
    train_test_parser = validate_subparsers.add_parser("train-test", help="Run a single train/test split backtest")
    train_test_parser.add_argument("symbol", type=str, help="Symbol to test")
    train_test_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    train_test_parser.add_argument("--strategy", type=str, required=True, help="Strategy to test")
    train_test_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    train_test_parser.add_argument("--period", type=str, help="History period")
    train_test_parser.add_argument("--rows", type=int, help="Rows for mock data")
    train_test_parser.add_argument("--train-ratio", type=float, help="Train ratio (e.g. 0.7)")
    train_test_parser.add_argument("--compare-benchmark", type=str, help="Benchmark to compare against")
    train_test_parser.add_argument("--param", action="append", help="Strategy parameter key=value")
    train_test_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # walk-forward
    wf_parser = validate_subparsers.add_parser("walk-forward", help="Run walk-forward cross-validation")
    wf_parser.add_argument("symbol", type=str, help="Symbol to test")
    wf_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    wf_parser.add_argument("--strategy", type=str, required=True, help="Strategy to test")
    wf_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    wf_parser.add_argument("--period", type=str, help="History period")
    wf_parser.add_argument("--rows", type=int, help="Rows for mock data")
    wf_parser.add_argument("--train-window", type=int, help="Train window rows")
    wf_parser.add_argument("--test-window", type=int, help="Test window rows")
    wf_parser.add_argument("--step", type=int, help="Step rows")
    wf_parser.add_argument("--expanding", action="store_true", help="Use expanding window")
    wf_parser.add_argument("--max-splits", type=int, help="Maximum number of splits")
    wf_parser.add_argument("--save-report", action="store_true", help="Save reports to disk")
    wf_parser.add_argument("--format", type=str, choices=["json", "markdown", "csv", "all"], help="Report format to save")
    wf_parser.add_argument("--param", action="append", help="Strategy parameter key=value")
    wf_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # robustness
    rob_parser = validate_subparsers.add_parser("robustness", help="Run parameter robustness test")
    rob_parser.add_argument("symbol", type=str, help="Symbol to test")
    rob_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    rob_parser.add_argument("--strategy", type=str, required=True, help="Strategy to test")
    rob_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    rob_parser.add_argument("--period", type=str, help="History period")
    rob_parser.add_argument("--rows", type=int, help="Rows for mock data")
    rob_parser.add_argument("--param-range", action="append", required=True, help="Parameter range: name=val1,val2,val3")
    rob_parser.add_argument("--max-runs", type=int, help="Maximum number of robustness runs")
    rob_parser.add_argument("--json", action="store_true", help="Output in JSON format")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bist_signal_bot",
        description="BIST Signal Bot CLI"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Format all output as JSON"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    healthcheck_parser = subparsers.add_parser("healthcheck", help="Check system components health")
    config_parser = subparsers.add_parser("config", help="View current configuration")
    config_parser.add_argument("--hide-secrets", action="store_true", default=True, help="Mask sensitive fields")
    config_parser.add_argument("--show-secrets", action="store_false", dest="hide_secrets", help="Show sensitive fields")

    symbols_parser = subparsers.add_parser("symbols", help="List default BIST seed symbol universe")
    validate_symbol_parser = subparsers.add_parser("validate-symbol", help="Validate a symbol format against BIST rules")
    validate_symbol_parser.add_argument("symbol", type=str, help="Symbol to validate")

    provider_status_parser = subparsers.add_parser("provider-status", help="Check market data provider status")
    storage_status_parser = subparsers.add_parser("storage-status", help="Check local storage status")
    calendar_parser = subparsers.add_parser("calendar-status", help="Check market calendar and session status")
    calendar_parser.add_argument("--at", type=str, help="ISO format datetime to check (default: now)")

    telegram_parser = subparsers.add_parser("telegram-test", help="Test Telegram configuration (dry-run by default)")
    telegram_parser.add_argument("--message", type=str, default="BIST Bot test mesajı", help="Message to send")
    telegram_parser.add_argument("--real", action="store_true", help="Send a real message if configured")

    mock_parser = subparsers.add_parser("mock-data", help="Generate mock market data for testing")
    mock_parser.add_argument("symbol", type=str, help="Symbol to generate data for")
    mock_parser.add_argument("--rows", type=int, default=252, help="Number of rows to generate")

    quality_parser = subparsers.add_parser("quality-demo", help="Generate mock data with synthetic errors to demonstrate quality checks")
    quality_parser.add_argument("symbol", type=str, help="Symbol to generate data for")
    quality_parser.add_argument("--rows", type=int, default=252, help="Number of rows")

    clean_parser = subparsers.add_parser("clean-data", help="Apply data cleaning policies to OHLCV data")
    clean_parser.add_argument("symbol", type=str, help="Symbol to clean")
    clean_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Source to read data from")
    clean_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")

    normalize_parser = subparsers.add_parser("normalize-data", help="Apply normalization to ensure proper column names and types")
    normalize_parser.add_argument("symbol", type=str, help="Symbol to normalize")
    normalize_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Source to read data from")
    normalize_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")

    adjust_parser = subparsers.add_parser("adjust-data", help="Apply price adjustments for corporate actions")
    adjust_parser.add_argument("symbol", type=str, help="Symbol to adjust")
    adjust_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Source to read data from")
    adjust_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")
    adjust_parser.add_argument("--policy", type=str, choices=["STRICT", "FLEXIBLE", "FLAG_ONLY"], default="FLEXIBLE", help="Adjustment Policy")

    ca_parser = subparsers.add_parser("corporate-actions", help="Manage corporate actions")
    ca_subparsers = ca_parser.add_subparsers(dest="ca_command", required=True)

    ca_list_parser = ca_subparsers.add_parser("list", help="List all corporate actions for a symbol")
    ca_list_parser.add_argument("symbol", type=str, help="Symbol")
    ca_list_parser.add_argument("--verified-only", action="store_true", help="Show only verified actions")

    ca_add_parser = ca_subparsers.add_parser("add", help="Add a new corporate action")
    ca_add_parser.add_argument("symbol", type=str, help="Symbol")
    ca_add_parser.add_argument("--type", type=str, required=True, choices=["DIVIDEND", "STOCK_SPLIT"], help="Action type")
    ca_add_parser.add_argument("--ex-date", type=str, required=True, help="Ex-dividend date (YYYY-MM-DD)")
    ca_add_parser.add_argument("--value", type=float, required=True, help="Dividend amount or split ratio")
    ca_add_parser.add_argument("--verified", action="store_true", help="Mark as verified")

    ca_export_parser = ca_subparsers.add_parser("export", help="Export corporate actions")
    ca_export_parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Export format")
    ca_export_parser.add_argument("--output", type=str, required=True, help="Output file path")

    ind_calc_parser = subparsers.add_parser("indicators", help="Calculate technical indicators for a symbol")
    ind_calc_parser.add_argument("symbol", type=str, help="Symbol to calculate indicators for")
    ind_calc_parser.add_argument("--source", type=str, choices=["local", "mock"], default="mock", help="Data source")
    ind_calc_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    ind_calc_parser.add_argument("--indicators", type=str, help="Comma-separated list of indicators to calculate (e.g. sma_20,rsi_14)")
    ind_calc_parser.add_argument("--default-set", action="store_true", help="Calculate default indicator set")
    ind_calc_parser.add_argument("--rows", type=int, default=500, help="Number of rows for mock data")

    momentum_features_parser = subparsers.add_parser("momentum-features", help="Calculate comprehensive momentum features for a symbol")
    momentum_features_parser.add_argument("symbol", type=str, help="Symbol")
    momentum_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    momentum_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    momentum_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")

    trend_parser = subparsers.add_parser("trend-features", help="Calculate trend features for a symbol")
    trend_parser.add_argument("symbol", type=str, help="Symbol")
    trend_parser.add_argument("--source", type=str, choices=["local", "mock"], default="mock", help="Data source")
    trend_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    trend_parser.add_argument("--rows", type=int, default=500, help="Number of rows for mock data")
    trend_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")

    download_parser = subparsers.add_parser("download-data", help="Download OHLCV data from provider")
    download_subparsers = download_parser.add_subparsers(dest="download_command", required=True)

    download_single = download_subparsers.add_parser("single", help="Download data for a single symbol")
    download_single.add_argument("symbol", type=str, help="Symbol to download")
    download_single.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")
    download_single.add_argument("--period", type=str, default="2y", help="Period (e.g. 2y, max)")

    download_batch = download_subparsers.add_parser("batch", help="Download data for multiple symbols")
    download_batch.add_argument("--symbols", type=str, nargs="+", help="List of symbols to download")
    download_batch.add_argument("--all-active", action="store_true", help="Download for all active symbols in universe")
    download_batch.add_argument("--group", type=str, help="Download for a specific symbol group")
    download_batch.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    download_batch.add_argument("--period", type=str, default="2y", help="Period")

    version_parser = subparsers.add_parser("version", help="Show application version")
    diagnose_parser = subparsers.add_parser("diagnose", help="Run diagnostic checks on the environment")

    universe_parser = subparsers.add_parser("universe", help="Manage symbol universe")
    universe_subparsers = universe_parser.add_subparsers(dest="universe_command", required=True)

    init_parser = universe_subparsers.add_parser("init", help="Initialize default universe")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing universe")

    list_parser = universe_subparsers.add_parser("list", help="List symbols in universe")
    list_parser.add_argument("--active-only", action="store_true", help="Show only active symbols")
    list_parser.add_argument("--group", type=str, help="Filter by group")

    add_parser = universe_subparsers.add_parser("add", help="Add symbol to universe")
    add_parser.add_argument("symbol", type=str, help="Symbol to add")
    add_parser.add_argument("--name", type=str, help="Company name")
    add_parser.add_argument("--group", type=str, help="Symbol group")

    remove_parser = universe_subparsers.add_parser("remove", help="Remove symbol from universe")
    remove_parser.add_argument("symbol", type=str, help="Symbol to remove")

    update_parser = universe_subparsers.add_parser("update", help="Update symbol from data provider")
    update_parser.add_argument("--symbol", type=str, help="Specific symbol to update (optional)")

    export_parser = universe_subparsers.add_parser("export", help="Export universe data")
    export_parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Export format")
    export_parser.add_argument("--output", type=str, required=True, help="Output file path")

    patterns_parser = subparsers.add_parser("patterns", help="Manage and run pattern detection")
    patterns_subparsers = patterns_parser.add_subparsers(dest="patterns_command", required=True)

    p_list_parser = patterns_subparsers.add_parser("list", help="List registered pattern detectors")

    p_detect_parser = patterns_subparsers.add_parser("detect", help="Run pattern detection on a symbol")
    p_detect_parser.add_argument("symbol", type=str, help="Symbol to detect patterns for")
    p_detect_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    p_detect_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    p_detect_parser.add_argument("--patterns", type=str, help="Comma-separated list of patterns to detect")
    p_detect_parser.add_argument("--default-set", action="store_true", help="Run default pattern set")

    pattern_features_parser = subparsers.add_parser("pattern-features", help="Calculate comprehensive pattern features for a symbol")
    pattern_features_parser.add_argument("symbol", type=str, help="Symbol")
    pattern_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    pattern_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    pattern_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")

    volume_features_parser = subparsers.add_parser("volume-features", help="Calculate volume features for a symbol")
    volume_features_parser.add_argument("symbol", type=str, help="Symbol")
    volume_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    volume_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    volume_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")

    volatility_features_parser = subparsers.add_parser("volatility-features", help="Calculate volatility features for a symbol")
    volatility_features_parser.add_argument("symbol", type=str, help="Symbol")
    volatility_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    volatility_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    volatility_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")

    divergence_parser = subparsers.add_parser("divergence", help="Divergence detection operations")
    divergence_subparsers = divergence_parser.add_subparsers(dest="subcommand", required=True)

    div_detect_parser = divergence_subparsers.add_parser("detect", help="Detect divergences for a symbol")
    div_detect_parser.add_argument("symbol", help="Symbol to check")
    div_detect_parser.add_argument("--source", choices=["local", "mock"], default="local", help="Data source")
    div_detect_parser.add_argument("--timeframe", default="1d", help="Timeframe (e.g. 1d, 1h)")
    div_detect_parser.add_argument("--indicators", help="Comma separated indicators (e.g. rsi,macd_hist,obv)")
    div_detect_parser.add_argument("--pivot-mode", choices=["LOOKBACK_ONLY", "CONFIRMED_LAGGED"], default="LOOKBACK_ONLY", help="Pivot detection mode")
    div_detect_parser.add_argument("--lookback", type=int, help="Lookback window for pivots")
    div_detect_parser.add_argument("--min-distance", type=int, dest="min_pivot_distance", help="Min distance between pivots")
    div_detect_parser.add_argument("--max-distance", type=int, dest="max_pivot_distance", help="Max distance between pivots")
    div_detect_parser.set_defaults(include_hidden=True, include_regular=True)

    strategies_parser = subparsers.add_parser("strategies", help="Strategy engine operations")
    strategies_subparsers = strategies_parser.add_subparsers(dest="strategies_cmd", required=True)

    # strategies list
    strategies_subparsers.add_parser("list", help="List registered strategies")

    # strategies run
    run_strat_parser = strategies_subparsers.add_parser("run", help="Run a strategy on a single symbol")
    run_strat_parser.add_argument("strategy", type=str, help="Strategy name")
    run_strat_parser.add_argument("symbol", type=str, help="Symbol to run strategy for")
    run_strat_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    run_strat_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g., 1d, 1wk)")
    run_strat_parser.add_argument("--period", type=str, help="History period")
    run_strat_parser.add_argument("--rows", type=int, help="Rows for mock data")
    run_strat_parser.add_argument("--param", type=str, action="append", help="Strategy parameters (e.g., fast_window=10)")
    run_strat_parser.add_argument("--save-output", action="store_true", help="Save features and signals to CSV")
    run_strat_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # strategies batch
    batch_strat_parser = strategies_subparsers.add_parser("batch", help="Run a strategy on multiple symbols")
    batch_strat_parser.add_argument("strategy", type=str, help="Strategy name")

    group = batch_strat_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbols", type=str, nargs="+", help="List of symbols")
    group.add_argument("--all", action="store_true", help="Run on all symbols in universe")
    group.add_argument("--group", type=str, help="Run on a specific symbol group")

    batch_strat_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    batch_strat_parser.add_argument("--timeframe", type=str, help="Timeframe")
    batch_strat_parser.add_argument("--period", type=str, help="History period")
    batch_strat_parser.add_argument("--param", type=str, action="append", help="Strategy parameters")
    batch_strat_parser.add_argument("--min-score", type=float, help="Minimum signal score to report")
    batch_strat_parser.add_argument("--save-output", action="store_true", help="Save summary report to CSV/JSON")
    batch_strat_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    benchmarks_parser = subparsers.add_parser("benchmarks", help="Benchmark strategy operations")
    benchmarks_subparsers = benchmarks_parser.add_subparsers(dest="benchmarks_cmd", required=True)

    # benchmarks list
    benchmarks_subparsers.add_parser("list", help="List registered benchmarks")

    # benchmarks run
    run_bench_parser = benchmarks_subparsers.add_parser("run", help="Run a benchmark on a single symbol")
    run_bench_parser.add_argument("benchmark", type=str, help="Benchmark name")
    run_bench_parser.add_argument("symbol", type=str, help="Symbol to run benchmark for")
    run_bench_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    run_bench_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g., 1d)")
    run_bench_parser.add_argument("--period", type=str, help="History period")
    run_bench_parser.add_argument("--rows", type=int, help="Rows for mock data")
    run_bench_parser.add_argument("--param", type=str, action="append", help="Benchmark parameters")
    run_bench_parser.add_argument("--save-output", action="store_true", help="Save features and signals to CSV")
    run_bench_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # benchmarks batch
    batch_bench_parser = benchmarks_subparsers.add_parser("batch", help="Run a benchmark on multiple symbols")
    batch_bench_parser.add_argument("benchmark", type=str, help="Benchmark name")

    group = batch_bench_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbols", type=str, nargs="+", help="List of symbols")
    group.add_argument("--all", action="store_true", help="Run on all symbols in universe")
    group.add_argument("--group", type=str, help="Run on a specific symbol group")

    batch_bench_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    batch_bench_parser.add_argument("--timeframe", type=str, help="Timeframe")
    batch_bench_parser.add_argument("--period", type=str, help="History period")
    batch_bench_parser.add_argument("--param", type=str, action="append", help="Benchmark parameters")
    batch_bench_parser.add_argument("--save-output", action="store_true", help="Save summary report to CSV/JSON")
    batch_bench_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # benchmarks default
    default_bench_parser = benchmarks_subparsers.add_parser("default", help="Run default set of benchmarks on a symbol")
    default_bench_parser.add_argument("symbol", type=str, help="Symbol to run default benchmarks for")
    default_bench_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    default_bench_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    default_bench_parser.add_argument("--period", type=str, help="History period")
    default_bench_parser.add_argument("--rows", type=int, help="Rows for mock data")
    default_bench_parser.add_argument("--json", action="store_true", help="Output in JSON format")


    add_costs_parser(subparsers)
    add_validate_backtest_parser(subparsers)
    add_backtest_parser(subparsers)
    return parser
