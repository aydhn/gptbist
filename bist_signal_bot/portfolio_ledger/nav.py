from datetime import datetime, timezone
import uuid
from typing import Any

from bist_signal_bot.portfolio_ledger.models import (
    ResearchPortfolio,
    PortfolioValuationSnapshot,
    PortfolioNavPoint
)
from bist_signal_bot.core.exceptions import PortfolioNavError

class PortfolioNavBuilder:
    def __init__(self, store: Any = None):
        self.store = store

    def build_nav_curve(self, portfolio: ResearchPortfolio, price_history: dict[str, Any] | None = None) -> list[PortfolioNavPoint]:
        # Simple simulated NAV curve generation if full history is passed
        points = []
        if price_history:
            # We would iterate over dates in price history and construct simulated nav.
            # Assuming just a mock here.
            now = datetime.now(timezone.utc)
            points.append(
                PortfolioNavPoint(
                    nav_id=f"nav_{uuid.uuid4().hex[:8]}",
                    portfolio_id=portfolio.portfolio_id,
                    timestamp=now,
                    simulated_nav=portfolio.initial_notional,
                    gross_return_pct=0.0,
                    net_return_pct=0.0,
                    drawdown_pct=0.0
                )
            )
        return points

    def append_nav_point(self, snapshot: PortfolioValuationSnapshot) -> PortfolioNavPoint:
        nav_point = PortfolioNavPoint(
            nav_id=f"nav_{uuid.uuid4().hex[:8]}",
            portfolio_id=snapshot.portfolio_id,
            timestamp=snapshot.generated_at,
            simulated_nav=snapshot.simulated_nav,
            gross_return_pct=snapshot.gross_return_pct,
            net_return_pct=snapshot.net_return_pct,
            cost_drag_pct=snapshot.total_cost_drag_pct
        )
        if self.store:
            self.store.append_nav_points([nav_point])
        return nav_point

    def drawdown_series(self, nav_points: list[PortfolioNavPoint]) -> list[PortfolioNavPoint]:
        if not nav_points:
            return []

        points_sorted = sorted(nav_points, key=lambda x: x.timestamp)
        max_nav = 0.0

        for p in points_sorted:
            if p.simulated_nav > max_nav:
                max_nav = p.simulated_nav

            if max_nav > 0:
                p.drawdown_pct = ((max_nav - p.simulated_nav) / max_nav) * 100.0
            else:
                p.drawdown_pct = 0.0

        return points_sorted

    def latest_nav(self, portfolio_id: str) -> PortfolioNavPoint | None:
        if not self.store:
            return None
        points = self.store.load_nav_points(portfolio_id, limit=1)
        return points[0] if points else None

    def nav_summary(self, nav_points: list[PortfolioNavPoint]) -> dict[str, Any]:
        if not nav_points:
            return {}

        start_nav = nav_points[0].simulated_nav
        end_nav = nav_points[-1].simulated_nav
        max_dd = max((p.drawdown_pct or 0.0) for p in nav_points)

        return {
            "start_nav": start_nav,
            "end_nav": end_nav,
            "max_drawdown_pct": max_dd,
            "data_points": len(nav_points)
        }
