from typing import Any
from bist_signal_bot.ensemble.models import (
    EnsembleExplanation, SignalVote, EnsembleConflict, EnsembleDecision, SignalVoteDirection
)

class EnsembleExplainer:
    def explain(
        self,
        symbol: str,
        votes: list[SignalVote],
        conflicts: list[EnsembleConflict],
        score_breakdown: dict[str, float],
        decision: EnsembleDecision,
        confidence: float,
        score: float
    ) -> EnsembleExplanation:

        pos = self.build_positive_factors(votes)
        neg = self.build_negative_factors(votes)
        neu = self.build_neutral_factors(votes)
        con = self.build_conflict_notes(conflicts)
        head = self.build_headline(symbol, decision, score, confidence)

        notes = []
        if confidence < 50:
            notes.append("Low overall confidence across components.")
        if conflicts:
            notes.append(f"{len(conflicts)} conflict(s) detected affecting consensus.")

        return EnsembleExplanation(
            symbol=symbol,
            headline=head,
            positive_factors=pos,
            negative_factors=neg,
            neutral_factors=neu,
            conflicts=con,
            score_breakdown=score_breakdown,
            confidence_notes=notes
        )

    def build_positive_factors(self, votes: list[SignalVote]) -> list[str]:
        res = []
        for v in sorted(votes, key=lambda x: x.weight, reverse=True):
            if v.direction == SignalVoteDirection.LONG_BIAS and v.weight > 0:
                reasons = ", ".join(v.reasons) if v.reasons else "Positive indication"
                res.append(f"{v.source_name} ({v.source_type.value}): {reasons}")
        return res

    def build_negative_factors(self, votes: list[SignalVote]) -> list[str]:
        res = []
        for v in sorted(votes, key=lambda x: x.weight, reverse=True):
            if v.direction in (SignalVoteDirection.SHORT_BIAS, SignalVoteDirection.REJECT) and v.weight > 0:
                reasons = ", ".join(v.reasons) if v.reasons else "Negative indication"
                res.append(f"{v.source_name} ({v.source_type.value}): {reasons}")
        return res

    def build_neutral_factors(self, votes: list[SignalVote]) -> list[str]:
        res = []
        for v in sorted(votes, key=lambda x: x.weight, reverse=True):
            if v.direction in (SignalVoteDirection.NEUTRAL, SignalVoteDirection.WATCH) and v.weight > 0:
                reasons = ", ".join(v.reasons) if v.reasons else "Neutral indication"
                res.append(f"{v.source_name} ({v.source_type.value}): {reasons}")
        return res

    def build_conflict_notes(self, conflicts: list[EnsembleConflict]) -> list[str]:
        return [f"[{c.severity}] {c.message}" for c in conflicts]

    def build_headline(self, symbol: str, decision: EnsembleDecision, score: float, confidence: float) -> str:
        if decision == EnsembleDecision.APPROVED_RESEARCH:
            return f"Strong consensus for {symbol} research candidate (Score: {score:.1f}, Conf: {confidence:.1f})"
        elif decision == EnsembleDecision.WATCH_ONLY:
            return f"Moderate signals for {symbol}, watch closely (Score: {score:.1f}, Conf: {confidence:.1f})"
        elif decision == EnsembleDecision.REJECTED:
            return f"{symbol} rejected by risk or strong negative consensus."
        elif decision == EnsembleDecision.CONFLICTED:
            return f"Highly conflicted signals for {symbol}. Review components."
        else:
            return f"{symbol} outcome: {decision.value} (Score: {score:.1f})"
