import pytest
from datetime import datetime, timezone
from bist_signal_bot.context_fusion.conflicts import ContextConflictResolver
from bist_signal_bot.context_fusion.models import (
    ContextLayerSummary, ContextLayer, ContextStatus, ContextDirection, ConflictType
)
from bist_signal_bot.config.settings import Settings

def _mock_summary(layer: ContextLayer, direction: ContextDirection):
    return ContextLayerSummary(
        summary_id="1", layer=layer, as_of=datetime.now(timezone.utc),
        signals=[], layer_score=50.0 if direction==ContextDirection.SUPPORTIVE else 10.0,
        layer_status=ContextStatus.SUPPORT if direction==ContextDirection.SUPPORTIVE else ContextStatus.HIGH_PRESSURE,
        dominant_direction=direction
    )

def test_high_score_high_risk_conflict():
    resolver = ContextConflictResolver(Settings())
    summaries = [
        _mock_summary(ContextLayer.TECHNICAL_SIGNAL, ContextDirection.SUPPORTIVE),
        _mock_summary(ContextLayer.RISK, ContextDirection.NEGATIVE)
    ]
    c = resolver.high_score_high_risk(summaries)
    assert c is not None
    assert c.conflict_type == ConflictType.HIGH_SCORE_HIGH_RISK

def test_technical_vs_macro_conflict():
    resolver = ContextConflictResolver(Settings())
    summaries = [
        _mock_summary(ContextLayer.TECHNICAL_SIGNAL, ContextDirection.SUPPORTIVE),
        _mock_summary(ContextLayer.MACRO, ContextDirection.NEGATIVE)
    ]
    c = resolver.technical_vs_macro(summaries)
    assert c is not None
    assert c.conflict_type == ConflictType.TECHNICAL_VS_MACRO
