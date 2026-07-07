import pytest
from datetime import datetime
import pandas as pd
from unittest.mock import MagicMock

from bist_signal_bot.portfolio.reporting import (
    correlation_to_dict, exposure_to_dict, allocation_to_dict,
    portfolio_risk_decision_to_dict, format_portfolio_risk_text
)
from bist_signal_bot.portfolio.models import (
    CorrelationMatrixResult, ExposureReport, AllocationResult,
    AllocationMethod, PortfolioRiskDecision, PortfolioDecisionStatus,
    PortfolioRejectReason, PortfolioState
)


def test_correlation_to_dict():
    result = CorrelationMatrixResult(
        symbols=["AAPL", "MSFT"],
        matrix=pd.DataFrame(),
        lookback_rows=100,
        method="pearson",
        generated_at=datetime.utcnow(),
        issues=["Some issue"],
        metadata={}
    )
    res_dict = correlation_to_dict(result)
    assert res_dict["symbol_count"] == 2
    assert res_dict["lookback_rows"] == 100
    assert res_dict["method"] == "pearson"
    assert res_dict["issues_count"] == 1


def test_exposure_to_dict():
    report = ExposureReport(
        gross_exposure_pct=0.8,
        net_exposure_pct=0.2,
        long_exposure_pct=0.5,
        short_exposure_pct=0.3,
        max_symbol_weight_pct=0.1,
        sector_weights={"TECH": 0.5},
        open_position_count=5,
        cash_pct=0.2,
        issues=["Warning limit"],
        metadata={}
    )
    res_dict = exposure_to_dict(report)
    assert res_dict["gross_exposure_pct"] == 0.8
    assert res_dict["net_exposure_pct"] == 0.2
    assert res_dict["max_symbol_weight_pct"] == 0.1
    assert res_dict["open_position_count"] == 5
    assert res_dict["cash_pct"] == 0.2
    assert res_dict["issues_count"] == 1


def test_allocation_to_dict():
    result = AllocationResult(
        method=AllocationMethod.EQUAL_WEIGHT,
        items=[],
        total_allocated_notional=10000.0,
        total_allocated_pct=0.5,
        rejected_symbols=["TSLA"],
        reduced_symbols=["AMZN"],
        issues=[],
        generated_at=datetime.utcnow()
    )
    res_dict = allocation_to_dict(result)
    assert res_dict["method"] == "EQUAL_WEIGHT"
    assert res_dict["total_allocated_pct"] == 0.5
    assert res_dict["items_count"] == 0
    assert res_dict["approved_count"] == 0
    assert res_dict["rejected_count"] == 1
    assert res_dict["reduced_count"] == 1


def test_portfolio_risk_decision_to_dict():
    decision = PortfolioRiskDecision(
        portfolio_state=PortfolioState(equity=100000.0, cash=100000.0),
        input_signals=[],
        trade_risk_decisions=[],
        allocation_result=AllocationResult(
            method=AllocationMethod.RISK_PARITY_SIMPLE,
            items=[],
            total_allocated_notional=0.0,
            total_allocated_pct=0.0,
            rejected_symbols=[],
            reduced_symbols=[],
            issues=[],
            generated_at=datetime.utcnow()
        ),
        exposure_report_before=ExposureReport(
            gross_exposure_pct=0.5, net_exposure_pct=0.5, long_exposure_pct=0.5,
            short_exposure_pct=0.0, max_symbol_weight_pct=0.1, sector_weights={},
            open_position_count=5, cash_pct=0.5, issues=[], metadata={}
        ),
        exposure_report_after=None,
        correlation_result=None,
        status=PortfolioDecisionStatus.APPROVED,
        approved_count=2,
        rejected_count=1,
        reduced_count=0,
        reject_reasons=[],
        warnings=[],
        generated_at=datetime.utcnow()
    )
    res_dict = portfolio_risk_decision_to_dict(decision)
    assert res_dict["status"] == "APPROVED"
    assert res_dict["approved_count"] == 2
    assert res_dict["rejected_count"] == 1
    assert res_dict["reduced_count"] == 0
    assert res_dict["disclaimer"] == "Portfolio risk research output only. Not investment advice. No order was sent."


def test_format_portfolio_risk_text():
    decision = PortfolioRiskDecision(
        portfolio_state=PortfolioState(equity=100000.0, cash=100000.0),
        input_signals=[],
        trade_risk_decisions=[],
        allocation_result=AllocationResult(
            method=AllocationMethod.RISK_PARITY_SIMPLE,
            items=[],
            total_allocated_notional=20000.0,
            total_allocated_pct=0.2,
            rejected_symbols=["TSLA"],
            reduced_symbols=[],
            issues=[],
            generated_at=datetime.utcnow()
        ),
        exposure_report_before=ExposureReport(
            gross_exposure_pct=0.5, net_exposure_pct=0.5, long_exposure_pct=0.5,
            short_exposure_pct=0.0, max_symbol_weight_pct=0.1, sector_weights={},
            open_position_count=5, cash_pct=0.5, issues=[], metadata={}
        ),
        exposure_report_after=ExposureReport(
            gross_exposure_pct=0.7, net_exposure_pct=0.7, long_exposure_pct=0.7,
            short_exposure_pct=0.0, max_symbol_weight_pct=0.1, sector_weights={},
            open_position_count=7, cash_pct=0.3, issues=[], metadata={}
        ),
        correlation_result=None,
        status=PortfolioDecisionStatus.PARTIALLY_APPROVED,
        approved_count=2,
        rejected_count=1,
        reduced_count=0,
        reject_reasons=[PortfolioRejectReason.MAX_SECTOR_WEIGHT_EXCEEDED],
        warnings=["High volatility in tech sector"],
        generated_at=datetime.utcnow()
    )

    text = format_portfolio_risk_text(decision)
    assert "--- Portfolio Risk Decision ---" in text
    assert "Status: PARTIALLY_APPROVED" in text
    assert "Approved: 2, Rejected: 1, Reduced: 0" in text
    assert "Reject Reasons: MAX_SECTOR_WEIGHT_EXCEEDED" in text
    assert "Allocation Method: RISK_PARITY_SIMPLE" in text
    assert "Total Allocated: 20.00%" in text
    assert "Gross Exposure Before: 50.00%" in text
    assert "Gross Exposure After: 70.00%" in text
    assert "Warnings: High volatility in tech sector" in text
    assert "Disclaimer: Portfolio risk research output only. Not investment advice. No order was sent." in text

def test_correlation_to_dict_mocked():
    mock_result = MagicMock()
    mock_result.summary.return_value = {"mocked": "value"}

    res = correlation_to_dict(mock_result)

    mock_result.summary.assert_called_once()
    assert res == {"mocked": "value"}
