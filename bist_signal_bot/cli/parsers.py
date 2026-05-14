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
    add_optimize_parser(subparsers)
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
    run_parser.add_argument("--use-risk-engine", action="store_true", help="Use risk engine")

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



    # Risk Engine commands
    risk_parser = subparsers.add_parser("risk", help="Risk engine operations")
    risk_subparsers = risk_parser.add_subparsers(dest="risk_cmd", required=True)

    # risk evaluate
    risk_eval_parser = risk_subparsers.add_parser("evaluate", help="Evaluate a strategy signal with the risk engine")
    risk_eval_parser.add_argument("symbol", type=str, help="Symbol to evaluate")
    risk_eval_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    risk_eval_parser.add_argument("--strategy", type=str, required=True, help="Strategy name")
    risk_eval_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    risk_eval_parser.add_argument("--rows", type=int, help="Rows for mock data")
    risk_eval_parser.add_argument("--param", type=str, action="append", help="Strategy parameters (e.g. key=val)")
    risk_eval_parser.add_argument("--equity", type=float, help="Account equity")
    risk_eval_parser.add_argument("--cash", type=float, help="Available cash")
    risk_eval_parser.add_argument("--daily-signal-count", type=int, help="Daily signal count")
    risk_eval_parser.add_argument("--open-position-count", type=int, help="Open position count")
    risk_eval_parser.add_argument("--portfolio-risk-pct", type=float, help="Current portfolio risk percent")
    risk_eval_parser.add_argument("--sizing", type=str, help="Position sizing method")
    risk_eval_parser.add_argument("--stop", type=str, help="Stop method")
    risk_eval_parser.add_argument("--target", type=str, help="Target method")
    risk_eval_parser.add_argument("--json", action="store_true", help="Output JSON")

    # risk size
    risk_size_parser = risk_subparsers.add_parser("size", help="Calculate position size")
    risk_size_parser.add_argument("symbol", type=str, help="Symbol to evaluate")
    risk_size_parser.add_argument("--side", type=str, required=True, choices=["LONG", "SHORT"], help="Trade side")
    risk_size_parser.add_argument("--entry", type=float, required=True, help="Entry price")
    risk_size_parser.add_argument("--stop", type=float, help="Stop price")
    risk_size_parser.add_argument("--target", type=float, help="Target price")
    risk_size_parser.add_argument("--equity", type=float, required=True, help="Account equity")
    risk_size_parser.add_argument("--method", type=str, help="Position sizing method")
    risk_size_parser.add_argument("--json", action="store_true", help="Output JSON")

    # risk stop-target
    risk_st_parser = risk_subparsers.add_parser("stop-target", help="Calculate stop/target reference")
    risk_st_parser.add_argument("symbol", type=str, help="Symbol to evaluate")
    risk_st_parser.add_argument("--side", type=str, required=True, choices=["LONG", "SHORT"], help="Trade side")
    risk_st_parser.add_argument("--entry", type=float, required=True, help="Entry price")
    risk_st_parser.add_argument("--atr", type=float, help="Optional ATR value for ATR-based methods")
    risk_st_parser.add_argument("--method-stop", type=str, help="Stop method")
    risk_st_parser.add_argument("--method-target", type=str, help="Target method")
    risk_st_parser.add_argument("--json", action="store_true", help="Output JSON")

    # risk config
    risk_cfg_parser = risk_subparsers.add_parser("config", help="Show risk configuration summary")
    risk_cfg_parser.add_argument("--json", action="store_true", help="Output JSON")

    add_costs_parser(subparsers)

    add_validate_backtest_parser(subparsers)
    add_backtest_parser(subparsers)

    # SCAN
    scan_parser = subparsers.add_parser("scan", help="Signal Scanner v1")
    scan_sub = scan_parser.add_subparsers(dest="scan_command", required=True)

    scan_sym = scan_sub.add_parser("symbols", help="Scan explicit symbols")
    scan_sym.add_argument("symbols", nargs="+")
    scan_sym.add_argument("--source", default="mock")
    scan_sym.add_argument("--strategy", required=True)
    scan_sym.add_argument("--top", type=int, default=10)
    scan_sym.add_argument("--sort", default="FINAL_SCORE")
    scan_sym.add_argument("--no-portfolio-risk", action="store_true")
    scan_sym.add_argument("--json", action="store_true")

    scan_wl = scan_sub.add_parser("watchlist", help="Scan a watchlist")
    scan_wl.add_argument("watchlist")
    scan_wl.add_argument("--source", default="mock")
    scan_wl.add_argument("--strategy", required=True)
    scan_wl.add_argument("--save-report", action="store_true")
    scan_wl.add_argument("--telegram", action="store_true")

    scan_group = scan_sub.add_parser("group", help="Scan a group")
    scan_group.add_argument("group")
    scan_group.add_argument("--source", default="mock")
    scan_group.add_argument("--strategy", required=True)
    scan_group.add_argument("--top", type=int, default=10)

    scan_all = scan_sub.add_parser("all", help="Scan all active symbols")
    scan_all.add_argument("--source", default="mock")
    scan_all.add_argument("--strategy", required=True)
    scan_all.add_argument("--top", type=int, default=10)
    scan_all.add_argument("--save-report", action="store_true")

    scan_recent = scan_sub.add_parser("recent", help="List recent scans")
    scan_recent.add_argument("--limit", type=int, default=20)
    scan_recent.add_argument("--json", action="store_true")

    scan_config = scan_sub.add_parser("config", help="Show scanner config")
    scan_config.add_argument("--json", action="store_true")


    # Runtime Parser
    parser_runtime = subparsers.add_parser('runtime', help="Runtime orchestrator commands")
    runtime_subparsers = parser_runtime.add_subparsers(dest='runtime_command', required=True)

    # run-once
    parser_run_once = runtime_subparsers.add_parser('run-once', help="Run the pipeline once")
    parser_run_once.add_argument('--source', default='mock', help="Data source")
    parser_run_once.add_argument('--strategy', default='moving_average_trend', help="Strategy name")
    parser_run_once.add_argument('--group', help="Universe group")
    parser_run_once.add_argument('--symbols', nargs='+', help="Specific symbols")
    parser_run_once.add_argument('--ml-filter', action='store_true', help="Enable ML filter")
    parser_run_once.add_argument('--ml-model-id', help="ML model ID")
    parser_run_once.add_argument('--regime-filter', action='store_true', help="Enable regime filter")
    parser_run_once.add_argument('--paper', action='store_true', help="Enable paper trading")
    parser_run_once.add_argument('--telegram', action='store_true', help="Send Telegram summary")

    # dry-run
    parser_dry_run = runtime_subparsers.add_parser('dry-run', help="Dry run the pipeline")
    parser_dry_run.add_argument('--source', default='mock', help="Data source")
    parser_dry_run.add_argument('--strategy', default='moving_average_trend', help="Strategy name")
    parser_dry_run.add_argument('--symbols', nargs='+', help="Specific symbols")

    # loop
    parser_loop = runtime_subparsers.add_parser('loop', help="Run the pipeline in a loop")
    parser_loop.add_argument('--interval', type=int, default=60, help="Interval in minutes")
    parser_loop.add_argument('--max-iterations', type=int, default=0, help="Max iterations")
    parser_loop.add_argument('--run-immediately', action='store_true', help="Run immediately")
    parser_loop.add_argument('--source', default='mock', help="Data source")
    parser_loop.add_argument('--strategy', default='moving_average_trend', help="Strategy name")
    parser_loop.add_argument('--symbols', nargs='+', help="Specific symbols")

    # status
    parser_status = runtime_subparsers.add_parser('status', help="Show runtime status")

    # history
    parser_history = runtime_subparsers.add_parser('history', help="Show run history")
    parser_history.add_argument('--limit', type=int, default=10, help="Limit")

    # unlock
    parser_unlock = runtime_subparsers.add_parser('unlock', help="Unlock runtime")
    parser_unlock.add_argument('--stale-only', action='store_true', help="Only clear stale lock")
    parser_unlock.add_argument('--force', action='store_true', help="Force clear lock")
    parser_unlock.add_argument('--confirm', action='store_true', help="Confirm force clear")

    # reset-state
    parser_reset = runtime_subparsers.add_parser('reset-state', help="Reset runtime state")
    parser_reset.add_argument('--confirm', action='store_true', help="Confirm reset")

    # config
    parser_config = runtime_subparsers.add_parser('config', help="Show runtime config")
    setup_monitor_parser(subparsers)
    return parser

