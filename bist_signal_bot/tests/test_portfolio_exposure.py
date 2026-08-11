from unittest.mock import MagicMock
import pytest
from bist_signal_bot.portfolio.exposure import ExposureAnalyzer
from bist_signal_bot.portfolio.models import PortfolioState, PortfolioHolding, PortfolioPositionSide, AllocationResult, AllocationResultItem
from bist_signal_bot.config.settings import Settings

def test_exposure_analyzer_calculate():
    h1 = PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1, sector="Tech")
    h2 = PortfolioHolding(symbol="B", side=PortfolioPositionSide.SHORT, quantity=5, avg_price=20.0, market_value=100.0, weight_pct=0.1, sector="Bank")
    state = PortfolioState(equity=1000.0, cash=800.0, holdings=[h1, h2])

    analyzer = ExposureAnalyzer()
    report = analyzer.calculate_exposure(state)

    assert report.gross_exposure_pct == 0.20
    assert report.net_exposure_pct == 0.0
    assert report.max_symbol_weight_pct == 0.10
    assert report.cash_pct == 0.80

def test_exposure_analyzer_limits():
    settings = MagicMock()
    settings.PORTFOLIO_MAX_GROSS_EXPOSURE_PCT = 0.15
    settings.PORTFOLIO_MAX_NET_EXPOSURE_PCT = 1.0
    settings.PORTFOLIO_MAX_SYMBOL_WEIGHT_PCT = 0.20
    settings.PORTFOLIO_MAX_SECTOR_WEIGHT_PCT = 0.40
    settings.PORTFOLIO_MIN_CASH_PCT = 0.05
    settings.PORTFOLIO_MAX_OPEN_POSITIONS = 5 # overriding after init
    h1 = PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1)
    h2 = PortfolioHolding(symbol="B", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1)
    state = PortfolioState(equity=1000.0, cash=800.0, holdings=[h1, h2])

    analyzer = ExposureAnalyzer()
    report = analyzer.calculate_exposure(state)

    ok, reasons, issues = analyzer.check_exposure_limits(report, settings)
    assert not ok
    assert len(reasons) > 0


def test_simulate_post_allocation_exposure():
    from datetime import datetime
    h1 = PortfolioHolding(symbol="EXISTING", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1, sector="Tech")
    state = PortfolioState(equity=1000.0, cash=900.0, holdings=[h1])

    alloc_item_new = AllocationResultItem(
        symbol="NEW",
        approved=True,
        original_notional=100.0,
        allocated_notional=100.0,
        allocated_weight_pct=0.1,
        quantity=5.0,
        reduction_pct=0.0,
        reasons=[],
        metadata={}
    )
    alloc_item_existing = AllocationResultItem(
        symbol="EXISTING",
        approved=True,
        original_notional=50.0,
        allocated_notional=50.0,
        allocated_weight_pct=0.05,
        quantity=5.0,
        reduction_pct=0.0,
        reasons=[],
        metadata={}
    )
    alloc_item_skip = AllocationResultItem(
        symbol="SKIP",
        approved=False,
        original_notional=100.0,
        allocated_notional=100.0,
        allocated_weight_pct=0.1,
        quantity=5.0,
        reduction_pct=0.0,
        reasons=[],
        metadata={}
    )
    alloc_item_zero = AllocationResultItem(
        symbol="ZERO",
        approved=True,
        original_notional=0.0,
        allocated_notional=0.0,
        allocated_weight_pct=0.0,
        quantity=0.0,
        reduction_pct=0.0,
        reasons=[],
        metadata={}
    )

    allocation = AllocationResult(
        method="EQUAL_WEIGHT",
        items=[alloc_item_new, alloc_item_existing, alloc_item_skip, alloc_item_zero],
        total_allocated_notional=150.0,
        total_allocated_pct=0.15,
        rejected_symbols=["SKIP"],
        reduced_symbols=[],
        issues=[],
        generated_at=datetime.utcnow()
    )

    analyzer = ExposureAnalyzer()
    report = analyzer.simulate_post_allocation_exposure(state, allocation)

    assert report.open_position_count == 2
    assert report.gross_exposure_pct == 250.0 / 1000.0
    assert report.cash_pct == (900.0 - 150.0) / 1000.0
