import uuid
from typing import List
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import (
    ContextSignal, ContextLayerSummary, EvidenceGap, EvidenceGapType,
    ContextLayer, ContextImportance, ContextStatus
)
from bist_signal_bot.context_fusion.sources import ContextSourceRegistry

class EvidenceGapAnalyzer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.registry = ContextSourceRegistry(self.settings)

    def detect_gaps(self, signals: List[ContextSignal], summaries: List[ContextLayerSummary]) -> List[EvidenceGap]:
        gaps = []
        expected_layers = self.registry.supported_layers()

        gaps.extend(self.missing_layer_gaps(expected_layers, summaries))
        gaps.extend(self.stale_context_gaps(signals))
        gaps.extend(self.low_sample_gaps(signals))
        gaps.extend(self.collector_failure_gaps(signals))

        return gaps

    def missing_layer_gaps(self, expected_layers: List[ContextLayer], summaries: List[ContextLayerSummary]) -> List[EvidenceGap]:
        gaps = []
        present = {s.layer for s in summaries if s.layer_status != ContextStatus.INSUFFICIENT_DATA}

        for layer in expected_layers:
            if layer not in present:
                is_optional = self.registry.is_layer_optional(layer)
                severity = ContextImportance.LOW if is_optional else ContextImportance.HIGH
                gaps.append(EvidenceGap(
                    gap_id=str(uuid.uuid4()),
                    gap_type=EvidenceGapType.MISSING_DATA,
                    layer=layer,
                    severity=severity,
                    message=f"Missing data for context layer: {layer.value}",
                    recommended_data_action=f"Ensure collector for {layer.value} is enabled and data is available."
                ))
        return gaps

    def stale_context_gaps(self, signals: List[ContextSignal]) -> List[EvidenceGap]:
        gaps = []
        for s in signals:
            if s.status == ContextStatus.STALE:
                gaps.append(EvidenceGap(
                    gap_id=str(uuid.uuid4()),
                    gap_type=EvidenceGapType.STALE_DATA,
                    layer=s.layer,
                    symbol=s.symbol,
                    severity=ContextImportance.MEDIUM,
                    message=f"Stale data detected in layer: {s.layer.value}. Signal: {s.title}",
                    recommended_data_action="Refresh data source."
                ))
        return gaps

    def low_sample_gaps(self, signals: List[ContextSignal]) -> List[EvidenceGap]:
        gaps = []
        for s in signals:
            if "low sample" in s.message.lower() or "insufficient sample" in s.message.lower():
                gaps.append(EvidenceGap(
                    gap_id=str(uuid.uuid4()),
                    gap_type=EvidenceGapType.LOW_SAMPLE_SIZE,
                    layer=s.layer,
                    symbol=s.symbol,
                    severity=ContextImportance.MEDIUM,
                    message=f"Low sample size in layer {s.layer.value}. Signal: {s.title}"
                ))
        return gaps

    def collector_failure_gaps(self, signals: List[ContextSignal]) -> List[EvidenceGap]:
        gaps = []
        for s in signals:
            if s.status == ContextStatus.ERROR:
                gaps.append(EvidenceGap(
                    gap_id=str(uuid.uuid4()),
                    gap_type=EvidenceGapType.FAILED_COLLECTOR,
                    layer=s.layer,
                    symbol=s.symbol,
                    severity=ContextImportance.HIGH,
                    message=f"Collector error in layer {s.layer.value}: {s.message}"
                ))
        return gaps

    def gap_penalty(self, gaps: List[EvidenceGap]) -> float:
        penalty = 0.0
        for g in gaps:
            if g.severity == ContextImportance.LOW:
                penalty += getattr(self.settings, "CONTEXT_EVIDENCE_GAP_PENALTY_LOW", 1.0)
            elif g.severity == ContextImportance.MEDIUM:
                penalty += getattr(self.settings, "CONTEXT_EVIDENCE_GAP_PENALTY_MEDIUM", 3.0)
            elif g.severity == ContextImportance.HIGH:
                penalty += getattr(self.settings, "CONTEXT_EVIDENCE_GAP_PENALTY_HIGH", 6.0)
            elif g.severity == ContextImportance.CRITICAL:
                # Same as high if critical not explicitly defined
                penalty += getattr(self.settings, "CONTEXT_EVIDENCE_GAP_PENALTY_HIGH", 6.0)
        return penalty
