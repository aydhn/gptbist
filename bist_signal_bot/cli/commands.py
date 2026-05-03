
from bist_signal_bot.data.cleaning import MarketDataCleaner
from bist_signal_bot.data.models import MissingValuePolicy, InvalidOhlcPolicy, OutlierPolicy, DuplicateTimestampPolicy
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
from bist_signal_bot.data.models import Timeframe
from bist_signal_bot.storage.local_store import LocalMarketDataStore

from datetime import date

from bist_signal_bot.core.audit import AuditEventType, AuditEvent
from bist_signal_bot.data.corporate_actions import CorporateActionStore
from bist_signal_bot.data.adjustments import PriceAdjustmentEngine
from bist_signal_bot.data.models import CorporateAction, CorporateActionType, AdjustmentPolicy
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
import argparse
import sys
import platform
from datetime import datetime

from bist_signal_bot.app.bootstrap import ApplicationContext
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.cli.formatting import print_output, format_success, format_warning, format_error
from bist_signal_bot.config.secrets import settings_safe_dump
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.symbol_utils import normalize_symbol
from bist_signal_bot.data.quality import DataQualityChecker
from bist_signal_bot.core.exceptions import InvalidSymbolError
from bist_signal_bot.storage.paths import get_market_data_dir, get_metadata_dir, get_market_data_index_path
from bist_signal_bot.calendar.session import BistMarketSessionService


def cmd_healthcheck(args, app_context: ApplicationContext) -> int:
    summary = run_healthcheck()
    if not args.verbose and "storage" in summary:
        # Simplify output if not verbose
        summary["storage"] = {"market_data_dir_path": summary["storage"]["market_data_dir_path"]}
    print_output(summary, as_json=args.json)
    return 0

def cmd_config(args, app_context: ApplicationContext) -> int:
    safe_config = settings_safe_dump(app_context.settings)
    print_output(safe_config, as_json=args.json)
    return 0

def cmd_symbols(args, app_context: ApplicationContext) -> int:
    symbols = app_context.symbol_universe.list_symbols(active_only=True)

    if getattr(args, "group", None):
        symbols = [s for s in symbols if getattr(s, "group", "") == args.group]

    if getattr(args, "yfinance", False):
        res = [getattr(s, "yfinance_ticker", str(s) + ".IS") for s in symbols]
    else:
        res = [{"symbol": getattr(s, "symbol", str(s)), "name": getattr(s, "name", ""), "group": getattr(s, "group", "")} for s in symbols]

    print_output(res, as_json=args.json)
    return 0

def cmd_validate_symbol(args, app_context: ApplicationContext) -> int:
    try:
        norm = normalize_symbol(args.symbol)
        valid = app_context.symbol_universe.contains(norm)
        yf_format = norm + ".IS"
        res = {
            "input": args.symbol,
            "normalized": norm,
            "valid": valid,
            "yfinance_format": yf_format
        }
        print_output(res, as_json=args.json)
        return 0 if valid else 1
    except Exception as e:
        if args.json:
            print_output({"input": args.symbol, "error": str(e), "valid": False}, as_json=True)
        else:
            print(format_error(str(e)))
        return 1

def cmd_provider_status(args, app_context: ApplicationContext) -> int:
    try:
        import yfinance
        yf_avail = True
    except ImportError:
        yf_avail = False

    res = {
        "default_provider": app_context.settings.DEFAULT_DATA_PROVIDER,
        "timeframe": app_context.settings.DEFAULT_TIMEFRAME,
        "period": app_context.settings.DEFAULT_HISTORY_PERIOD,
        "yfinance_importable": yf_avail
    }
    print_output(res, as_json=args.json)
    return 0

def cmd_storage_status(args, app_context: ApplicationContext) -> int:
    market_dir = get_market_data_dir(app_context.settings)
    meta_dir = get_metadata_dir(app_context.settings)
    idx_path = get_market_data_index_path(app_context.settings)

    res = {
        "market_data_dir": str(market_dir),
        "market_data_dir_exists": market_dir.exists(),
        "metadata_dir": str(meta_dir),
        "metadata_dir_exists": meta_dir.exists(),
        "index_file": str(idx_path),
        "index_file_exists": idx_path.exists(),
        "storage_format": app_context.settings.STORAGE_FORMAT
    }
    print_output(res, as_json=args.json)
    return 0

def cmd_calendar_status(args, app_context: ApplicationContext) -> int:
    at_time = None
    if getattr(args, "at", None):
        try:
            at_time = datetime.fromisoformat(args.at)
        except ValueError:
            print(format_error("Invalid datetime format. Use ISO format like 2026-04-24T18:20:00+03:00"))
            return 2

    status = app_context.session_service.get_status(now=at_time)
    res = {
        "now": status.now.isoformat(),
        "trading_day": status.is_trading_day,
        "market_open": status.is_market_open,
        "session_type": status.day_type.value,
        "next_trading_day": status.next_trading_day.isoformat() if status.next_trading_day else None,
        "previous_trading_day": status.previous_trading_day.isoformat() if status.previous_trading_day else None,
        "daily_signal_enabled": app_context.settings.BIST_DAILY_SIGNAL_ENABLED,
        "intraday_signal_enabled": app_context.settings.BIST_INTRADAY_SIGNAL_ENABLED
    }
    print_output(res, as_json=args.json)
    return 0

def cmd_telegram_test(args, app_context: ApplicationContext) -> int:
    if not app_context.settings.ENABLE_TELEGRAM:
        print(format_warning("Telegram is not enabled in settings."))
        return 1

    if not app_context.notifier:
        print(format_error("Notifier could not be initialized."))
        return 1

    try:
        res = app_context.notifier.send_text(title="CLI Test", body=args.message)
        out = {
            "success": res.success,
            "dry_run": res.dry_run,
            "message": args.message
        }
        if args.json:
            print_output(out, as_json=True)
        else:
            print(format_success("Telegram test message processed."))
            print_output(out)
        return 0 if res.success else 1
    except Exception as e:
        print(format_error(f"Telegram test failed: {e}"))
        return 1

def cmd_mock_data(args, app_context: ApplicationContext) -> int:
    try:
        norm = normalize_symbol(args.symbol)
    except Exception as e:
        print(format_error(str(e)))
        return 1

    provider = MockMarketDataProvider(rows=args.rows)
    from bist_signal_bot.data.models import Timeframe
    mdf = provider.fetch_one(norm, Timeframe.DAILY)

    saved = False
    path = None
    if getattr(args, "save", False) and app_context.local_store:
        app_context.local_store.write_ohlcv(mdf)
        saved = True
        path = str(app_context.local_store._get_file_path(norm, provider.vendor, Timeframe.DAILY))

    res = {
        "symbol": norm,
        "row_count": len(mdf.data),
        "start": mdf.data.index.min().strftime("%Y-%m-%d") if not mdf.data.empty else None,
        "end": mdf.data.index.max().strftime("%Y-%m-%d") if not mdf.data.empty else None,
        "close_last": float(mdf.data["close"].iloc[-1]) if not mdf.data.empty else None,
        "saved": saved,
        "file_path": path
    }
    print_output(res, as_json=args.json)
    return 0

def cmd_quality_demo(args, app_context: ApplicationContext) -> int:
    try:
        norm = normalize_symbol(args.symbol)
    except Exception as e:
        print(format_error(str(e)))
        return 1

    provider = MockMarketDataProvider(rows=args.rows)
    from bist_signal_bot.data.models import Timeframe
    mdf = provider.fetch_one(norm, Timeframe.DAILY)

    checker = DataQualityChecker()
    report = checker.check(mdf)

    res = {
        "symbol": norm,
        "score": report.score,
        "passed": report.passed,
        "issue_count": len(report.issues),
        "warning_count": report.warning_count(),
        "error_count": report.error_count()
    }
    print_output(res, as_json=args.json)
    return 0

def cmd_version(args, app_context: ApplicationContext) -> int:
    res = {
        "app_name": app_context.settings.APP_NAME,
        "python_version": sys.version.split(" ")[0],
        "platform": platform.platform()
    }
    print_output(res, as_json=args.json)
    return 0

def cmd_diagnose(args, app_context: ApplicationContext) -> int:
    # Combine some results
    hc = run_healthcheck()
    config = settings_safe_dump(app_context.settings)

    res = {
        "health": hc,
        "config": config,
    }
    print_output(res, as_json=args.json)
    return 0

