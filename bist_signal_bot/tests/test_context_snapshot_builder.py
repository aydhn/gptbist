import pytest
from datetime import datetime, timezone
from bist_signal_bot.context_fusion.snapshot import UnifiedContextSnapshotBuilder
from bist_signal_bot.context_fusion.models import (
    ContextSignal, ContextLayer, ContextDirection, ContextStatus, ContextImportance
)
from bist_signal_bot.config.settings import Settings

def test_snapshot_builder():
    builder = UnifiedContextSnapshotBuilder(Settings())
    signals = [
        ContextSignal(
            context_id="1", layer=ContextLayer.TECHNICAL_SIGNAL, symbol="ASELS",
            as_of=datetime.now(timezone.utc), title="Test", direction=ContextDirection.SUPPORTIVE,
            status=ContextStatus.SUPPORT, importance=ContextImportance.HIGH, message="test", score=80.0
        )
    ]
    from bist_signal_bot.context_fusion.scoring import CompositeResearchScore
    score = CompositeResearchScore(
        score_id="1", symbol="ASELS", as_of=datetime.now(timezone.utc),
        base_score=80.0, adjusted_score=80.0, final_status=ContextStatus.SUPPORT
    )
    snap = builder.build_for_symbol("ASELS", signals, [], [], score)
    assert snap.symbol == "ASELS"
    assert len(snap.layer_summaries) == 1
    assert "TECHNICAL_SIGNAL" in snap.key_supports
