import pytest
from bist_signal_bot.context_fusion.weights import ContextWeightManager
from bist_signal_bot.context_fusion.models import ContextLayer
from bist_signal_bot.config.settings import Settings

def test_normalize_weights():
    manager = ContextWeightManager(Settings())
    weights = {ContextLayer.TECHNICAL_SIGNAL: 1.0, ContextLayer.ML: 1.0}
    norm = manager.normalize_weights(weights)
    assert norm[ContextLayer.TECHNICAL_SIGNAL] == 0.5
    assert norm[ContextLayer.ML] == 0.5

def test_missing_layer_adjustment():
    manager = ContextWeightManager(Settings())
    base_weights = {ContextLayer.TECHNICAL_SIGNAL: 0.8, ContextLayer.ML: 0.2}
    from bist_signal_bot.context_fusion.models import ContextLayerSummary, ContextStatus, ContextDirection
    from datetime import datetime, timezone

    # Only tech summary provided
    summaries = [
        ContextLayerSummary(
            summary_id="1", layer=ContextLayer.TECHNICAL_SIGNAL, as_of=datetime.now(timezone.utc),
            signals=[], layer_score=50.0, layer_status=ContextStatus.SUPPORT, dominant_direction=ContextDirection.SUPPORTIVE
        )
    ]
    adj = manager.adjust_for_missing_layers(base_weights, summaries)
    assert ContextLayer.ML not in adj
    assert adj[ContextLayer.TECHNICAL_SIGNAL] == 1.0
