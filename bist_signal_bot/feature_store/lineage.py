from datetime import datetime, timezone
import uuid
from typing import Any
from bist_signal_bot.feature_store.models import FeatureLineageEdge

class FeatureLineageTracker:
    def __init__(self):
        self._edges: list[FeatureLineageEdge] = []

    def add_edge(self, from_object_id: str, to_object_id: str, relation: str, process_name: str | None = None) -> FeatureLineageEdge:
        edge = FeatureLineageEdge(
            edge_id=f"edge_{uuid.uuid4().hex[:8]}",
            from_object_id=from_object_id,
            to_object_id=to_object_id,
            relation=relation,
            process_name=process_name,
            created_at=datetime.now(timezone.utc)
        )
        self._edges.append(edge)
        return edge

    def feature_lineage(self, feature_name: str) -> list[FeatureLineageEdge]:
        return [e for e in self._edges if e.to_object_id == feature_name or e.from_object_id == feature_name]

    def feature_set_lineage(self, feature_set_id: str) -> list[FeatureLineageEdge]:
        return [e for e in self._edges if e.to_object_id == feature_set_id or e.from_object_id == feature_set_id]

    def build_lineage_graph(self, feature_set_id: str) -> dict[str, Any]:
        edges = self.feature_set_lineage(feature_set_id)
        nodes = set()
        for e in edges:
            nodes.add(e.from_object_id)
            nodes.add(e.to_object_id)
        return {
            "nodes": list(nodes),
            "edges": [{"from": e.from_object_id, "to": e.to_object_id, "relation": e.relation} for e in edges]
        }

    def link_dataset_to_feature(self, dataset_id: str, feature_name: str) -> FeatureLineageEdge:
        return self.add_edge(dataset_id, feature_name, "DERIVED_FROM", "feature_computation")

    def link_feature_to_model_or_signal(self, feature_name: str, object_id: str, object_type: str) -> FeatureLineageEdge:
        return self.add_edge(feature_name, object_id, f"CONSUMED_BY_{object_type}", "model_inference")
