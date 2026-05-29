import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import (
    ContextLayerSummary, ContextConflict, EvidenceGap, ContextLayer,
    CompositeResearchScore, ContextStatus, ContextDirection, ContextImportance
)

class CompositeResearchScorer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def score(self, layer_summaries: List[ContextLayerSummary], conflicts: Optional[List[ContextConflict]] = None, gaps: Optional[List[EvidenceGap]] = None, weights: Optional[Dict[ContextLayer, float]] = None) -> CompositeResearchScore:
        conflicts = conflicts or []
        gaps = gaps or []
        weights = weights or {}

        symbol = layer_summaries[0].symbol if layer_summaries else None
        strategy_name = layer_summaries[0].strategy_name if layer_summaries else None

        b_score = self.base_score(layer_summaries, weights)
        adj_score, conflict_pen = self.apply_conflict_penalty(b_score, conflicts)
        adj_score, gap_pen = self.apply_gap_penalty(adj_score, gaps)

        contributors = self.positive_negative_contributors(layer_summaries)

        status = self.final_status(adj_score, conflicts, gaps)

        return CompositeResearchScore(
            score_id=str(uuid.uuid4()),
            symbol=symbol,
            strategy_name=strategy_name,
            as_of=datetime.now(timezone.utc),
            base_score=b_score,
            adjusted_score=adj_score,
            layer_scores={s.layer.value: s.layer_score for s in layer_summaries},
            layer_weights={k.value: v for k, v in weights.items()},
            positive_contributors=contributors["positive"],
            negative_contributors=contributors["negative"],
            conflict_penalty=conflict_pen,
            evidence_gap_penalty=gap_pen,
            final_status=status
        )

    def base_score(self, layer_summaries: List[ContextLayerSummary], weights: Dict[ContextLayer, float]) -> Optional[float]:
        total_score = 0.0
        total_weight = 0.0

        for s in layer_summaries:
            w = weights.get(s.layer, 0.0)
            if s.layer_score is not None and w > 0:
                total_score += s.layer_score * w
                total_weight += w

        if total_weight <= 0:
            return None

        return max(0.0, min(100.0, total_score / total_weight))

    def apply_conflict_penalty(self, score: Optional[float], conflicts: List[ContextConflict]) -> Tuple[Optional[float], Optional[float]]:
        if score is None:
            return None, None

        penalty = sum(c.score_impact or 0.0 for c in conflicts)
        adj = max(0.0, score - penalty)
        return adj, penalty

    def apply_gap_penalty(self, score: Optional[float], gaps: List[EvidenceGap]) -> Tuple[Optional[float], Optional[float]]:
        if score is None:
            return None, None

        penalty = 0.0
        for g in gaps:
            if g.severity == ContextImportance.LOW:
                penalty += getattr(self.settings, "CONTEXT_EVIDENCE_GAP_PENALTY_LOW", 1.0)
            elif g.severity == ContextImportance.MEDIUM:
                penalty += getattr(self.settings, "CONTEXT_EVIDENCE_GAP_PENALTY_MEDIUM", 3.0)
            elif g.severity in [ContextImportance.HIGH, ContextImportance.CRITICAL]:
                penalty += getattr(self.settings, "CONTEXT_EVIDENCE_GAP_PENALTY_HIGH", 6.0)

        adj = max(0.0, score - penalty)
        return adj, penalty

    def positive_negative_contributors(self, layer_summaries: List[ContextLayerSummary]) -> Dict[str, List[str]]:
        pos = []
        neg = []
        for s in layer_summaries:
            if s.dominant_direction == ContextDirection.SUPPORTIVE:
                pos.append(s.layer.value)
            elif s.dominant_direction in [ContextDirection.NEGATIVE, ContextDirection.BLOCKING_RESEARCH]:
                neg.append(s.layer.value)
        return {"positive": pos, "negative": neg}

    def final_status(self, score: Optional[float], conflicts: List[ContextConflict], gaps: List[EvidenceGap]) -> ContextStatus:
        if score is None:
            return ContextStatus.INSUFFICIENT_DATA

        has_critical_conflict = any(c.severity == ContextImportance.CRITICAL for c in conflicts)
        if has_critical_conflict:
            return ContextStatus.CONFLICTED

        strong_th = getattr(self.settings, "CONTEXT_STRONG_SUPPORT_THRESHOLD", 75.0)
        pressure_th = getattr(self.settings, "CONTEXT_PRESSURE_THRESHOLD", 40.0)

        if score >= strong_th:
            return ContextStatus.STRONG_SUPPORT
        elif score > 50.0:
            return ContextStatus.SUPPORT
        elif score >= pressure_th:
            return ContextStatus.NEUTRAL
        elif score > 20.0:
            return ContextStatus.PRESSURE
        else:
            return ContextStatus.HIGH_PRESSURE
