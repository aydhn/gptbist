from unittest.mock import MagicMock
from bist_signal_bot.portfolio.exposure import ExposureAnalyzer
from bist_signal_bot.portfolio.models import PortfolioState, PortfolioHolding, PortfolioPositionSide, AllocationResult, AllocationResultItem

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


def test_exposure_analyzer_calculate_zero_equity():
    import datetime
    state = PortfolioState.model_construct(
        equity=0.0,
        cash=0.0,
        holdings=[],
        timestamp=datetime.datetime.now(datetime.UTC),
        daily_signal_count=0
    )
    analyzer = ExposureAnalyzer()
    report = analyzer.calculate_exposure(state)
    assert report.gross_exposure_pct == 0.0
    assert report.cash_pct == 1.0
    assert "Portfolio equity is zero or negative" in report.issues

def test_exposure_analyzer_limits_all_exceeded():
    from bist_signal_bot.portfolio.models import ExposureReport, PortfolioRejectReason
    settings = MagicMock()
    settings.PORTFOLIO_MAX_GROSS_EXPOSURE_PCT = 1.0
    settings.PORTFOLIO_MAX_NET_EXPOSURE_PCT = 0.5
    settings.PORTFOLIO_MAX_SYMBOL_WEIGHT_PCT = 0.20
    settings.PORTFOLIO_MAX_SECTOR_WEIGHT_PCT = 0.40
    settings.PORTFOLIO_MIN_CASH_PCT = 0.05
    settings.PORTFOLIO_MAX_OPEN_POSITIONS = 5

    report = ExposureReport(
        gross_exposure_pct=1.5,
        net_exposure_pct=0.8,
        long_exposure_pct=1.0,
        short_exposure_pct=-0.2,
        max_symbol_weight_pct=0.30,
        sector_weights={"Tech": 0.50},
        open_position_count=10,
        cash_pct=0.01,
        issues=[],
        metadata={}
    )

    analyzer = ExposureAnalyzer()
    ok, reasons, issues = analyzer.check_exposure_limits(report, settings)

    assert not ok
    assert len(reasons) == 6
    assert PortfolioRejectReason.MAX_GROSS_EXPOSURE_EXCEEDED in reasons
    assert PortfolioRejectReason.MAX_NET_EXPOSURE_EXCEEDED in reasons
    assert PortfolioRejectReason.MAX_SYMBOL_WEIGHT_EXCEEDED in reasons
    assert PortfolioRejectReason.MAX_SECTOR_WEIGHT_EXCEEDED in reasons
    assert PortfolioRejectReason.INSUFFICIENT_CASH in reasons
    assert PortfolioRejectReason.MAX_POSITIONS_EXCEEDED in reasons

def test_sector_exposure_from_holdings():
    analyzer = ExposureAnalyzer()

    # Empty holdings
    assert analyzer.sector_exposure_from_holdings([]) == {}

    # Zero total market value
    h_zero = PortfolioHolding(symbol="Z", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=0.0, weight_pct=0.0)
    assert analyzer.sector_exposure_from_holdings([h_zero]) == {}

    # Normal holdings
    h1 = PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1, sector="Tech")
    h2 = PortfolioHolding(symbol="B", side=PortfolioPositionSide.LONG, quantity=5, avg_price=20.0, market_value=200.0, weight_pct=0.2, sector="Bank")
    h3 = PortfolioHolding(symbol="C", side=PortfolioPositionSide.LONG, quantity=5, avg_price=20.0, market_value=100.0, weight_pct=0.1) # No sector, should default to UNKNOWN

    sectors = analyzer.sector_exposure_from_holdings([h1, h2, h3])
    assert len(sectors) == 3
    assert sectors["Tech"] == 100.0 / 400.0
    assert sectors["Bank"] == 200.0 / 400.0
    assert sectors["UNKNOWN"] == 100.0 / 400.0

def test_simulate_post_allocation_exposure_edge_cases():
    from datetime import datetime
    from unittest.mock import patch

    # Test existing holding but with quantity that makes new_qty <= 0
    h1 = PortfolioHolding(symbol="EXISTING_NEG_QTY", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1, sector="Tech")
    state1 = PortfolioState(equity=1000.0, cash=900.0, holdings=[h1])
    alloc_item_neg_qty = AllocationResultItem(
        symbol="EXISTING_NEG_QTY",
        approved=True,
        original_notional=50.0,
        allocated_notional=50.0,
        allocated_weight_pct=0.05,
        quantity=-10.0,  # new_qty = 10 + (-10) = 0
        reduction_pct=0.0,
        reasons=[],
        metadata={}
    )
    allocation1 = AllocationResult(
        method="EQUAL_WEIGHT",
        items=[alloc_item_neg_qty],
        total_allocated_notional=50.0,
        total_allocated_pct=0.05,
        rejected_symbols=[],
        reduced_symbols=[],
        issues=[],
        generated_at=datetime.utcnow()
    )
    analyzer = ExposureAnalyzer()
    report1 = analyzer.simulate_post_allocation_exposure(state1, allocation1)
    # The existing holding is replaced, but since new_qty <= 0, new_avg falls back to existing.avg_price
    # The holding is still added to sim_holdings (count remains 1)
    assert report1.open_position_count == 1

    # Test new holding with item.quantity <= 0
    state2 = PortfolioState(equity=1000.0, cash=900.0, holdings=[])
    alloc_item_zero_qty = AllocationResultItem(
        symbol="NEW_ZERO_QTY",
        approved=True,
        original_notional=50.0,
        allocated_notional=50.0,
        allocated_weight_pct=0.05,
        quantity=0.0,  # quantity = 0 triggers fallback to avg_price = 1.0
        reduction_pct=0.0,
        reasons=[],
        metadata={}
    )
    allocation2 = AllocationResult(
        method="EQUAL_WEIGHT",
        items=[alloc_item_zero_qty],
        total_allocated_notional=50.0,
        total_allocated_pct=0.05,
        rejected_symbols=[],
        reduced_symbols=[],
        issues=[],
        generated_at=datetime.utcnow()
    )
    report2 = analyzer.simulate_post_allocation_exposure(state2, allocation2)
    assert report2.open_position_count == 1

    # Test sim_equity <= 0 override using mock to avoid Pydantic validation error
    state3 = PortfolioState(equity=1000.0, cash=900.0, holdings=[])
    alloc_item_neg_equity = AllocationResultItem(
        symbol="ANY",
        approved=True,
        original_notional=50.0,
        allocated_notional=50.0,
        allocated_weight_pct=0.05,
        quantity=1.0,
        reduction_pct=0.0,
        reasons=[],
        metadata={}
    )
    allocation3 = AllocationResult(
        method="EQUAL_WEIGHT",
        items=[alloc_item_neg_equity],
        total_allocated_notional=50.0,
        total_allocated_pct=0.05,
        rejected_symbols=[],
        reduced_symbols=[],
        issues=[],
        generated_at=datetime.utcnow()
    )

    # Instead of bypassing validation in production, we patch the instance property directly
    # to simulate the error condition entering calculate_exposure during simulation
    with patch('bist_signal_bot.portfolio.exposure.PortfolioState') as mock_state_class:
        from unittest.mock import MagicMock
        mock_instance = MagicMock(spec=PortfolioState)
        mock_instance.equity = -100.0
        mock_instance.cash = 900.0
        mock_instance.holdings = []
        mock_state_class.return_value = mock_instance

        report3 = analyzer.simulate_post_allocation_exposure(state3, allocation3)
        assert "Portfolio equity is zero or negative" in report3.issues
