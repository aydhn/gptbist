import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import (
    ContextSignal, ContextLayerSummary, ContextConflict, EvidenceGap,
    ResearchGraph, CompositeResearchScore, UnifiedContextSnapshot,
    ContextLayer, ContextDirection, ContextImportance
)

class UnifiedContextSnapshotBuilder:
    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings or Settings()
        from bist_signal_bot.context_fusion.normalization import ContextNormalizer
        from bist_signal_bot.context_fusion.sources import ContextSourceRegistry
        self.normalizer = ContextNormalizer(self.settings)
        self.registry = ContextSourceRegistry(self.settings)

    def build_for_signal(self, signal_payload: Dict[str, Any], signals: List[ContextSignal], conflicts: List[ContextConflict], gaps: List[EvidenceGap], score: CompositeResearchScore, graph: Optional[ResearchGraph] = None) -> UnifiedContextSnapshot:
        symbol = signal_payload.get("symbol", "UNKNOWN")
        strategy_name = signal_payload.get("strategy_name")
        signal_id = signal_payload.get("signal_id")

        summaries = self.summarize_layers(signals)
        supports = self.key_supports(summaries)
        pressures = self.key_pressures(summaries, conflicts)
        reviews = self.required_reviews(conflicts, gaps)

        warnings = []
        if not summaries:
            warnings.append("No context layers available for this signal.")

        return UnifiedContextSnapshot(
            snapshot_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            symbol=symbol,
            strategy_name=strategy_name,
            signal_id=signal_id,
            as_of=datetime.now(timezone.utc),
            layer_summaries=summaries,
            context_signals=signals,
            conflicts=conflicts,
            evidence_gaps=gaps,
            research_graph=graph,
            composite_score=score,
            key_supports=supports,
            key_pressures=pressures,
            required_reviews=reviews,
            warnings=warnings
        )

    def build_for_symbol(self, symbol: str, signals: List[ContextSignal], conflicts: List[ContextConflict], gaps: List[EvidenceGap], score: CompositeResearchScore, strategy_name: Optional[str] = None, signal_id: Optional[str] = None, graph: Optional[ResearchGraph] = None) -> UnifiedContextSnapshot:
        summaries = self.summarize_layers(signals)
        supports = self.key_supports(summaries)
        pressures = self.key_pressures(summaries, conflicts)
        reviews = self.required_reviews(conflicts, gaps)

        warnings = []
        if not summaries:
            warnings.append("No context layers available for this symbol.")

        return UnifiedContextSnapshot(
            snapshot_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            symbol=symbol,
            strategy_name=strategy_name,
            signal_id=signal_id,
            as_of=datetime.now(timezone.utc),
            layer_summaries=summaries,
            context_signals=signals,
            conflicts=conflicts,
            evidence_gaps=gaps,
            research_graph=graph,
            composite_score=score,
            key_supports=supports,
            key_pressures=pressures,
            required_reviews=reviews,
            warnings=warnings
        )

    def summarize_layers(self, signals: List[ContextSignal]) -> List[ContextLayerSummary]:
        summaries = []
        layer_map: Dict[ContextLayer, List[ContextSignal]] = {}
        for s in signals:
            layer_map.setdefault(s.layer, []).append(s)

        for layer, sigs in layer_map.items():
            summaries.append(self.normalizer.normalize_layer_summary(sigs, layer))

        return summaries

    def key_supports(self, summaries: List[ContextLayerSummary]) -> List[str]:
        return [s.layer.value for s in summaries if s.dominant_direction == ContextDirection.SUPPORTIVE]

    def key_pressures(self, summaries: List[ContextLayerSummary], conflicts: List[ContextConflict]) -> List[str]:
        pressures = [s.layer.value for s in summaries if s.dominant_direction in [ContextDirection.NEGATIVE, ContextDirection.BLOCKING_RESEARCH]]
        if any(c.severity in [ContextImportance.HIGH, ContextImportance.CRITICAL] for c in conflicts):
            pressures.append("Critical Conflicts Detected")
        return list(set(pressures))

    def required_reviews(self, conflicts: List[ContextConflict], gaps: List[EvidenceGap]) -> List[str]:
        reviews = []
        for c in conflicts:
            if c.severity in [ContextImportance.HIGH, ContextImportance.CRITICAL] and c.suggested_review_reason:
                reviews.append(c.suggested_review_reason)
        for g in gaps:
            if g.severity in [ContextImportance.HIGH, ContextImportance.CRITICAL] and getattr(self.settings, "REVIEW_REQUIRE_ON_HIGH_EVIDENCE_GAP", False):
                reviews.append(f"Review required due to evidence gap in {g.layer.value}")
        return list(set(reviews))
