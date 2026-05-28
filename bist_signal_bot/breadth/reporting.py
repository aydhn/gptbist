import pandas as pd
from typing import Any
from bist_signal_bot.breadth.models import (
    AdvanceDeclineSummary, BreadthDivergence, BreadthInputRow, BreadthMetric, BreadthRegimeSnapshot,
    BreadthReport, BreadthUniverseSnapshot, HighLowBreadthSummary, ParticipationSummary,
    SectorBreadthSummary, VolumeBreadthSummary
)

def universe_to_dict(snapshot: BreadthUniverseSnapshot) -> dict[str, Any]:
    return {
        "universe_id": snapshot.universe_id,
        "name": snapshot.name,
        "as_of": snapshot.as_of,
        "scope": snapshot.scope.value,
        "symbols": snapshot.symbols,
        "sectors": snapshot.sectors,
        "active_count": snapshot.active_count,
        "excluded_symbols": snapshot.excluded_symbols,
        "warnings": snapshot.warnings,
        "metadata": snapshot.metadata
    }

def input_row_to_dict(row: BreadthInputRow) -> dict[str, Any]:
    return {
        "row_id": row.row_id,
        "symbol": row.symbol,
        "as_of": row.as_of,
        "sector": row.sector,
        "close": row.close,
        "previous_close": row.previous_close,
        "volume": row.volume,
        "turnover": row.turnover,
        "ma_20": row.ma_20,
        "ma_50": row.ma_50,
        "ma_200": row.ma_200,
        "high_20d": row.high_20d,
        "low_20d": row.low_20d,
        "high_252d": row.high_252d,
        "low_252d": row.low_252d,
        "return_1d_pct": row.return_1d_pct,
        "warnings": row.warnings,
        "metadata": row.metadata
    }

def metric_to_dict(metric: BreadthMetric) -> dict[str, Any]:
    return {
        "metric_id": metric.metric_id,
        "metric_type": metric.metric_type.value,
        "scope": metric.scope.value,
        "scope_name": metric.scope_name,
        "as_of": metric.as_of,
        "value": metric.value,
        "numerator": metric.numerator,
        "denominator": metric.denominator,
        "status": metric.status.value,
        "warnings": metric.warnings,
        "metadata": metric.metadata
    }

def advance_decline_to_dict(summary: AdvanceDeclineSummary) -> dict[str, Any]:
    return {
        "summary_id": summary.summary_id,
        "scope": summary.scope.value,
        "scope_name": summary.scope_name,
        "as_of": summary.as_of,
        "advances": summary.advances,
        "declines": summary.declines,
        "unchanged": summary.unchanged,
        "net_advances": summary.net_advances,
        "advance_decline_ratio": summary.advance_decline_ratio,
        "advance_percent": summary.advance_percent,
        "status": summary.status.value,
        "warnings": summary.warnings,
        "disclaimer": summary.disclaimer,
        "metadata": summary.metadata
    }

def participation_to_dict(summary: ParticipationSummary) -> dict[str, Any]:
    return {
        "participation_id": summary.participation_id,
        "scope": summary.scope.value,
        "scope_name": summary.scope_name,
        "as_of": summary.as_of,
        "above_ma_20_pct": summary.above_ma_20_pct,
        "above_ma_50_pct": summary.above_ma_50_pct,
        "above_ma_200_pct": summary.above_ma_200_pct,
        "positive_return_pct": summary.positive_return_pct,
        "participation_score": summary.participation_score,
        "breadth_thrust_score": summary.breadth_thrust_score,
        "status": summary.status.value,
        "warnings": summary.warnings,
        "disclaimer": summary.disclaimer,
        "metadata": summary.metadata
    }

def high_low_to_dict(summary: HighLowBreadthSummary) -> dict[str, Any]:
    return {
        "highlow_id": summary.highlow_id,
        "scope": summary.scope.value,
        "scope_name": summary.scope_name,
        "as_of": summary.as_of,
        "new_high_20d_count": summary.new_high_20d_count,
        "new_low_20d_count": summary.new_low_20d_count,
        "new_high_52w_count": summary.new_high_52w_count,
        "new_low_52w_count": summary.new_low_52w_count,
        "high_low_spread": summary.high_low_spread,
        "high_low_score": summary.high_low_score,
        "status": summary.status.value,
        "warnings": summary.warnings,
        "metadata": summary.metadata
    }

def volume_breadth_to_dict(summary: VolumeBreadthSummary) -> dict[str, Any]:
    return {
        "volume_breadth_id": summary.volume_breadth_id,
        "scope": summary.scope.value,
        "scope_name": summary.scope_name,
        "as_of": summary.as_of,
        "up_volume": summary.up_volume,
        "down_volume": summary.down_volume,
        "unchanged_volume": summary.unchanged_volume,
        "up_volume_ratio": summary.up_volume_ratio,
        "down_volume_ratio": summary.down_volume_ratio,
        "volume_breadth_score": summary.volume_breadth_score,
        "status": summary.status.value,
        "warnings": summary.warnings,
        "metadata": summary.metadata
    }

