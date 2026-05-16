from typing import Any
from bist_signal_bot.adaptive.models import (
    AdaptivePolicy,
    AdaptiveStrategyCandidate,
    AdaptiveEvidence,
    AdaptiveEvidenceType,
    AdaptiveConfidenceLevel,
    AdaptiveDecisionStatus
)

class AdaptiveScorer:
    def score_candidate(self, candidate: AdaptiveStrategyCandidate, policy: AdaptivePolicy) -> AdaptiveStrategyCandidate:
        if not candidate.evidence_items:
            candidate.status = AdaptiveDecisionStatus.INSUFFICIENT_EVIDENCE
            candidate.reasons.append("No evidence found")
            return candidate

        if len(candidate.evidence_items) < policy.min_evidence_count:
            candidate.status = AdaptiveDecisionStatus.INSUFFICIENT_EVIDENCE
            candidate.reasons.append(f"Insufficient evidence count ({len(candidate.evidence_items)} < {policy.min_evidence_count})")

        evidence_by_type = {}
        for ev in candidate.evidence_items:
            if ev.evidence_type not in evidence_by_type:
                evidence_by_type[ev.evidence_type] = []
            evidence_by_type[ev.evidence_type].append(ev)

        weights = {
            AdaptiveEvidenceType.WALK_FORWARD: 0.25,
            AdaptiveEvidenceType.BACKTEST: 0.20,
            AdaptiveEvidenceType.OPTIMIZATION: 0.15,
            AdaptiveEvidenceType.PAPER_TRADING: 0.15,
            AdaptiveEvidenceType.SCANNER_HISTORY: 0.10,
            AdaptiveEvidenceType.REGIME: 0.10,
            AdaptiveEvidenceType.RUNTIME_PERFORMANCE: 0.05
        }

        total_weight = 0.0
        composite_score = 0.0

        for ev_type, weight in weights.items():
            items = evidence_by_type.get(ev_type, [])
            if items:
                avg_score = sum(self.score_evidence(ev, policy) for ev in items) / len(items)
                composite_score += avg_score * weight
                total_weight += weight

        if total_weight > 0:
            candidate.composite_score = composite_score / total_weight
        else:
            candidate.composite_score = sum(ev.score for ev in candidate.evidence_items if ev.score is not None) / len(candidate.evidence_items)

        candidate.confidence = self.confidence_from_evidence(candidate.evidence_items)

        return self.apply_policy_filters(candidate, policy)

    def score_evidence(self, evidence: AdaptiveEvidence, policy: AdaptivePolicy) -> float:
        return evidence.score if evidence.score is not None else 50.0

    def confidence_from_evidence(self, evidence_items: list[AdaptiveEvidence]) -> AdaptiveConfidenceLevel:
        if not evidence_items:
            return AdaptiveConfidenceLevel.UNKNOWN

        avg_conf = sum(ev.confidence for ev in evidence_items if ev.confidence is not None)
        count = sum(1 for ev in evidence_items if ev.confidence is not None)

        if count == 0:
            if len(evidence_items) > 10: return AdaptiveConfidenceLevel.HIGH
            if len(evidence_items) > 3: return AdaptiveConfidenceLevel.MEDIUM
            return AdaptiveConfidenceLevel.LOW

        avg = avg_conf / count
        types = set(ev.evidence_type for ev in evidence_items)
        if len(types) >= 4:
            avg += 10.0

        if avg >= 75.0: return AdaptiveConfidenceLevel.HIGH
        if avg >= 40.0: return AdaptiveConfidenceLevel.MEDIUM
        return AdaptiveConfidenceLevel.LOW

    def apply_policy_filters(self, candidate: AdaptiveStrategyCandidate, policy: AdaptivePolicy) -> AdaptiveStrategyCandidate:
        if candidate.status == AdaptiveDecisionStatus.INSUFFICIENT_EVIDENCE:
            return candidate

        for ev in candidate.evidence_items:
            metrics = ev.metrics
            dd = metrics.get("max_drawdown_pct", 0)
            if dd > policy.max_allowed_drawdown_pct:
                candidate.status = AdaptiveDecisionStatus.REJECTED
                candidate.reasons.append(f"Max drawdown ({dd}%) exceeds limit ({policy.max_allowed_drawdown_pct}%)")
                return candidate

            pf = metrics.get("profit_factor", 1.0)
            if pf < policy.min_profit_factor:
                candidate.status = AdaptiveDecisionStatus.WATCH_ONLY
                candidate.reasons.append(f"Profit factor ({pf}) below limit ({policy.min_profit_factor})")
                return candidate

            if policy.reject_high_overfit_warning and "HIGH_OVERFIT_RISK" in ev.warnings:
                candidate.status = AdaptiveDecisionStatus.REJECTED
                candidate.reasons.append("High overfit risk detected")
                return candidate

        if candidate.status == AdaptiveDecisionStatus.SKIPPED:
            candidate.status = AdaptiveDecisionStatus.APPROVED_RESEARCH

        return candidate

    def normalize_score(self, value: float, min_value: float, max_value: float, inverse: bool = False) -> float:
        if max_value <= min_value:
            return 50.0
        clamped = max(min_value, min(max_value, value))
        norm = (clamped - min_value) / (max_value - min_value) * 100.0
        if inverse:
            return 100.0 - norm
        return norm