def add_paper_parser(subparsers: argparse._SubParsersAction) -> None:
    paper_parser = subparsers.add_parser("paper", help="Paper trading commands")
    paper_subparsers = paper_parser.add_subparsers(dest="paper_command", required=True)

    # Init
    init_parser = paper_subparsers.add_parser("init", help="Initialize a paper trading account")
    init_parser.add_argument("--account", help="Account ID to initialize")
    init_parser.add_argument("--cash", type=float, help="Initial cash amount")
    init_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing ledger")

    # Status
    status_parser = paper_subparsers.add_parser("status", help="Show paper account status")
    status_parser.add_argument("--account", help="Account ID")
    status_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Run-once
    run_parser = paper_subparsers.add_parser("run-once", help="Run a strategy and create paper orders")
    run_parser.add_argument("symbols", nargs="+", help="Symbols to run on")
    run_parser.add_argument("--account", help="Account ID")
    run_parser.add_argument("--source", choices=["mock", "local"], default="local", help="Data source")
    run_parser.add_argument("--strategy", required=True, help="Strategy name")
    run_parser.add_argument("--timeframe", default="1D", help="Timeframe (e.g., 1D, 1W)")
    run_parser.add_argument("--rows", type=int, default=500, help="Number of rows to fetch")
    run_parser.add_argument("--param", action="append", help="Strategy parameter (key=value)")
    run_parser.add_argument("--execution", default="LATEST_CLOSE_RESEARCH", help="Execution mode")
    run_parser.add_argument("--no-trade-risk", action="store_true", help="Disable trade-level risk engine")
    run_parser.add_argument("--no-portfolio-risk", action="store_true", help="Disable portfolio risk engine")
    run_parser.add_argument("--telegram-summary", action="store_true", help="Send summary to Telegram")
    run_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Positions
    pos_parser = paper_subparsers.add_parser("positions", help="List open positions")
    pos_parser.add_argument("--account", help="Account ID")
    pos_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Orders
    orders_parser = paper_subparsers.add_parser("orders", help="List orders")
    orders_parser.add_argument("--account", help="Account ID")
    orders_parser.add_argument("--status", help="Filter by order status")
    orders_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Fills
    fills_parser = paper_subparsers.add_parser("fills", help="List fills")
    fills_parser.add_argument("--account", help="Account ID")
    fills_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Trades
    trades_parser = paper_subparsers.add_parser("trades", help="List trades")
    trades_parser.add_argument("--account", help="Account ID")
    trades_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Close
    close_parser = paper_subparsers.add_parser("close", help="Close an open position")
    close_parser.add_argument("symbol", help="Symbol to close")
    close_parser.add_argument("--account", help="Account ID")
    close_parser.add_argument("--source", choices=["mock", "local"], default="local", help="Data source")
    close_parser.add_argument("--manual-price", type=float, help="Manual execution price")

    # Reset
    reset_parser = paper_subparsers.add_parser("reset", help="Reset a paper account")
    reset_parser.add_argument("--account", help="Account ID")
    reset_parser.add_argument("--cash", type=float, help="Initial cash amount after reset")
    reset_parser.add_argument("--confirm", action="store_true", help="Must confirm to reset")

    # Export
    export_parser = paper_subparsers.add_parser("export", help="Export ledger to CSV")
    export_parser.add_argument("--account", help="Account ID")

    # Config
    config_parser = paper_subparsers.add_parser("config", help="Show paper trading config")
    config_parser.add_argument("--json", action="store_true", help="Output JSON")

