
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.ops.models import OpsRunbook, OpsRunbookStep, OpsRunbookType, OpsIncident, OpsStatus
from bist_signal_bot.ops.storage import OpsStore

class OpsRunbookRegistry:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None, store: OpsStore | None = None):
        self.settings = settings
        from bist_signal_bot.storage.paths import get_data_dir
        self.base_dir = base_dir or get_data_dir()
        self.store = store or OpsStore(settings, self.base_dir)

    def default_runbooks(self) -> list[OpsRunbook]:
        return [
            OpsRunbook(
                runbook_id="rb_store_repair", runbook_type=OpsRunbookType.STORE_REPAIR, title="Store Integrity Repair", description="Steps to diagnose and repair JSONL store corruption.",
                steps=[
                    OpsRunbookStep(step_id="step_1", runbook_type=OpsRunbookType.STORE_REPAIR, title="Identify corrupted lines", description="Run store integrity check to locate invalid JSON lines.", command_hint="python -m bist_signal_bot ops store-check"),
                    OpsRunbookStep(step_id="step_2", runbook_type=OpsRunbookType.STORE_REPAIR, title="Backup current state", description="Create a backup before manual editing.", command_hint="python -m bist_signal_bot ops backup --scope DATA --confirm")
                ]
            ),
            OpsRunbook(
                runbook_id="rb_stale_refresh", runbook_type=OpsRunbookType.STALE_DATA_REFRESH, title="Refresh Stale Data", description="Steps to refresh local data stores.",
                steps=[OpsRunbookStep(step_id="step_1", runbook_type=OpsRunbookType.STALE_DATA_REFRESH, title="Check staleness", description="Identify which modules are stale.", command_hint="python -m bist_signal_bot ops staleness")]
            )
        ]

    def get_runbook(self, runbook_type: OpsRunbookType) -> OpsRunbook | None:
        for rb in self.default_runbooks():
            if rb.runbook_type == runbook_type: return rb
        return None

    def runbook_for_incident(self, incident: OpsIncident) -> OpsRunbook:
        mapping = {"STORE_CORRUPTION": OpsRunbookType.STORE_REPAIR, "STALE_DATA": OpsRunbookType.STALE_DATA_REFRESH}
        r_type = mapping.get(incident.incident_type.name, OpsRunbookType.GENERAL_DIAGNOSTIC)
        rb = self.get_runbook(r_type)
        if rb: return rb
        return OpsRunbook(runbook_id="rb_general", runbook_type=OpsRunbookType.GENERAL_DIAGNOSTIC, title="General Diagnostic", description="Run health check and doctor.", steps=[OpsRunbookStep(step_id="step_1", runbook_type=OpsRunbookType.GENERAL_DIAGNOSTIC, title="Health check", description="Run healthcheck.", command_hint="python -m bist_signal_bot healthcheck --ops")])

    def validate_runbook(self, runbook: OpsRunbook) -> list[str]:
        return [f"Step {step.step_id} is destructive but lacks requires_confirm=True." for step in runbook.steps if step.destructive and not step.requires_confirm]

    def mark_step_status(self, runbook: OpsRunbook, step_id: str, status: OpsStatus) -> OpsRunbook:
        new_rb = runbook.model_copy(deep=True)
        for s in new_rb.steps:
            if s.step_id == step_id: s.status = status
        return new_rb