def cmd_download_data(args, app_context: ApplicationContext) -> int:
    if not args.symbols and not args.all and not args.group:
        print(format_error("Lütfen symbol(ler) belirtin, --all veya --group kullanın."))
        return 1

    if args.symbols and args.all:
        print(format_error("--all parametresi ile symbol listesi aynı anda kullanılamaz."))
        return 1

    try:
        from bist_signal_bot.data.downloader import MarketDataDownloader
        from bist_signal_bot.data.models import Timeframe
        from bist_signal_bot.data.symbol_universe import SymbolGroup

        downloader = MarketDataDownloader(
            data_service=app_context.data_service,
            universe=app_context.symbol_universe,
            settings=app_context.settings,
            audit_logger=app_context.audit_logger,
            notifier=app_context.notifier
        )

        timeframe = Timeframe(args.timeframe)
        period = args.period
        refresh = args.refresh
        save = not args.no_save

        continue_on_error = app_context.settings.DOWNLOAD_CONTINUE_ON_ERROR
        if args.continue_on_error:
            continue_on_error = True
        elif args.fail_fast:
            continue_on_error = False

        if args.all:
            result = downloader.download_universe(
                active_only=True,
                timeframe=timeframe,
                period=period,
                refresh=refresh,
                save=save
            )
        elif args.group:
            try:
                group = SymbolGroup(args.group)
            except ValueError:
                print(format_error(f"Geçersiz grup adı: {args.group}"))
                return 1

            result = downloader.download_universe(
                group=group,
                active_only=True,
                timeframe=timeframe,
                period=period,
                refresh=refresh,
                save=save
            )
        else:
            if len(args.symbols) == 1:
                res = downloader.download_symbol(
                    args.symbols[0],
                    timeframe=timeframe,
                    period=period,
                    refresh=refresh,
                    save=save
                )
                if args.json:
                    print_output(res.model_dump(), as_json=True)
                else:
                    print_output(f"Sembol: {res.symbol}")
                    print_output(f"Durum: {res.status.value}")
                    print_output(f"Satır: {res.row_count}")
                    print_output(f"Cache: {res.from_cache}")
                    print_output(f"Kaydedildi: {res.saved}")
                    if res.error:
                        print_output(f"Hata: {res.error}")
                return 0 if res.status == "SUCCESS" else 1
            else:
                result = downloader.download_symbols(
                    args.symbols,
                    timeframe=timeframe,
                    period=period,
                    refresh=refresh,
                    save=save,
                    continue_on_error=continue_on_error
                )

        if args.telegram_summary:
            downloader.send_download_summary(result)

        if args.json:
            out = result.summary()
            out["results"] = [r.model_dump() for r in result.results]
            print_output(out, as_json=True)
        else:
            print_output(format_success("Toplu indirme tamamlandı."))
            print_output(result.summary())

        return 0 if result.failed_count == 0 else 1

    except Exception as e:
        print(format_error(str(e)))
        return 1

def cmd_universe(args, app_context) -> int:
    from bist_signal_bot.data.universe_store import UniverseStore
    from bist_signal_bot.data.universe_updater import UniverseUpdater
    from bist_signal_bot.data.models import UniverseFileFormat, SymbolGroup
    from pathlib import Path

    store = UniverseStore(app_context.settings)
    updater = UniverseUpdater(store, app_context.settings, app_context.audit_logger, app_context.notifier)

    if args.universe_command == "init":
        res = store.initialize_default_universe(overwrite=args.overwrite)
        if args.json:
            print_output(res.summary(), as_json=True)
        else:
            if res.success:
                print(format_success(res.message))
            else:
                print(format_error(res.message))
        return 0 if res.success else 1

    elif args.universe_command == "list":
        if not store.exists():
            print(format_error("Universe file not found. Run 'universe init' first."))
            return 1

        universe = store.load_universe()
        if args.group:
            try:
                group = SymbolGroup(args.group)
                infos = universe.filter_by_group(group, active_only=args.active_only)
                symbols = [i.symbol for i in infos]
            except ValueError:
                print(format_error(f"Geçersiz grup adı: {args.group}"))
                return 1
        else:
            symbols = universe.list_symbols(active_only=args.active_only)

        if args.yfinance:
            from bist_signal_bot.data.symbol_utils import to_yfinance_symbol
            symbols = [to_yfinance_symbol(s) for s in symbols]

        res = {"count": len(symbols), "symbols": symbols}
        if args.json:
            print_output(res, as_json=True)
        else:
            for s in symbols:
                print(s)
            print(f"\nTotal: {len(symbols)}")
        return 0

    elif args.universe_command == "validate":
        if not store.exists():
            print(format_error("Universe file not found. Run 'universe init' first."))
            return 1
        universe = store.load_universe()
        report = updater.validate_universe(universe)
        if args.json:
            print_output(report.summary(), as_json=True)
        else:
            if report.passed:
                print(format_success("Universe validation passed."))
            else:
                print(format_error("Universe validation failed."))
            for issue in report.issues:
                msg = f"[{issue.severity}] "
                if issue.symbol:
                    msg += f"{issue.symbol}: "
                msg += issue.message
                print(msg)
            print(f"\nTotal: {report.total_symbols}, Active: {report.active_symbols}, Issues: {len(report.issues)}")
        return 0 if report.passed else 1

    elif args.universe_command == "add":
        res = updater.add_symbol(args.symbol, args.name, args.groups, args.notes)
        if args.json:
            print_output(res.summary(), as_json=True)
        else:
            if res.success:
                print(format_success(res.message))
            else:
                print(format_error(res.message))
        return 0 if res.success else 1

    elif args.universe_command == "remove":
        res = updater.remove_symbol(args.symbol)
        if args.json:
            print_output(res.summary(), as_json=True)
        else:
            if res.success:
                print(format_success(res.message))
            else:
                print(format_error(res.message))
        return 0 if res.success else 1

    elif args.universe_command == "deactivate":
        res = updater.deactivate_symbol(args.symbol)
        if args.json:
            print_output(res.summary(), as_json=True)
        else:
            if res.success:
                print(format_success(res.message))
            else:
                print(format_error(res.message))
        return 0 if res.success else 1

    elif args.universe_command == "activate":
        res = updater.activate_symbol(args.symbol)
        if args.json:
            print_output(res.summary(), as_json=True)
        else:
            if res.success:
                print(format_success(res.message))
            else:
                print(format_error(res.message))
        return 0 if res.success else 1

    elif args.universe_command == "import":
        path = Path(args.path)
        res = updater.import_from_file(path, merge=args.merge, deactivate_missing=args.deactivate_missing)
        if args.json:
            print_output(res.summary(), as_json=True)
        else:
            if res.success:
                print(format_success(res.message))
            else:
                print(format_error(res.message))
        return 0 if res.success else 1

    elif args.universe_command == "export":
        fmt = UniverseFileFormat(args.format)
        out_path = Path(args.output) if args.output else None
        res = updater.export_to_file(fmt, out_path)
        if args.json:
            print_output(res.summary(), as_json=True)
        else:
            if res.success:
                print(format_success(res.message))
            else:
                print(format_error(res.message))
        return 0 if res.success else 1

    elif args.universe_command == "snapshot":
        res = updater.create_snapshot()
        if args.json:
            print_output(res.summary(), as_json=True)
        else:
            if res.success:
                print(format_success(res.message))
            else:
                print(format_error(res.message))
        return 0 if res.success else 1

    elif args.universe_command == "watchlist":
        if args.watchlist_command == "list":
            lists = store.list_watchlists()
            res = {"watchlists": lists}
            if args.json:
                print_output(res, as_json=True)
            else:
                for wl in lists:
                    print(wl)
            return 0
        elif args.watchlist_command == "show":
            syms = store.load_watchlist(args.name)
            res = {"watchlist": args.name, "symbols": syms}
            if args.json:
                print_output(res, as_json=True)
            else:
                for s in syms:
                    print(s)
            return 0
        elif args.watchlist_command == "add":
            res = updater.add_to_watchlist(args.name, args.symbols)
            if args.json:
                print_output(res.summary(), as_json=True)
            else:
                if res.success:
                    print(format_success(res.message))
                else:
                    print(format_error(res.message))
            return 0 if res.success else 1
        elif args.watchlist_command == "remove":
            res = updater.remove_from_watchlist(args.name, args.symbols)
            if args.json:
                print_output(res.summary(), as_json=True)
            else:
                if res.success:
                    print(format_success(res.message))
                else:
                    print(format_error(res.message))
            return 0 if res.success else 1
    else:
        print(format_error("Missing universe sub-command"))
        return 1