def add_optimize_parser(subparsers) -> None:
    add_ml_dataset_parser(subparsers)
    opt_parser = subparsers.add_parser("optimize", help="Strategy Optimizer commands")
    opt_subparsers = opt_parser.add_subparsers(dest="opt_command", required=True)

    # strategy
    s_parser = opt_subparsers.add_parser("strategy", help="Optimize strategy parameters")
    s_parser.add_argument("symbol")
    s_parser.add_argument("--source", choices=["local", "mock"], default="local")
    s_parser.add_argument("--strategy", required=True)
    s_parser.add_argument("--timeframe", default="1d")
    s_parser.add_argument("--rows", type=int, default=1000)
    s_parser.add_argument("--method", choices=["GRID_SEARCH", "RANDOM_SEARCH"])
    s_parser.add_argument("--objective", choices=["COMPOSITE", "SHARPE", "SORTINO", "CALMAR", "TOTAL_RETURN", "PROFIT_FACTOR", "MAX_DRAWDOWN"])
    s_parser.add_argument("--param-range", action="append", help="e.g. fast_window=10,20,30")
    s_parser.add_argument("--max-combinations", type=int)
    s_parser.add_argument("--seed", type=int)
    s_parser.add_argument("--top", type=int)
    s_parser.add_argument("--min-trades", type=int)
    s_parser.add_argument("--max-drawdown", type=float)
    s_parser.add_argument("--min-profit-factor", type=float)
    s_parser.add_argument("--require-positive-return", action="store_true")
    s_parser.add_argument("--compare-benchmark", action="store_true")
    s_parser.add_argument("--save-report", action="store_true")
    s_parser.add_argument("--format", default="all")
    s_parser.add_argument("--output-dir")
    s_parser.add_argument("--json", action="store_true")

    # walk-forward
    wf_parser = opt_subparsers.add_parser("walk-forward", help="Walk-forward optimization")
    wf_parser.add_argument("symbol")
    wf_parser.add_argument("--source", choices=["local", "mock"], default="local")
    wf_parser.add_argument("--strategy", required=True)
    wf_parser.add_argument("--timeframe", default="1d")
    wf_parser.add_argument("--rows", type=int, default=2000)
    wf_parser.add_argument("--method", choices=["WALK_FORWARD_GRID", "WALK_FORWARD_RANDOM"])
    wf_parser.add_argument("--objective", choices=["COMPOSITE", "SHARPE", "SORTINO", "TOTAL_RETURN"])
    wf_parser.add_argument("--param-range", action="append")
    wf_parser.add_argument("--max-combinations", type=int)
    wf_parser.add_argument("--train-window", type=int)
    wf_parser.add_argument("--test-window", type=int)
    wf_parser.add_argument("--step", type=int)
    wf_parser.add_argument("--max-splits", type=int)
    wf_parser.add_argument("--save-report", action="store_true")
    wf_parser.add_argument("--format", default="all")
    wf_parser.add_argument("--json", action="store_true")

    # search-space
    ss_parser = opt_subparsers.add_parser("search-space", help="Show default search space for a strategy")
    ss_parser.add_argument("--strategy", required=True)
    ss_parser.add_argument("--json", action="store_true")

    # recent
    r_parser = opt_subparsers.add_parser("recent", help="List recent optimizations")
    r_parser.add_argument("--limit", type=int, default=20)
    r_parser.add_argument("--json", action="store_true")

    # config
    c_parser = opt_subparsers.add_parser("config", help="Show optimization config")
    c_parser.add_argument("--json", action="store_true")

