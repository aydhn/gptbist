import pandas as pd
from typing import Any

from bist_signal_bot.adaptive.models import (
    AdaptiveRecommendation,
    AdaptiveStrategyCandidate,
    AdaptiveRefreshPlan,
    ModelRefreshRecommendation
)

def adaptive_recommendation_to_dict(result: AdaptiveRecommendation) -> dict[str, Any]:
    return result.safe_public_dict()

def adaptive_candidates_to_dataframe(candidates: list[AdaptiveStrategyCandidate]) -> pd.DataFrame:
    if not candidates:
        return pd.DataFrame()
    records = []
    for c in candidates:
        records.append({
            "symbol": c.symbol,
            "strategy": c.strategy_name,
            "status": c.status.value,
            "score": round(c.composite_score, 2),
            "confidence": c.confidence.value,
            "evidence_count": len(c.evidence_items),
            "reasons": "; ".join(c.reasons),
            "warnings": "; ".join(c.warnings)
        })
    return pd.DataFrame(records)

def refresh_plan_to_dataframe(plan: AdaptiveRefreshPlan) -> pd.DataFrame:
    if not plan or not plan.items:
        return pd.DataFrame()
    records = []
    for item in plan.items:
        records.append({
            "action": item.action.value,
            "symbol": item.symbol,
            "strategy": item.strategy_name,
            "reason": item.reason,
            "priority": item.priority,
            "requires_confirm": item.requires_confirm,
            "command": " ".join(item.command_preview)
        })
    return pd.DataFrame(records)

def model_refresh_to_dataframe(items: list[ModelRefreshRecommendation]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame()
    records = []
    for item in items:
        records.append({
            "model_id": item.model_id,
            "model_type": item.model_type,
            "should_retrain": item.should_retrain,
            "reason": item.reason,
            "age_days": round(item.model_age_days, 1) if item.model_age_days else None,
            "drift_score": round(item.drift_score, 2) if item.drift_score else None,
            "command": " ".join(item.recommended_command) if item.recommended_command else None
        })
    return pd.DataFrame(records)

def format_adaptive_recommendation_text(result: AdaptiveRecommendation) -> str:
    lines = [
        f"Adaptive Recommendation ID: {result.recommendation_id}",
        f"Status: {result.status.value} | Mode: {result.mode.value}",
        f"Generated At: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "-" * 40,
        f"Candidates Processed: {len(result.candidates)}",
        f"Candidates Selected: {len(result.selected_candidates)}"
    ]
    if result.selected_candidates:
        lines.append("Top Candidates:")
        for i, c in enumerate(result.selected_candidates[:5], 1):
            lines.append(f"  {i}. {c.symbol} | {c.strategy_name} | Score: {c.composite_score:.1f} | Conf: {c.confidence.value}")
    if result.refresh_plan and result.refresh_plan.items:
        lines.append("-" * 40)
        lines.append(f"Refresh Actions Recommended: {len(result.refresh_plan.items)}")
        for item in result.refresh_plan.items[:3]:
            lines.append(f"  - {item.action.value} for {item.symbol or 'ALL'} | {item.reason}")
    lines.append("-" * 40)
    lines.append(result.disclaimer)
    return "\n".join(lines)

def format_adaptive_report_markdown(result: AdaptiveRecommendation) -> str:
    md = [
        "# Adaptive Research Recommendation",
        f"**ID:** `{result.recommendation_id}`",
        f"**Status:** `{result.status.value}`",
        f"**Mode:** `{result.mode.value}`",
        f"**Generated At:** {result.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "> **Disclaimer:** " + result.disclaimer,
        "",
        "## Summary",
        f"- Total Candidates Processed: {len(result.candidates)}",
        f"- Candidates Selected: {len(result.selected_candidates)}",
        ""
    ]
    if result.selected_candidates:
        md.append("## Top Candidates")
        md.append("| Symbol | Strategy | Score | Confidence | Status |")
        md.append("|---|---|---|---|---|")
        for c in result.selected_candidates:
            md.append(f"| {c.symbol} | {c.strategy_name} | {c.composite_score:.1f} | {c.confidence.value} | {c.status.value} |")
        md.append("")
    if result.refresh_plan and result.refresh_plan.items:
        md.append("## Refresh Plan")
        md.append("| Action | Target | Reason | Command |")
        md.append("|---|---|---|---|")
        for item in result.refresh_plan.items:
            target = f"{item.symbol or 'ALL'} / {item.strategy_name or 'ALL'}"
            cmd = f"`{' '.join(item.command_preview)}`" if item.command_preview else ""
            md.append(f"| {item.action.value} | {target} | {item.reason} | {cmd} |")
        md.append("")
    if result.model_refresh_recommendations:
        md.append("## Model Refresh Recommendations")
        md.append("| Model ID | Action | Reason | Age (Days) | Command |")
        md.append("|---|---|---|---|---|")
        for m in result.model_refresh_recommendations:
            action = "RETRAIN" if m.should_retrain else "KEEP"
            age = f"{m.model_age_days:.1f}" if m.model_age_days else "-"
            cmd = f"`{' '.join(m.recommended_command)}`" if m.recommended_command else ""
            md.append(f"| {m.model_id or '-'} | {action} | {m.reason} | {age} | {cmd} |")
        md.append("")
    return "\n".join(md)

def format_refresh_plan_text(plan: AdaptiveRefreshPlan) -> str:
    lines = [
        f"Adaptive Refresh Plan ID: {plan.plan_id}",
        f"Status: {plan.status.value}",
        "-" * 40
    ]
    for i, item in enumerate(plan.items, 1):
        lines.append(f"{i}. Action: {item.action.value}")
        lines.append(f"   Target: {item.symbol or 'ALL'} / {item.strategy_name or 'ALL'}")
        lines.append(f"   Reason: {item.reason}")
        if item.command_preview:
            lines.append(f"   Command: {' '.join(item.command_preview)}")
        lines.append("")
    lines.append(plan.disclaimer)
    return "\n".join(lines)
