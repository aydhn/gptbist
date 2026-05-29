import pytest
from datetime import datetime, timezone
from bist_signal_bot.context_fusion.scoring import CompositeResearchScorer
from bist_signal_bot.context_fusion.models import (
    ContextLayerSummary, ContextLayer, ContextStatus, ContextDirection, ContextConflict,
    ConflictType, ContextImportance, EvidenceGap, EvidenceGapType
)
from bist_signal_bot.config.settings import Settings

def test_composite_scoring_base():
    scorer = CompositeResearchScorer(Settings())
    summaries = [
        ContextLayerSummary(
            summary_id="1", layer=ContextLayer.TECHNICAL_SIGNAL, as_of=datetime.now(timezone.utc),
            signals=[], layer_score=80.0, layer_status=ContextStatus.SUPPORT, dominant_direction=ContextDirection.SUPPORTIVE
        ),
        ContextLayerSummary(
            summary_id="2", layer=ContextLayer.RISK, as_of=datetime.now(timezone.utc),
            signals=[], layer_score=40.0, layer_status=ContextStatus.PRESSURE, dominant_direction=ContextDirection.NEGATIVE
        )
    ]
    weights = {ContextLayer.TECHNICAL_SIGNAL: 0.5, ContextLayer.RISK: 0.5}
    score = scorer.score(summaries, weights=weights)
    assert score.base_score == 60.0
    assert score.adjusted_score == 60.0

def test_composite_scoring_with_penalties():
    scorer = CompositeResearchScorer(Settings())
    summaries = [
        ContextLayerSummary(
            summary_id="1", layer=ContextLayer.TECHNICAL_SIGNAL, as_of=datetime.now(timezone.utc),
            signals=[], layer_score=80.0, layer_status=ContextStatus.SUPPORT, dominant_direction=ContextDirection.SUPPORTIVE
        )
    ]
    weights = {ContextLayer.TECHNICAL_SIGNAL: 1.0}
    conflicts = [
        ContextConflict(
            conflict_id="1", conflict_type=ConflictType.HIGH_SCORE_HIGH_RISK,
            severity=ContextImportance.HIGH, score_impact=10.0, message="test"
        )
    ]
    gaps = [
        EvidenceGap(
            gap_id="1", gap_type=EvidenceGapType.MISSING_DATA, layer=ContextLayer.RISK,
            severity=ContextImportance.HIGH, message="test"
        )
    ]
    # Assuming gap penalty HIGH is 6.0
    score = scorer.score(summaries, conflicts=conflicts, gaps=gaps, weights=weights)
    assert score.base_score == 80.0
    assert score.adjusted_score == 64.0 # 80 - 10 - 6