def add_ml_dataset_parser(subparsers):
    ml_parser = subparsers.add_parser("ml-dataset", help="ML dataset builder commands")
    ml_sub = ml_parser.add_subparsers(dest="ml_command")

    build_parser = ml_sub.add_parser("build", help="Build an ML dataset")
    build_parser.add_argument("symbols", nargs="+", help="Symbols to include")
    build_parser.add_argument("--source", choices=["mock", "local"], help="Data source")
    build_parser.add_argument("--timeframe", help="Timeframe")
    build_parser.add_argument("--rows", type=int, help="Number of rows")
    build_parser.add_argument("--period", help="Data period")
    build_parser.add_argument("--task", choices=["CLASSIFICATION", "REGRESSION"], help="Task type")
    build_parser.add_argument("--feature-level", choices=["basic", "advanced", "full"], help="Feature set level")
    build_parser.add_argument("--label-type", choices=["FORWARD_RETURN", "BINARY_DIRECTION", "MULTICLASS_DIRECTION", "THRESHOLD_EVENT"], help="Label type")
    build_parser.add_argument("--horizon", type=int, help="Label horizon bars")
    build_parser.add_argument("--pos-threshold", type=float, help="Positive threshold")
    build_parser.add_argument("--neg-threshold", type=float, help="Negative threshold")
    build_parser.add_argument("--include-mtf", action="store_true", help="Include MTF features")
    build_parser.add_argument("--include-raw-ohlcv", action="store_true", help="Include raw OHLCV")
    build_parser.add_argument("--no-trend", action="store_true", help="Exclude trend features")
    build_parser.add_argument("--no-momentum", action="store_true", help="Exclude momentum features")
    build_parser.add_argument("--no-volatility", action="store_true", help="Exclude volatility features")
    build_parser.add_argument("--no-volume", action="store_true", help="Exclude volume features")
    build_parser.add_argument("--no-patterns", action="store_true", help="Exclude pattern features")
    build_parser.add_argument("--no-divergence", action="store_true", help="Exclude divergence features")
    build_parser.add_argument("--split", choices=["none", "train-test"], help="Dataset split mode")
    build_parser.add_argument("--train-ratio", type=float, help="Train ratio (0-1)")
    build_parser.add_argument("--fill-method", choices=["none", "ffill", "bfill", "zero", "median"], help="Fill missing method")
    build_parser.add_argument("--drop-na-features", action="store_true", help="Drop rows with NA features")
    build_parser.add_argument("--save", action="store_true", help="Save dataset to store")
    build_parser.add_argument("--format", choices=["csv", "json", "parquet", "all"], help="Output format")
    build_parser.add_argument("--output-dir", help="Output directory")
    build_parser.add_argument("--json", action="store_true", help="Output JSON summary")

    schema_parser = ml_sub.add_parser("schema", help="Show ML dataset schema")
    schema_parser.add_argument("symbols", nargs="+", help="Symbols to check schema for")
    schema_parser.add_argument("--source", choices=["mock", "local"], help="Data source")
    schema_parser.add_argument("--json", action="store_true", help="Output JSON summary")

    recent_parser = ml_sub.add_parser("recent", help="List recent ML datasets")
    recent_parser.add_argument("--limit", type=int, default=10, help="Number of datasets to list")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON summary")

    config_parser = ml_sub.add_parser("config", help="Show ML dataset configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON summary")


