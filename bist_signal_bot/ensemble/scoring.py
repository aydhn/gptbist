from datetime import datetime
import uuid
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.ensemble.models import (
    ConsensusSignal, SignalVote, EnsembleWeights, EnsembleMode,
    SignalVoteDirection, EnsembleDecision, EnsembleConflict, SignalSourceType
)
from bist_signal_bot.ensemble.conflicts import ConflictResolver
from bist_signal_bot.ensemble.explainability import EnsembleExplainer

class EnsembleScorer:
    def __init__(self, settings: Settings | None = None, resolver: ConflictResolver | None = None, explainer: EnsembleExplainer | None = None):
        self.settings = settings or get_settings()
        self.resolver = resolver or ConflictResolver()
        self.explainer = explainer or EnsembleExplainer()

    def score_consensus(
        self,
        symbol: str,
        votes: list[SignalVote],
        weights: EnsembleWeights,
        mode: EnsembleMode,
        as_of_date: datetime
    ) -> ConsensusSignal:

        norm_weights = weights.normalized()
        w_map = norm_weights.to_source_weight_map()

        for v in votes:
            v.weight = w_map.get(v.source_type, 0.0)

        score, breakdown = self.weighted_score(votes)
        conf = self.weighted_confidence(votes)
        agr = self.agreement_ratio(votes)
        dr = self.direction_from_votes(votes)

        conflicts = self.resolver.detect_conflicts(symbol, votes)
        c_score = self.resolver.conflict_score(conflicts)
        c_rec = self.resolver.recommended_action(conflicts)

        decision = self.decision_from_score(score, conf, agr, c_score, c_rec, mode)

        expl = self.explainer.explain(
            symbol=symbol,
            votes=votes,
            conflicts=conflicts,
            score_breakdown=breakdown,
            decision=decision,
            confidence=conf,
            score=score
        )

        warnings = [c.message for c in conflicts if c.severity in ("HIGH", "CRITICAL")]
        for v in votes:
            warnings.extend(v.warnings)

        if decision in (EnsembleDecision.REJECTED, EnsembleDecision.SKIPPED):
            final_dir = SignalVoteDirection.REJECT
        elif decision in (EnsembleDecision.WATCH_ONLY, EnsembleDecision.CONFLICTED):
            final_dir = SignalVoteDirection.WATCH if dr == SignalVoteDirection.UNKNOWN else dr
        else:
            final_dir = dr

        return ConsensusSignal(
            consensus_id=str(uuid.uuid4()),
            symbol=symbol,
            as_of_date=as_of_date,
            mode=mode,
            decision=decision,
            direction=final_dir,
            consensus_score=score,
            confidence=conf,
            agreement_ratio=agr,
            conflict_score=c_score,
            votes=votes,
            conflicts=conflicts,
            explanation=expl,
            warnings=list(set(warnings))
        )

    def weighted_score(self, votes: list[SignalVote]) -> tuple[float, dict[str, float]]:
        total_weight = 0.0
        weighted_sum = 0.0
        breakdown = {}

        for v in votes:
            if v.weight > 0:
                s = v.score if v.score is not None else 50.0
                if v.direction == SignalVoteDirection.SHORT_BIAS:
                    s = 100.0 - s
                elif v.direction == SignalVoteDirection.REJECT:
                    s = 0.0

                total_weight += v.weight
                val = s * v.weight
                weighted_sum += val
                breakdown[v.source_name] = s

        final = (weighted_sum / total_weight) if total_weight > 0 else 50.0
        return final, breakdown

    def weighted_confidence(self, votes: list[SignalVote]) -> float:
        total_weight = 0.0
        weighted_sum = 0.0

        for v in votes:
            if v.weight > 0:
                c = v.confidence if v.confidence is not None else 50.0
                total_weight += v.weight
                weighted_sum += c * v.weight

        return (weighted_sum / total_weight) if total_weight > 0 else 0.0

    def agreement_ratio(self, votes: list[SignalVote]) -> float:
        active = [v for v in votes if v.weight > 0]
        if not active: return 0.0

        dirs = [v.direction for v in active]
        if not dirs: return 0.0

        from collections import Counter
        c = Counter(dirs)
        most_common = c.most_common(1)[0][1]
        return most_common / len(dirs)

    def direction_from_votes(self, votes: list[SignalVote]) -> SignalVoteDirection:
        active = [v for v in votes if v.weight > 0]
        if not active: return SignalVoteDirection.UNKNOWN

        longs = sum(v.weight for v in active if v.direction == SignalVoteDirection.LONG_BIAS)
        shorts = sum(v.weight for v in active if v.direction == SignalVoteDirection.SHORT_BIAS)
        rejects = sum(v.weight for v in active if v.direction == SignalVoteDirection.REJECT)

        if rejects > 0 and rejects > (longs + shorts) * 0.5:
            return SignalVoteDirection.REJECT

        if longs > shorts * 1.5:
            return SignalVoteDirection.LONG_BIAS
        elif shorts > longs * 1.5:
            return SignalVoteDirection.SHORT_BIAS
        else:
            return SignalVoteDirection.NEUTRAL

    def decision_from_score(
        self,
        score: float,
        confidence: float,
        agreement_ratio: float,
        conflict_score: float,
        conflict_rec: EnsembleDecision,
        mode: EnsembleMode
    ) -> EnsembleDecision:

        if conflict_rec == EnsembleDecision.REJECTED:
            return EnsembleDecision.REJECTED

        if agreement_ratio < getattr(self.settings, "ENSEMBLE_MIN_AGREEMENT_RATIO", 0.60):
            return EnsembleDecision.INSUFFICIENT_AGREEMENT

        if conflict_score > getattr(self.settings, "ENSEMBLE_HIGH_CONFLICT_SCORE", 60.0):
            return EnsembleDecision.CONFLICTED

        if (score >= getattr(self.settings, "ENSEMBLE_MIN_APPROVED_SCORE", 70.0) and
            confidence >= getattr(self.settings, "ENSEMBLE_MIN_APPROVED_CONFIDENCE", 55.0) and
            conflict_score <= getattr(self.settings, "ENSEMBLE_MAX_CONFLICT_SCORE", 35.0) and
            conflict_rec not in (EnsembleDecision.REDUCE_CONFIDENCE, EnsembleDecision.WATCH_ONLY)):
            return EnsembleDecision.APPROVED_RESEARCH

        if score >= 55.0 or conflict_rec == EnsembleDecision.WATCH_ONLY:
            return EnsembleDecision.WATCH_ONLY

        return EnsembleDecision.REJECTED

    def rank_consensus(self, signals: list[ConsensusSignal]) -> list[ConsensusSignal]:
        def priority(d: EnsembleDecision):
            p = {
                EnsembleDecision.APPROVED_RESEARCH: 0,
                EnsembleDecision.WATCH_ONLY: 1,
                EnsembleDecision.REDUCE_CONFIDENCE: 2,
                EnsembleDecision.CONFLICTED: 3,
                EnsembleDecision.INSUFFICIENT_AGREEMENT: 4,
                EnsembleDecision.REJECTED: 5,
                EnsembleDecision.SKIPPED: 6,
                EnsembleDecision.ERROR: 7
            }
            return p.get(d, 99)

        return sorted(signals, key=lambda s: (
            priority(s.decision),
            -s.consensus_score,
            -s.confidence,
            -s.agreement_ratio,
            s.conflict_score,
            s.symbol
        ))
