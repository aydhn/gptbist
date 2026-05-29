import pytest
from datetime import datetime, timezone
from bist_signal_bot.context_fusion.evidence_gaps import EvidenceGapAnalyzer
from bist_signal_bot.context_fusion.models import (
    ContextLayerSummary, ContextLayer, ContextStatus, ContextDirection,
    ContextSignal, ContextImportance, EvidenceGapType
)
from bist_signal_bot.config.settings import Settings

def test_missing_layer_gap():
    analyzer = EvidenceGapAnalyzer(Settings())
    summaries = [
        ContextLayerSummary(
            summary_id="1", layer=ContextLayer.TECHNICAL_SIGNAL, as_of=datetime.now(timezone.utc),
            signals=[], layer_score=50.0, layer_status=ContextStatus.SUPPORT, dominant_direction=ContextDirection.SUPPORTIVE
        )
    ]
    gaps = analyzer.missing_layer_gaps([ContextLayer.TECHNICAL_SIGNAL, ContextLayer.RISK], summaries)
    assert len(gaps) == 1
    assert gaps[0].layer == ContextLayer.RISK
    assert gaps[0].gap_type == EvidenceGapType.MISSING_DATA

def test_stale_context_gap():
    analyzer = EvidenceGapAnalyzer(Settings())
    signals = [
        ContextSignal(
            context_id="1", layer=ContextLayer.TECHNICAL_SIGNAL, as_of=datetime.now(timezone.utc),
            title="Test", direction=ContextDirection.SUPPORTIVE, status=ContextStatus.STALE,
            importance=ContextImportance.HIGH, message="test"
        )
    ]
    gaps = analyzer.stale_context_gaps(signals)
    assert len(gaps) == 1
    assert gaps[0].gap_type == EvidenceGapType.STALE_DATA
