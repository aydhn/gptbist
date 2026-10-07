import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from bist_signal_bot.portfolio.reporting import (
    correlation_to_dict,
    exposure_to_dict,
    allocation_to_dict,
    portfolio_risk_decision_to_dict,
    format_portfolio_risk_text
)
from bist_signal_bot.portfolio.models import (
    PortfolioDecisionStatus,
    AllocationMethod,
    PortfolioRejectReason
)

def test_correlation_to_dict():
    mock_result = MagicMock()
    mock_result.summary.return_value = {"summary": "correlation"}
    assert correlation_to_dict(mock_result) == {"summary": "correlation"}
    mock_result.summary.assert_called_once()

def test_exposure_to_dict():
    mock_report = MagicMock()
    mock_report.summary.return_value = {"summary": "exposure"}
    assert exposure_to_dict(mock_report) == {"summary": "exposure"}
    mock_report.summary.assert_called_once()

def test_allocation_to_dict():
    mock_result = MagicMock()
    mock_result.summary.return_value = {"summary": "allocation"}
    assert allocation_to_dict(mock_result) == {"summary": "allocation"}
    mock_result.summary.assert_called_once()

def test_portfolio_risk_decision_to_dict():
    mock_decision = MagicMock()
    mock_decision.summary.return_value = {"summary": "decision"}
    assert portfolio_risk_decision_to_dict(mock_decision) == {"summary": "decision"}
    mock_decision.summary.assert_called_once()

def test_format_portfolio_risk_text_full():
    mock_decision = MagicMock()
    mock_decision.status = PortfolioDecisionStatus.APPROVED
    mock_decision.approved_count = 5
    mock_decision.rejected_count = 2
    mock_decision.reduced_count = 1

    mock_decision.reject_reasons = [PortfolioRejectReason.MAX_POSITIONS_EXCEEDED, PortfolioRejectReason.INSUFFICIENT_CASH]

    mock_decision.allocation_result.method = AllocationMethod.EQUAL_WEIGHT
    mock_decision.allocation_result.total_allocated_pct = 0.75

    mock_decision.exposure_report_before.gross_exposure_pct = 0.50
    mock_decision.exposure_report_after.gross_exposure_pct = 1.25

    mock_decision.warnings = ["High volatility detected", "Low liquidity in some assets"]
    mock_decision.disclaimer = "Test disclaimer"

    result = format_portfolio_risk_text(mock_decision)

    assert "--- Portfolio Risk Decision ---" in result
    assert "Status: APPROVED" in result
    assert "Approved: 5, Rejected: 2, Reduced: 1" in result
    assert "Reject Reasons: MAX_POSITIONS_EXCEEDED, INSUFFICIENT_CASH" in result
    assert "Allocation Method: EQUAL_WEIGHT" in result
    assert "Total Allocated: 75.00%" in result
    assert "Gross Exposure Before: 50.00%" in result
    assert "Gross Exposure After: 125.00%" in result
    assert "Warnings: High volatility detected, Low liquidity in some assets" in result
    assert "Disclaimer: Test disclaimer" in result

def test_format_portfolio_risk_text_minimal():
    mock_decision = MagicMock()
    mock_decision.status = PortfolioDecisionStatus.REJECTED
    mock_decision.approved_count = 0
    mock_decision.rejected_count = 5
    mock_decision.reduced_count = 0

    mock_decision.reject_reasons = []

    mock_decision.allocation_result.method = AllocationMethod.VOLATILITY_SCALED
    mock_decision.allocation_result.total_allocated_pct = 0.0

    mock_decision.exposure_report_before.gross_exposure_pct = 0.80
    mock_decision.exposure_report_after = None

    mock_decision.warnings = []
    mock_decision.disclaimer = "Basic disclaimer"

    result = format_portfolio_risk_text(mock_decision)

    assert "--- Portfolio Risk Decision ---" in result
    assert "Status: REJECTED" in result
    assert "Approved: 0, Rejected: 5, Reduced: 0" in result
    assert "Reject Reasons" not in result
    assert "Allocation Method: VOLATILITY_SCALED" in result
    assert "Total Allocated: 0.00%" in result
    assert "Gross Exposure Before: 80.00%" in result
    assert "Gross Exposure After" not in result
    assert "Warnings" not in result
    assert "Disclaimer: Basic disclaimer" in result