def cmd_adjust_data(args: argparse.Namespace, ctx: ApplicationContext) -> int:
    from bist_signal_bot.data.models import Timeframe
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.cli.formatting import format_success, format_error, print_output
    from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol

    try:
        symbol = ensure_valid_internal_symbol(args.symbol.upper())
    except Exception as e:
        print_output({"error": str(e)}, as_json=args.json)
        return 1

    timeframe = Timeframe(args.timeframe)
    source = args.source

    try:
        if args.policy:
            policy = AdjustmentPolicy(args.policy)
        else:
            policy = AdjustmentPolicy(ctx.settings.DEFAULT_ADJUSTMENT_POLICY)
    except Exception as e:
        print_output(format_error(f"Invalid adjustment policy: {args.policy}"), args.json)
        return 1

    store = CorporateActionStore(ctx.settings)
    engine = PriceAdjustmentEngine(
        settings=ctx.settings,
        action_store=store,
        policy=policy,
        require_verified_actions=args.require_verified,
        strict=False  # Keep false in CLI to see reports instead of just crashing
    )

    try:
        mdf = None
        if source == "local":
            local_store = LocalMarketDataStore(ctx.settings)
            mdf = local_store.read_ohlcv(symbol, ctx.settings.DEFAULT_DATA_PROVIDER, timeframe)
        elif source == "mock":
            provider = MockMarketDataProvider(rows=252)
            mdf = provider.fetch_one(symbol, timeframe)

        if not mdf:
             print_output(format_error("Failed to load data."), args.json)
             return 1

        adj_result = engine.adjust_market_data(mdf)
        report = adj_result.report

        saved_adjusted = False
        if args.save_adjusted and source == "local":
             local_store = LocalMarketDataStore(ctx.settings)
             local_store.write_adjusted_ohlcv(adj_result.market_data)
             saved_adjusted = True

        out = report.summary()
        out["saved_adjusted"] = saved_adjusted

        # Log audit
        ctx.audit_logger.log_universe_update(
            event_type=AuditEventType.DATA_ADJUSTMENT,
            message=f"Adjusted data for {symbol}",
            action="ADJUST_DATA",
            symbols_affected=[symbol],
            issue_count=report.issue_count()
        )

        print_output(out, args.json)
        return 0 if report.status.value != "FAILED" else 1

    except Exception as e:
        print_output(format_error(f"Adjustment failed: {str(e)}"), args.json)
        return 1

def cmd_corporate_actions(args: argparse.Namespace, ctx: ApplicationContext) -> int:
    from bist_signal_bot.cli.formatting import format_success, format_error, print_output
    from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
    store = CorporateActionStore(ctx.settings)

    if args.ca_command == "init":
        try:
            path = store.initialize_empty(overwrite=args.overwrite)
            ctx.audit_logger.log_universe_update(
                event_type=AuditEventType.CORPORATE_ACTIONS_INIT,
                message="Initialized corporate actions store",
                action="INIT",
                symbols_affected=[],
                file_path=str(path)
            )
            msg = f"Initialized corporate actions store at {path}"
            print_output({"message": msg, "path": str(path)} if args.json else format_success(msg), args.json)
            return 0
        except Exception as e:
            print_output({"error": str(e)}, as_json=args.json)
            return 1

    elif args.ca_command == "list":
        try:
            actions = store.load_actions()
            if args.symbol:
                symbol = ensure_valid_internal_symbol(args.symbol.upper())
                actions = [a for a in actions if a.symbol == symbol]

            out = [a.model_dump(mode="json") for a in actions]
            if args.json:
                print_output(out, as_json=True)
            else:
                if not actions:
                    print("No corporate actions found.")
                for a in actions:
                    print(f"{a.symbol} | {a.action_date} | {a.action_type.value} | Ratio: {a.ratio} | Cash: {a.cash_amount}")
            return 0
        except Exception as e:
            print_output({"error": str(e)}, as_json=args.json)
            return 1

    elif args.ca_command == "add":
        try:
            symbol = ensure_valid_internal_symbol(args.symbol.upper())
            action_type = CorporateActionType(args.type)
            action_date = date.fromisoformat(args.date)

            action = CorporateAction(
                symbol=symbol,
                action_date=action_date,
                action_type=action_type,
                ratio=args.ratio,
                cash_amount=args.cash,
                description=args.description
            )

            store.add_action(action)
            ctx.audit_logger.log_universe_update(
                event_type=AuditEventType.CORPORATE_ACTIONS_ADD,
                message=f"Added action for {symbol}",
                action="ADD",
                symbols_affected=[symbol]
            )
            msg = f"Successfully added {action_type.value} action for {symbol} on {action_date}"
            print_output({"message": msg, "action": action.model_dump(mode="json")} if args.json else format_success(msg), args.json)
            return 0
        except Exception as e:
            print_output({"error": str(e)}, as_json=args.json)
            return 1

    elif args.ca_command == "remove":
        try:
            symbol = ensure_valid_internal_symbol(args.symbol.upper())
            action_type = CorporateActionType(args.type)
            action_date = date.fromisoformat(args.date)

            removed = store.remove_action(symbol, action_date, action_type)

            if removed:
                ctx.audit_logger.log_universe_update(
                    event_type=AuditEventType.CORPORATE_ACTIONS_REMOVE,
                    message=f"Removed action for {symbol}",
                    action="REMOVE",
                    symbols_affected=[symbol]
                )
                msg = f"Successfully removed {action_type.value} action for {symbol} on {action_date}"
                print_output({"message": msg, "removed": True} if args.json else format_success(msg), args.json)
                return 0
            else:
                msg = f"Action not found for {symbol} on {action_date}"
                print_output({"message": msg, "removed": False} if args.json else format_error(msg), args.json)
                return 1
        except Exception as e:
            print_output({"error": str(e)}, as_json=args.json)
            return 1

    elif args.ca_command == "import":
        try:
            path = Path(args.path)
            report = store.import_actions(path)

            ctx.audit_logger.log_universe_update(
                event_type=AuditEventType.CORPORATE_ACTIONS_IMPORT,
                message=f"Imported corporate actions from {path.name}",
                action="IMPORT",
                symbols_affected=[],
                file_path=str(path),
                validation_passed=report.passed,
                issue_count=len(report.issues)
            )

            if args.json:
                print_output(report.summary(), as_json=True)
            else:
                from bist_signal_bot.cli.formatting import format_corporate_action_validation
                print(format_corporate_action_validation(report))
            return 0 if report.passed else 1
        except Exception as e:
            print_output({"error": str(e)}, as_json=args.json)
            return 1

    elif args.ca_command == "export":
        try:
            out_path = Path(args.output) if args.output else None
            path = store.export_actions(out_path, format=args.format)

            ctx.audit_logger.log_universe_update(
                event_type=AuditEventType.CORPORATE_ACTIONS_EXPORT,
                message=f"Exported corporate actions to {path.name}",
                action="EXPORT",
                symbols_affected=[],
                file_path=str(path)
            )

            msg = f"Exported corporate actions to {path}"
            print_output({"message": msg, "path": str(path)} if args.json else format_success(msg), args.json)
            return 0
        except Exception as e:
            print_output({"error": str(e)}, as_json=args.json)
            return 1

    elif args.ca_command == "validate":
        try:
            actions = store.load_actions()
            report = store.validate_actions(actions)

            ctx.audit_logger.log_universe_update(
                event_type=AuditEventType.CORPORATE_ACTIONS_VALIDATE,
                message="Validated corporate actions store",
                action="VALIDATE",
                symbols_affected=[],
                validation_passed=report.passed,
                issue_count=len(report.issues)
            )

            if args.json:
                print_output(report.summary(), as_json=True)
            else:
                from bist_signal_bot.cli.formatting import format_corporate_action_validation
                print(format_corporate_action_validation(report))
            return 0 if report.passed else 1
        except Exception as e:
            print_output({"error": str(e)}, as_json=args.json)
            return 1
    else:
        print(format_error("Missing corporate-actions sub-command"))
        return 1


