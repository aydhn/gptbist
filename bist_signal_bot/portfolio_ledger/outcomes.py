from datetime import datetime, timezone
import uuid
from typing import Any

from bist_signal_bot.portfolio_ledger.models import (
    ResearchPortfolio,
    PortfolioOutcomeResult,
    PortfolioOutcomeLabel,
    ResearchPortfolioPosition,
    PortfolioNavPoint
)

class PortfolioOutcomeEvaluator:
    def __init__(self, data_service: Any = None):
        self.data_service = data_service

    def evaluate_outcome(
        self,
        portfolio: ResearchPortfolio,
        horizon_days: int = 5,
        benchmark_symbol: str | None = None,
        nav_points: list[PortfolioNavPoint] | None = None
    ) -> PortfolioOutcomeResult:
        now = datetime.now(timezone.utc)

        # In a real setup, we'd calculate exact gross and net return over `horizon_days`
        # Here we just take the current snapshot values for demonstration
        gross_return_pct = None
        net_return_pct = None

        if portfolio.current_simulated_nav is not None and portfolio.initial_notional > 0:
            gross_return_pct = ((portfolio.current_simulated_nav / portfolio.initial_notional) - 1.0) * 100.0
            # Assume a simplified net
            net_return_pct = gross_return_pct - 0.2  # arbitrary 20 bps cost drag mock if not fully tracked

        label = self.label_outcome(gross_return_pct, net_return_pct)

        bench_rtn = None
        excess = None
        warnings = []
        if benchmark_symbol:
            bench_rtn = self.calculate_benchmark_return(benchmark_symbol, portfolio.created_at, now)
            if bench_rtn is not None and net_return_pct is not None:
                excess = net_return_pct - bench_rtn
        else:
            warnings.append("No benchmark provided; excess return not calculated.")

        max_dd = self.calculate_max_drawdown(nav_points or [])
        hit_rate = self.position_hit_rate(portfolio.positions)

        result = PortfolioOutcomeResult(
            outcome_id=f"out_{uuid.uuid4().hex[:8]}",
            portfolio_id=portfolio.portfolio_id,
            generated_at=now,
            horizon_days=horizon_days,
            label=label,
            gross_return_pct=gross_return_pct,
            net_return_pct=net_return_pct,
            benchmark_return_pct=bench_rtn,
            excess_return_pct=excess,
            max_drawdown_pct=max_dd,
            hit_rate_positions_pct=hit_rate,
            warnings=warnings
        )
        return result

    def label_outcome(self, gross_return_pct: float | None, net_return_pct: float | None) -> PortfolioOutcomeLabel:
        if net_return_pct is None:
            return PortfolioOutcomeLabel.INSUFFICIENT_DATA

        if net_return_pct > 2.0:
            return PortfolioOutcomeLabel.POSITIVE
        elif net_return_pct < -2.0:
            return PortfolioOutcomeLabel.NEGATIVE
        elif -0.5 <= net_return_pct <= 0.5:
            return PortfolioOutcomeLabel.NEUTRAL
        else:
            return PortfolioOutcomeLabel.MIXED

    def calculate_benchmark_return(self, benchmark_symbol: str | None, start: datetime, end: datetime) -> float | None:
        if not self.data_service or not benchmark_symbol:
            return None
        # Mock calculation
        return 1.5

    def calculate_max_drawdown(self, nav_points: list[PortfolioNavPoint]) -> float | None:
        if not nav_points:
            return None

        max_nav = 0.0
        max_dd = 0.0
        for p in nav_points:
            if p.simulated_nav > max_nav:
                max_nav = p.simulated_nav
            else:
                dd = (max_nav - p.simulated_nav) / max_nav * 100.0
                if dd > max_dd:
                    max_dd = dd
        return max_dd

    def position_hit_rate(self, positions: list[ResearchPortfolioPosition]) -> float | None:
        if not positions:
            return None

        hits = sum(1 for p in positions if p.gross_return_pct is not None and p.gross_return_pct > 0)
        total = len(positions)
        return (hits / total * 100.0) if total > 0 else 0.0
