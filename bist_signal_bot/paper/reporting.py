import pandas as pd
from typing import Any

from bist_signal_bot.paper.models import (
    PaperLedgerState,
    PaperRunResult,
    PaperPosition,
    PaperOrder,
    PaperFill
)


def paper_state_to_dict(state: PaperLedgerState) -> dict[str, Any]:
    return state.model_dump()

def paper_run_result_to_dict(result: PaperRunResult) -> dict[str, Any]:
    return result.model_dump()

def paper_positions_to_dataframe(positions: list[PaperPosition]) -> pd.DataFrame:
    if not positions:
        return pd.DataFrame()
    return pd.DataFrame([p.model_dump() for p in positions])

def paper_orders_to_dataframe(orders: list[PaperOrder]) -> pd.DataFrame:
    if not orders:
        return pd.DataFrame()
    return pd.DataFrame([o.model_dump() for o in orders])

def paper_fills_to_dataframe(fills: list[PaperFill]) -> pd.DataFrame:
    if not fills:
        return pd.DataFrame()
    return pd.DataFrame([f.model_dump() for f in fills])

def format_paper_status_text(state: PaperLedgerState) -> str:
    lines = [
        "BIST Bot Paper Account Status",
        "=============================",
        f"Account ID : {state.account.account_id}",
        f"Status     : {state.account.status.value}",
        f"Cash       : {state.account.cash:,.2f} TRY",
        f"Equity     : {state.account.equity:,.2f} TRY",
        f"Real. PnL  : {state.account.realized_pnl:,.2f} TRY",
        f"Unreal. PnL: {state.account.unrealized_pnl:,.2f} TRY",
        f"Total Cost : {state.account.total_costs:,.2f} TRY",
        f"Updated    : {state.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Open Positions: {len(state.open_positions())}",
        f"Total Orders  : {len(state.orders)}",
        f"Total Fills   : {len(state.fills)}",
        f"Total Trades  : {len(state.trades)}",
        "",
        "Disclaimer: Paper trading simulation only. Not investment advice. No real order was sent."
    ]
    return "\n".join(lines)

def format_paper_run_text(result: PaperRunResult) -> str:
    lines = [
        "BIST Bot Paper Trading Run Result",
        "=================================",
        f"Status         : {result.status}",
        f"Account ID     : {result.account.account_id}",
        f"Signals Found  : {len(result.signals)}",
        f"Risk Dec.      : {len(result.risk_decisions)}",
        f"Orders Created : {len(result.orders)}",
        f"Fills Simulated: {len(result.fills)}",
        f"Elapsed        : {result.elapsed_seconds:.2f}s",
        "",
        f"Final Cash     : {result.account.cash:,.2f} TRY",
        f"Final Equity   : {result.account.equity:,.2f} TRY"
    ]

    if result.issues:
        lines.append("")
        lines.append("Issues:")
        for issue in result.issues:
            lines.append(f"- {issue}")

    lines.extend([
        "",
        "Disclaimer: Paper trading simulation only. Not investment advice. No real order was sent."
    ])
    return "\n".join(lines)