def cmd_clean_data(args: argparse.Namespace, ctx: ApplicationContext) -> int:
    symbol = args.symbol.upper()
    try:
        symbol = ensure_valid_internal_symbol(symbol)
    except Exception as e:
        print_output({"error": str(e)}, as_json=args.json)
        return 1

    timeframe = Timeframe(args.timeframe)
    source = args.source

    # Optional policies
    cleaner_kwargs = {"settings": ctx.settings, "strict": args.strict}

    if args.policy_missing:
        try:
            cleaner_kwargs["missing_value_policy"] = MissingValuePolicy(args.policy_missing)
        except Exception as e:
            print_output(format_error(f"Invalid missing policy: {args.policy_missing}"), args.json)
            return 1

    if args.policy_invalid_ohlc:
        try:
            cleaner_kwargs["invalid_ohlc_policy"] = InvalidOhlcPolicy(args.policy_invalid_ohlc)
        except Exception as e:
            print_output(format_error(f"Invalid invalid ohlc policy: {args.policy_invalid_ohlc}"), args.json)
            return 1

    if args.policy_outlier:
        try:
            cleaner_kwargs["outlier_policy"] = OutlierPolicy(args.policy_outlier)
        except Exception as e:
            print_output(format_error(f"Invalid outlier policy: {args.policy_outlier}"), args.json)
            return 1

    if args.policy_duplicate:
        try:
            cleaner_kwargs["duplicate_timestamp_policy"] = DuplicateTimestampPolicy(args.policy_duplicate)
        except Exception as e:
            print_output(format_error(f"Invalid duplicate policy: {args.policy_duplicate}"), args.json)
            return 1

    cleaner = MarketDataCleaner(**cleaner_kwargs)

    try:
        mdf = None
        if source == "local":
            store = LocalMarketDataStore(ctx.settings)
            mdf = store.read_ohlcv(symbol, ctx.settings.DEFAULT_DATA_PROVIDER, timeframe)
        elif source == "mock":
            provider = MockMarketDataProvider(rows=252)
            mdf = provider.fetch_one(symbol, timeframe)

        if not mdf:
             print_output(format_error("Failed to load data."), args.json)
             return 1

        # Add some issues if mock to show cleaning
        if source == "mock" and not mdf.is_empty():
            import numpy as np
            # simulate a duplicate
            last_date = mdf.data.index[-1]
            mdf.data.loc[last_date] = mdf.data.iloc[-1]
            # simulate missing
            mdf.data.iloc[10, 0] = np.nan # open missing

        cleaned_mdf = cleaner.clean_market_data(mdf)
        report = cleaned_mdf.report

        saved = False
        if args.save:
             store = LocalMarketDataStore(ctx.settings)
             store.write_ohlcv(cleaned_mdf.market_data)
             saved = True

        res = {
            "symbol": report.symbol,
            "status": report.status.value,
            "input_rows": int(report.input_rows),
            "output_rows": int(report.output_rows),
            "dropped_rows": int(report.dropped_rows),
            "filled_values": int(report.filled_values),
            "flagged_outliers": int(report.flagged_outliers),
            "usable_for_backtest": bool(report.usable_for_backtest),
            "usable_for_ml": bool(report.usable_for_ml),
            "issue_count": int(report.issue_count()),
            "saved": saved
        }

        print_output(res, args.json)
        return 0 if report.status.value != "FAILED" else 1

    except Exception as e:
        print_output(format_error(f"Cleaning failed: {str(e)}"), args.json)
        return 1

def cmd_normalize_data(args, app_context) -> int:
    from bist_signal_bot.data.normalizer import MarketDataNormalizer
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.models import Timeframe, DataVendor
    from bist_signal_bot.cli.formatting import format_success, format_error, print_output
    import pandas as pd

    symbol = args.symbol
    source = args.source
    timeframe = Timeframe(args.timeframe)
    save = args.save

    settings = app_context.settings.model_copy()
    if args.strict:
        settings.NORMALIZATION_STRICT = True

    normalizer = MarketDataNormalizer(settings)
    store = app_context.local_store

    try:
        if source == "local":
            if not store.exists(symbol, DataVendor.YFINANCE, timeframe):
                print(format_error(f"Local data not found for {symbol} ({timeframe.value})"))
                return 1
            # Read directly to get raw CSV without data_service's auto-normalization to show before/after
            import pandas as pd
            from bist_signal_bot.storage.paths import get_ohlcv_file_path
            file_path = get_ohlcv_file_path(symbol, DataVendor.YFINANCE.value, timeframe.value, settings, "csv")
            try:
                df = pd.read_csv(file_path, parse_dates=["timestamp"] if "timestamp" in pd.read_csv(file_path, nrows=0).columns else None)
            except Exception as e:
                df = pd.read_csv(file_path) # Fallback if no timestamp

            vendor = DataVendor.YFINANCE

        elif source == "mock":
            mock_provider = MockMarketDataProvider()
            mdf = mock_provider.fetch_one(symbol, timeframe)
            df = mdf.data
            vendor = DataVendor.UNKNOWN
        else:
            print(format_error(f"Unknown source: {source}"))
            return 1

        res = normalizer.normalize_dataframe(df, symbol, timeframe, vendor)

        saved = False
        if save:
            store.write_ohlcv(res.market_data)
            saved = True

        if args.json:
            out = res.report.summary()
            out["saved"] = saved
            print_output(out, as_json=True)
        else:
            print_output(f"Symbol: {res.report.symbol}")
            print_output(f"Status: {res.report.status.value}")
            print_output(f"Input Rows: {res.report.input_rows}")
            print_output(f"Output Rows: {res.report.output_rows}")
            print_output(f"Issue Count: {res.report.issue_count()}")
            print_output(f"Output Columns: {res.report.output_columns}")
            print_output(f"Saved: {saved}")

        return 0 if res.report.status.value != "FAILED" else 1

    except Exception as e:
        print(format_error(str(e)))
        return 1

def cmd_indicators(args: argparse.Namespace, ctx: ApplicationContext) -> int:
    from bist_signal_bot.indicators.registry import IndicatorRegistry
    from bist_signal_bot.indicators.engine import IndicatorEngine
    from bist_signal_bot.indicators.models import IndicatorCategory
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.models import Timeframe, DataVendor
    from bist_signal_bot.core.audit import AuditEventType, AuditEvent
    from bist_signal_bot.cli.formatting import format_success, format_error, print_output
    from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
    from bist_signal_bot.storage.local_store import LocalMarketDataStore

    if args.indicators_command == "list":
        try:
            registry = IndicatorRegistry.create_default_registry()
            category = None
            if args.category:
                category = IndicatorCategory(args.category.upper())

            specs = registry.list_specs(category)

            if args.json:
                out = [s.model_dump() for s in specs]
                print_output(out, as_json=True)
            else:
                print(f"Registered Indicators (Count: {len(specs)})")
                print("-" * 50)
                for s in specs:
                    print(f"Name: {s.name}")
                    print(f"  Category: {s.category.value}")
                    print(f"  Required: {s.required_columns}")
                    print(f"  Params: {s.default_params}")
                    print(f"  Outputs: {s.output_columns}")
                    print("-" * 50)
            return 0
        except Exception as e:
            print_output({"error": str(e)}, as_json=args.json)
            return 1

    elif args.indicators_command == "calc":
        symbol = args.symbol.upper()
        try:
            symbol = ensure_valid_internal_symbol(symbol)
        except Exception as e:
            print_output({"error": str(e)}, as_json=args.json)
            return 1

        timeframe = Timeframe(args.timeframe)

        engine = IndicatorEngine(settings=ctx.settings)

        try:
            if args.source == "local":
                store = LocalMarketDataStore(ctx.settings)
                mdf = store.read_ohlcv(symbol, ctx.settings.DEFAULT_DATA_PROVIDER, timeframe)
            else:
                provider = MockMarketDataProvider(rows=args.rows)
                mdf = provider.fetch_one(symbol, timeframe)

            if not mdf or mdf.is_empty():
                print_output(format_error("Failed to load data or data is empty."), args.json)
                return 1

            if args.default_set or (not args.indicator and not args.default_set):
                result = engine.calculate_default_set(mdf)
            else:
                requests = engine.parse_requests(args.indicator)
                result = engine.calculate_many(mdf, requests)

            if args.save_output:
                print("Save output not yet fully supported (Phase 16 scope).")

            if ctx.audit_logger:
                ctx.audit_logger.log_indicator_calculation(
                    symbol=symbol,
                    timeframe=timeframe.value,
                    indicators=[r.indicator for r in result.results],
                    success_count=result.success_count,
                    failed_count=result.failed_count,
                    elapsed_seconds=result.elapsed_seconds,
                    run_id=ctx.runtime_context.run_id
                )

            if args.json:
                print_output(result.summary(), as_json=True)
            else:
                print(f"Indicator Calculation Result for {symbol}")
                print(f"Requested: {result.requested_count}, Success: {result.success_count}, Failed: {result.failed_count}")
                print(f"Elapsed: {result.elapsed_seconds:.4f}s")
                print("\nAdded columns:")
                for r in result.results:
                    if r.status == "SUCCESS":
                        print(f"  {r.indicator}: {r.output_columns}")
                    else:
                        print(f"  {r.indicator}: FAILED")
                        for issue in r.issues:
                            print(f"    - {issue.message}")

                print("\nLast 5 rows of calculated indicators (sample):")
                calc_cols = [c for r in result.results for c in r.output_columns]
                if calc_cols:
                    print(result.output_data[calc_cols].tail(5).to_string())

            return 0 if result.failed_count == 0 else 1

        except Exception as e:
            print_output(format_error(f"Calculation failed: {str(e)}"), args.json)
            return 1

    else:
        print_output(format_error("Missing indicators sub-command"), args.json)
        return 1


