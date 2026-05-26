from datetime import datetime, timezone
import uuid
from typing import Any

from bist_signal_bot.portfolio_ledger.models import (
    ResearchPortfolio,
    ResearchPortfolioPosition,
    PortfolioValuationSnapshot,
    PortfolioValuationStatus
)
from bist_signal_bot.core.exceptions import PortfolioValuationError

class PortfolioValuationEngine:
    def __init__(self, data_service: Any = None):
        self.data_service = data_service

    def value_portfolio(self, portfolio: ResearchPortfolio, price_data: dict[str, Any] | None = None) -> PortfolioValuationSnapshot:
        now = datetime.now(timezone.utc)

        symbols = [p.symbol for p in portfolio.positions]
        if price_data is None:
            price_data = self.load_latest_prices(symbols)

        valued_positions = []
        missing_prices = []
        total_cost_drag_pct = 0.0
        total_turnover_pct = 0.0 # Will be populated by rebalance tracking mainly, keep zero here unless estimating daily turnover

        for pos in portfolio.positions:
            latest_price = price_data.get(pos.symbol)
            if latest_price is None:
                missing_prices.append(pos.symbol)

            valued_pos = self.value_position(pos, latest_price)
            valued_positions.append(valued_pos)

            if valued_pos.estimated_cost_bps is not None:
                total_cost_drag_pct += (valued_pos.estimated_cost_bps / 10000.0) * valued_pos.current_weight

        simulated_nav = self.calculate_simulated_nav(portfolio, valued_positions)

        # Calculate overall gross/net return since inception
        gross_return_pct = None
        net_return_pct = None

        if portfolio.initial_notional > 0:
            gross_nav = simulated_nav  # For simulation purposes we treat NAV as gross NAV before cost drag compounding
            net_nav = simulated_nav * (1.0 - total_cost_drag_pct) # very simplified cost drag application

            gross_return_pct = ((gross_nav / portfolio.initial_notional) - 1.0) * 100.0
            net_return_pct = ((net_nav / portfolio.initial_notional) - 1.0) * 100.0

        status = PortfolioValuationStatus.PASS
        if missing_prices:
            status = PortfolioValuationStatus.INSUFFICIENT_DATA

        warnings = []
        if missing_prices:
            warnings.append(f"Missing prices for symbols: {', '.join(missing_prices)}")

        snapshot = PortfolioValuationSnapshot(
            valuation_id=f"val_{uuid.uuid4().hex[:8]}",
            portfolio_id=portfolio.portfolio_id,
            generated_at=now,
            status=status,
            simulated_nav=simulated_nav,
            gross_return_pct=gross_return_pct,
            net_return_pct=net_return_pct,
            total_cost_drag_pct=total_cost_drag_pct * 100.0,
            total_turnover_pct=total_turnover_pct,
            positions=valued_positions,
            missing_prices=missing_prices,
            warnings=warnings
        )
        return snapshot

    def value_position(self, position: ResearchPortfolioPosition, latest_price: float | None) -> ResearchPortfolioPosition:
        returns = self.calculate_position_returns(position, latest_price)

        # Copy to avoid mutating original
        new_pos = position.model_copy()
        new_pos.latest_price = latest_price
        new_pos.gross_return_pct = returns.get('gross_return_pct')
        new_pos.net_return_pct = returns.get('net_return_pct')

        if new_pos.gross_return_pct is not None:
            new_pos.contribution_to_return_pct = new_pos.gross_return_pct * new_pos.current_weight

        return new_pos

    def load_latest_prices(self, symbols: list[str]) -> dict[str, float]:
        if not self.data_service:
            # Fallback if no data service is provided
            return {sym: 100.0 for sym in symbols}

        # In a real implementation this would fetch from data_service
        # For now return mock prices if calling without proper setup in tests
        return {sym: 100.0 for sym in symbols}

    def calculate_simulated_nav(self, portfolio: ResearchPortfolio, positions: list[ResearchPortfolioPosition]) -> float:
        # Simple weighted NAV calculation:
        # Simulated NAV = Initial Notional * (1 + sum(weight * return))
        total_contribution = 0.0
        for pos in positions:
            if pos.contribution_to_return_pct is not None:
                total_contribution += pos.contribution_to_return_pct / 100.0

        return portfolio.initial_notional * (1.0 + total_contribution)

    def calculate_position_returns(self, position: ResearchPortfolioPosition, latest_price: float | None) -> dict[str, float | None]:
        if latest_price is None or position.entry_research_price is None or position.entry_research_price <= 0:
            return {"gross_return_pct": None, "net_return_pct": None}

        gross_rtn = (latest_price / position.entry_research_price) - 1.0

        cost_bps = position.estimated_cost_bps or 0.0
        slip_bps = position.estimated_slippage_bps or 0.0

        total_drag = (cost_bps + slip_bps) / 10000.0

        net_rtn = gross_rtn - total_drag

        return {
            "gross_return_pct": gross_rtn * 100.0,
            "net_return_pct": net_rtn * 100.0
        }
