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

def _format_base_info(decision: PortfolioRiskDecision) -> list[str]:
    return [
        f"--- Portfolio Risk Decision ---",
        f"Status: {decision.status.value}",
        f"Approved: {decision.approved_count}, Rejected: {decision.rejected_count}, Reduced: {decision.reduced_count}"
    ]

def _format_reject_reasons(decision: PortfolioRiskDecision) -> list[str]:
    if decision.reject_reasons:
        reasons = [r.value for r in decision.reject_reasons]
        return [f"Reject Reasons: {', '.join(reasons)}"]
    return []

def _format_allocation_summary(decision: PortfolioRiskDecision) -> list[str]:
    return [
        f"Allocation Method: {decision.allocation_result.method.value}",
        f"Total Allocated: {decision.allocation_result.total_allocated_pct:.2%}"
    ]

def _format_exposure_summary(decision: PortfolioRiskDecision) -> list[str]:
    lines = [f"Gross Exposure Before: {decision.exposure_report_before.gross_exposure_pct:.2%}"]
    if decision.exposure_report_after:
        lines.append(f"Gross Exposure After: {decision.exposure_report_after.gross_exposure_pct:.2%}")
    return lines

def _format_warnings(decision: PortfolioRiskDecision) -> list[str]:
    if decision.warnings:
        return [f"Warnings: {', '.join(decision.warnings)}"]
    return []

def format_portfolio_risk_text(decision: PortfolioRiskDecision) -> str:
    lines = []
    lines.extend(_format_base_info(decision))
    lines.extend(_format_reject_reasons(decision))
    lines.extend(_format_allocation_summary(decision))
    lines.extend(_format_exposure_summary(decision))
    lines.extend(_format_warnings(decision))
    lines.append(f"\nDisclaimer: {decision.disclaimer}")

    return "\n".join(lines)
