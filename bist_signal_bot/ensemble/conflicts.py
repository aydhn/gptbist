from typing import Optional
from bist_signal_bot.ensemble.models import EnsembleConflict, SignalVote, ConflictType, EnsembleDecision, SignalVoteDirection, SignalSourceType
import uuid

class ConflictResolver:
    def detect_conflicts(self, symbol: str, votes: list[SignalVote]) -> list[EnsembleConflict]:
        conflicts = []

        dir_conflict = self.directional_conflict(symbol, votes)
        if dir_conflict: conflicts.append(dir_conflict)

        ml_tech = self.ml_technical_conflict(symbol, votes)
        if ml_tech: conflicts.append(ml_tech)

        fund_tech = self.fundamental_technical_conflict(symbol, votes)
        if fund_tech: conflicts.append(fund_tech)

        breadth = self.breadth_signal_conflict(symbol, votes)
        if breadth: conflicts.append(breadth)

        risk = self.risk_conflict(symbol, votes)
        if risk: conflicts.append(risk)

        data_qual = self.data_quality_conflict(symbol, votes)
        if data_qual: conflicts.append(data_qual)

        return conflicts

    def _create_conflict(self, symbol: str, type: ConflictType, severity: str, message: str, votes: list[SignalVote], rec: EnsembleDecision) -> EnsembleConflict:
        return EnsembleConflict(
            conflict_id=str(uuid.uuid4())[:8],
            conflict_type=type,
            symbol=symbol,
            severity=severity,
            message=message,
            involved_votes=[v.vote_id for v in votes],
            recommended_action=rec
        )

    def directional_conflict(self, symbol: str, votes: list[SignalVote]) -> Optional[EnsembleConflict]:
        longs = [v for v in votes if v.direction == SignalVoteDirection.LONG_BIAS and v.weight > 0]
        shorts = [v for v in votes if v.direction == SignalVoteDirection.SHORT_BIAS and v.weight > 0]

        if longs and shorts:
            return self._create_conflict(
                symbol,
                ConflictType.DIRECTIONAL_CONFLICT,
                "MEDIUM",
                f"Directional conflict: {len(longs)} LONG vs {len(shorts)} SHORT biases.",
                longs + shorts,
                EnsembleDecision.REDUCE_CONFIDENCE
            )
        return None

    def ml_technical_conflict(self, symbol: str, votes: list[SignalVote]) -> Optional[EnsembleConflict]:
        mls = [v for v in votes if v.source_type == SignalSourceType.ML and v.weight > 0]
        techs = [v for v in votes if v.source_type in (SignalSourceType.STRATEGY, SignalSourceType.INDICATOR, SignalSourceType.PATTERN) and v.weight > 0]

        if mls and techs:
            ml_vote = mls[0]
            for t in techs:
                if ml_vote.direction != SignalVoteDirection.NEUTRAL and t.direction != SignalVoteDirection.NEUTRAL:
                    if ml_vote.direction != t.direction:
                        return self._create_conflict(
                            symbol,
                            ConflictType.ML_TECHNICAL_CONFLICT,
                            "HIGH",
                            f"ML prediction ({ml_vote.direction.value}) conflicts with Technical signal ({t.direction.value}).",
                            [ml_vote, t],
                            EnsembleDecision.CONFLICTED
                        )
        return None

    def fundamental_technical_conflict(self, symbol: str, votes: list[SignalVote]) -> Optional[EnsembleConflict]:
        funds = [v for v in votes if v.source_type == SignalSourceType.FUNDAMENTAL and v.weight > 0]
        techs = [v for v in votes if v.source_type in (SignalSourceType.STRATEGY, SignalSourceType.INDICATOR) and v.weight > 0]

        if funds and techs:
            fund = funds[0]
            for t in techs:
                if fund.direction == SignalVoteDirection.SHORT_BIAS and t.direction == SignalVoteDirection.LONG_BIAS:
                    return self._create_conflict(
                        symbol,
                        ConflictType.FUNDAMENTAL_TECHNICAL_CONFLICT,
                        "MEDIUM",
                        "Weak fundamentals but positive technical momentum.",
                        [fund, t],
                        EnsembleDecision.WATCH_ONLY
                    )
        return None

    def breadth_signal_conflict(self, symbol: str, votes: list[SignalVote]) -> Optional[EnsembleConflict]:
        breadths = [v for v in votes if v.source_type == SignalSourceType.BREADTH and v.weight > 0]
        techs = [v for v in votes if v.source_type == SignalSourceType.STRATEGY and v.weight > 0]

        if breadths and techs:
            b = breadths[0]
            for t in techs:
                if b.direction == SignalVoteDirection.SHORT_BIAS and t.direction == SignalVoteDirection.LONG_BIAS:
                    return self._create_conflict(
                        symbol,
                        ConflictType.BREADTH_SIGNAL_CONFLICT,
                        "MEDIUM",
                        "Negative market breadth but positive technical signal.",
                        [b, t],
                        EnsembleDecision.REDUCE_CONFIDENCE
                    )
        return None

    def risk_conflict(self, symbol: str, votes: list[SignalVote]) -> Optional[EnsembleConflict]:
        risks = [v for v in votes if v.source_type in (SignalSourceType.RISK, SignalSourceType.PORTFOLIO_RISK)]
        longs = [v for v in votes if v.direction == SignalVoteDirection.LONG_BIAS]

        for r in risks:
            if r.direction == SignalVoteDirection.REJECT and longs:
                return self._create_conflict(
                    symbol,
                    ConflictType.RISK_CONFLICT,
                    "CRITICAL",
                    "Risk engine rejected despite positive signals.",
                    [r] + longs,
                    EnsembleDecision.REJECTED
                )
        return None

    def data_quality_conflict(self, symbol: str, votes: list[SignalVote]) -> Optional[EnsembleConflict]:
        stale = [v for v in votes if any("stale" in w.lower() or "missing" in w.lower() for w in v.warnings)]
        if stale:
            return self._create_conflict(
                symbol,
                ConflictType.DATA_QUALITY_CONFLICT,
                "HIGH",
                "Data quality issues detected in components.",
                stale,
                EnsembleDecision.WATCH_ONLY
            )
        return None

    def conflict_score(self, conflicts: list[EnsembleConflict]) -> float:
        score = 0.0
        for c in conflicts:
            if c.severity == "CRITICAL":
                score += 50.0
            elif c.severity == "HIGH":
                score += 30.0
            elif c.severity == "MEDIUM":
                score += 15.0
            else:
                score += 5.0
        return min(100.0, score)

    def recommended_action(self, conflicts: list[EnsembleConflict]) -> EnsembleDecision:
        if not conflicts:
            return EnsembleDecision.APPROVED_RESEARCH

        recs = [c.recommended_action for c in conflicts]

        if EnsembleDecision.REJECTED in recs:
            return EnsembleDecision.REJECTED
        if EnsembleDecision.CONFLICTED in recs:
            return EnsembleDecision.CONFLICTED
        if EnsembleDecision.WATCH_ONLY in recs:
            return EnsembleDecision.WATCH_ONLY
        if EnsembleDecision.REDUCE_CONFIDENCE in recs:
            return EnsembleDecision.REDUCE_CONFIDENCE

        return EnsembleDecision.APPROVED_RESEARCH
