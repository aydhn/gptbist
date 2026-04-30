
from bist_signal_bot.data.cleaning import MarketDataCleaner
from bist_signal_bot.data.models import MissingValuePolicy, InvalidOhlcPolicy, OutlierPolicy, DuplicateTimestampPolicy
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
from bist_signal_bot.data.models import Timeframe
from bist_signal_bot.storage.local_store import LocalMarketDataStore

from datetime import date

from bist_signal_bot.core.audit import AuditEventType
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
        print_output(format_error(str(e)), args.json)
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
            print_output(format_error(str(e)), args.json)
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
            print_output(format_error(str(e)), args.json)
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
            print_output(format_error(str(e)), args.json)
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
            print_output(format_error(str(e)), args.json)
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
            print_output(format_error(str(e)), args.json)
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
            print_output(format_error(str(e)), args.json)
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
            print_output(format_error(str(e)), args.json)
            return 1
    else:
        print(format_error("Missing corporate-actions sub-command"))
        return 1


def cmd_clean_data(args: argparse.Namespace, ctx: ApplicationContext) -> int:
    symbol = args.symbol.upper()
    try:
        symbol = ensure_valid_internal_symbol(symbol)
    except Exception as e:
        print_output(format_error(str(e)), args.json)
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
