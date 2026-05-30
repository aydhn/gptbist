import uuid
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.data_catalog.models import (
    DataLineageEdge,
    DatasetRecord,
    LineageRelationType,
)
from bist_signal_bot.config.settings import Settings, get_settings


class DataLineageTracker:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._edges: list[DataLineageEdge] = []

    def add_edge(
        self,
        from_dataset_id: str,
        to_dataset_id: str,
        relation_type: LineageRelationType,
        process_name: str | None = None,
        source_ref: str | None = None,
    ) -> DataLineageEdge:
        edge = DataLineageEdge(
            edge_id=f"edge_{uuid.uuid4().hex[:12]}",
            from_dataset_id=from_dataset_id,
            to_dataset_id=to_dataset_id,
            relation_type=relation_type,
            created_at=datetime.now(timezone.utc),
            process_name=process_name,
            source_ref=source_ref
        )
        self._edges.append(edge)
        return edge

    def lineage_for_dataset(self, dataset_id: str, direction: str = "both") -> list[DataLineageEdge]:
        res = []
        for e in self._edges:
            if direction in ("forward", "both") and e.from_dataset_id == dataset_id:
                res.append(e)
            if direction in ("backward", "both") and e.to_dataset_id == dataset_id:
                res.append(e)
        return res

    def lineage_graph(self, dataset_id: str) -> dict[str, Any]:
        # Simple local representation
        edges = self.lineage_for_dataset(dataset_id)
        return {
            "dataset_id": dataset_id,
            "edges_count": len(edges),
            "edges": [e.model_dump() for e in edges]
        }

    def edges_for_process(self, process_name: str) -> list[DataLineageEdge]:
        return [e for e in self._edges if e.process_name == process_name]

    def detect_orphan_datasets(self, datasets: list[DatasetRecord], edges: list[DataLineageEdge]) -> list[str]:
        connected_ids = set()
        for e in edges:
            connected_ids.add(e.from_dataset_id)
            connected_ids.add(e.to_dataset_id)

        orphans = []
        for ds in datasets:
            if ds.dataset_id not in connected_ids:
                orphans.append(ds.dataset_id)

        return orphans
