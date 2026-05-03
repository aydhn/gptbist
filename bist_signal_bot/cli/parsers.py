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




    # clean-data
    clean_parser = subparsers.add_parser("clean-data", help="Clean OHLCV data for a symbol")
    clean_parser.add_argument("symbol", type=str, help="Symbol to clean")
    clean_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Source to read data from")
    clean_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")
    clean_parser.add_argument("--save", action="store_true", help="Save cleaned data to local store")
    clean_parser.add_argument("--policy-missing", type=str, help="Missing value policy")
    clean_parser.add_argument("--policy-invalid-ohlc", type=str, help="Invalid OHLC policy")
    clean_parser.add_argument("--policy-outlier", type=str, help="Outlier policy")
    clean_parser.add_argument("--policy-duplicate", type=str, help="Duplicate timestamp policy")
    clean_parser.add_argument("--strict", action="store_true", help="Fail strictly on cleaning errors")
    clean_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # normalize-data
    normalize_parser = subparsers.add_parser("normalize-data", help="Normalize OHLCV data for a symbol")
    normalize_parser.add_argument("symbol", type=str, help="Symbol to normalize")
    normalize_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Source to read data from")
    normalize_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")
    normalize_parser.add_argument("--save", action="store_true", help="Save normalized data to local store")
    normalize_parser.add_argument("--strict", action="store_true", help="Fail strictly on normalization errors")
    normalize_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # adjust-data
    adjust_parser = subparsers.add_parser("adjust-data", help="Apply price adjustments to OHLCV data for a symbol")
    adjust_parser.add_argument("symbol", type=str, help="Symbol to adjust")
    adjust_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Source to read data from")
    adjust_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")
    adjust_parser.add_argument("--policy", type=str, help="Adjustment policy (e.g. FLAG_ONLY, MANUAL_SPLIT_ADJUST, USE_PROVIDER_ADJUSTED)")
    adjust_parser.add_argument("--save-adjusted", action="store_true", help="Save adjusted data to local store")
    adjust_parser.add_argument("--require-verified", action="store_true", help="Only apply verified corporate actions")
    adjust_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # corporate-actions
    ca_parser = subparsers.add_parser("corporate-actions", help="Manage corporate actions")
    ca_subparsers = ca_parser.add_subparsers(dest="ca_command", help="Corporate actions commands")

    # indicators


    # indicators
    indicators_parser = subparsers.add_parser("indicators", help="Manage indicators")
    indicators_subparsers = indicators_parser.add_subparsers(dest="indicators_command", help="Indicators commands")

    # indicators list
    ind_list_parser = indicators_subparsers.add_parser("list", help="List registered indicators")
    ind_list_parser.add_argument("--category", type=str, help="Filter by category")
    ind_list_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # indicators calc
    ind_calc_parser = indicators_subparsers.add_parser("calc", help="Calculate indicators")
    ind_calc_parser.add_argument("symbol", type=str, help="Symbol to calculate for")
    ind_calc_parser.add_argument("--source", type=str, choices=["local", "mock"], default="mock", help="Data source")
    ind_calc_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    ind_calc_parser.add_argument("--indicator", action="append", help="Indicator format: name:param=value")
    ind_calc_parser.add_argument("--default-set", action="store_true", help="Calculate default indicator set")
    ind_calc_parser.add_argument("--rows", type=int, default=500, help="Number of rows for mock data")
    ind_calc_parser.add_argument("--save-output", action="store_true", help="Save output to reports folder")
    ind_calc_parser.add_argument("--json", action="store_true", help="Output in JSON format")



    # momentum-features
    momentum_features_parser = subparsers.add_parser("momentum-features", help="Generate momentum features")
    momentum_features_parser.add_argument("symbol", type=str, help="Symbol to process")
    momentum_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    momentum_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    momentum_features_parser.add_argument("--rows", type=int, help="Mock data rows")
    momentum_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")
    momentum_features_parser.add_argument("--save-output", action="store_true", help="Save output to CSV")
    momentum_features_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # trend-features
    trend_parser = subparsers.add_parser("trend-features", help="Calculate trend features for a symbol")
    trend_parser.add_argument("symbol", type=str, help="Symbol to calculate features for")
    trend_parser.add_argument("--source", type=str, choices=["local", "mock"], default="mock", help="Data source")
    trend_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    trend_parser.add_argument("--rows", type=int, default=500, help="Number of rows for mock data")
    trend_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")
    trend_parser.add_argument("--save-output", action="store_true", help="Save output to reports folder")
    trend_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # ca init
    ca_init_parser = ca_subparsers.add_parser("init", help="Initialize corporate actions store")
    ca_init_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing store")
    ca_init_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # ca list
    ca_list_parser = ca_subparsers.add_parser("list", help="List corporate actions")
    ca_list_parser.add_argument("--symbol", type=str, help="Filter by symbol")
    ca_list_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # ca add
    ca_add_parser = ca_subparsers.add_parser("add", help="Add a corporate action")
    ca_add_parser.add_argument("symbol", type=str, help="Symbol")
    ca_add_parser.add_argument("--date", type=str, required=True, help="Action date (YYYY-MM-DD)")
    ca_add_parser.add_argument("--type", type=str, required=True, help="Action type (e.g. SPLIT, CASH_DIVIDEND)")
    ca_add_parser.add_argument("--ratio", type=float, help="Ratio (for splits)")
    ca_add_parser.add_argument("--cash", type=float, help="Cash amount (for dividends)")
    ca_add_parser.add_argument("--description", type=str, help="Description")
    ca_add_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # ca remove
    ca_remove_parser = ca_subparsers.add_parser("remove", help="Remove a corporate action")
    ca_remove_parser.add_argument("symbol", type=str, help="Symbol")
    ca_remove_parser.add_argument("--date", type=str, required=True, help="Action date (YYYY-MM-DD)")
    ca_remove_parser.add_argument("--type", type=str, required=True, help="Action type")
    ca_remove_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # ca import
    ca_import_parser = ca_subparsers.add_parser("import", help="Import corporate actions from CSV or JSON")
    ca_import_parser.add_argument("path", type=str, help="Path to import file")
    ca_import_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # ca export
    ca_export_parser = ca_subparsers.add_parser("export", help="Export corporate actions to CSV or JSON")
    ca_export_parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Export format")
    ca_export_parser.add_argument("--output", type=str, help="Output file path")
    ca_export_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # ca validate
    ca_validate_parser = ca_subparsers.add_parser("validate", help="Validate corporate actions store")
    ca_validate_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # download-data
    download_parser = subparsers.add_parser("download-data", help="Download OHLCV data for symbols")
    download_parser.add_argument("symbols", type=str, nargs="*", help="List of symbols to download")
    download_parser.add_argument("--all", action="store_true", help="Download for all active seed symbols")
    download_parser.add_argument("--group", type=str, help="Download for a specific symbol group")
    download_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")
    download_parser.add_argument("--period", type=str, default="2y", help="Period (e.g. 2y, max)")
    download_parser.add_argument("--refresh", action="store_true", help="Force refresh from provider (ignore cache)")
    download_parser.add_argument("--no-save", action="store_true", help="Do not save fetched data to local store")
    download_parser.add_argument("--continue-on-error", action="store_true", help="Continue downloading on error")
    download_parser.add_argument("--fail-fast", action="store_true", help="Stop on first error")
    download_parser.add_argument("--telegram-summary", action="store_true", help="Send a summary to Telegram")
    download_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # version
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # diagnose
    diagnose_parser = subparsers.add_parser("diagnose", help="Show detailed diagnostic output")
    diagnose_parser.add_argument("--json", action="store_true", help="Output in JSON format")


    # universe
    universe_parser = subparsers.add_parser("universe", help="Manage symbol universe")
    universe_subparsers = universe_parser.add_subparsers(dest="universe_command", help="Universe commands")

    # universe init
    init_parser = universe_subparsers.add_parser("init", help="Initialize default universe")
    init_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing universe")
    init_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe list
    list_parser = universe_subparsers.add_parser("list", help="List universe symbols")
    list_parser.add_argument("--active-only", action="store_true", help="List only active symbols")
    list_parser.add_argument("--group", type=str, help="Filter by symbol group")
    list_parser.add_argument("--yfinance", action="store_true", help="List in yfinance format")
    list_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe validate
    validate_parser = universe_subparsers.add_parser("validate", help="Validate universe file")
    validate_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe add
    add_parser = universe_subparsers.add_parser("add", help="Add a symbol to the universe")
    add_parser.add_argument("symbol", type=str, help="Symbol to add")
    add_parser.add_argument("--name", type=str, help="Company/Asset name")
    add_parser.add_argument("--groups", type=str, nargs="*", help="Symbol groups")
    add_parser.add_argument("--notes", type=str, help="Notes")
    add_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe remove
    remove_parser = universe_subparsers.add_parser("remove", help="Remove a symbol from the universe")
    remove_parser.add_argument("symbol", type=str, help="Symbol to remove")
    remove_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe deactivate
    deactivate_parser = universe_subparsers.add_parser("deactivate", help="Deactivate a symbol in the universe")
    deactivate_parser.add_argument("symbol", type=str, help="Symbol to deactivate")
    deactivate_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe activate
    activate_parser = universe_subparsers.add_parser("activate", help="Activate a symbol in the universe")
    activate_parser.add_argument("symbol", type=str, help="Symbol to activate")
    activate_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe import
    import_parser = universe_subparsers.add_parser("import", help="Import a universe from CSV or JSON")
    import_parser.add_argument("path", type=str, help="Path to import file")
    import_parser.add_argument("--merge", action="store_true", help="Merge with existing universe")
    import_parser.add_argument("--deactivate-missing", action="store_true", help="Deactivate symbols not in import file")
    import_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe export
    export_parser = universe_subparsers.add_parser("export", help="Export universe to CSV or JSON")
    export_parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Export format")
    export_parser.add_argument("--output", type=str, help="Output file path")
    export_parser.add_argument("--json", action="store_true", help="Output in JSON format (for CLI response, not file content)")

    # universe snapshot
    snapshot_parser = universe_subparsers.add_parser("snapshot", help="Create a universe snapshot")
    snapshot_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe watchlist
    watchlist_parser = universe_subparsers.add_parser("watchlist", help="Manage watchlists")
    watchlist_subparsers = watchlist_parser.add_subparsers(dest="watchlist_command", help="Watchlist commands")

    # universe watchlist list
    wl_list_parser = watchlist_subparsers.add_parser("list", help="List watchlists")
    wl_list_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe watchlist show
    wl_show_parser = watchlist_subparsers.add_parser("show", help="Show watchlist symbols")
    wl_show_parser.add_argument("name", type=str, help="Watchlist name")
    wl_show_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe watchlist add
    wl_add_parser = watchlist_subparsers.add_parser("add", help="Add symbols to watchlist")
    wl_add_parser.add_argument("name", type=str, help="Watchlist name")
    wl_add_parser.add_argument("symbols", type=str, nargs="+", help="Symbols to add")
    wl_add_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # universe watchlist remove
    wl_remove_parser = watchlist_subparsers.add_parser("remove", help="Remove symbols from watchlist")
    wl_remove_parser.add_argument("name", type=str, help="Watchlist name")
    wl_remove_parser.add_argument("symbols", type=str, nargs="+", help="Symbols to remove")
    wl_remove_parser.add_argument("--json", action="store_true", help="Output in JSON format")









    # patterns
    patterns_parser = subparsers.add_parser("patterns", help="Manage pattern detection")
    patterns_subparsers = patterns_parser.add_subparsers(dest="patterns_command", help="Pattern commands")

    # patterns list
    p_list_parser = patterns_subparsers.add_parser("list", help="List available patterns")
    p_list_parser.add_argument("--category", type=str, help="Filter by category (e.g. BREAKOUT, CANDLE)")
    p_list_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # patterns detect
    p_detect_parser = patterns_subparsers.add_parser("detect", help="Detect specific patterns on a symbol")
    p_detect_parser.add_argument("symbol", type=str, help="Symbol to process")
    p_detect_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    p_detect_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    p_detect_parser.add_argument("--rows", type=int, help="Mock data rows")
    p_detect_parser.add_argument("--pattern", type=str, action="append", help="Pattern to detect (e.g. price_breakout:window=20)")
    p_detect_parser.add_argument("--default-set", action="store_true", help="Run default pattern set")
    p_detect_parser.add_argument("--save-output", action="store_true", help="Save output to CSV")
    p_detect_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # pattern-features
    pattern_features_parser = subparsers.add_parser("pattern-features", help="Generate pattern and price action features")
    pattern_features_parser.add_argument("symbol", type=str, help="Symbol to process")
    pattern_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    pattern_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    pattern_features_parser.add_argument("--rows", type=int, help="Mock data rows")
    pattern_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")
    pattern_features_parser.add_argument("--save-output", action="store_true", help="Save output to CSV")
    pattern_features_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # volume-features
    volume_features_parser = subparsers.add_parser("volume-features", help="Generate volume features")
    volume_features_parser.add_argument("symbol", type=str, help="Symbol to process")
    volume_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    volume_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    volume_features_parser.add_argument("--rows", type=int, help="Mock data rows")
    volume_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")
    volume_features_parser.add_argument("--save-output", action="store_true", help="Save output to CSV")
    volume_features_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # volatility-features
    volatility_features_parser = subparsers.add_parser("volatility-features", help="Generate volatility features")
    volatility_features_parser.add_argument("symbol", type=str, help="Symbol to process")
    volatility_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    volatility_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    volatility_features_parser.add_argument("--rows", type=int, help="Mock data rows")
    volatility_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")
    volatility_features_parser.add_argument("--save-output", action="store_true", help="Save output to CSV")
    volatility_features_parser.add_argument("--json", action="store_true", help="Output in JSON format")


    # Divergence Commands
    divergence_parser = subparsers.add_parser("divergence", help="Divergence feature engine")
    divergence_subparsers = divergence_parser.add_subparsers(dest="subcommand", help="Divergence subcommands")

    # Divergence Detect
    div_detect_parser = divergence_subparsers.add_parser("detect", help="Detect divergence features")
    div_detect_parser.add_argument("symbol", help="Stock symbol to detect divergence")
    div_detect_parser.add_argument("--source", choices=["local", "mock"], default="local", help="Data source")
    div_detect_parser.add_argument("--timeframe", default="1d", help="Timeframe (e.g. 1d, 1h)")
    div_detect_parser.add_argument("--rows", type=int, help="Number of rows to fetch (mock source)")
    div_detect_parser.add_argument("--level", choices=["basic", "advanced", "full"], help="Feature level")
    div_detect_parser.add_argument("--indicators", nargs="+", help="Specific indicators to use")
    div_detect_parser.add_argument("--pivot-mode", choices=["LOOKBACK_ONLY", "CONFIRMED_LAGGED"], default="LOOKBACK_ONLY", help="Pivot detection mode")
    div_detect_parser.add_argument("--lookback", type=int, help="Lookback for pivot detection")
    div_detect_parser.add_argument("--confirmation-bars", type=int, help="Confirmation bars for CONFIRMED_LAGGED mode")
    div_detect_parser.add_argument("--min-pivot-distance", type=int, help="Minimum bars between pivots")
    div_detect_parser.add_argument("--max-pivot-distance", type=int, help="Maximum bars between pivots")
    div_detect_parser.add_argument("--include-hidden", dest="include_hidden", action="store_true", help="Include hidden divergences")
    div_detect_parser.add_argument("--no-hidden", dest="include_hidden", action="store_false", help="Exclude hidden divergences")
    div_detect_parser.add_argument("--include-regular", dest="include_regular", action="store_true", help="Include regular divergences")
    div_detect_parser.add_argument("--no-regular", dest="include_regular", action="store_false", help="Exclude regular divergences")
    div_detect_parser.set_defaults(include_hidden=True, include_regular=True)
    div_detect_parser.add_argument("--save-output", action="store_true", help="Save output to CSV")
    div_detect_parser.add_argument("--json", action="store_true", help="Output in JSON format")


    # STRATEGIES Command
    parser_strategies = subparsers.add_parser("strategies", help="Strategy engine operations")
    strategies_subparsers = parser_strategies.add_subparsers(dest="strategies_cmd", required=True)

    # strategies list
    list_strat_parser = strategies_subparsers.add_parser("list", help="List available strategies")
    list_strat_parser.add_argument("--category", type=str, help="Filter by category (e.g., TREND_FOLLOWING)")
    list_strat_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # strategies run
    run_strat_parser = strategies_subparsers.add_parser("run", help="Run strategy on a single symbol")
    run_strat_parser.add_argument("symbol", type=str, help="Symbol to run strategy for")
    run_strat_parser.add_argument("--strategy", type=str, required=True, help="Strategy name")
    run_strat_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    run_strat_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g., 1d, 1wk)")
    run_strat_parser.add_argument("--period", type=str, help="History period")
    run_strat_parser.add_argument("--rows", type=int, help="Rows for mock data")
    run_strat_parser.add_argument("--param", type=str, action="append", help="Strategy parameters (e.g., --param fast=20)")
    run_strat_parser.add_argument("--allow-short", action="store_true", help="Allow short signal candidates")
    run_strat_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # strategies batch
    batch_strat_parser = strategies_subparsers.add_parser("batch", help="Run strategy on multiple symbols")
    batch_strat_parser.add_argument("--strategy", type=str, required=True, help="Strategy name")

    group = batch_strat_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbols", type=str, nargs="+", help="List of symbols")
    group.add_argument("--all", action="store_true", help="Run on all symbols")
    group.add_argument("--group", type=str, help="Run on symbol group")

    batch_strat_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    batch_strat_parser.add_argument("--param", type=str, action="append", help="Strategy parameters")
    batch_strat_parser.add_argument("--allow-short", action="store_true", help="Allow short signal candidates")
    batch_strat_parser.add_argument("--fail-fast", action="store_true", help="Stop batch on first error")
    batch_strat_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # BENCHMARKS Command
    parser_benchmarks = subparsers.add_parser("benchmarks", help="Benchmark reference operations")
    benchmarks_subparsers = parser_benchmarks.add_subparsers(dest="benchmarks_cmd", required=True)

    # benchmarks list
    list_bench_parser = benchmarks_subparsers.add_parser("list", help="List available benchmarks")
    list_bench_parser.add_argument("--category", type=str, help="Filter by category (e.g., BUY_AND_HOLD)")
    list_bench_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # benchmarks run
    run_bench_parser = benchmarks_subparsers.add_parser("run", help="Run benchmark on a single symbol")
    run_bench_parser.add_argument("symbol", type=str, help="Symbol to run benchmark for")
    run_bench_parser.add_argument("--benchmark", type=str, required=True, help="Benchmark name")
    run_bench_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    run_bench_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g., 1d)")
    run_bench_parser.add_argument("--period", type=str, help="History period")
    run_bench_parser.add_argument("--rows", type=int, help="Rows for mock data")
    run_bench_parser.add_argument("--param", type=str, action="append", help="Benchmark parameters (e.g., --param window=200)")
    run_bench_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # benchmarks batch
    batch_bench_parser = benchmarks_subparsers.add_parser("batch", help="Run benchmark on multiple symbols")
    batch_bench_parser.add_argument("--benchmark", type=str, required=True, help="Benchmark name")

    b_group = batch_bench_parser.add_mutually_exclusive_group(required=True)
    b_group.add_argument("--symbols", type=str, nargs="+", help="List of symbols")
    b_group.add_argument("--all", action="store_true", help="Run on all symbols")
    b_group.add_argument("--group", type=str, help="Run on symbol group")

    batch_bench_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    batch_bench_parser.add_argument("--param", type=str, action="append", help="Benchmark parameters")
    batch_bench_parser.add_argument("--fail-fast", action="store_true", help="Stop batch on first error")
    batch_bench_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # benchmarks default
    default_bench_parser = benchmarks_subparsers.add_parser("default", help="Run default set of benchmarks on a symbol")
    default_bench_parser.add_argument("symbol", type=str, help="Symbol to run default benchmarks for")
    default_bench_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    default_bench_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    default_bench_parser.add_argument("--period", type=str, help="History period")
    default_bench_parser.add_argument("--rows", type=int, help="Rows for mock data")
    default_bench_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        args.command = "healthcheck"
        args.json = False
        args.verbose = False
    return args
