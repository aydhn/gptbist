from typing import Any
import pandas as pd
from bist_signal_bot.ensemble.models import ConsensusSignal, EnsembleResult, SignalVote, EnsembleConflict, EnsembleExplanation

def consensus_signal_to_dict(signal: ConsensusSignal) -> dict[str, Any]:
    return signal.model_dump(mode='json')

def ensemble_result_to_dict(result: EnsembleResult) -> dict[str, Any]:
    d = result.model_dump(mode='json')
    d["summary"] = result.summary()
    return d

def votes_to_dataframe(votes: list[SignalVote]) -> pd.DataFrame:
    if not votes:
        return pd.DataFrame()
    data = [v.model_dump() for v in votes]
    return pd.DataFrame(data)

def consensus_to_dataframe(signals: list[ConsensusSignal]) -> pd.DataFrame:
    if not signals:
        return pd.DataFrame()
    data = [s.summary() for s in signals]
    return pd.DataFrame(data)

def conflicts_to_dataframe(conflicts: list[EnsembleConflict]) -> pd.DataFrame:
    if not conflicts:
        return pd.DataFrame()
    data = [c.model_dump() for c in conflicts]
    return pd.DataFrame(data)

def format_consensus_signal_text(signal: ConsensusSignal) -> str:
    lines = [
        f"Consensus for {signal.symbol} (Score: {signal.consensus_score:.1f})",
        f"Decision: {signal.decision.value} | Direction: {signal.direction.value}",
        f"Confidence: {signal.confidence:.1f} | Agreement: {signal.agreement_ratio:.1%}",
        f"Conflict Score: {signal.conflict_score:.1f}"
    ]
    if signal.explanation:
        lines.append("\nExplanation:")
        lines.append(format_explanation_text(signal.explanation))
    if signal.warnings:
        lines.append("\nWarnings:")
        for w in signal.warnings:
            lines.append(f" - {w}")
    lines.append(f"\n{signal.disclaimer}")
    return "\n".join(lines)

def format_ensemble_result_text(result: EnsembleResult) -> str:
    lines = [
        "=== Ensemble Result ===",
        f"Mode: {result.request.mode.value}",
        f"Symbols processed: {len(result.request.symbols)}",
        f"Consensus generated: {len(result.consensus_signals)}",
        f"Elapsed: {result.elapsed_seconds:.2f}s"
    ]

    if result.ranked_signals:
        lines.append("\nTop Candidates:")
        for i, sig in enumerate(result.ranked_signals[:5], 1):
            lines.append(f"{i}. {sig.symbol} - {sig.decision.value} (Score: {sig.consensus_score:.1f}, Conf: {sig.confidence:.1f})")

    if result.warnings:
        lines.append("\nWarnings:")
        for w in result.warnings:
            lines.append(f" - {w}")

    lines.append(f"\n{result.disclaimer}")
    return "\n".join(lines)

def format_ensemble_report_markdown(result: EnsembleResult) -> str:
    lines = [
        "# Ensemble Analysis Report",
        f"**Mode:** {result.request.mode.value}  ",
        f"**Symbols Processed:** {len(result.request.symbols)}  ",
        f"**Date:** {result.request.as_of_date or 'Now'}",
        "\n## Summary",
        f"- Consensus count: {len(result.consensus_signals)}",
        f"- Rejected count: {len(result.rejected_signals)}",
        f"- Elapsed time: {result.elapsed_seconds:.2f}s",
        "\n## Top Ranked Signals"
    ]

    for s in result.ranked_signals:
        lines.append(f"### {s.symbol} - {s.decision.value}")
        lines.append(f"- **Score:** {s.consensus_score:.1f}")
        lines.append(f"- **Confidence:** {s.confidence:.1f}")
        lines.append(f"- **Agreement:** {s.agreement_ratio:.1%}")
        lines.append(f"- **Conflict Score:** {s.conflict_score:.1f}")
        if s.explanation:
            lines.append("\n#### Factors")
            for p in s.explanation.positive_factors:
                lines.append(f"  - (+) {p}")
            for n in s.explanation.negative_factors:
                lines.append(f"  - (-) {n}")
        lines.append("\n---\n")

    lines.append(f"\n_Disclaimer: {result.disclaimer}_")
    return "\n".join(lines)

def format_explanation_text(explanation: EnsembleExplanation) -> str:
    lines = [f"Headline: {explanation.headline}"]
    if explanation.positive_factors:
        lines.append("Positive:")
        for p in explanation.positive_factors:
            lines.append(f"  + {p}")
    if explanation.negative_factors:
        lines.append("Negative:")
        for n in explanation.negative_factors:
            lines.append(f"  - {n}")
    if explanation.conflicts:
        lines.append("Conflicts:")
        for c in explanation.conflicts:
            lines.append(f"  ! {c}")
    return "\n".join(lines)