def sector_breadth_to_dict(summary: SectorBreadthSummary) -> dict[str, Any]:
    return {
        "sector_breadth_id": summary.sector_breadth_id,
        "sector": summary.sector,
        "as_of": summary.as_of,
        "symbols_count": summary.symbols_count,
        "advance_percent": summary.advance_percent,
        "above_ma_50_pct": summary.above_ma_50_pct,
        "above_ma_200_pct": summary.above_ma_200_pct,
        "up_volume_ratio": summary.up_volume_ratio,
        "sector_breadth_score": summary.sector_breadth_score,
        "status": summary.status.value,
        "leading_symbols": summary.leading_symbols,
        "lagging_symbols": summary.lagging_symbols,
        "warnings": summary.warnings,
        "disclaimer": summary.disclaimer,
        "metadata": summary.metadata
    }

def divergence_to_dict(divergence: BreadthDivergence) -> dict[str, Any]:
    return {
        "divergence_id": divergence.divergence_id,
        "as_of": divergence.as_of,
        "scope": divergence.scope.value,
        "scope_name": divergence.scope_name,
        "divergence_type": divergence.divergence_type.value,
        "index_return_pct": divergence.index_return_pct,
        "breadth_change_pct": divergence.breadth_change_pct,
        "participation_change_pct": divergence.participation_change_pct,
        "divergence_score": divergence.divergence_score,
        "status": divergence.status.value,
        "message": divergence.message,
        "warnings": divergence.warnings,
        "disclaimer": divergence.disclaimer,
        "metadata": divergence.metadata
    }

def regime_to_dict(snapshot: BreadthRegimeSnapshot) -> dict[str, Any]:
    return {
        "regime_id": snapshot.regime_id,
        "as_of": snapshot.as_of,
        "scope": snapshot.scope.value,
        "scope_name": snapshot.scope_name,
        "label": snapshot.label.value,
        "breadth_score": snapshot.breadth_score,
        "participation_score": snapshot.participation_score,
        "volume_breadth_score": snapshot.volume_breadth_score,
        "divergence_score": snapshot.divergence_score,
        "sector_confirmation_score": snapshot.sector_confirmation_score,
        "status": snapshot.status.value,
        "warnings": snapshot.warnings,
        "disclaimer": snapshot.disclaimer,
        "metadata": snapshot.metadata
    }

def breadth_report_to_dict(report: BreadthReport) -> dict[str, Any]:
    return {
        "report_id": report.report_id,
        "generated_at": report.generated_at,
        "scope": report.scope.value,
        "scope_name": report.scope_name,
        "universe": universe_to_dict(report.universe) if report.universe else None,
        "advance_decline": advance_decline_to_dict(report.advance_decline) if report.advance_decline else None,
        "participation": participation_to_dict(report.participation) if report.participation else None,
        "high_low": high_low_to_dict(report.high_low) if report.high_low else None,
        "volume_breadth": volume_breadth_to_dict(report.volume_breadth) if report.volume_breadth else None,
        "sector_breadth": [sector_breadth_to_dict(s) for s in report.sector_breadth],
        "divergences": [divergence_to_dict(d) for d in report.divergences],
        "regime": regime_to_dict(report.regime) if report.regime else None,
        "metrics": [metric_to_dict(m) for m in report.metrics],
        "key_findings": report.key_findings,
        "warnings": report.warnings,
        "disclaimer": report.disclaimer,
        "metadata": report.metadata
    }

def sector_breadth_to_dataframe(summaries: list[SectorBreadthSummary]) -> pd.DataFrame:
    dicts = [sector_breadth_to_dict(s) for s in summaries]
    return pd.DataFrame(dicts)

def metrics_to_dataframe(metrics: list[BreadthMetric]) -> pd.DataFrame:
    dicts = [metric_to_dict(m) for m in metrics]
    return pd.DataFrame(dicts)

def format_advance_decline_text(summary: AdvanceDeclineSummary) -> str:
    return f"Advances: {summary.advances}, Declines: {summary.declines}, Unchanged: {summary.unchanged}, A/D Ratio: {summary.advance_decline_ratio}"

def format_participation_text(summary: ParticipationSummary) -> str:
    return f"Participation Score: {summary.participation_score}, >20MA: {summary.above_ma_20_pct}%, >50MA: {summary.above_ma_50_pct}%, >200MA: {summary.above_ma_200_pct}%"

def format_sector_breadth_text(summaries: list[SectorBreadthSummary]) -> str:
    res = []
    for s in summaries:
        res.append(f"{s.sector}: Score {s.sector_breadth_score}, AD {s.advance_percent}%")
    return "\n".join(res)

def format_breadth_regime_text(snapshot: BreadthRegimeSnapshot) -> str:
    return f"Regime: {snapshot.label.value}, Score: {snapshot.breadth_score}, Status: {snapshot.status.value}"

def format_breadth_report_markdown(report: BreadthReport) -> str:
    lines = [
        f"# Breadth Report - {report.scope_name}",
        f"Generated At: {report.generated_at}",
        f"\n**Disclaimer**: {report.disclaimer}\n"
    ]
    if report.regime:
        lines.append("## Regime")
        lines.append(format_breadth_regime_text(report.regime))
    if report.advance_decline:
        lines.append("\n## Advance/Decline")
        lines.append(format_advance_decline_text(report.advance_decline))
    if report.participation:
        lines.append("\n## Participation")
        lines.append(format_participation_text(report.participation))
    if report.sector_breadth:
        lines.append("\n## Sector Breadth")
        lines.append(format_sector_breadth_text(report.sector_breadth))
    if report.divergences:
        lines.append("\n## Divergences")
        for d in report.divergences:
            lines.append(f"- {d.divergence_type.value}: {d.message}")

    return "\n".join(lines)
