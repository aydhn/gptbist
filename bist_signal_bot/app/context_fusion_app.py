from pathlib import Path
from typing import Optional
from bist_signal_bot.config.settings import Settings

from bist_signal_bot.context_fusion.storage import ContextFusionStore
from bist_signal_bot.context_fusion.sources import ContextSourceRegistry
from bist_signal_bot.context_fusion.collectors import ContextCollector
from bist_signal_bot.context_fusion.normalization import ContextNormalizer
from bist_signal_bot.context_fusion.weights import ContextWeightManager
from bist_signal_bot.context_fusion.conflicts import ContextConflictResolver
from bist_signal_bot.context_fusion.evidence_gaps import EvidenceGapAnalyzer
from bist_signal_bot.context_fusion.research_graph import ResearchGraphBuilder
from bist_signal_bot.context_fusion.scoring import CompositeResearchScorer
from bist_signal_bot.context_fusion.snapshot import UnifiedContextSnapshotBuilder
from bist_signal_bot.context_fusion.engine import ContextFusionEngine

def create_context_fusion_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ContextFusionStore:
    return ContextFusionStore(settings=settings, base_dir=base_dir)

def create_context_source_registry(settings: Optional[Settings] = None) -> ContextSourceRegistry:
    return ContextSourceRegistry(settings=settings)

def create_context_collector(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ContextCollector:
    return ContextCollector(settings=settings, base_dir=base_dir)

def create_context_normalizer(settings: Optional[Settings] = None) -> ContextNormalizer:
    return ContextNormalizer(settings=settings)

def create_context_weight_manager(settings: Optional[Settings] = None) -> ContextWeightManager:
    return ContextWeightManager(settings=settings)

def create_context_conflict_resolver(settings: Optional[Settings] = None) -> ContextConflictResolver:
    return ContextConflictResolver(settings=settings)

def create_evidence_gap_analyzer(settings: Optional[Settings] = None) -> EvidenceGapAnalyzer:
    return EvidenceGapAnalyzer(settings=settings)

def create_research_graph_builder(settings: Optional[Settings] = None) -> ResearchGraphBuilder:
    return ResearchGraphBuilder(settings=settings)

def create_composite_research_scorer(settings: Optional[Settings] = None) -> CompositeResearchScorer:
    return CompositeResearchScorer(settings=settings)

def create_unified_context_snapshot_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> UnifiedContextSnapshotBuilder:
    return UnifiedContextSnapshotBuilder(settings=settings, base_dir=base_dir)

def create_context_fusion_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ContextFusionEngine:
    return ContextFusionEngine(
        collector=create_context_collector(settings, base_dir),
        normalizer=create_context_normalizer(settings),
        weight_manager=create_context_weight_manager(settings),
        conflict_resolver=create_context_conflict_resolver(settings),
        gap_analyzer=create_evidence_gap_analyzer(settings),
        graph_builder=create_research_graph_builder(settings),
        scorer=create_composite_research_scorer(settings),
        snapshot_builder=create_unified_context_snapshot_builder(settings, base_dir),
        store=create_context_fusion_store(settings, base_dir),
        settings=settings
    )
