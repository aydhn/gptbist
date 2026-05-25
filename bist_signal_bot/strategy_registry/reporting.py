import pandas as pd
from typing import Any
from bist_signal_bot.strategy_registry.models import (
    StrategyDefinition,
    StrategyEvidenceRef,
    StrategyScoreComponent,
    StrategyScorecard,
    StrategyLifecycleEvent,
    StrategyPromotionResult,
    StrategyRegistrySnapshot
)

def strategy_definition_to_dict(definition: StrategyDefinition) -> dict[str, Any]:
    return {
        "strategy_id": definition.strategy_id,
        "strategy_name": definition.strategy_name,
        "display_name": definition.display_name,
        "version": definition.version,
        "family": definition.family.value,
        "status": definition.status.value,
        "module_path": definition.module_path,
        "class_name": definition.class_name,
        "default_parameters": definition.default_parameters,
        "parameter_schema": definition.parameter_schema,
        "supported_timeframes": definition.supported_timeframes,
        "supported_order_sides": definition.supported_order_sides,
        "supported_universes": definition.supported_universes,
        "requires_adjusted_prices": definition.requires_adjusted_prices,
        "supports_short": definition.supports_short,
        "supports_cost_model": definition.supports_cost_model,
        "created_at": definition.created_at.isoformat(),
        "updated_at": definition.updated_at.isoformat(),
        "owner": definition.owner,
        "tags": definition.tags,
        "warnings": definition.warnings,
        "disclaimer": definition.disclaimer,
        "metadata": definition.metadata
    }

def strategy_evidence_to_dict(evidence: StrategyEvidenceRef) -> dict[str, Any]:
    return {
        "evidence_id": evidence.evidence_id,
        "strategy_id": evidence.strategy_id,
        "evidence_type": evidence.evidence_type.value,
        "source_ref": evidence.source_ref,
        "symbol": evidence.symbol,
        "created_at": evidence.created_at.isoformat(),
        "title": evidence.title,
        "summary": evidence.summary,
        "score": evidence.score,
        "status": evidence.status,
        "warnings": evidence.warnings,
        "metadata": evidence.metadata
    }

def score_component_to_dict(component: StrategyScoreComponent) -> dict[str, Any]:
    return {
        "component_id": component.component_id,
        "name": component.name,
        "evidence_type": component.evidence_type.value,
        "score": component.score,
        "weight": component.weight,
        "status": component.status.value if component.status else None,
        "message": component.message,
        "evidence_refs": component.evidence_refs,
        "warnings": component.warnings,
        "metadata": component.metadata
    }

def scorecard_to_dict(scorecard: StrategyScorecard) -> dict[str, Any]:
    return {
        "scorecard_id": scorecard.scorecard_id,
        "strategy_id": scorecard.strategy_id,
        "strategy_name": scorecard.strategy_name,
        "version": scorecard.version,
        "generated_at": scorecard.generated_at.isoformat(),
        "components": [score_component_to_dict(c) for c in scorecard.components],
        "aggregate_score": scorecard.aggregate_score,
        "confidence_score": scorecard.confidence_score,
        "robustness_score": scorecard.robustness_score,
        "overfit_risk_score": scorecard.overfit_risk_score,
        "execution_penalty_score": scorecard.execution_penalty_score,
        "drift_risk_score": scorecard.drift_risk_score,
        "status": scorecard.status.value,
        "gate_decision": scorecard.gate_decision.value,
        "recommended_actions": scorecard.recommended_actions,
        "warnings": scorecard.warnings,
        "disclaimer": scorecard.disclaimer,
        "metadata": scorecard.metadata
    }

def lifecycle_event_to_dict(event: StrategyLifecycleEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "strategy_id": event.strategy_id,
        "strategy_name": event.strategy_name,
        "event_type": event.event_type.value,
        "previous_status": event.previous_status.value if event.previous_status else None,
        "new_status": event.new_status.value if event.new_status else None,
        "created_at": event.created_at.isoformat(),
        "reason": event.reason,
        "actor": event.actor,
        "evidence_refs": event.evidence_refs,
        "warnings": event.warnings,
        "disclaimer": event.disclaimer,
        "metadata": event.metadata
    }

