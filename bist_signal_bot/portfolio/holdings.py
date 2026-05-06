from typing import Any, Optional
from datetime import datetime
from bist_signal_bot.portfolio.models import PortfolioState, PortfolioHolding, PortfolioPositionSide

def build_portfolio_state(
    equity: float,
    cash: float,
    holdings: Optional[list[PortfolioHolding]] = None,
    daily_signal_count: int = 0
) -> PortfolioState:
    """Builds a PortfolioState object."""
    return PortfolioState(
        equity=equity,
        cash=cash,
        holdings=holdings or [],
        daily_signal_count=daily_signal_count,
        timestamp=datetime.utcnow()
    )

def holding_from_dict(data: dict[str, Any]) -> PortfolioHolding:
    """Creates a PortfolioHolding from a dictionary."""
    return PortfolioHolding(**data)

def update_holding_prices(state: PortfolioState, latest_prices: dict[str, float]) -> PortfolioState:
    """Updates the market value and last price of holdings in the PortfolioState."""
    updated_holdings = []
    total_market_value = 0.0

    for h in state.holdings:
        if h.symbol in latest_prices:
            last_price = latest_prices[h.symbol]
            market_value = last_price * h.quantity

            pnl = None
            if h.side == PortfolioPositionSide.LONG:
                pnl = (last_price - h.avg_price) * h.quantity
            elif h.side == PortfolioPositionSide.SHORT:
                pnl = (h.avg_price - last_price) * h.quantity

            updated_h = h.model_copy(update={
                "last_price": last_price,
                "market_value": market_value,
                "unrealized_pnl": pnl
            })
            updated_holdings.append(updated_h)
            total_market_value += market_value
        else:
            updated_holdings.append(h)
            total_market_value += h.market_value

    new_equity = state.cash + total_market_value

    for h in updated_holdings:
        if new_equity > 0:
            h.weight_pct = h.market_value / new_equity

    return state.model_copy(update={
        "holdings": updated_holdings,
        "equity": new_equity,
        "timestamp": datetime.utcnow()
    })

def portfolio_state_from_backtest_snapshot(snapshot: Any, positions: list[Any], daily_signals: int = 0) -> PortfolioState:
    """Creates a PortfolioState from backtest snapshot and positions."""
    holdings = []
    for pos in positions:
        from bist_signal_bot.backtesting.models import PositionState
        side = PortfolioPositionSide.LONG if pos.state == PositionState.LONG else (PortfolioPositionSide.SHORT if pos.state == PositionState.SHORT else PortfolioPositionSide.FLAT)
        if side == PortfolioPositionSide.FLAT:
            continue

        weight = pos.market_value / snapshot.equity if snapshot.equity > 0 else 0.0

        holdings.append(PortfolioHolding(
            symbol=pos.symbol,
            side=side,
            quantity=pos.quantity,
            avg_price=pos.avg_price,
            last_price=pos.last_price,
            market_value=pos.market_value,
            weight_pct=weight,
            unrealized_pnl=pos.unrealized_pnl,
            opened_at=pos.opened_at,
            metadata={"backtest_position": True}
        ))

    return PortfolioState(
        equity=snapshot.equity,
        cash=snapshot.cash,
        holdings=holdings,
        timestamp=snapshot.timestamp,
        daily_signal_count=daily_signals
    )
