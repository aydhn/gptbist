import logging
from typing import Any

from .models import ResearchRun
from .ledger import ResearchLedger
from ..core.exceptions import ResearchLineageError

class ResearchLineageResolver:
    def __init__(self, ledger: ResearchLedger, logger: logging.Logger | None = None):
        self.ledger = ledger
        self.logger = logger or logging.getLogger(__name__)

    def link_runs(self, parent_run_id: str, child_run_id: str, relation: str, confirm: bool = False) -> dict[str, Any]:
        parent = self.ledger.get_run(parent_run_id)
        child = self.ledger.get_run(child_run_id)

        if not parent or not child:
            raise ResearchLineageError("Both parent and child runs must exist to link them.")

        if parent_run_id not in child.lineage.source_run_ids:
            child.lineage.source_run_ids.append(parent_run_id)
            child.lineage.parent_run_id = parent_run_id
            self.ledger.append_run(child, message=f"Linked to parent {parent_run_id} ({relation})")

        return {"parent": parent_run_id, "child": child_run_id, "relation": relation}

    def build_lineage_graph(self, run_ids: list[str]) -> dict[str, Any]:
        graph = {}
        for run_id in run_ids:
            run = self.ledger.get_run(run_id)
            if run:
                graph[run_id] = {
                    "parent": run.lineage.parent_run_id,
                    "sources": run.lineage.source_run_ids
                }
        return graph

    def find_children(self, run_id: str) -> list[ResearchRun]:
        entries = self.ledger.load_entries(limit=5000)
        children = []
        for e in entries:
            if run_id in e.run.lineage.source_run_ids or e.run.lineage.parent_run_id == run_id:
                children.append(e.run)
        return children

    def find_parents(self, run_id: str) -> list[ResearchRun]:
        run = self.ledger.get_run(run_id)
        if not run: return []
        parents = []
        if run.lineage.parent_run_id:
            p = self.ledger.get_run(run.lineage.parent_run_id)
            if p: parents.append(p)
        for s_id in run.lineage.source_run_ids:
            if s_id != run.lineage.parent_run_id:
                s = self.ledger.get_run(s_id)
                if s: parents.append(s)
        return parents

    def lineage_summary(self, run_id: str) -> dict[str, Any]:
        parents = self.find_parents(run_id)
        children = self.find_children(run_id)
        return {
            "run_id": run_id,
            "parents_count": len(parents),
            "children_count": len(children)
        }