def promotion_result_to_dict(result: StrategyPromotionResult) -> dict[str, Any]:
    return {
        "promotion_id": result.promotion_id,
        "request": {
            "strategy_id": result.request.strategy_id,
            "target_status": result.request.target_status.value,
            "reason": result.request.reason,
            "require_scorecard": result.request.require_scorecard,
            "require_validation": result.request.require_validation,
            "require_monte_carlo": result.request.require_monte_carlo,
            "require_governance_pass": result.request.require_governance_pass,
            "confirm": result.request.confirm,
            "metadata": result.request.metadata
        },
        "decision": result.decision.value,
        "previous_status": result.previous_status.value,
        "new_status": result.new_status.value if result.new_status else None,
        "scorecard": scorecard_to_dict(result.scorecard) if result.scorecard else None,
        "event": lifecycle_event_to_dict(result.event) if result.event else None,
        "blocked_reasons": result.blocked_reasons,
        "warnings": result.warnings,
        "disclaimer": result.disclaimer,
        "metadata": result.metadata
    }

def snapshot_to_dict(snapshot: StrategyRegistrySnapshot) -> dict[str, Any]:
    return {
        "snapshot_id": snapshot.snapshot_id,
        "created_at": snapshot.created_at.isoformat(),
        "strategies_count": snapshot.strategies_count,
        "status_counts": snapshot.status_counts,
        "scorecards_count": snapshot.scorecards_count,
        "blocked_strategies": snapshot.blocked_strategies,
        "candidate_strategies": snapshot.candidate_strategies,
        "validated_research_strategies": snapshot.validated_research_strategies,
        "warnings": snapshot.warnings,
        "checksum_sha256": snapshot.checksum_sha256,
        "disclaimer": snapshot.disclaimer,
        "metadata": snapshot.metadata
    }

def strategies_to_dataframe(strategies: list[StrategyDefinition]) -> pd.DataFrame:
    if not strategies:
        return pd.DataFrame()
    data = [strategy_definition_to_dict(s) for s in strategies]
    return pd.DataFrame(data)

def scorecards_to_dataframe(scorecards: list[StrategyScorecard]) -> pd.DataFrame:
    if not scorecards:
        return pd.DataFrame()
    data = [scorecard_to_dict(s) for s in scorecards]
    return pd.DataFrame(data)

def format_strategy_definition_text(definition: StrategyDefinition) -> str:
    lines = [
        f"Strategy: {definition.display_name} ({definition.strategy_name})",
        f"ID: {definition.strategy_id}",
        f"Version: {definition.version}",
        f"Family: {definition.family.value}",
        f"Status: {definition.status.value}",
        f"Timeframes: {', '.join(definition.supported_timeframes)}",
        f"Universes: {', '.join(definition.supported_universes)}",
        f"Sides: {', '.join(definition.supported_order_sides)}",
        f"Module: {definition.module_path}.{definition.class_name}",
        f"Created At: {definition.created_at.isoformat()}"
    ]
    if definition.warnings:
        lines.append("\nWarnings:")
        for w in definition.warnings:
            lines.append(f"- {w}")
    lines.append(f"\nDisclaimer: {definition.disclaimer}")
    return "\n".join(lines)

