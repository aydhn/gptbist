import json
import logging
from pathlib import Path
from typing import Any, List, Optional, Dict
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import (
    ContextSignal, ContextLayerSummary, UnifiedContextSnapshot,
    ContextConflict, EvidenceGap, ResearchGraph, CompositeResearchScore,
    ContextFusionReport
)
from bist_signal_bot.storage.paths import get_context_fusion_dir

logger = logging.getLogger(__name__)

class ContextFusionStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir

    def append_context_signals(self, signals: List[ContextSignal]) -> Path:
        target_dir = get_context_fusion_dir(self.settings) / "signals"
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / "context_signals.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            for s in signals:
                f.write(json.dumps(s.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return file_path

    def append_layer_summaries(self, summaries: List[ContextLayerSummary]) -> Path:
        target_dir = get_context_fusion_dir(self.settings) / "summaries"
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / "context_layer_summaries.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            for s in summaries:
                f.write(json.dumps(s.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return file_path

    def append_snapshot(self, snapshot: UnifiedContextSnapshot) -> Path:
        target_dir = get_context_fusion_dir(self.settings) / "snapshots"
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / "unified_context_snapshots.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(snapshot.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return file_path

    def load_snapshots(self, symbol: Optional[str] = None, limit: int = 1000) -> List[UnifiedContextSnapshot]:
        target_dir = get_context_fusion_dir(self.settings) / "snapshots"
        file_path = target_dir / "unified_context_snapshots.jsonl"
        if not file_path.exists():
            return []

        results = []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if symbol is None or data.get("symbol") == symbol:
                        results.append(UnifiedContextSnapshot(**data))
                        if len(results) >= limit:
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse snapshot: {e}")
        return results

    def get_snapshot(self, snapshot_id: str) -> Optional[UnifiedContextSnapshot]:
        snapshots = self.load_snapshots(limit=10000)
        return next((s for s in snapshots if s.snapshot_id == snapshot_id), None)

    def load_latest_snapshot(self, symbol: str, strategy_name: Optional[str] = None) -> Optional[UnifiedContextSnapshot]:
        snapshots = self.load_snapshots(symbol=symbol, limit=100)
        if not strategy_name:
            return snapshots[0] if snapshots else None
        return next((s for s in snapshots if s.strategy_name == strategy_name), None)

    def append_conflicts(self, conflicts: List[ContextConflict]) -> Path:
        target_dir = get_context_fusion_dir(self.settings) / "conflicts"
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / "context_conflicts.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            for c in conflicts:
                f.write(json.dumps(c.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return file_path

    def load_conflicts(self, symbol: Optional[str] = None, limit: int = 1000) -> List[ContextConflict]:
        target_dir = get_context_fusion_dir(self.settings) / "conflicts"
        file_path = target_dir / "context_conflicts.jsonl"
        if not file_path.exists():
            return []

        results = []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if symbol is None or data.get("symbol") == symbol:
                        results.append(ContextConflict(**data))
                        if len(results) >= limit:
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse conflict: {e}")
        return results

    def append_gaps(self, gaps: List[EvidenceGap]) -> Path:
        target_dir = get_context_fusion_dir(self.settings) / "gaps"
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / "evidence_gaps.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            for g in gaps:
                f.write(json.dumps(g.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return file_path

    def load_gaps(self, symbol: Optional[str] = None, limit: int = 1000) -> List[EvidenceGap]:
        target_dir = get_context_fusion_dir(self.settings) / "gaps"
        file_path = target_dir / "evidence_gaps.jsonl"
        if not file_path.exists():
            return []

        results = []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if symbol is None or data.get("symbol") == symbol:
                        results.append(EvidenceGap(**data))
                        if len(results) >= limit:
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse gap: {e}")
        return results

    def append_graph(self, graph: ResearchGraph) -> Path:
        target_dir = get_context_fusion_dir(self.settings) / "graphs"
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / "research_graphs.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(graph.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return file_path

    def append_score(self, score: CompositeResearchScore) -> Path:
        target_dir = get_context_fusion_dir(self.settings) / "scores"
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / "composite_research_scores.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(score.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return file_path

    def save_report(self, report: ContextFusionReport, markdown_text: str) -> Dict[str, Path]:
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        target_dir = get_context_fusion_dir(self.settings) / "reports" / date_str
        target_dir.mkdir(parents=True, exist_ok=True)

        json_path = target_dir / "context_fusion_report.json"
        md_path = target_dir / "context_fusion_report.md"

        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        return {"json": json_path, "md": md_path}
