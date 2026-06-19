import pandas as pd
from typing import Any

from bist_signal_bot.portfolio.models import (
    CorrelationMatrixResult, ExposureReport, AllocationResult, PortfolioRiskDecision
)

def correlation_to_dict(result: CorrelationMatrixResult) -> dict[str, Any]:
    return result.summary()

def exposure_to_dict(report: ExposureReport) -> dict[str, Any]:
    return report.summary()

def allocation_to_dict(result: AllocationResult) -> dict[str, Any]:
    return result.summary()

def portfolio_risk_decision_to_dict(decision: PortfolioRiskDecision) -> dict[str, Any]:
    return decision.summary()

def format_portfolio_risk_text(decision: PortfolioRiskDecision) -> str:
    lines = [
        f"--- Portfolio Risk Decision ---",
        f"Status: {decision.status.value}",
        f"Approved: {decision.approved_count}, Rejected: {decision.rejected_count}, Reduced: {decision.reduced_count}"
    ]

    if decision.reject_reasons:
        reasons = [r.value for r in decision.reject_reasons]
        lines.append(f"Reject Reasons: {', '.join(reasons)}")

    lines.append(f"Allocation Method: {decision.allocation_result.method.value}")
    lines.append(f"Total Allocated: {decision.allocation_result.total_allocated_pct:.2%}")

    lines.append(f"Gross Exposure Before: {decision.exposure_report_before.gross_exposure_pct:.2%}")
    if decision.exposure_report_after:
        lines.append(f"Gross Exposure After: {decision.exposure_report_after.gross_exposure_pct:.2%}")

    if decision.warnings:
        lines.append(f"Warnings: {', '.join(decision.warnings)}")

    lines.append(f"\nDisclaimer: {decision.disclaimer}")

    return "\n".join(lines)
