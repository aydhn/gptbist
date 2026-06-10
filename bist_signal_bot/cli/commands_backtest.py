import logging
import json
from bist_signal_bot.backtesting.engine import BacktestEngine
from bist_signal_bot.strategies.engine import StrategyEngine
from bist_signal_bot.costs.engine import TransactionCostEngine
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.cli.formatting import print_output, format_backtest_summary
from bist_signal_bot.core.audit import AuditEventType, AuditEvent

logger = logging.getLogger("bist_signal_bot.cli")

def handle_backtest_command(args, ctx) -> int:
    from bist_signal_bot.cli.commands import cmd_backtest_run, cmd_backtest_report
    if args.backtest_cmd == "run":
        if getattr(args, "report", False):
            return cmd_backtest_run(args, ctx)

        try:
            symbol = args.symbol.upper()
            strategy_name = args.strategy

            # Setup engines
            strategy_engine = StrategyEngine(settings=ctx.settings)
            cost_engine = TransactionCostEngine.from_settings(ctx.settings)
            engine = BacktestEngine(strategy_engine, cost_engine, settings=ctx.settings)

            # Setup config overrides
            config = engine.build_default_config()
            if getattr(args, "initial_capital", None) is not None:
                config.initial_capital = args.initial_capital
            if getattr(args, "execution", None) is not None:
                from bist_signal_bot.backtesting.models import ExecutionPriceMode
                config.execution_price_mode = ExecutionPriceMode(args.execution)
            if getattr(args, "cost_scenario", None) is not None:
                from bist_signal_bot.costs.models import CostScenario
                config.scenario = CostScenario(args.cost_scenario)
            if getattr(args, "max_position_size_pct", None) is not None:
                config.max_position_size_pct = args.max_position_size_pct
            if getattr(args, "allow_short", False):
                config.allow_short = True
            if getattr(args, "no_costs", False):
                config.commission_enabled = False
                config.slippage_enabled = False

            # Parse params
            params = strategy_engine.parse_params(args.param)

            # Get data
            if args.source == "mock":
                rows = getattr(args, "rows", 252) or 252
                provider = MockMarketDataProvider(rows=rows)
                mdf = provider.fetch_one(symbol, args.timeframe)
            else:
                service = MarketDataService(settings=ctx.settings)
                period = getattr(args, "period", ctx.settings.DOWNLOAD_DEFAULT_PERIOD) or ctx.settings.DOWNLOAD_DEFAULT_PERIOD
                mdf = service.get_ohlcv(symbol, args.timeframe, period=period)

            if mdf is None or mdf.data.empty:
                print_output({"error": f"No data found for {symbol}"}, as_json=args.json)
                return 1

            # Run backtest
            result = engine.run_single_symbol(
                strategy_name=strategy_name,
                symbol=symbol,
                data=mdf,
                params=params,
                config=config
            )

            # Log Audit
            if ctx.audit_logger and ctx.audit_logger.settings.ENABLE_AUDIT_LOG:
                ctx.audit_logger.log_event(AuditEvent(
                    event_type=AuditEventType.BACKTEST_RUN,
                    message=f"Ran backtest {strategy_name} for {symbol}",
                    symbol=symbol,
                    metadata=result.summary()
                ))

            if getattr(args, "json", False):
                print_output(result.summary(), as_json=True)
            else:
                print(format_backtest_summary(result))

            return 0

        except Exception as e:
            logger.error(f"Backtest run error: {e}", exc_info=True)
            print_output({"error": str(e)}, as_json=getattr(args, "json", False))
            return 1

    elif args.backtest_cmd == "report":
         return cmd_backtest_report(args, ctx)

    elif args.backtest_cmd == "batch":
        try:
            strategy_name = args.strategy

            if args.all:
                symbols = ["ASELS", "GARAN", "THYAO", "BIMAS", "EREGL"]
            elif args.group:
                symbols = ["ASELS", "THYAO"]
            elif args.symbols:
                symbols = [s.upper() for s in args.symbols]
            else:
                print_output({"error": "Must specify --symbols, --group, or --all"}, as_json=getattr(args, "json", False))
                return 1

            strategy_engine = StrategyEngine(settings=ctx.settings)
            cost_engine = TransactionCostEngine.from_settings(ctx.settings)
            engine = BacktestEngine(strategy_engine, cost_engine, settings=ctx.settings)

            config = engine.build_default_config()
            if getattr(args, "initial_capital", None) is not None:
                config.initial_capital = args.initial_capital
            if getattr(args, "execution", None) is not None:
                from bist_signal_bot.backtesting.models import ExecutionPriceMode
                config.execution_price_mode = ExecutionPriceMode(args.execution)
            if getattr(args, "cost_scenario", None) is not None:
                from bist_signal_bot.costs.models import CostScenario
                config.scenario = CostScenario(args.cost_scenario)
            if getattr(args, "max_position_size_pct", None) is not None:
                config.max_position_size_pct = args.max_position_size_pct
            if getattr(args, "allow_short", False):
                config.allow_short = True
            if getattr(args, "no_costs", False):
                config.commission_enabled = False
                config.slippage_enabled = False

            params = strategy_engine.parse_params(args.param)

            # Pre-fetch data
            symbols_data = {}
            if args.source == "mock":
                from bist_signal_bot.data.models import DataFetchRequest, Timeframe
                provider = MockMarketDataProvider()
                req = DataFetchRequest(symbols=symbols, timeframe=Timeframe.DAILY, period="2y")
                results = provider.fetch_ohlcv(req)
                for sym, mdf in results.items():
                    if mdf and not mdf.data.empty:
                        symbols_data[sym] = mdf
            else:
                service = MarketDataService(settings=ctx.settings)
                for sym in symbols:
                    mdf = service.get_ohlcv(sym, "1d")
                    if mdf and not mdf.data.empty:
                        symbols_data[sym] = mdf

            results = engine.run_batch_symbols(
                strategy_name=strategy_name,
                symbols_data=symbols_data,
                params=params,
                config=config
            )

            # Log Audit
            summary_dict = {sym: res.summary() for sym, res in results.items()}
            if ctx.audit_logger and ctx.audit_logger.settings.ENABLE_AUDIT_LOG:
                ctx.audit_logger.log_event(AuditEvent(
                    event_type=AuditEventType.BACKTEST_RUN,
                    message=f"Ran batch backtest {strategy_name}",
                    symbol="ALL",
                    metadata={"batch_size": len(results)}
                ))

            if getattr(args, "json", False):
                print_output(summary_dict, as_json=True)
            else:
                print(f"Batch Backtest Results: {strategy_name}")
                print("=" * 50)
                for sym, res in results.items():
                    print(f"\n[{sym}]")
                    print(format_backtest_summary(res))

            return 0

        except Exception as e:
            logger.error(f"Backtest batch error: {e}", exc_info=True)
            print_output({"error": str(e)}, as_json=getattr(args, "json", False))
            return 1
