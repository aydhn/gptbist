from typing import List, Dict, Any
import pandas as pd

from bist_signal_bot.valuation.models import (
    ValuationMarketInput, ValuationMultiple, ValuationBand,
    PeerValuationComparison, ValuationRiskAssessment, ValuationReport
)

def market_input_to_dict(input: ValuationMarketInput) -> Dict[str, Any]:
    return input.model_dump(mode="json")

def multiple_to_dict(multiple: ValuationMultiple) -> Dict[str, Any]:
    return multiple.model_dump(mode="json")

def band_to_dict(band: ValuationBand) -> Dict[str, Any]:
    return band.model_dump(mode="json")

def peer_comparison_to_dict(comparison: PeerValuationComparison) -> Dict[str, Any]:
    return comparison.model_dump(mode="json")

def risk_assessment_to_dict(assessment: ValuationRiskAssessment) -> Dict[str, Any]:
    return assessment.model_dump(mode="json")

def valuation_report_to_dict(report: ValuationReport) -> Dict[str, Any]:
    return report.model_dump(mode="json")

def multiples_to_dataframe(multiples: List[ValuationMultiple]) -> pd.DataFrame:
    if not multiples:
        return pd.DataFrame()
    data = [multiple_to_dict(m) for m in multiples]
    return pd.DataFrame(data)

def bands_to_dataframe(bands: List[ValuationBand]) -> pd.DataFrame:
    if not bands:
        return pd.DataFrame()
    data = [band_to_dict(b) for b in bands]
    return pd.DataFrame(data)

def format_market_input_text(input: ValuationMarketInput) -> str:
    lines = [
        f"**Market Inputs for {input.symbol} as of {input.as_of.strftime('%Y-%m-%d')}**",
        f"- Price: {input.price if input.price is not None else 'N/A'} {input.currency}",
        f"- Shares Outstanding: {input.shares_outstanding if input.shares_outstanding is not None else 'N/A'}",
        f"- Market Cap: {input.market_cap if input.market_cap is not None else 'N/A'} {input.currency}",
        f"- Enterprise Value: {input.enterprise_value if input.enterprise_value is not None else 'N/A'} {input.currency}",
        f"- Net Debt: {input.net_debt if input.net_debt is not None else 'N/A'} {input.currency}"
    ]
    if input.warnings:
        lines.append("- **Warnings**:")
        for w in input.warnings:
            lines.append(f"  - {w}")
    return "\n".join(lines)

def format_multiples_text(multiples: List[ValuationMultiple]) -> str:
    if not multiples:
        return "No multiples calculated."
    lines = ["**Valuation Multiples**"]
    for m in multiples:
        val_str = f"{m.value:.2f}" if m.value is not None else "N/A"
        lines.append(f"- {m.metric_type.value}: {val_str} ({m.status.value})")
    return "\n".join(lines)

def format_bands_text(bands: List[ValuationBand]) -> str:
    if not bands:
        return "No historical bands available."
    lines = ["**Historical Valuation Bands**"]
    for b in bands:
        pr_str = f"{b.percentile_rank:.1f}%" if b.percentile_rank is not None else "N/A"
        lines.append(f"- {b.metric_type.value}: Percentile {pr_str} - Status: {b.status.value}")
    return "\n".join(lines)

def format_peer_comparison_text(comparisons: List[PeerValuationComparison]) -> str:
    if not comparisons:
        return "No peer comparisons available."
    lines = ["**Peer Relative Valuation**"]
    for c in comparisons:
        dp_str = f"{c.relative_discount_premium_pct:+.1f}%" if c.relative_discount_premium_pct is not None else "N/A"
        lines.append(f"- {c.metric_type.value}: Premium/Discount: {dp_str} - Status: {c.status.value}")
    return "\n".join(lines)

def format_valuation_risk_text(assessment: ValuationRiskAssessment) -> str:
    score_str = f"{assessment.valuation_score:.1f}/100" if assessment.valuation_score is not None else "N/A"
    lines = [
        "**Valuation Risk Assessment**",
        f"- Valuation Score: {score_str}",
        f"- Risk Level: {assessment.valuation_risk_level.value}",
        f"- Recommended Decision: {assessment.recommended_decision}"
    ]
    if assessment.expensive_metrics:
        lines.append("- **Expensive Flags**:")
        for m in assessment.expensive_metrics:
            lines.append(f"  - {m}")
    if assessment.cheap_metrics:
        lines.append("- **Cheap Flags**:")
        for m in assessment.cheap_metrics:
            lines.append(f"  - {m}")
    if assessment.data_quality_warnings:
        lines.append("- **Data Quality Warnings**:")
        for w in assessment.data_quality_warnings:
            lines.append(f"  - {w}")

    lines.append("")
    lines.append(f"*{assessment.disclaimer}*")
    return "\n".join(lines)

def format_valuation_report_markdown(report: ValuationReport) -> str:
    lines = [
        f"# Valuation Report for {report.symbol or 'Multiple Symbols'}",
        f"Generated at: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ""
    ]

    if report.risk_assessments:
        lines.append(format_valuation_risk_text(report.risk_assessments[0]))
        lines.append("")

    if report.market_inputs:
        lines.append(format_market_input_text(report.market_inputs[0]))
        lines.append("")

    if report.multiples:
        lines.append(format_multiples_text(report.multiples))
        lines.append("")

    if report.bands:
        lines.append(format_bands_text(report.bands))
        lines.append("")

    if report.peer_comparisons:
        lines.append(format_peer_comparison_text(report.peer_comparisons))
        lines.append("")

    if report.warnings:
        lines.append("## General Warnings")
        for w in report.warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append("---")
    lines.append(f"*{report.disclaimer}*")
    return "\n".join(lines)
