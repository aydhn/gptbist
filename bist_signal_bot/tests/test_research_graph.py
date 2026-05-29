import pytest
from datetime import datetime, timezone
from bist_signal_bot.context_fusion.research_graph import ResearchGraphBuilder
from bist_signal_bot.context_fusion.models import (
    ContextLayerSummary, ContextLayer, ContextStatus, ContextDirection, ContextSignal, ContextImportance
)
from bist_signal_bot.config.settings import Settings

def test_build_research_graph():
    builder = ResearchGraphBuilder(Settings())
    signals = [
        ContextSignal(
            context_id="1", layer=ContextLayer.TECHNICAL_SIGNAL, symbol="ASELS",
            as_of=datetime.now(timezone.utc), title="Test", direction=ContextDirection.SUPPORTIVE,
            status=ContextStatus.SUPPORT, importance=ContextImportance.HIGH, message="test"
        )
    ]
    summaries = [
        ContextLayerSummary(
            summary_id="1", layer=ContextLayer.TECHNICAL_SIGNAL, symbol="ASELS", as_of=datetime.now(timezone.utc),
            signals=[], layer_score=50.0, layer_status=ContextStatus.SUPPORT, dominant_direction=ContextDirection.SUPPORTIVE
        )
    ]
    graph = builder.build_graph("ASELS", "sig_1", summaries, signals)
    assert graph is not None
    assert graph.symbol == "ASELS"
    assert len(graph.nodes) >= 2 # symbol node + context node (+ signal node)
    assert len(graph.edges) >= 1
