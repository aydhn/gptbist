import json
from typing import Any
from bist_signal_bot.explainability.models import (
    FeatureContribution, IndicatorExplanation, StrategyRuleTrace,
    MLExplanation, EnsembleExplanation, RiskExplanation,
    ExecutionExplanation, HistoryContextExplanation, SignalExplanation,
    EvidenceCard, DecisionTrace
)

def feature_contribution_to_dict(contribution: FeatureContribution) -> dict[str, Any]:
    return contribution.model_dump()

def indicator_explanation_to_dict(explanation: IndicatorExplanation) -> dict[str, Any]:
    return explanation.model_dump()

def rule_trace_to_dict(trace: StrategyRuleTrace) -> dict[str, Any]:
    return trace.model_dump()

def ml_explanation_to_dict(explanation: MLExplanation) -> dict[str, Any]:
    return explanation.model_dump()

def ensemble_explanation_to_dict(explanation: EnsembleExplanation) -> dict[str, Any]:
    return explanation.model_dump()

def risk_explanation_to_dict(explanation: RiskExplanation) -> dict[str, Any]:
    return explanation.model_dump()

def execution_explanation_to_dict(explanation: ExecutionExplanation) -> dict[str, Any]:
    return explanation.model_dump()

def history_context_to_dict(explanation: HistoryContextExplanation) -> dict[str, Any]:
    return explanation.model_dump()

def signal_explanation_to_dict(explanation: SignalExplanation) -> dict[str, Any]:
    return explanation.model_dump()

def evidence_card_to_dict(card: EvidenceCard) -> dict[str, Any]:
    return card.model_dump()

def decision_trace_to_dict(trace: DecisionTrace) -> dict[str, Any]:
    return trace.model_dump()

def format_signal_explanation_text(explanation: SignalExplanation) -> str:
    lines = [
        f"Signal Explanation: {explanation.symbol} ({explanation.strategy_name or 'N/A'})",
        f"Summary: {explanation.summary}",
        f"Status: {explanation.final_status}",
        f"Disclaimer: {explanation.disclaimer}"
    ]
    return "\n".join(lines)

def format_evidence_card_text(card: EvidenceCard) -> str:
    lines = [
        f"Evidence Card: {card.symbol}",
        f"Summary: {card.summary}",
        f"Status: {card.overall_status}",
    ]
    for section in card.sections:
        lines.append(f"\n--- {section.title} ---")
        lines.append(section.body)
    lines.append(f"\nDisclaimer: {card.disclaimer}")
    return "\n".join(lines)

def format_evidence_card_markdown(card: EvidenceCard) -> str:
    lines = [
        f"# Evidence Card: {card.symbol}",
        f"**Strategy**: {card.strategy_name or 'N/A'}",
        f"**Summary**: {card.summary}",
        f"**Status**: {card.overall_status}",
        ""
    ]
    for section in card.sections:
        lines.append(f"## {section.title}")
        lines.append(section.body)
        lines.append("")
    lines.append(f"_{card.disclaimer}_")
    return "\n".join(lines)

def format_decision_trace_text(trace: DecisionTrace) -> str:
    lines = [
        f"Decision Trace: {trace.symbol}",
        f"Final Decision: {trace.final_decision}"
    ]
    for i, stage in enumerate(trace.stages, 1):
        lines.append(f"{i}. {stage['name']}: {stage['status']} - {stage.get('message', '')}")
    lines.append(f"\nDisclaimer: {trace.disclaimer}")
    return "\n".join(lines)

def format_explainability_report_markdown(cards: list[EvidenceCard], traces: list[DecisionTrace]) -> str:
    lines = ["# Explainability Report\n"]
    lines.append("## Evidence Cards\n")
    for card in cards:
        lines.append(format_evidence_card_markdown(card))
        lines.append("\n---\n")
    lines.append("## Decision Traces\n")
    for trace in traces:
        lines.append(format_decision_trace_text(trace))
        lines.append("\n---\n")
    lines.append("_This report is research-only. It is not investment advice or permission for real orders. No real order was sent._")
    return "\n".join(lines)