def cmd_trend_features(args, ctx) -> int:
    from bist_signal_bot.features.trend_features import TrendFeatureBuilder
    from bist_signal_bot.indicators.engine import IndicatorEngine
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.models import Timeframe, DataVendor
    from bist_signal_bot.cli.formatting import format_success, format_error, print_output
    from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
    import pandas as pd
    import time

    symbol = args.symbol.upper()
    try:
        symbol = ensure_valid_internal_symbol(symbol)
    except Exception as e:
        print_output({"error": str(e)}, as_json=args.json)
        return 1

    engine = IndicatorEngine(settings=ctx.settings)
    builder = TrendFeatureBuilder(indicator_engine=engine, settings=ctx.settings)

    start_time = time.time()

    try:
        if args.source == "mock":
            provider = MockMarketDataProvider(rows=args.rows if args.rows else 500)
            mdf = provider.fetch_one(symbol, timeframe=Timeframe(args.timeframe))
        else:
            from bist_signal_bot.data.universe_store import UniverseStore
            from bist_signal_bot.data.storage import LocalDataStore

            store = LocalDataStore(ctx.settings)
            mdf = store.load_market_data(symbol, timeframe=Timeframe(args.timeframe), vendor=DataVendor.YFINANCE)
            if mdf.is_empty:
                print_output(format_error(f"Local data not found for {symbol} / {args.timeframe}."), args.json)
                return 1

        if args.level == "basic":
            result = builder.build_basic_trend_features(mdf)
        elif args.level == "advanced":
            result = builder.build_advanced_trend_features(mdf)
        else:
            result = builder.build_full_trend_features(mdf)

        elapsed = time.time() - start_time

        # Log to audit
        if ctx.settings.ENABLE_AUDIT_LOG:
            from bist_signal_bot.core.audit import AuditEvent, AuditEventType
            ctx.audit_logger.log_event(
                AuditEvent(
                    event_type=AuditEventType.TREND_FEATURE_CALCULATION,
                    message=f"Calculated trend features for {symbol}",
                    metadata={
                        "symbol": symbol,
                        "timeframe": args.timeframe,
                        "level": args.level,
                        "requested_count": result.requested_count,
                        "success_count": sum(1 for r in result.results if r.status == "SUCCESS"),
                        "failed_count": sum(1 for r in result.results if r.status != "SUCCESS"),
                        "elapsed_seconds": elapsed
                    }
                )
            )

        # Optional save
        if getattr(args, "save_output", False):
            import os
            from bist_signal_bot.config.paths import get_reports_dir

            out_dir = get_reports_dir(ctx.settings)
            os.makedirs(out_dir, exist_ok=True)

            ts_str = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            csv_path = out_dir / f"{symbol}_{args.timeframe}_trend_{args.level}_{ts_str}.csv"

            result.output_data.to_csv(csv_path)

        success_count = sum(1 for r in result.results if r.status == "SUCCESS")
        failed_count = sum(1 for r in result.results if r.status != "SUCCESS")

        # Format summary
        df = result.output_data
        summary = {}
        if not df.empty:
            last_row = df.iloc[-1].to_dict()
            summary = {
                "close": last_row.get("close"),
                "sma_20": last_row.get("sma_20"),
                "sma_50": last_row.get("sma_50"),
                "price_above_sma_20": last_row.get("price_above_sma_20"),
                "ma_cross_state_sma_20_50": last_row.get("ma_cross_state_sma_20_50"),
            }
            if "adx_14" in last_row:
                summary["adx_14"] = last_row.get("adx_14")
            if "trend_strength_score" in last_row:
                summary["trend_strength_score"] = last_row.get("trend_strength_score")

        out = {
            "symbol": symbol,
            "level": args.level,
            "rows": len(df),
            "requested_indicators": result.requested_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "output_trend_columns": list(df.columns),
            "trend_feature_summary": summary
        }

        print_output(out, args.json)
        return 0

    except Exception as e:
        print(f"Trend feature calculation error: {e}")
        print_output({"error": str(e)}, as_json=args.json)
        return 1

def cmd_momentum_features(args, ctx) -> int:
    from bist_signal_bot.features.momentum_features import MomentumFeatureBuilder
    from bist_signal_bot.indicators.engine import IndicatorEngine
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.models import Timeframe, DataVendor
    from bist_signal_bot.cli.formatting import format_success, format_error, print_output
    from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
    import pandas as pd
    import time

    symbol = args.symbol.upper()
    try:
        symbol = ensure_valid_internal_symbol(symbol)
    except Exception as e:
        print_output({"error": str(e)}, as_json=args.json)
        return 1

    engine = IndicatorEngine(settings=ctx.settings)
    builder = MomentumFeatureBuilder(indicator_engine=engine, settings=ctx.settings)

    start_time = time.time()

    try:
        if args.source == "mock":
            provider = MockMarketDataProvider(rows=args.rows if args.rows else 500)
            mdf = provider.fetch_one(symbol, timeframe=Timeframe(args.timeframe))
        else:
            from bist_signal_bot.data.universe_store import UniverseStore
            from bist_signal_bot.data.storage import LocalDataStore

            store = LocalDataStore(ctx.settings)
            mdf = store.load_market_data(symbol, timeframe=Timeframe(args.timeframe), vendor=DataVendor.YFINANCE)
            if mdf.is_empty:
                print_output(format_error(f"Local data not found for {symbol} / {args.timeframe}."), args.json)
                return 1

        if args.level == "basic":
            result = builder.build_basic_momentum_features(mdf)
        elif args.level == "advanced":
            result = builder.build_advanced_momentum_features(mdf)
        else:
            result = builder.build_full_momentum_features(mdf)

        elapsed = time.time() - start_time

        # Log to audit
        if ctx.settings.ENABLE_AUDIT_LOG:
            from bist_signal_bot.core.audit import AuditEvent, AuditEventType
            ctx.audit_logger.log_event(
                AuditEvent(
                    event_type=AuditEventType.MOMENTUM_FEATURE_CALCULATION,
                    message=f"Calculated momentum features for {symbol}",
                    metadata={
                        "symbol": symbol,
                        "timeframe": args.timeframe,
                        "level": args.level,
                        "requested_count": result.requested_count,
                        "success_count": sum(1 for r in result.results if r.status == "SUCCESS"),
                        "failed_count": sum(1 for r in result.results if r.status != "SUCCESS"),
                        "elapsed_seconds": elapsed
                    }
                )
            )

        # Optional save
        if getattr(args, "save_output", False):
            import os
            from bist_signal_bot.config.paths import get_reports_dir

            out_dir = get_reports_dir(ctx.settings)
            os.makedirs(out_dir, exist_ok=True)

            ts_str = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            csv_path = out_dir / f"{symbol}_{args.timeframe}_momentum_{args.level}_{ts_str}.csv"

            result.output_data.to_csv(csv_path)

        success_count = sum(1 for r in result.results if r.status == "SUCCESS")
        failed_count = sum(1 for r in result.results if r.status != "SUCCESS")

        # Format summary
        df = result.output_data
        summary = {}
        if not df.empty:
            last_row = df.iloc[-1].to_dict()
            summary = {
                "close": last_row.get("close")
            }
            if "rsi_14" in last_row: summary["rsi_14"] = last_row.get("rsi_14")
            if "roc_pct_10" in last_row: summary["roc_pct_10"] = last_row.get("roc_pct_10")
            if "stoch_k_14" in last_row: summary["stoch_k_14"] = last_row.get("stoch_k_14")
            if "stoch_d_14_3" in last_row: summary["stoch_d_14_3"] = last_row.get("stoch_d_14_3")
            if "mfi_14" in last_row: summary["mfi_14"] = last_row.get("mfi_14")
            if "momentum_strength_score" in last_row: summary["momentum_strength_score"] = last_row.get("momentum_strength_score")
            if "momentum_direction_score" in last_row: summary["momentum_direction_score"] = last_row.get("momentum_direction_score")

        out = {
            "symbol": symbol,
            "level": args.level,
            "rows": len(df),
            "requested_indicators": result.requested_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "output_momentum_columns": list(df.columns),
            "momentum_feature_summary": summary
        }

        print_output(out, args.json)
        return 0

    except Exception as e:
        print(f"Momentum feature calculation error: {e}")
        print_output({"error": str(e)}, as_json=args.json)
        return 1


