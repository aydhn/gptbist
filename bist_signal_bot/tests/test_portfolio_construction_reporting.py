import pandas as pd
from datetime import datetime, timezone
from bist_signal_bot.portfolio_construction.reporting import format_portfolio_construction_text, positions_to_dataframe
from bist_signal_bot.portfolio_construction.models import (
    PortfolioConstructionResult,
    PortfolioConstructionRequest,
    PortfolioConstructionStatus,
    PortfolioWeightingMethod,
    PortfolioPositionResearch,
    PortfolioConstraintViolation,
    ConstraintType,
    ConstraintSeverity
)

import pytest
from bist_signal_bot.portfolio_construction.reporting import format_rebalance_simulation_text
from bist_signal_bot.portfolio_construction.models import RebalanceSimulation

def test_reporting_disclaimers():
    sim = RebalanceSimulation(
        rebalance_id="reb1",
        current_weights={"A": 0.5},
        target_weights={"A": 0.6},
        actions=[],
        estimated_turnover_pct=10.0
    )

    text = format_rebalance_simulation_text(sim)
    assert "research-only" in text
    assert "Not an order list" in text or "not an order list" in text


def _make_dummy_request() -> PortfolioConstructionRequest:
    return PortfolioConstructionRequest(
        request_id="req1",
        symbols=["AAPL"],
        strategy_names=["strat1"],
        weighting_method=PortfolioWeightingMethod.EQUAL_WEIGHT,
        max_positions=10,
        portfolio_notional=10000.0,
        current_weights={}
    )

def test_format_portfolio_construction_text_basic():
    request = _make_dummy_request()
    dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = PortfolioConstructionResult(
        result_id="res1",
        request=request,
        generated_at=dt,
        status=PortfolioConstructionStatus.PASS,
        weighting_method=PortfolioWeightingMethod.EQUAL_WEIGHT,
        diversification_score=85.5,
        portfolio_score=92.1,
        estimated_turnover_pct=5.0,
        positions=[
            PortfolioPositionResearch(
                position_id="p1",
                symbol="AAPL",
                current_weight=0.0,
                target_weight=0.5,
                weight_delta=0.5
            )
        ]
    )

    text = format_portfolio_construction_text(result)

    assert "BIST Bot Portfolio Construction Result" in text
    assert "Result ID: res1" in text
    assert "Generated At: 2025-01-01T12:00:00+00:00" in text
    assert "Status: PASS" in text
    assert "Weighting Method: EQUAL_WEIGHT" in text
    assert "Diversification Score: 85.5" in text
    assert "Portfolio Score: 92.1" in text
    assert "Estimated Turnover: 5.0%" in text
    assert "Constraint Violations: 0" in text
    assert "AAPL: 50.00%" in text
    assert result.disclaimer in text

def test_format_portfolio_construction_text_none_values():
    request = _make_dummy_request()
    result = PortfolioConstructionResult(
        result_id="res2",
        request=request,
        status=PortfolioConstructionStatus.INSUFFICIENT_DATA,
        weighting_method=PortfolioWeightingMethod.EQUAL_WEIGHT,
        diversification_score=None,
        portfolio_score=None,
        estimated_turnover_pct=None,
        violations=[
            PortfolioConstraintViolation(
                violation_id="v1",
                constraint_type=ConstraintType.MAX_SYMBOL_WEIGHT,
                severity=ConstraintSeverity.HIGH,
                message="Too heavy"
            )
        ]
    )

    text = format_portfolio_construction_text(result)

    assert "Diversification Score: N/A" in text
    assert "Portfolio Score: N/A" in text
    assert "Estimated Turnover: 0.0%" in text
    assert "Constraint Violations: 1" in text

def test_positions_to_dataframe_empty():
    df = positions_to_dataframe([])
    assert isinstance(df, pd.DataFrame)
    assert df.empty

def test_positions_to_dataframe_populated():
    positions = [
        PortfolioPositionResearch(
            position_id="p1",
            symbol="AAPL",
            current_weight=0.0,
            target_weight=0.5,
            weight_delta=0.5
        ),
        PortfolioPositionResearch(
            position_id="p2",
            symbol="MSFT",
            current_weight=0.2,
            target_weight=0.5,
            weight_delta=0.3
        )
    ]
    df = positions_to_dataframe(positions)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df["symbol"]) == ["AAPL", "MSFT"]
    assert list(df["target_weight"]) == [0.5, 0.5]
