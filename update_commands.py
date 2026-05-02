import re

with open("bist_signal_bot/cli/commands.py", "r") as f:
    content = f.read()

new_commands = """
def cmd_patterns_list(args, ctx) -> int:
    from bist_signal_bot.patterns.engine import PatternRegistry
    from bist_signal_bot.patterns.models import PatternCategory
    from bist_signal_bot.cli.formatting import print_output

    registry = PatternRegistry.create_default_pattern_registry()

    category = None
    if args.category:
        try:
            category = PatternCategory[args.category.upper()]
        except KeyError:
            print_output({"error": f"Invalid category: {args.category}"}, as_json=args.json)
            return 1

    specs = registry.list_specs(category=category)

    out = []
    for spec in specs:
        out.append({
            "name": spec.name,
            "display_name": spec.display_name,
            "category": spec.category.value,
            "description": spec.description,
            "default_params": spec.default_params
        })

    print_output(out, as_json=args.json)
    return 0

def cmd_patterns_detect(args, ctx) -> int:
    from bist_signal_bot.patterns.engine import PatternEngine, PatternRegistry
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.data_service import MarketDataService
    from bist_signal_bot.cli.formatting import print_output
    import logging

    logger = logging.getLogger("bist_signal_bot.cli")

    try:
        symbol = args.symbol.upper()

        if args.source == "mock":
            rows = args.rows or 200
            provider = MockMarketDataProvider(rows=rows)
            mdf = provider.fetch_one(symbol, args.timeframe)
        else:
            service = MarketDataService(settings=ctx.settings)
            mdf = service.get_ohlcv(symbol, args.timeframe)

        if mdf is None or mdf.data.empty:
            print_output({"error": "No data found or available"}, as_json=args.json)
            return 1

        engine = PatternEngine(settings=ctx.settings)

        requests = []
        if args.default_set:
            result = engine.detect_default_set(mdf)
        else:
            if not args.pattern:
                print_output({"error": "No patterns requested. Use --pattern or --default-set"}, as_json=args.json)
                return 1
            requests = engine.parse_requests(args.pattern)
            result = engine.detect_many(mdf, requests)

        df = result.output_data

        if args.save_output:
            out_dir = ctx.settings.DATA_DIR / "features"
            out_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(out_dir / f"{symbol}_{args.timeframe}_patterns.csv")

        print_output(result.summary(), as_json=args.json)
        return 0

    except Exception as e:
        logger.error(f"Pattern detection error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1

def cmd_pattern_features(args, ctx) -> int:
    from bist_signal_bot.features.pattern_features import PatternFeatureBuilder
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.data_service import MarketDataService
    from bist_signal_bot.cli.formatting import print_output, format_pattern_batch_result
    from bist_signal_bot.core.audit import AuditEventType, AuditEvent
    import pandas as pd
    import logging

    logger = logging.getLogger("bist_signal_bot.cli")

    try:
        symbol = args.symbol.upper()

        if args.source == "mock":
            rows = args.rows or 200
            provider = MockMarketDataProvider(rows=rows)
            mdf = provider.fetch_one(symbol, args.timeframe)
        else:
            service = MarketDataService(settings=ctx.settings)
            mdf = service.get_ohlcv(symbol, args.timeframe)

        if mdf is None or mdf.data.empty:
            print_output({"error": "No data found or available"}, as_json=args.json)
            return 1

        builder = PatternFeatureBuilder(settings=ctx.settings)

        if args.level == "basic":
            result = builder.build_basic_pattern_features(mdf)
        elif args.level == "advanced":
            result = builder.build_advanced_pattern_features(mdf)
        else:
            result = builder.build_full_pattern_features(mdf)

        ctx.audit_logger.log_event(
            ctx.audit_logger._audit_file and ctx.audit_logger.settings.ENABLE_AUDIT_LOG and AuditEvent(
                event_type=AuditEventType.PATTERN_FEATURE_CALCULATION,
                message=f"Calculated pattern features for {symbol}",
                symbol=symbol,
                metadata={
                    "timeframe": args.timeframe,
                    "level": args.level,
                    "requested_count": result.requested_count,
                    "success_count": result.success_count,
                    "failed_count": result.failed_count,
                    "elapsed_seconds": result.elapsed_seconds
                }
            )
        )

        df = result.output_data

        if args.save_output:
            out_dir = ctx.settings.DATA_DIR / "features"
            out_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(out_dir / f"{symbol}_{args.timeframe}_pattern_{args.level}.csv")

        if args.json:
            print_output(result.summary(), as_json=True)
        else:
            print(f"Symbol: {symbol}\\nLevel: {args.level}\\nRows: {len(df)}")
            print(format_pattern_batch_result(result))

        return 0

    except Exception as e:
        logger.error(f"Pattern feature error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1
"""

insertion_point = content.find("    # Add commands to registry")

content = content[:insertion_point] + new_commands + content[insertion_point:]

# Find command registry and add the new commands
reg_point = content.find("    \"volatility-features\": cmd_volatility_features,")
if reg_point != -1:
    end_of_line = content.find("\n", reg_point)
    content = content[:end_of_line] + "\n    \"patterns\": lambda a, c: cmd_patterns_list(a, c) if a.patterns_command == 'list' else cmd_patterns_detect(a, c),\n    \"pattern-features\": cmd_pattern_features," + content[end_of_line:]

with open("bist_signal_bot/cli/commands.py", "w") as f:
    f.write(content)