def setup_ml_train_parser(subparsers):
    setup_monitor_parser(subparsers)
    ml_train_parser = subparsers.add_parser("ml-train", help="Train and evaluate ML models or generate predictions")
    ml_train_subparsers = ml_train_parser.add_subparsers(dest="ml_train_command", required=True)

    # train command
    train_parser = ml_train_subparsers.add_parser("train", help="Train an ML model")
    train_parser.add_argument("--dataset", type=str, help="Path to a pre-built feature dataset (CSV/Parquet)")
    train_parser.add_argument("--symbols", nargs="+", help="Symbols to build dataset for (if --dataset not provided)")
    train_parser.add_argument("--source", type=str, default="local", choices=["mock", "local"], help="Data source")
    train_parser.add_argument("--rows", type=int, help="Number of rows per symbol")
    train_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    train_parser.add_argument("--task", type=str, default="CLASSIFICATION", choices=["CLASSIFICATION", "REGRESSION"], help="ML task type")
    train_parser.add_argument("--model", type=str, help="Model type (e.g. RANDOM_FOREST_CLASSIFIER, LOGISTIC_REGRESSION, etc.)")
    train_parser.add_argument("--target", type=str, help="Target column name")
    train_parser.add_argument("--scaler", type=str, choices=["NONE", "STANDARD", "ROBUST", "MINMAX"], help="Scaler type")
    train_parser.add_argument("--imputer", type=str, choices=["NONE", "MEDIAN", "MEAN", "ZERO"], help="Imputer type")
    train_parser.add_argument("--train-ratio", type=float, help="Train/test split ratio (e.g. 0.7)")
    train_parser.add_argument("--seed", type=int, help="Random seed")
    train_parser.add_argument("--max-train-rows", type=int, help="Maximum number of train rows")
    train_parser.add_argument("--model-param", action="append", help="Model hyperparameter (key=value)")
    train_parser.add_argument("--save-model", action="store_true", help="Save the trained model to the registry")
    train_parser.add_argument("--save-report", action="store_true", help="Save the training report")
    train_parser.add_argument("--format", type=str, help="Report formats (json,markdown,csv,all)")
    train_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # predict command
    predict_parser = ml_train_subparsers.add_parser("predict", help="Generate predictions using a saved model")
    predict_parser.add_argument("--model-id", type=str, help="Model ID from the registry")
    predict_parser.add_argument("--model-path", type=str, help="Direct path to the model directory")
    predict_parser.add_argument("--dataset", type=str, help="Path to a pre-built feature dataset")
    predict_parser.add_argument("--symbols", nargs="+", help="Symbols to predict (fetches data dynamically)")
    predict_parser.add_argument("--source", type=str, default="local", choices=["mock", "local"], help="Data source")
    predict_parser.add_argument("--rows", type=int, help="Number of rows per symbol")
    predict_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    predict_parser.add_argument("--all-rows", action="store_true", help="Predict for all rows instead of only the latest")
    predict_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # models command
    models_parser = ml_train_subparsers.add_parser("models", help="List saved ML models")
    models_parser.add_argument("--limit", type=int, default=20, help="Max number of models to list")
    models_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # show command
    show_parser = ml_train_subparsers.add_parser("show", help="Show details of a saved ML model")
    show_parser.add_argument("model_id", type=str, help="Model ID")
    show_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # delete command
    delete_parser = ml_train_subparsers.add_parser("delete", help="Delete a saved ML model")
    delete_parser.add_argument("model_id", type=str, help="Model ID")
    delete_parser.add_argument("--confirm", action="store_true", help="Confirm deletion", required=True)

    # config command
    config_parser = ml_train_subparsers.add_parser("config", help="Show ML training configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

def setup_monitor_parser(subparsers):
    monitor_parser = subparsers.add_parser("monitor", help="Monitoring and Self-Healing commands")
    monitor_subparsers = monitor_parser.add_subparsers(dest="monitor_command", required=True)

    # status command
    status_parser = monitor_subparsers.add_parser("status", help="Show overall monitoring status")
    status_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # heartbeat command
    hb_parser = monitor_subparsers.add_parser("heartbeat", help="Show or send heartbeats")
    hb_parser.add_argument("--component", type=str, help="Component to record heartbeat for")
    hb_parser.add_argument("--status", type=str, help="Health status (e.g. HEALTHY)")
    hb_parser.add_argument("--message", type=str, help="Heartbeat message")
    hb_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # diagnostics command
    diag_parser = monitor_subparsers.add_parser("diagnostics", help="Run diagnostic checks")
    diag_parser.add_argument("--save-report", action="store_true", help="Save the diagnostics report")
    diag_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # alerts command
    alerts_parser = monitor_subparsers.add_parser("alerts", help="List recent active alerts")
    alerts_parser.add_argument("--limit", type=int, default=20, help="Max number of alerts to list")
    alerts_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # test-alert command
    test_alert_parser = monitor_subparsers.add_parser("test-alert", help="Generate and optionally send a test alert")
    test_alert_parser.add_argument("--telegram", action="store_true", help="Actually send via Telegram if configured")

    # metrics command
    metrics_parser = monitor_subparsers.add_parser("metrics", help="List recent monitoring metrics")
    metrics_parser.add_argument("--limit", type=int, default=100, help="Max number of metrics to list")
    metrics_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # repair command
    repair_parser = monitor_subparsers.add_parser("repair", help="Run self-healing actions")
    repair_parser.add_argument("--dry-run", action="store_true", help="Show suggested actions without running them")
    repair_parser.add_argument("--auto-safe", action="store_true", help="Run all safe auto-repair actions")
    repair_parser.add_argument("--clear-stale-lock", action="store_true", help="Clear stale runtime lock")
    repair_parser.add_argument("--reset-state", action="store_true", help="Reset stuck runtime state")
    repair_parser.add_argument("--confirm", action="store_true", help="Confirm destructive actions")

    # cleanup command
    cleanup_parser = monitor_subparsers.add_parser("cleanup", help="Cleanup old monitoring files")
    cleanup_parser.add_argument("--retention-days", type=int, default=30, help="Days to keep files")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    cleanup_parser.add_argument("--confirm", action="store_true", help="Confirm cleanup")

    # config command
    config_parser = monitor_subparsers.add_parser("config", help="Show monitoring configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
