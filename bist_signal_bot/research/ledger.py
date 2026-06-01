from typing import Any
import logging
import uuid
from typing import Any
from datetime import datetime

from ..config.settings import Settings, get_settings
from .models import (
    ResearchRun, ResearchLedgerEntry, ResearchTag,
    ResearchArtifactRef, ResearchRunStatus, ResearchQuery
)
from .storage import ResearchStore
from ..core.exceptions import ResearchLedgerError

class ResearchLedger:
    def __init__(self, storage: ResearchStore, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.storage = storage
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)

    def append_run(self, run: ResearchRun, message: str | None = None) -> ResearchLedgerEntry:
        # Secret redaction handled in model via safe_public_dict where needed, or we just trust run data has no secrets
        # Append-only
        entry_id = f"rle_{uuid.uuid4().hex[:8]}"
        entry = ResearchLedgerEntry(
            entry_id=entry_id,
            run=run,
            message=message or f"Appended research run {run.run_id}",
            metadata={"no_real_order_sent": True}
        )
        self.storage.append_ledger_entry(entry)
        self.logger.info(f"Research run appended to ledger: {run.run_id} ({entry_id})")
        return entry

    def load_entries(self, limit: int = 100, query: ResearchQuery | None = None) -> list[ResearchLedgerEntry]:
        all_entries = self.storage.load_ledger_entries(limit=10000) # Load more to filter
        if not query:
            return all_entries[:limit]

        filtered = []
        for e in all_entries:
            run = e.run
            if query.run_types and run.run_type not in query.run_types: continue
            if query.status and run.status not in query.status: continue
            if query.symbols and not any(s in run.symbols for s in query.symbols): continue
            if query.strategies and run.strategy_name not in query.strategies: continue
            if query.tags:
                run_tag_names = [t.tag for t in run.tags]
                if not any(qt in run_tag_names for qt in query.tags): continue

            if query.start_date and run.started_at < query.start_date: continue
            if query.end_date and run.started_at > query.end_date: continue

            filtered.append(e)
            if len(filtered) >= limit:
                break
        return filtered

    def get_run(self, run_id: str) -> ResearchRun | None:
        entries = self.storage.load_ledger_entries(limit=5000)
        for e in entries:
            if e.run.run_id == run_id:
                return e.run
        return None

    def tag_run(self, run_id: str, tags: list[ResearchTag], confirm: bool = False) -> ResearchRun:
        if self.settings.RESEARCH_REQUIRE_CONFIRM_FOR_TAG_EDIT and not confirm:
            raise ResearchLedgerError("Confirm is required to tag a run")

        run = self.get_run(run_id)
        if not run:
            raise ResearchLedgerError(f"Run {run_id} not found")

        run.tags.extend(tags)
        # Since it's append-only, we append a new entry representing the updated run
        self.append_run(run, message=f"Added tags to {run_id}")
        return run

    def add_artifact(self, run_id: str, artifact: ResearchArtifactRef, confirm: bool = False) -> ResearchRun:
        run = self.get_run(run_id)
        if not run:
            raise ResearchLedgerError(f"Run {run_id} not found")
        run.artifacts.append(artifact)
        self.append_run(run, message=f"Added artifact {artifact.artifact_id} to {run_id}")
        return run

    def mark_run_status(self, run_id: str, status: ResearchRunStatus, confirm: bool = False) -> ResearchRun:
        if self.settings.RESEARCH_REQUIRE_CONFIRM_FOR_EDITS and not confirm:
            raise ResearchLedgerError("Confirm is required to edit run status")
        run = self.get_run(run_id)
        if not run:
            raise ResearchLedgerError(f"Run {run_id} not found")
        run.status = status
        self.append_run(run, message=f"Updated status of {run_id} to {status.value}")
        return run

    def summarize_recent(self, limit: int = 20) -> dict[str, Any]:
        entries = self.load_entries(limit=limit)
        return {
            "total_recent": len(entries),
            "runs": [e.run.summary() for e in entries]
        }

    def log_whatif_run(self, result: Any, tags: list[str] | None = None) -> Any:
        metrics = {
            "elapsed_seconds": getattr(result, "elapsed_seconds", 0.0),
            "status": getattr(result, "status", "UNKNOWN")
        }
        if hasattr(result, "comparison") and result.comparison:
            metrics["best_scenario_id"] = result.comparison.best_scenario_id

        event = dict(
            event_id=str(uuid.uuid4()),
            event_type=ResearchEventType.WHATIF_RUN,
            source_id=getattr(result, "run_id", "unknown"),
            metrics=metrics,
            tags=tags or ["whatif"],
            metadata={"source_type": getattr(result.request, "source_type", "unknown")} if hasattr(result, "request") else {}
        )
        return self.append_event(event)
