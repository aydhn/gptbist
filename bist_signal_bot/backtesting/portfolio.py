from datetime import datetime
from typing import Any

from bist_signal_bot.backtesting.models import (

    BacktestFill,
    BacktestTrade,
    PortfolioSnapshot,
)
from bist_signal_bot.costs.models import OrderSide
from bist_signal_bot.signals.models import SignalDirection
from bist_signal_bot.core.exceptions import PortfolioAccountingError

class BacktestPosition:
    def __init__(self, symbol: str, side: SignalDirection, quantity: float, avg_price: float, entry_time: datetime, metadata: dict[str, Any] | None = None):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.avg_price = avg_price
        self.entry_time = entry_time
        self.last_price = avg_price
        self.realized_pnl = 0.0
        self.metadata = metadata or {}

    def market_value(self, current_price: float) -> float:
        self.last_price = current_price
        return self.quantity * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        self.last_price = current_price
        if self.side == SignalDirection.LONG:
            return (current_price - self.avg_price) * self.quantity
        elif self.side == SignalDirection.SHORT:
            return (self.avg_price - current_price) * self.quantity
        return 0.0

class BacktestPortfolio:
    def __init__(self, initial_capital: float, allow_short: bool = False, use_fractional_shares: bool = False):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.allow_short = allow_short
        self.use_fractional_shares = use_fractional_shares

        self.positions: dict[str, BacktestPosition] = {}
        self.trades: list[BacktestTrade] = []
        self.fills: list[BacktestFill] = []
        self.snapshots: list[PortfolioSnapshot] = []

    def can_open_position(self, symbol: str, notional: float) -> bool:
        return notional <= self.cash

    def open_long(self, symbol: str, quantity: float, fill: BacktestFill, reason: str) -> BacktestTrade:
        if fill.side != OrderSide.BUY:
            raise PortfolioAccountingError("open_long requires a BUY fill")
        if not self.use_fractional_shares and not quantity.is_integer():
             raise PortfolioAccountingError("Fractional shares not allowed")

        total_cost_from_cash = fill.gross_notional + fill.total_cost
        if total_cost_from_cash > self.cash:
            raise PortfolioAccountingError(f"Insufficient cash for open_long. Required: {total_cost_from_cash}, Available: {self.cash}")

        self.cash -= total_cost_from_cash
        self.fills.append(fill)

        if symbol in self.positions:
            raise PortfolioAccountingError(f"Position already exists for {symbol}")

        pos = BacktestPosition(symbol=symbol, side=SignalDirection.LONG, quantity=quantity, avg_price=fill.price, entry_time=fill.filled_at, metadata={"fill_id": fill.order_id})
        self.positions[symbol] = pos

        trade = BacktestTrade(symbol=symbol, entry_time=fill.filled_at, side=SignalDirection.LONG, quantity=quantity, entry_price=fill.price, entry_cost=fill.total_cost, entry_reason=reason)
        self.trades.append(trade)
        return trade

    def close_position(self, symbol: str, fill: BacktestFill, reason: str) -> BacktestTrade | None:
        if symbol not in self.positions:
            raise PortfolioAccountingError(f"Cannot close non-existent position for {symbol}")

        pos = self.positions[symbol]
        if pos.side == SignalDirection.LONG and fill.side != OrderSide.SELL:
             raise PortfolioAccountingError("Closing a LONG position requires a SELL fill")

        self.fills.append(fill)

        if pos.side == SignalDirection.LONG:
             net_proceeds = fill.gross_notional - fill.total_cost
             self.cash += net_proceeds
             gross_pnl = (fill.price - pos.avg_price) * pos.quantity
             net_pnl = gross_pnl - fill.total_cost - self._get_entry_cost(symbol, pos.entry_time)

        del self.positions[symbol]

        open_trade = self._find_open_trade(symbol, pos.entry_time)
        if open_trade:
            open_trade.exit_time = fill.filled_at
            open_trade.exit_price = fill.price
            open_trade.exit_cost = fill.total_cost
            open_trade.exit_reason = reason
            open_trade.gross_pnl = gross_pnl
            open_trade.net_pnl = net_pnl
            open_trade.return_pct = (net_pnl / (pos.quantity * pos.avg_price)) * 100.0 if pos.quantity * pos.avg_price > 0 else 0.0
            return open_trade
        return None

    def mark_to_market(self, timestamp: datetime, prices: dict[str, float]) -> PortfolioSnapshot:
        position_value = self.position_value(prices)
        equity = self.cash + position_value
        snap = PortfolioSnapshot(timestamp=timestamp, cash=self.cash, position_value=position_value, equity=equity, gross_exposure=position_value, net_exposure=position_value, open_positions=len(self.positions))
        self.snapshots.append(snap)
        return snap

    def current_equity(self, prices: dict[str, float]) -> float:
        return self.cash + self.position_value(prices)

    def position_value(self, prices: dict[str, float]) -> float:
        return sum(pos.market_value(prices.get(symbol, pos.last_price)) for symbol, pos in self.positions.items())

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions

    def get_position(self, symbol: str) -> BacktestPosition | None:
        return self.positions.get(symbol)

    def _find_open_trade(self, symbol: str, entry_time: datetime) -> BacktestTrade | None:
        for t in reversed(self.trades):
            if t.symbol == symbol and t.entry_time == entry_time and not t.is_closed():
                return t
        return None

    def _get_entry_cost(self, symbol: str, entry_time: datetime) -> float:
        trade = self._find_open_trade(symbol, entry_time)
        return trade.entry_cost if trade else 0.0