def cmd_volatility_features(args, ctx) -> int:
    from bist_signal_bot.features.volatility_features import VolatilityFeatureBuilder
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.data_service import MarketDataService
    from bist_signal_bot.cli.formatting import print_output
    from bist_signal_bot.core.audit import AuditEventType, AuditEvent
    from datetime import datetime
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

        builder = VolatilityFeatureBuilder(settings=ctx.settings)

        if args.level == "basic":
            result = builder.build_basic_volatility_features(mdf)
        elif args.level == "advanced":
            result = builder.build_advanced_volatility_features(mdf)
        else:
            result = builder.build_full_volatility_features(mdf)

        ctx.audit_logger.log_event(
            ctx.audit_logger._audit_file and ctx.audit_logger.settings.ENABLE_AUDIT_LOG and AuditEvent(
                event_type=AuditEventType.VOLATILITY_FEATURE_CALCULATION,
                message=f"Calculated volatility features for {symbol}",
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
            ts_str = datetime.now().strftime("%Y%md%H%M%S")
            csv_path = out_dir / f"{symbol}_{args.timeframe}_volatility_{args.level}_{ts_str}.csv"
            df.to_csv(csv_path)

        summary = {}
        if not df.empty:
            last_row = df.iloc[-1].to_dict()
            summary["close"] = last_row.get("close")
            if "atr_pct_14" in last_row: summary["atr_pct_14"] = last_row.get("atr_pct_14")
            if "hist_vol_20" in last_row: summary["hist_vol_20"] = last_row.get("hist_vol_20")
            if "range_pct" in last_row: summary["range_pct"] = last_row.get("range_pct")
            if "gap_pct" in last_row: summary["gap_pct"] = last_row.get("gap_pct")
            if "vol_regime_state_20_252" in last_row: summary["vol_regime_state"] = last_row.get("vol_regime_state_20_252")
            if "volatility_risk_score" in last_row: summary["volatility_risk_score"] = last_row.get("volatility_risk_score")
            if "volatility_regime_score" in last_row: summary["volatility_regime_score"] = last_row.get("volatility_regime_score")

            # Clean up nan for dict dump
            summary = {k: None if pd.isna(v) else v for k, v in summary.items()}

        out_data = {
            "symbol": symbol,
            "level": args.level,
            "rows": len(df),
            "requested_count": result.requested_count,
            "success_count": result.success_count,
            "failed_count": result.failed_count,
            "output_volatility_columns": list(df.columns),
            "volatility_feature_summary": summary
        }

        print_output(out_data, as_json=args.json)
        return 0

    except Exception as e:
        logger.error(f"Command error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1

def cmd_volume_features(args, ctx) -> int:
    from bist_signal_bot.features.volume_features import VolumeFeatureBuilder
    from bist_signal_bot.indicators.engine import IndicatorEngine
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.models import Timeframe, DataVendor
    from bist_signal_bot.cli.formatting import format_success, format_error, print_output
    from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
    from bist_signal_bot.core.audit import AuditEventType, AuditEvent
    import pandas as pd
    import time

    symbol = args.symbol.upper()
    try:
        symbol = ensure_valid_internal_symbol(symbol)
    except Exception as e:
        print_output({"error": str(e)}, as_json=args.json)
        return 1

    # logger not in ctx

    start_time = time.time()
    try:
        engine = IndicatorEngine(settings=ctx.settings)
        builder = VolumeFeatureBuilder(indicator_engine=engine, settings=ctx.settings)

        if args.source == "mock":
            provider = MockMarketDataProvider()
            rows = args.rows or 250
            req = __import__("bist_signal_bot.data.models").data.models.DataFetchRequest(symbols=[symbol], timeframe=Timeframe(args.timeframe), rows=args.rows or 250); mdf = provider.fetch_ohlcv(req).get(symbol)
        else:
            from bist_signal_bot.data.data_service import LocalDataService
            service = LocalDataService(ctx.settings)
            mdf = service.load_data(symbol, Timeframe(args.timeframe))

        if mdf is None or len(mdf.data) == 0:
            print_output({"error": f"No data available for {symbol}"}, as_json=args.json)
            return 1

        if args.level == "basic":
            result = builder.build_basic_volume_features(mdf)
        elif args.level == "advanced":
            result = builder.build_advanced_volume_features(mdf)
        else:
            result = builder.build_full_volume_features(mdf)

        summary = result.summary()

        ctx.audit_logger.log_event(
            ctx.audit_logger._audit_file and ctx.audit_logger.settings.ENABLE_AUDIT_LOG and AuditEvent(
                event_type=AuditEventType.VOLUME_FEATURE_CALCULATION,
                symbol=symbol,
                message=f"Calculated volume features for {symbol}",
                metadata={
                    "timeframe": args.timeframe,
                    "level": args.level,
                    "requested_count": result.requested_count,
                    "success_count": result.success_count,
                    "failed_count": result.failed_count,
                    "elapsed_seconds": round(time.time() - start_time, 4)
                }
            )
        )

        if args.save_output:
            out_dir = ctx.settings.DATA_DIR / "features"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{symbol}_{args.timeframe}_volume_{args.level}.csv"
            result.output_data.to_csv(out_file)
            summary["saved_to"] = str(out_file)

        if args.json:
            import json
            print(json.dumps(summary, indent=2))
        else:
            print(f"Volume Feature Calculation for {symbol}")
            print(f"Level: {args.level}")
            print(f"Requested: {result.requested_count}, Success: {result.success_count}, Failed: {result.failed_count}")
            print(f"Output columns: {len(result.output_data.columns)}")
            if len(result.output_data) > 0:
                print("\nVolume feature summary:")

                # Show key volume feature columns if they exist
                last_row = result.output_data.iloc[-1]
                cols_to_show = [
                    "close", "volume",
                    f"volume_ratio_{ctx.settings.VOLUME_WINDOW}",
                    f"volume_zscore_{ctx.settings.VOLUME_WINDOW}",
                    f"volume_spike_{ctx.settings.VOLUME_WINDOW}_{str(ctx.settings.VOLUME_SPIKE_MULTIPLIER).replace('.', '_')}",
                    f"cmf_{ctx.settings.VOLUME_CMF_WINDOW}",
                    f"liquidity_score_{ctx.settings.VOLUME_LIQUIDITY_WINDOW}",
                    "volume_activity_score",
                    "volume_pressure_score"
                ]
                for col in cols_to_show:
                    if col in last_row.index:
                        print(f"  {col}: {last_row[col]}")

        return 0

    except Exception as e:
        # logger not in ctx
        print_output({"error": f"Volume feature calculation error: {e}"}, as_json=args.json)
        return 1
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
            print(f"Symbol: {symbol}\nLevel: {args.level}\nRows: {len(df)}")
            print(format_pattern_batch_result(result))

        return 0

    except Exception as e:
        logger.error(f"Pattern feature error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1

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
            print(f"Symbol: {symbol}\nLevel: {args.level}\nRows: {len(df)}")
            print(format_pattern_batch_result(result))

        return 0

    except Exception as e:
        logger.error(f"Pattern feature error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1
def cmd_divergence_detect(args, ctx) -> int:
    from bist_signal_bot.divergence.engine import DivergenceEngine
    from bist_signal_bot.features.divergence_features import DivergenceFeatureBuilder
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.data_service import MarketDataService
    from bist_signal_bot.cli.formatting import print_output, format_divergence_result
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

        engine = DivergenceEngine(settings=ctx.settings)
        builder = DivergenceFeatureBuilder(divergence_engine=engine, settings=ctx.settings)

        if args.level:
            if args.level == "basic":
                result_obj = builder.build_basic_divergence_features(mdf)
            elif args.level == "advanced":
                result_obj = builder.build_advanced_divergence_features(mdf)
            else:
                result_obj = builder.build_full_divergence_features(mdf)
        else:
            # Manual options
            kwargs = {
                "pivot_mode": args.pivot_mode,
            }
            if args.lookback is not None: kwargs["lookback"] = args.lookback
            if args.confirmation_bars is not None: kwargs["confirmation_bars"] = args.confirmation_bars
            if args.min_pivot_distance is not None: kwargs["min_pivot_distance"] = args.min_pivot_distance
            if args.max_pivot_distance is not None: kwargs["max_pivot_distance"] = args.max_pivot_distance
            kwargs["include_hidden"] = args.include_hidden
            kwargs["include_regular"] = args.include_regular

            req = engine.parse_request(indicators=args.indicators, **kwargs)
            result_obj = engine.detect(mdf, req)

        result = result_obj.result
        df = result_obj.output_data

        ctx.audit_logger.log_event(
            ctx.audit_logger._audit_file and ctx.audit_logger.settings.ENABLE_AUDIT_LOG and AuditEvent(
                event_type=AuditEventType.DIVERGENCE_DETECTION,
                message=f"Calculated divergence features for {symbol}",
                symbol=symbol,
                metadata={
                    "timeframe": args.timeframe,
                    "pivot_mode": result.pivot_mode.value,
                    "indicators": result.requested_indicators,
                    "detected_count": result.detected_count,
                    "bullish_count": result.bullish_count(),
                    "bearish_count": result.bearish_count(),
                    "elapsed_seconds": result.elapsed_seconds
                }
            )
        )

        if args.save_output:
            out_dir = ctx.settings.DATA_DIR / "features"
            out_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(out_dir / f"{symbol}_{args.timeframe}_divergence.csv")

        if args.json:
            print_output(result.summary(), as_json=True)
        else:
            print(f"Symbol: {symbol}\\nTimeframe: {args.timeframe}\\nPivot Mode: {result.pivot_mode.value}\\nRows: {len(df)}\\n")

            lines = [
                "Divergence feature summary",
                f"Requested indicators: {', '.join(result.requested_indicators)}",
                f"Detected count: {result.detected_count}",
                f"Bullish count: {result.bullish_count()}",
                f"Bearish count: {result.bearish_count()}",
                f"Strong count: {result.strong_count()}",
                f"Output columns: {', '.join(result.output_columns)}"
            ]

            if result.events:
                lines.append("\\nLast 5 events:")
                for e in result.events[-5:]:
                    lines.append(f"  {e.divergence_type.value} on {e.indicator} (Strength: {e.strength.value})")

            print("\\n".join(lines))

        return 0

    except Exception as e:
        logger.error(f"Divergence feature error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1

def cmd_mtf_features(args, ctx) -> int:
    from bist_signal_bot.features.multi_timeframe_features import MultiTimeframeFeatureBuilder
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.data_service import MarketDataService
    from bist_signal_bot.data.models import Timeframe
    from bist_signal_bot.cli.formatting import print_output, format_multi_timeframe_result
    from bist_signal_bot.core.audit import AuditEventType, AuditEvent
    import pandas as pd
    import logging

    logger = logging.getLogger("bist_signal_bot.cli")

    try:
        symbol = args.symbol.upper()
        base_tf = Timeframe(args.base_timeframe)

        if args.source == "mock":
            rows = args.rows or 252
            provider = MockMarketDataProvider(rows=rows)
            mdf = provider.fetch_one(symbol, base_tf)
        else:
            service = MarketDataService(settings=ctx.settings)
            period = args.period or "2y"
            mdf = service.get_ohlcv(symbol, base_tf, period=period)

        if mdf is None or mdf.data.empty:
            print_output({"error": "No data found or available"}, as_json=args.json)
            return 1

        if args.alignment_mode:
            ctx.settings.MTF_ALIGNMENT_MODE = args.alignment_mode
        if args.no_forward_fill:
            ctx.settings.MTF_FORWARD_FILL = False
        if args.no_shift_higher_tf:
            ctx.settings.MTF_SHIFT_HIGHER_TF_BY_ONE_BAR = False
        if args.drop_unaligned:
            ctx.settings.MTF_DROP_UNALIGNED_ROWS = True

        ctx.settings.MTF_BASE_TIMEFRAME = base_tf.value
        if args.higher:
            ctx.settings.MTF_HIGHER_TIMEFRAMES = ",".join(args.higher)

        builder = MultiTimeframeFeatureBuilder(settings=ctx.settings)

        if args.level == "basic":
            result = builder.build_basic_mtf_features(mdf, symbol=symbol)
        elif args.level == "advanced":
            result = builder.build_advanced_mtf_features(mdf, symbol=symbol)
        else:
            result = builder.build_full_mtf_features(mdf, symbol=symbol)

        df = result.output_data

        if args.save_output:
            out_dir = ctx.settings.DATA_DIR / "features"
            out_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(out_dir / f"{symbol}_mtf_{args.base_timeframe}_{args.level}.csv")

        if args.json:
            out_dict = result.summary()
            if len(df) > 0:
                last_row = df.iloc[-1].to_dict()
                last_row = {k: v for k, v in last_row.items() if not pd.isna(v)}
                out_dict['sample_last_row'] = last_row
            print_output(out_dict, as_json=True)
        else:
            print(format_multi_timeframe_result(result))

        return 0

    except Exception as e:
        logger.error(f"MTF feature error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1

def cmd_strategies_list(args, ctx) -> int:
    from bist_signal_bot.strategies.registry import get_registry
    from bist_signal_bot.cli.formatting import print_output
    import logging

    logger = logging.getLogger("bist_signal_bot.cli")

    try:
        registry = get_registry()

        category = None
        if args.category:
            from bist_signal_bot.strategies.models import StrategyCategory
            category = StrategyCategory(args.category)

        specs = registry.list_specs(category)

        if args.json:
            print_output([s.model_dump() for s in specs], as_json=True)
            return 0

        print(f"Registered Strategies ({len(specs)}):")
        print("-" * 50)

        for spec in specs:
            print(f"Name: {spec.name}")
            print(f"Category: {spec.category.value}")
            print(f"Position Side: {spec.position_side.value}")
            print(f"Supports Short: {spec.supports_short}")
            print(f"Supports MTF: {spec.supports_multi_timeframe}")
            print(f"Required Columns: {', '.join(spec.required_columns) if spec.required_columns else 'None'}")
            print(f"Default Params: {spec.default_params}")
            print("-" * 50)

        return 0

    except Exception as e:
        logger.error(f"Strategy list error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1

def cmd_strategies_run(args, ctx) -> int:
    from bist_signal_bot.strategies.engine import StrategyEngine
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.data_service import MarketDataService
    from bist_signal_bot.cli.formatting import print_output
    from bist_signal_bot.core.audit import AuditEventType, AuditEvent
    import logging

    logger = logging.getLogger("bist_signal_bot.cli")

    try:
        symbol = args.symbol.upper()
        strategy_name = args.strategy.lower()

        engine = StrategyEngine(settings=ctx.settings)
        params = engine.parse_params(args.param)

        if args.allow_short:
            params["allow_short"] = True

        if args.source == "mock":
            rows = args.rows or 252
            provider = MockMarketDataProvider(rows=rows)
            mdf = provider.fetch_one(symbol, args.timeframe)
            data_service = provider
        else:
            service = MarketDataService(settings=ctx.settings)
            period = args.period or ctx.settings.DEFAULT_HISTORY_PERIOD
            mdf = service.get_ohlcv(symbol, args.timeframe, period=period)
            data_service = service

        if mdf is None or mdf.data.empty:
            print_output({"error": f"No data found for {symbol}"}, as_json=args.json)
            return 1

        engine.data_service = data_service
        result = engine.run_strategy_on_data(
            strategy_name=strategy_name,
            symbol=symbol,
            data=mdf,
            params=params,
            timeframe=args.timeframe
        )

        # Log audit event if configured
        if ctx.audit_logger.settings.ENABLE_AUDIT_LOG and result.candidate:
            ctx.audit_logger.log_event(AuditEvent(
                event_type=AuditEventType.SIGNAL_CANDIDATE_GENERATED,
                message=f"Generated signal candidate for {symbol}",
                symbol=symbol,
                metadata=result.summary()
            ))

        if args.json:
            print_output(result.summary(), as_json=True)
        else:
            print(f"Strategy Execution Result:")
            print(f"Symbol: {symbol}")
            print(f"Strategy: {strategy_name}")
            print(f"Status: {result.status}")
            print(f"Elapsed: {result.elapsed_seconds:.3f}s")

            if result.candidate:
                c = result.candidate
                print(f"\n--- SIGNAL CANDIDATE ---")
                print(f"Direction: {c.direction.value}")
                print(f"Score: {c.score:.1f}")
                print(f"Strength: {c.strength.value}")
                print(f"Status: {c.status.value}")

                if c.reasons:
                    print("\nReasons:")
                    for r in c.reasons:
                        print(f"  - {r.message}")

                if c.risk_notes:
                    print("\nRisk Notes:")
                    for rn in c.risk_notes:
                        print(f"  - {rn.message}")

                print(f"\n{c.disclaimer}")
            else:
                print("\nNo actionable candidate generated.")

            if result.issues:
                print("\nIssues:")
                for issue in result.issues:
                    print(f"  - [{issue.severity.upper()}] {issue.message}")

        return 0

    except Exception as e:
        logger.error(f"Strategy run error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1

def cmd_strategies_batch(args, ctx) -> int:
    from bist_signal_bot.strategies.engine import StrategyEngine
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.data_service import MarketDataService
    from bist_signal_bot.cli.formatting import print_output
    from bist_signal_bot.core.audit import AuditEventType, AuditEvent
    import logging

    logger = logging.getLogger("bist_signal_bot.cli")

    try:
        strategy_name = args.strategy.lower()

        # Determine symbols to run
        if args.all:
            # We would normally get this from universe, using mock fallback for tests
            symbols = ["ASELS", "GARAN", "THYAO", "BIMAS", "EREGL"]
        elif args.group:
            # Placeholder for group logic
            symbols = ["ASELS", "THYAO"]
        elif args.symbols:
            symbols = [s.upper() for s in args.symbols]
        else:
            print_output({"error": "Must specify --symbols, --group, or --all"}, as_json=args.json)
            return 1

        engine = StrategyEngine(settings=ctx.settings)
        params = engine.parse_params(args.param)

        if args.allow_short:
            params["allow_short"] = True

        if args.source == "mock":
            # Mock data provider is sufficient for batch testing
            engine.data_service = MockMarketDataProvider()
        else:
            engine.data_service = MarketDataService(settings=ctx.settings)

        continue_on_error = not getattr(args, "fail_fast", False)

        batch_result = engine.run_strategy_batch(
            strategy_name=strategy_name,
            symbols=symbols,
            params=params,
            continue_on_error=continue_on_error
        )

        if ctx.audit_logger.settings.ENABLE_AUDIT_LOG:
            ctx.audit_logger.log_event(AuditEvent(
                event_type=AuditEventType.STRATEGY_BATCH_RUN,
                message=f"Ran batch strategy {strategy_name} on {len(symbols)} symbols",
                symbol="ALL",
                metadata=batch_result.summary()
            ))

        if args.json:
            print_output(batch_result.summary(), as_json=True)
        else:
            print(f"Batch Strategy Result: {strategy_name}")
            print(f"Processed: {batch_result.symbol_count}")
            print(f"Success: {batch_result.success_count}")
            print(f"Failed: {batch_result.failed_count}")
            print(f"Elapsed: {batch_result.elapsed_seconds:.2f}s")
            print(f"\nSignals generated: {len(batch_result.candidates)}")
            print(f"  LONG: {batch_result.long_count()}")
            print(f"  SHORT: {batch_result.short_count()}")
            print(f"  WATCH: {batch_result.watch_count()}")

            if batch_result.issues:
                print(f"\nTop Issues:")
                for issue in batch_result.issues[:5]:
                    print(f"  - {issue}")

            print(f"\nResearch signal candidates only. Not investment advice.")

        return 0

    except Exception as e:
        logger.error(f"Strategy batch error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1


def cmd_benchmarks_list(args, ctx) -> int:
    from bist_signal_bot.benchmarks.registry import create_default_benchmark_registry
    from bist_signal_bot.cli.formatting import print_output
    import logging

    logger = logging.getLogger("bist_signal_bot.cli")

    try:
        registry = create_default_benchmark_registry()

        category = None
        if getattr(args, "category", None):
            from bist_signal_bot.benchmarks.models import BenchmarkCategory
            category = BenchmarkCategory(args.category)

        specs = registry.list_specs(category)

        if args.json:
            print_output([s.model_dump() for s in specs], as_json=True)
            return 0

        print(f"Registered Benchmarks ({len(specs)}):")
        print("-" * 50)

        for spec in specs:
            print(f"Name: {spec.name}")
            print(f"Category: {spec.category.value}")
            print(f"Required Columns: {', '.join(spec.required_columns) if spec.required_columns else 'None'}")
            print(f"Supports Portfolio: {spec.supports_portfolio}")
            print(f"Deterministic: {spec.deterministic}")
            print(f"Default Params: {spec.default_params}")
            print("-" * 50)

        return 0

    except Exception as e:
        logger.error(f"Benchmark list error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1


def cmd_benchmarks_run(args, ctx) -> int:
    from bist_signal_bot.benchmarks.engine import BenchmarkEngine
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.data_service import MarketDataService
    from bist_signal_bot.cli.formatting import print_output, format_benchmark_result
    from bist_signal_bot.core.audit import AuditEventType, AuditEvent
    import logging

    logger = logging.getLogger("bist_signal_bot.cli")

    try:
        symbol = args.symbol.upper() if args.symbol else None
        benchmark_name = args.benchmark.lower()

        engine = BenchmarkEngine(settings=ctx.settings)
        params = engine.parse_params(args.param)

        if args.source == "mock":
            rows = args.rows or 252
            provider = MockMarketDataProvider(rows=rows)
            mdf = provider.fetch_one(symbol, args.timeframe) if symbol else None
            data_service = provider
        else:
            service = MarketDataService(settings=ctx.settings)
            period = args.period or ctx.settings.DOWNLOAD_DEFAULT_PERIOD
            mdf = service.get_ohlcv(symbol, args.timeframe, period=period) if symbol else None
            data_service = service

        if (mdf is None or mdf.data.empty) and benchmark_name != "cash":
            print_output({"error": f"No data found for {symbol}"}, as_json=args.json)
            return 1

        engine.data_service = data_service
        result = engine.run_on_data(
            benchmark_name=benchmark_name,
            symbol=symbol,
            data=mdf,
            params=params,
            timeframe=args.timeframe
        )

        if ctx.audit_logger.settings.ENABLE_AUDIT_LOG:
            ctx.audit_logger.log_event(AuditEvent(
                event_type=AuditEventType.BENCHMARK_RUN,
                message=f"Ran benchmark {benchmark_name} for {symbol}",
                symbol=symbol,
                metadata=result.summary()
            ))

        if args.json:
            print_output(result.summary(), as_json=True)
        else:
            print(format_benchmark_result(result))

        return 0

    except Exception as e:
        logger.error(f"Benchmark run error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1

def cmd_benchmarks_batch(args, ctx) -> int:
    from bist_signal_bot.benchmarks.engine import BenchmarkEngine
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.data_service import MarketDataService
    from bist_signal_bot.cli.formatting import print_output, format_benchmark_batch
    from bist_signal_bot.core.audit import AuditEventType, AuditEvent
    import logging

    logger = logging.getLogger("bist_signal_bot.cli")

    try:
        benchmark_name = args.benchmark.lower()

        if args.all:
            symbols = ["ASELS", "GARAN", "THYAO", "BIMAS", "EREGL"]
        elif args.group:
            symbols = ["ASELS", "THYAO"]
        elif args.symbols:
            symbols = [s.upper() for s in args.symbols]
        else:
            print_output({"error": "Must specify --symbols, --group, or --all"}, as_json=args.json)
            return 1

        engine = BenchmarkEngine(settings=ctx.settings)
        params = engine.parse_params(args.param)

        if args.source == "mock":
            engine.data_service = MockMarketDataProvider()
        else:
            engine.data_service = MarketDataService(settings=ctx.settings)

        continue_on_error = not getattr(args, "fail_fast", False)

        batch_result = engine.run_batch(
            benchmark_name=benchmark_name,
            symbols=symbols,
            params=params,
            continue_on_error=continue_on_error
        )

        if ctx.audit_logger.settings.ENABLE_AUDIT_LOG:
            ctx.audit_logger.log_event(AuditEvent(
                event_type=AuditEventType.BENCHMARK_BATCH_RUN,
                message=f"Ran batch benchmark {benchmark_name}",
                symbol="ALL",
                metadata=batch_result.summary()
            ))

        if args.json:
            print_output(batch_result.summary(), as_json=True)
        else:
            print(format_benchmark_batch(batch_result))

        return 0

    except Exception as e:
        logger.error(f"Benchmark batch error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1


def cmd_benchmarks_default(args, ctx) -> int:
    from bist_signal_bot.benchmarks.engine import BenchmarkEngine
    from bist_signal_bot.data.mock_provider import MockMarketDataProvider
    from bist_signal_bot.data.data_service import MarketDataService
    from bist_signal_bot.cli.formatting import print_output, format_benchmark_result
    from bist_signal_bot.core.audit import AuditEventType, AuditEvent
    import logging

    logger = logging.getLogger("bist_signal_bot.cli")

    try:
        symbol = args.symbol.upper()

        engine = BenchmarkEngine(settings=ctx.settings)

        if args.source == "mock":
            rows = args.rows or 252
            provider = MockMarketDataProvider(rows=rows)
            mdf = provider.fetch_one(symbol, args.timeframe)
        else:
            service = MarketDataService(settings=ctx.settings)
            period = args.period or ctx.settings.DOWNLOAD_DEFAULT_PERIOD
            mdf = service.get_ohlcv(symbol, args.timeframe, period=period)

        if mdf is None or mdf.data.empty:
            print_output({"error": f"No data found for {symbol}"}, as_json=args.json)
            return 1

        results = engine.run_default_benchmarks(symbol=symbol, data=mdf)

        if ctx.audit_logger.settings.ENABLE_AUDIT_LOG:
            ctx.audit_logger.log_event(AuditEvent(
                event_type=AuditEventType.BENCHMARK_RUN,
                message=f"Ran default benchmarks for {symbol}",
                symbol=symbol,
                metadata={"benchmarks_run": list(results.keys())}
            ))

        if args.json:
            out = {k: v.summary() for k, v in results.items()}
            print_output(out, as_json=True)
        else:
            print(f"Default Benchmarks for {symbol}")
            print("=" * 50)
            for k, v in results.items():
                print(f"\n[{k.upper()}]")
                print(format_benchmark_result(v))

        return 0

    except Exception as e:
        logger.error(f"Benchmark default error: {e}", exc_info=True)
        print_output({"error": str(e)}, as_json=args.json)
        return 1
