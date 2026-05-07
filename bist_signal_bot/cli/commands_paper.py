import argparse
import json
import logging
import sys

from bist_signal_bot.config.settings import settings
from bist_signal_bot.paper.engine import PaperTradingEngine
from bist_signal_bot.paper.ledger import PaperLedgerStore
from bist_signal_bot.paper.reporting import format_paper_status_text, format_paper_run_text
from bist_signal_bot.strategies.engine import StrategyEngine
from bist_signal_bot.data.market_data import MarketDataService
from bist_signal_bot.paper.models import PaperRunRequest, PaperExecutionMode


def get_engine() -> PaperTradingEngine:
    ledger = PaperLedgerStore(settings)
    strat = StrategyEngine(settings)
    data = MarketDataService(settings)
    return PaperTradingEngine(
        ledger_store=ledger,
        strategy_engine=strat,
        data_service=data,
        settings=settings
    )

def handle_paper_init(args: argparse.Namespace) -> None:
    engine = get_engine()
    acc_id = args.account or settings.PAPER_DEFAULT_ACCOUNT_ID
    try:
        state = engine.initialize_account(acc_id, args.cash, args.overwrite)
        print(f"Account {state.account.account_id} initialized with {state.account.cash} cash.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def handle_paper_status(args: argparse.Namespace) -> None:
    engine = get_engine()
    acc_id = args.account or settings.PAPER_DEFAULT_ACCOUNT_ID
    try:
        if args.json:
            print(json.dumps(engine.status(acc_id), indent=2))
        else:
            state = engine.load_state(acc_id)
            print(format_paper_status_text(state))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def handle_paper_run_once(args: argparse.Namespace) -> None:
    engine = get_engine()
    acc_id = args.account or settings.PAPER_DEFAULT_ACCOUNT_ID

    params = {}
    if args.param:
        for p in args.param:
            try:
                k, v = p.split('=', 1)
                try:
                    params[k] = float(v) if '.' in v else int(v)
                except ValueError:
                    params[k] = v
            except ValueError:
                print(f"Invalid param format: {p}. Use key=value")
                sys.exit(1)

    req = PaperRunRequest(
        account_id=acc_id,
        symbols=args.symbols,
        strategy_name=args.strategy,
        source=args.source,
        timeframe=args.timeframe,
        execution_mode=PaperExecutionMode(args.execution),
        use_trade_risk=not args.no_trade_risk,
        use_portfolio_risk=not args.no_portfolio_risk,
        params=params
    )

    # Force mock source internally for simplicity in tests if specified

    try:
        res = engine.run_once(req)
        if args.json:
            print(res.model_dump_json(indent=2))
        else:
            print(format_paper_run_text(res))
    except Exception as e:
         print(f"Error: {e}")
         sys.exit(1)

def handle_paper_positions(args: argparse.Namespace) -> None:
    engine = get_engine()
    acc_id = args.account or settings.PAPER_DEFAULT_ACCOUNT_ID
    try:
        state = engine.load_state(acc_id)
        if args.json:
            print(json.dumps([p.model_dump() for p in state.open_positions()], indent=2))
        else:
            pos = state.open_positions()
            if not pos:
                print("No open positions.")
            for p in pos:
                print(f"{p.symbol} {p.side.value} Qty: {p.quantity} Avg: {p.avg_entry_price:.2f} Mkt: {p.market_value:.2f} PnL: {p.unrealized_pnl:.2f}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def handle_paper_orders(args: argparse.Namespace) -> None:
    engine = get_engine()
    acc_id = args.account or settings.PAPER_DEFAULT_ACCOUNT_ID
    try:
        state = engine.load_state(acc_id)
        orders = state.orders
        if args.status:
            orders = [o for o in orders if o.status.value == args.status]

        if args.json:
            print(json.dumps([o.model_dump() for o in orders], indent=2))
        else:
            if not orders:
                print("No orders found.")
            for o in orders:
                print(f"[{o.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {o.order_id[:8]} {o.symbol} {o.side.value} {o.quantity} {o.status.value}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def handle_paper_fills(args: argparse.Namespace) -> None:
    engine = get_engine()
    acc_id = args.account or settings.PAPER_DEFAULT_ACCOUNT_ID
    try:
        state = engine.load_state(acc_id)
        if args.json:
            print(json.dumps([f.model_dump() for f in state.fills], indent=2))
        else:
            if not state.fills:
                print("No fills found.")
            for f in state.fills:
                print(f"[{f.filled_at.strftime('%Y-%m-%d %H:%M:%S')}] {f.fill_id[:8]} {f.symbol} {f.side.value} {f.quantity} @ {f.fill_price:.2f} (Eff: {f.effective_price:.2f})")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def handle_paper_trades(args: argparse.Namespace) -> None:
    engine = get_engine()
    acc_id = args.account or settings.PAPER_DEFAULT_ACCOUNT_ID
    try:
        state = engine.load_state(acc_id)
        if args.json:
            print(json.dumps([t.model_dump() for t in state.trades], indent=2))
        else:
            if not state.trades:
                print("No trades found.")
            for t in state.trades:
                print(f"[{t.status}] {t.symbol} {t.side.value} Qty: {t.quantity} Entry: {t.entry_price:.2f} Exit: {t.exit_price or 0:.2f} Net PnL: {t.net_pnl or 0:.2f}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def handle_paper_close(args: argparse.Namespace) -> None:
    engine = get_engine()
    acc_id = args.account or settings.PAPER_DEFAULT_ACCOUNT_ID

    try:
        mode = PaperExecutionMode.MANUAL_PRICE if args.manual_price else PaperExecutionMode.LATEST_CLOSE_RESEARCH
        res = engine.close_position(
            account_id=acc_id,
            symbol=args.symbol,
            execution_mode=mode,
            manual_price=args.manual_price
        )
        print(format_paper_run_text(res))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def handle_paper_reset(args: argparse.Namespace) -> None:
    if not args.confirm:
        print("Error: You must provide --confirm to reset the account.")
        sys.exit(1)

    engine = get_engine()
    acc_id = args.account or settings.PAPER_DEFAULT_ACCOUNT_ID
    try:
        state = engine.initialize_account(acc_id, args.cash, overwrite=True)
        print(f"Account {state.account.account_id} reset to {state.account.cash} cash.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def handle_paper_export(args: argparse.Namespace) -> None:
    engine = get_engine()
    acc_id = args.account or settings.PAPER_DEFAULT_ACCOUNT_ID
    try:
        state = engine.load_state(acc_id)
        paths = engine.ledger_store.export_csv(state)
        for name, p in paths.items():
             print(f"Exported {name} to {p}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def handle_paper_config(args: argparse.Namespace) -> None:
    config = {
        "ENABLE_PAPER_TRADING": settings.ENABLE_PAPER_TRADING,
        "PAPER_DEFAULT_ACCOUNT_ID": settings.PAPER_DEFAULT_ACCOUNT_ID,
        "PAPER_INITIAL_CASH": settings.PAPER_INITIAL_CASH,
        "PAPER_REQUIRE_RISK_APPROVAL": settings.PAPER_REQUIRE_RISK_APPROVAL,
        "PAPER_USE_PORTFOLIO_RISK": settings.PAPER_USE_PORTFOLIO_RISK,
        "PAPER_USE_TRADE_RISK": settings.PAPER_USE_TRADE_RISK,
        "PAPER_EXECUTION_MODE": settings.PAPER_EXECUTION_MODE
    }
    if args.json:
         print(json.dumps(config, indent=2))
    else:
         for k, v in config.items():
              print(f"{k}: {v}")

def handle_paper_command(args: argparse.Namespace) -> None:
    if args.paper_command == "init":
        handle_paper_init(args)
    elif args.paper_command == "status":
        handle_paper_status(args)
    elif args.paper_command == "run-once":
        handle_paper_run_once(args)
    elif args.paper_command == "positions":
        handle_paper_positions(args)
    elif args.paper_command == "orders":
        handle_paper_orders(args)
    elif args.paper_command == "fills":
        handle_paper_fills(args)
    elif args.paper_command == "trades":
        handle_paper_trades(args)
    elif args.paper_command == "close":
        handle_paper_close(args)
    elif args.paper_command == "reset":
        handle_paper_reset(args)
    elif args.paper_command == "export":
        handle_paper_export(args)
    elif args.paper_command == "config":
        handle_paper_config(args)
