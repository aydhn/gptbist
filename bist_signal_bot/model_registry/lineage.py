import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.model_registry.models import ModelLineageEdge


class ModelLineageTracker:
    def __init__(self, settings: Settings | None = None, store: Any = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)
        self.store = store

    def add_edge(self, from_object_id: str, to_object_id: str, relation: str, process_name: str | None = None) -> ModelLineageEdge:
        edge = ModelLineageEdge(
            edge_id=f"edge_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            from_object_id=from_object_id,
            to_object_id=to_object_id,
            relation=relation,
            process_name=process_name,
            created_at=datetime.now(timezone.utc)
        )

        if self.store:
            self.store.append_lineage_edges([edge])

        return edge

    def link_dataset_to_experiment(self, dataset_id: str, run_id: str) -> ModelLineageEdge:
        return self.add_edge(dataset_id, run_id, "USED_FOR_TRAINING", "ml_training")

    def link_feature_set_to_model(self, feature_set_id: str, model_id: str) -> ModelLineageEdge:
        return self.add_edge(feature_set_id, model_id, "PROVIDES_FEATURES", "model_registration")

    def link_model_to_signal_or_strategy(self, model_id: str, object_id: str, object_type: str) -> ModelLineageEdge:
        return self.add_edge(model_id, object_id, f"FILTERS_{object_type.upper()}", "ml_inference")

    def model_lineage(self, model_id: str) -> list[ModelLineageEdge]:
        if not self.store:
            return []

        edges = self.store.load_lineage_edges()

        # Simple traversal for MVP (just immediate connections)
        model_edges = [e for e in edges if e.from_object_id == model_id or e.to_object_id == model_id]

        # For a full graph, we would do a BFS/DFS from the model_id
        # Assuming model_id is connected to experiment which is connected to dataset

        return model_edges

    def build_lineage_graph(self, model_id: str) -> dict[str, Any]:
        edges = self.model_lineage(model_id)

        nodes = set()
        for e in edges:
            nodes.add(e.from_object_id)
            nodes.add(e.to_object_id)

        return {
            "nodes": list(nodes),
            "edges": [{"from": e.from_object_id, "to": e.to_object_id, "relation": e.relation} for e in edges]
        }