def format_scorecard_text(scorecard: StrategyScorecard) -> str:
    lines = [
        f"Scorecard ID: {scorecard.scorecard_id}",
        f"Strategy: {scorecard.strategy_name} (v{scorecard.version})",
        f"Generated At: {scorecard.generated_at.isoformat()}",
        f"Status: {scorecard.status.value}",
        f"Gate Decision: {scorecard.gate_decision.value}",
        f"\nScores:",
        f"  Aggregate Score: {scorecard.aggregate_score if scorecard.aggregate_score is not None else 'N/A'}",
        f"  Confidence Score: {scorecard.confidence_score if scorecard.confidence_score is not None else 'N/A'}",
        f"  Robustness Score: {scorecard.robustness_score if scorecard.robustness_score is not None else 'N/A'}",
        f"  Overfit Risk Score: {scorecard.overfit_risk_score if scorecard.overfit_risk_score is not None else 'N/A'}",
        f"  Execution Penalty: {scorecard.execution_penalty_score if scorecard.execution_penalty_score is not None else 'N/A'}",
        f"  Drift Risk Score: {scorecard.drift_risk_score if scorecard.drift_risk_score is not None else 'N/A'}",
        f"\nComponents:"
    ]

    for comp in scorecard.components:
        lines.append(f"  - {comp.name}: {comp.score if comp.score is not None else 'N/A'} (Weight: {comp.weight})")
        if comp.message:
            lines.append(f"    {comp.message}")

    if scorecard.warnings:
        lines.append("\nWarnings:")
        for w in scorecard.warnings:
            lines.append(f"- {w}")

    if scorecard.recommended_actions:
        lines.append("\nRecommended Actions:")
        for a in scorecard.recommended_actions:
            lines.append(f"- {a}")

    lines.append(f"\nDisclaimer: {scorecard.disclaimer}")
    return "\n".join(lines)

def format_promotion_result_text(result: StrategyPromotionResult) -> str:
    lines = [
        f"Promotion ID: {result.promotion_id}",
        f"Target Status: {result.request.target_status.value}",
        f"Decision: {result.decision.value}",
        f"Previous Status: {result.previous_status.value}",
        f"New Status: {result.new_status.value if result.new_status else 'No change'}",
    ]

    if result.blocked_reasons:
        lines.append("\nBlocked Reasons:")
        for r in result.blocked_reasons:
            lines.append(f"- {r}")

    if result.warnings:
        lines.append("\nWarnings:")
        for w in result.warnings:
            lines.append(f"- {w}")

    lines.append(f"\nDisclaimer: {result.disclaimer}")
    return "\n".join(lines)

def format_strategy_registry_snapshot_text(snapshot: StrategyRegistrySnapshot) -> str:
    lines = [
        f"Snapshot ID: {snapshot.snapshot_id}",
        f"Created At: {snapshot.created_at.isoformat()}",
        f"Total Strategies: {snapshot.strategies_count}",
        f"Total Scorecards: {snapshot.scorecards_count}",
        f"\nStatus Counts:"
    ]

    for status, count in snapshot.status_counts.items():
        lines.append(f"  - {status}: {count}")

    if snapshot.checksum_sha256:
        lines.append(f"\nChecksum (SHA256): {snapshot.checksum_sha256}")

    lines.append(f"\nDisclaimer: {snapshot.disclaimer}")
    return "\n".join(lines)

def format_strategy_registry_report_markdown(strategies: list[StrategyDefinition], scorecards: list[StrategyScorecard]) -> str:
    lines = [
        "# Strategy Registry Report",
        "",
        "> **DISCLAIMER:** This report contains operational research metadata only. Not investment advice. No real order was sent.",
        "",
        f"**Total Strategies:** {len(strategies)}",
        f"**Total Scorecards:** {len(scorecards)}",
        "",
        "## Status Distribution"
    ]

    status_counts = {}
    for s in strategies:
        status_counts[s.status.value] = status_counts.get(s.status.value, 0) + 1

    for status, count in status_counts.items():
        lines.append(f"- **{status}:** {count}")

    lines.append("")
    lines.append("## Strategies")

    for strategy in sorted(strategies, key=lambda s: s.strategy_name):
        lines.append(f"### {strategy.display_name} ({strategy.strategy_name})")
        lines.append(f"- **Version:** {strategy.version}")
        lines.append(f"- **Family:** {strategy.family.value}")
        lines.append(f"- **Status:** {strategy.status.value}")

        # Find scorecard
        sc = next((s for s in scorecards if s.strategy_id == strategy.strategy_id), None)
        if sc:
            lines.append(f"- **Aggregate Score:** {sc.aggregate_score if sc.aggregate_score is not None else 'N/A'}")
            lines.append(f"- **Gate Decision:** {sc.gate_decision.value}")

        if strategy.warnings:
            lines.append("- **Warnings:**")
            for w in strategy.warnings:
                lines.append(f"  - {w}")

        lines.append("")

    return "\n".join(lines)
