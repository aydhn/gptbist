import pandas as pd
import uuid
from datetime import datetime, UTC
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import PaperExecutionError
from bist_signal_bot.paper.models import (
    PaperAccount,
    PaperFill,
    PaperLedgerState,
    PaperLedgerEvent,
    PaperLedgerEventType,
    PaperOrder,
    PaperOrderSide,
    PaperOrderStatus,
    PaperPosition,
    PaperPositionSide,
    PaperTrade,
    PaperExecutionMode
)
from bist_signal_bot.costs.engine import TransactionCostEngine
from bist_signal_bot.costs.models import TransactionCostBreakdown

class PaperExecutionSimulator:
    def __init__(self, cost_engine: Optional[TransactionCostEngine] = None, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.cost_engine = cost_engine or TransactionCostEngine.from_settings(self.settings)

    def simulate_fill(
        self,
        order: PaperOrder,
        data: Optional[pd.DataFrame] = None,
        mode: PaperExecutionMode = PaperExecutionMode.LATEST_CLOSE_RESEARCH,
        manual_price: Optional[float] = None
    ) -> PaperFill:

        if order.status not in [PaperOrderStatus.ACCEPTED, PaperOrderStatus.CREATED]:
             raise PaperExecutionError(f"Cannot simulate fill for order in status {order.status}")

        fill_price = None
        metadata = {"simulation_mode": mode.value}

        if mode == PaperExecutionMode.MANUAL_PRICE:
            if manual_price is None:
                raise PaperExecutionError("manual_price is required for MANUAL_PRICE mode")
            fill_price = manual_price

        elif mode == PaperExecutionMode.LATEST_CLOSE_RESEARCH:
            if data is None or data.empty:
                raise PaperExecutionError("Dataframe is required for LATEST_CLOSE_RESEARCH")
            fill_price = float(data.iloc[-1]['close'])
            metadata["warning"] = "Research simulation only. Uses latest close price."

        elif mode == PaperExecutionMode.NEXT_OPEN_SIMULATED:
            # Need next bar, which we can't easily get without full knowledge of dataframe bounds.
            # Assuming we'll receive the appropriate single row or the dataframe has the "next" bar at the end.
             if data is None or data.empty:
                raise PaperExecutionError("Dataframe is required for NEXT_OPEN_SIMULATED")
             fill_price = float(data.iloc[-1]['open']) # Simplistic assumption for paper

        elif mode == PaperExecutionMode.NEXT_CLOSE_SIMULATED:
             if data is None or data.empty:
                raise PaperExecutionError("Dataframe is required for NEXT_CLOSE_SIMULATED")
             fill_price = float(data.iloc[-1]['close']) # Simplistic assumption for paper

        if fill_price is None or fill_price <= 0:
            raise PaperExecutionError(f"Invalid fill price determined: {fill_price}")

        # Calculate costs
        cost_breakdown = self.calculate_fill_cost(order, fill_price)

        fill = PaperFill(
            fill_id=str(uuid.uuid4()),
            order_id=order.order_id,
            account_id=order.account_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            requested_price=order.requested_price,
            fill_price=fill_price,
            effective_price=cost_breakdown.effective_price,
            gross_notional=order.quantity * fill_price,
            commission=cost_breakdown.commission.commission_amount,
            slippage=cost_breakdown.slippage.slippage_total_amount,
            spread=cost_breakdown.spread.spread_total_amount,
            tax=cost_breakdown.tax_amount,
            other_fees=cost_breakdown.other_fees,
            total_cost=cost_breakdown.total_cost,
            filled_at=datetime.now(UTC),
            execution_mode=mode,
            metadata=metadata
        )
        return fill

    def calculate_fill_cost(self, order: PaperOrder, price: float) -> TransactionCostBreakdown:
        from bist_signal_bot.costs.models import TradeCostInput, OrderSide, OrderType
        side = OrderSide.BUY if order.side.value == "BUY" else OrderSide.SELL
        input_data = TradeCostInput(
            symbol=order.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=order.quantity,
            price=price,
            notional=order.quantity * price
        )
        return self.cost_engine.calculate_trade_cost(input_data)

    def apply_fill_to_ledger(self, state: PaperLedgerState, fill: PaperFill) -> PaperLedgerState:
        # Pre-checks
        if fill.side == PaperOrderSide.BUY:
            total_cost = fill.gross_notional + fill.total_cost
            if state.account.cash < total_cost and self.settings.PAPER_REJECT_IF_INSUFFICIENT_CASH:
                 raise PaperExecutionError("Insufficient cash for BUY fill", context={"cash": state.account.cash, "required": total_cost})

        open_positions = {p.symbol: p for p in state.positions if p.is_open}
        position = open_positions.get(fill.symbol)

        if fill.side == PaperOrderSide.SELL:
             if not position:
                 raise PaperExecutionError(f"Cannot sell {fill.symbol}, no open position.")
             if fill.quantity > position.quantity:
                  raise PaperExecutionError(f"Cannot sell {fill.quantity} of {fill.symbol}, only {position.quantity} held.")

        # Process BUY
        if fill.side == PaperOrderSide.BUY:
             state.account.cash -= (fill.gross_notional + fill.total_cost)
             state.account.total_costs += fill.total_cost

             if not position:
                 pos_id = str(uuid.uuid4())
                 position = PaperPosition(
                     position_id=pos_id,
                     account_id=state.account.account_id,
                     symbol=fill.symbol,
                     side=PaperPositionSide.LONG,
                     quantity=fill.quantity,
                     avg_entry_price=fill.effective_price,
                     last_price=fill.effective_price,
                     market_value=fill.quantity * fill.effective_price
                 )
                 state.positions.append(position)

                 state.events.append(PaperLedgerEvent(
                     event_id=str(uuid.uuid4()),
                     account_id=state.account.account_id,
                     event_type=PaperLedgerEventType.POSITION_OPENED,
                     symbol=fill.symbol,
                     position_id=pos_id,
                     message=f"Opened LONG position for {fill.quantity} {fill.symbol}"
                 ))

                 # Create Trade record
                 trade = PaperTrade(
                     trade_id=str(uuid.uuid4()),
                     account_id=state.account.account_id,
                     symbol=fill.symbol,
                     side=PaperPositionSide.LONG,
                     entry_fill_id=fill.fill_id,
                     quantity=fill.quantity,
                     entry_price=fill.effective_price,
                     entry_time=fill.filled_at,
                     total_cost=fill.total_cost,
                     status="OPEN"
                 )
                 state.trades.append(trade)
             else:
                 # Add to existing position
                 new_qty = position.quantity + fill.quantity
                 # VWAP for entry
                 new_avg_price = ((position.quantity * position.avg_entry_price) + (fill.quantity * fill.effective_price)) / new_qty
                 position.quantity = new_qty
                 position.avg_entry_price = new_avg_price
                 position.last_price = fill.effective_price
                 position.market_value = new_qty * fill.effective_price
                 position.updated_at = datetime.now(UTC)

                 # Note: Adding to existing trade logic is simplified. Usually treated as a single average trade or FIFO queue.
                 # We update the active trade if there is one.
                 active_trades = [t for t in state.trades if t.symbol == fill.symbol and t.status == "OPEN"]
                 if active_trades:
                     active_trades[0].quantity += fill.quantity
                     active_trades[0].entry_price = new_avg_price
                     active_trades[0].total_cost += fill.total_cost

        # Process SELL
        elif fill.side == PaperOrderSide.SELL:
             state.account.cash += (fill.gross_notional - fill.total_cost)
             state.account.total_costs += fill.total_cost

             new_qty = position.quantity - fill.quantity

             # Calculate realized PnL
             # PnL = Proceeds - Cost Basis
             proceeds = fill.gross_notional - fill.total_cost
             cost_basis = fill.quantity * position.avg_entry_price
             realized_pnl = proceeds - cost_basis

             state.account.realized_pnl += realized_pnl

             active_trades = [t for t in state.trades if t.symbol == fill.symbol and t.status == "OPEN"]
             active_trade = active_trades[0] if active_trades else None

             if new_qty <= 0.000001: # Float precision close
                 position.quantity = 0.0
                 position.is_open = False
                 position.closed_at = datetime.now(UTC)
                 position.realized_pnl += realized_pnl
                 position.market_value = 0.0

                 state.events.append(PaperLedgerEvent(
                     event_id=str(uuid.uuid4()),
                     account_id=state.account.account_id,
                     event_type=PaperLedgerEventType.POSITION_CLOSED,
                     symbol=fill.symbol,
                     position_id=position.position_id,
                     message=f"Closed LONG position for {fill.symbol}"
                 ))

                 if active_trade:
                      active_trade.exit_fill_id = fill.fill_id
                      active_trade.exit_price = fill.effective_price
                      active_trade.exit_time = fill.filled_at
                      active_trade.gross_pnl = fill.gross_notional - (fill.quantity * active_trade.entry_price)
                      active_trade.net_pnl = active_trade.gross_pnl - fill.total_cost - active_trade.total_cost
                      active_trade.status = "CLOSED"
                      if active_trade.entry_price > 0:
                          active_trade.return_pct = active_trade.net_pnl / (fill.quantity * active_trade.entry_price)

             else:
                 position.quantity = new_qty
                 position.realized_pnl += realized_pnl
                 position.last_price = fill.effective_price
                 position.market_value = new_qty * fill.effective_price
                 position.updated_at = datetime.now(UTC)
                 # Partial close on trade not fully modeled for simplicity here

        state.fills.append(fill)

        # Update order status
        for order in state.orders:
             if order.order_id == fill.order_id:
                 order.status = PaperOrderStatus.FILLED
                 order.updated_at = datetime.now(UTC)
                 break

        state.events.append(PaperLedgerEvent(
             event_id=str(uuid.uuid4()),
             account_id=state.account.account_id,
             event_type=PaperLedgerEventType.ORDER_FILLED,
             symbol=fill.symbol,
             order_id=fill.order_id,
             fill_id=fill.fill_id,
             message=f"Filled {fill.side.value} order for {fill.quantity} {fill.symbol} @ {fill.fill_price}"
        ))

        # Re-eval equity
        unrealized = sum(p.quantity * (p.last_price - p.avg_entry_price) for p in state.positions if p.is_open)
        market_val = sum(p.quantity * p.last_price for p in state.positions if p.is_open)
        state.account.unrealized_pnl = unrealized
        state.account.equity = state.account.cash + market_val

        return state

    def mark_to_market(self, state: PaperLedgerState, latest_prices: dict[str, float]) -> PaperLedgerState:
        for position in state.positions:
             if position.is_open and position.symbol in latest_prices:
                  new_price = latest_prices[position.symbol]
                  position.last_price = new_price
                  position.market_value = position.quantity * new_price
                  position.unrealized_pnl = position.market_value - (position.quantity * position.avg_entry_price)
                  position.updated_at = datetime.now(UTC)

        unrealized = sum(p.unrealized_pnl for p in state.positions if p.is_open)
        market_val = sum(p.market_value for p in state.positions if p.is_open)
        state.account.unrealized_pnl = unrealized
        state.account.equity = state.account.cash + market_val
        state.account.updated_at = datetime.now(UTC)

        state.events.append(PaperLedgerEvent(
             event_id=str(uuid.uuid4()),
             account_id=state.account.account_id,
             event_type=PaperLedgerEventType.MARK_TO_MARKET,
             message="Mark-to-market executed"
        ))

        return state
