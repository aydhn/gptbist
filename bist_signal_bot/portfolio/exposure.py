from typing import Any
from bist_signal_bot.portfolio.models import (
    PortfolioState, ExposureReport, AllocationResult,
    PortfolioPositionSide, PortfolioRejectReason
)
from bist_signal_bot.config.settings import Settings

class ExposureAnalyzer:
    def calculate_exposure(self, state: PortfolioState) -> ExposureReport:
        equity = state.equity
        if equity <= 0:
            return ExposureReport(
                gross_exposure_pct=0.0,
                net_exposure_pct=0.0,
                long_exposure_pct=0.0,
                short_exposure_pct=0.0,
                max_symbol_weight_pct=0.0,
                sector_weights={},
                open_position_count=0,
                cash_pct=1.0,
                issues=["Portfolio equity is zero or negative"],
                metadata={}
            )

        gross = 0.0
        net = 0.0
        long_exp = 0.0
        short_exp = 0.0
        max_sym_wt = 0.0

        for h in state.holdings:
            wt = h.market_value / equity
            gross += wt
            if h.side == PortfolioPositionSide.LONG:
                net += wt
                long_exp += wt
            elif h.side == PortfolioPositionSide.SHORT:
                net -= wt
                short_exp += wt
            if wt > max_sym_wt:
                max_sym_wt = wt

        cash_pct = state.cash / equity
        sectors = state.sector_weights()

        return ExposureReport(
            gross_exposure_pct=gross,
            net_exposure_pct=net,
            long_exposure_pct=long_exp,
            short_exposure_pct=short_exp,
            max_symbol_weight_pct=max_sym_wt,
            sector_weights=sectors,
            open_position_count=len(state.holdings),
            cash_pct=cash_pct,
            issues=[],
            metadata={}
        )

    def simulate_post_allocation_exposure(self, state: PortfolioState, allocation: AllocationResult) -> ExposureReport:
        from bist_signal_bot.portfolio.models import PortfolioHolding
        from datetime import datetime

        sim_holdings = list(state.holdings)
        sim_cash = state.cash
        sim_equity = state.equity

        for item in allocation.items:
            if not item.approved or item.allocated_notional <= 0:
                continue

            existing = next((h for h in sim_holdings if h.symbol == item.symbol), None)

            sim_cash -= item.allocated_notional

            if existing:
                new_qty = existing.quantity + item.quantity
                new_mv = existing.market_value + item.allocated_notional
                new_avg = new_mv / new_qty if new_qty > 0 else existing.avg_price
                sim_holdings.remove(existing)
                sim_holdings.append(PortfolioHolding(
                    symbol=existing.symbol,
                    side=existing.side,
                    quantity=new_qty,
                    avg_price=new_avg,
                    last_price=existing.last_price,
                    market_value=new_mv,
                    weight_pct=0.0,
                    sector=existing.sector,
                    opened_at=existing.opened_at,
                    metadata=existing.metadata
                ))
            else:
                sim_holdings.append(PortfolioHolding(
                    symbol=item.symbol,
                    side=PortfolioPositionSide.LONG, # Defaulting to long for simple mock
                    quantity=item.quantity,
                    avg_price=item.allocated_notional / item.quantity if item.quantity > 0 else 1.0,
                    last_price=item.allocated_notional / item.quantity if item.quantity > 0 else 1.0,
                    market_value=item.allocated_notional,
                    weight_pct=0.0,
                    sector="UNKNOWN",
                    opened_at=datetime.utcnow()
                ))

        for h in sim_holdings:
            h.weight_pct = h.market_value / sim_equity if sim_equity > 0 else 0.0

        sim_state = PortfolioState(
            equity=sim_equity,
            cash=sim_cash,
            holdings=sim_holdings,
            timestamp=datetime.utcnow(),
            daily_signal_count=state.daily_signal_count
        )

        return self.calculate_exposure(sim_state)

    def check_exposure_limits(self, report: ExposureReport, settings: Settings) -> tuple[bool, list[PortfolioRejectReason], list[str]]:
        reasons = []
        issues = []

        max_gross = getattr(settings, "PORTFOLIO_MAX_GROSS_EXPOSURE_PCT", 1.0)
        max_net = getattr(settings, "PORTFOLIO_MAX_NET_EXPOSURE_PCT", 1.0)
        max_sym = getattr(settings, "PORTFOLIO_MAX_SYMBOL_WEIGHT_PCT", 0.20)
        max_sec = getattr(settings, "PORTFOLIO_MAX_SECTOR_WEIGHT_PCT", 0.40)
        min_cash = getattr(settings, "PORTFOLIO_MIN_CASH_PCT", 0.05)
        max_pos = getattr(settings, "PORTFOLIO_MAX_OPEN_POSITIONS", 5)

        if report.gross_exposure_pct > max_gross:
            reasons.append(PortfolioRejectReason.MAX_GROSS_EXPOSURE_EXCEEDED)
            issues.append(f"Gross exposure {report.gross_exposure_pct:.2%} exceeds {max_gross:.2%}")

        if abs(report.net_exposure_pct) > max_net:
            reasons.append(PortfolioRejectReason.MAX_NET_EXPOSURE_EXCEEDED)
            issues.append(f"Net exposure {abs(report.net_exposure_pct):.2%} exceeds {max_net:.2%}")

        if report.max_symbol_weight_pct > max_sym:
            reasons.append(PortfolioRejectReason.MAX_SYMBOL_WEIGHT_EXCEEDED)
            issues.append(f"Symbol weight {report.max_symbol_weight_pct:.2%} exceeds {max_sym:.2%}")

        if any(w > max_sec for w in report.sector_weights.values()):
            reasons.append(PortfolioRejectReason.MAX_SECTOR_WEIGHT_EXCEEDED)
            issues.append(f"A sector weight exceeds {max_sec:.2%}")

        if report.cash_pct < min_cash:
            reasons.append(PortfolioRejectReason.INSUFFICIENT_CASH)
            issues.append(f"Cash pct {report.cash_pct:.2%} below {min_cash:.2%}")

        if report.open_position_count > max_pos:
            reasons.append(PortfolioRejectReason.MAX_POSITIONS_EXCEEDED)
            issues.append(f"Open positions {report.open_position_count} exceeds {max_pos}")

        return (len(reasons) == 0, reasons, issues)

    def sector_exposure_from_holdings(self, holdings: list[Any]) -> dict[str, float]:
        if not holdings:
            return {}

        sectors = {}
        total_mv = sum(h.market_value for h in holdings)
        if total_mv <= 0:
            return {}

        for h in holdings:
            s = h.sector or "UNKNOWN"
            sectors[s] = sectors.get(s, 0.0) + (h.market_value / total_mv)

        return sectors
