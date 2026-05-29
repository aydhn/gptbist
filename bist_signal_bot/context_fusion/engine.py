import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import (
    UnifiedContextSnapshot, ContextFusionReport, ContextConflict, EvidenceGap
)
from bist_signal_bot.context_fusion.collectors import ContextCollector
from bist_signal_bot.context_fusion.normalization import ContextNormalizer
from bist_signal_bot.context_fusion.weights import ContextWeightManager
from bist_signal_bot.context_fusion.conflicts import ContextConflictResolver
from bist_signal_bot.context_fusion.evidence_gaps import EvidenceGapAnalyzer
from bist_signal_bot.context_fusion.research_graph import ResearchGraphBuilder
from bist_signal_bot.context_fusion.scoring import CompositeResearchScorer
from bist_signal_bot.context_fusion.snapshot import UnifiedContextSnapshotBuilder
from bist_signal_bot.context_fusion.storage import ContextFusionStore
from bist_signal_bot.core.audit import AuditLogger, AuditEvent

logger = logging.getLogger(__name__)

class ContextFusionEngine:
    def __init__(self,
                 collector: ContextCollector,
                 normalizer: ContextNormalizer,
                 weight_manager: ContextWeightManager,
                 conflict_resolver: ContextConflictResolver,
                 gap_analyzer: EvidenceGapAnalyzer,
                 graph_builder: ResearchGraphBuilder,
                 scorer: CompositeResearchScorer,
                 snapshot_builder: UnifiedContextSnapshotBuilder,
                 store: ContextFusionStore,
                 settings: Settings | None = None,
                 logger_instance: logging.Logger | None = None):
        self.collector = collector
        self.normalizer = normalizer
        self.weight_manager = weight_manager
        self.conflict_resolver = conflict_resolver
        self.gap_analyzer = gap_analyzer
        self.graph_builder = graph_builder
        self.scorer = scorer
        self.snapshot_builder = snapshot_builder
        self.store = store
        self.settings = settings or Settings()
        self.logger = logger_instance or logger

    def build_snapshot_for_signal(self, signal_payload: Dict[str, Any], save: bool = False) -> UnifiedContextSnapshot:
        symbol = signal_payload.get("symbol", "UNKNOWN")
        strategy_name = signal_payload.get("strategy_name")
        signal_id = signal_payload.get("signal_id")

        signals = self.collector.collect_for_signal(signal_payload)
        summaries = self.snapshot_builder.summarize_layers(signals)

        conflicts = self.conflict_resolver.detect_conflicts(summaries)
        gaps = self.gap_analyzer.detect_gaps(signals, summaries)

        weights = self.weight_manager.dynamic_weights(symbol, strategy_name, summaries)
        score = self.scorer.score(summaries, conflicts, gaps, weights)

        graph = None
        if getattr(self.settings, "CONTEXT_FUSION_BUILD_RESEARCH_GRAPH", True):
            graph = self.graph_builder.build_graph(symbol, signal_id, summaries, signals)

        snapshot = self.snapshot_builder.build_for_signal(signal_payload, signals, conflicts, gaps, score, graph)

        if save and getattr(self.settings, "CONTEXT_FUSION_SAVE_RESULTS", True):
            self.store.append_context_signals(signals)
            self.store.append_layer_summaries(summaries)
            if conflicts:
                self.store.append_conflicts(conflicts)
            if gaps:
                self.store.append_gaps(gaps)
            if graph:
                self.store.append_graph(graph)
            self.store.append_score(score)
            self.store.append_snapshot(snapshot)

        self._log_audit("UNIFIED_CONTEXT_SNAPSHOT_CREATED", snapshot)
        return snapshot

    def build_snapshot_for_symbol(self, symbol: str, strategy_name: Optional[str] = None, save: bool = False) -> UnifiedContextSnapshot:
        return self.build_snapshot_for_signal({"symbol": symbol, "strategy_name": strategy_name}, save=save)

    def build_report(self, symbols: Optional[List[str]] = None, limit: int = 50) -> ContextFusionReport:
        symbols = symbols or []
        snapshots = []
        for sym in symbols:
            snap = self.store.load_latest_snapshot(sym)
            if snap:
                snapshots.append(snap)

        if not snapshots and not symbols:
            snapshots = self.store.load_snapshots(limit=limit)

        snapshots.sort(key=lambda s: s.composite_score.adjusted_score if s.composite_score else 0.0, reverse=True)

        all_conflicts = []
        all_gaps = []
        key_findings = []

        for s in snapshots:
            all_conflicts.extend(s.conflicts)
            all_gaps.extend(s.evidence_gaps)

        if snapshots:
            top_sym = snapshots[0].symbol
            key_findings.append(f"Highest composite score for {top_sym}.")

        report = ContextFusionReport(
            report_id=str(uuid.uuid4()),
            generated_at=datetime.now(timezone.utc),
            snapshots=snapshots,
            conflicts=all_conflicts,
            evidence_gaps=all_gaps,
            key_findings=key_findings
        )

        self._log_audit("CONTEXT_FUSION_REPORT_CREATED", report)
        return report

    def refresh_recent_context(self, limit: int = 100) -> List[UnifiedContextSnapshot]:
        return self.store.load_snapshots(limit=limit)

    def explain_conflicts(self, snapshot: UnifiedContextSnapshot) -> List[str]:
        return [f"[{c.severity.value}] {c.conflict_type.value}: {c.message}" for c in snapshot.conflicts]

    def context_health(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        snapshots = self.store.load_snapshots(symbol=symbol, limit=100)
        total = len(snapshots)
        conflicts = sum(len(s.conflicts) for s in snapshots)
        gaps = sum(len(s.evidence_gaps) for s in snapshots)

        return {
            "status": "pass",
            "snapshots_analyzed": total,
            "total_conflicts": conflicts,
            "total_evidence_gaps": gaps,
            "healthy": total > 0 and conflicts < total and gaps < total * 2
        }

    def _log_audit(self, event_type: str, item: Any):
        try:
            audit_logger = AuditLogger(self.settings)

            meta = {
                "no_real_order_sent": True
            }
            if isinstance(item, UnifiedContextSnapshot):
                meta.update({
                    "snapshot_id": item.snapshot_id,
                    "symbol": item.symbol,
                    "signal_id": item.signal_id,
                    "composite_score": item.composite_score.adjusted_score if item.composite_score else None,
                    "conflict_count": len(item.conflicts),
                    "evidence_gap_count": len(item.evidence_gaps)
                })
            elif isinstance(item, ContextFusionReport):
                meta.update({
                    "report_id": item.report_id,
                    "snapshot_count": len(item.snapshots),
                    "conflict_count": len(item.conflicts),
                    "evidence_gap_count": len(item.evidence_gaps)
                })

            audit_logger.log_event(AuditEvent(
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                actor="ContextFusionEngine",
                status="SUCCESS",
                resource_type=type(item).__name__,
                resource_id=getattr(item, "snapshot_id", getattr(item, "report_id", "UNKNOWN")),
                details=meta
            ))
        except Exception as e:
            self.logger.error(f"Failed to log audit event {event_type}: {e}")
