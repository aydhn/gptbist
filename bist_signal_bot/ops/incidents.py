
import datetime
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_data_dir
from bist_signal_bot.core.exceptions import OpsIncidentError
from bist_signal_bot.ops.models import OpsIncident, OpsIncidentType, OpsStatus, OpsSeverity, OpsCheckResult, OpsCheckType
from bist_signal_bot.ops.storage import OpsStore

class OpsIncidentManager:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None, store: OpsStore | None = None):
        self.settings = settings
        self.base_dir = base_dir or get_data_dir()
        self.store = store or OpsStore(settings, self.base_dir)

    def create_incident(self, incident_type: OpsIncidentType, title: str, description: str, severity: OpsSeverity = OpsSeverity.MEDIUM, related_check_ids: list[str] | None = None, save: bool = False) -> OpsIncident:
        now = datetime.datetime.now()
        inc = OpsIncident(
            incident_id=f"inc_{now.strftime('%Y%m%d%H%M%S')}_{incident_type.name}", incident_type=incident_type,
            status=OpsStatus.FAIL, severity=severity, title=title, description=description, detected_at=now, related_check_ids=related_check_ids or []
        )
        if save: self.store.append_incident(inc)
        return inc

    def incident_type_from_check(self, check: OpsCheckResult) -> OpsIncidentType:
        if check.check_type == OpsCheckType.STORE_INTEGRITY: return OpsIncidentType.STORE_CORRUPTION
        elif check.check_type == OpsCheckType.STALENESS: return OpsIncidentType.STALE_DATA
        elif check.check_type == OpsCheckType.CONFIG: return OpsIncidentType.CONFIG_INVALID
        elif check.check_type == OpsCheckType.SCHEDULER: return OpsIncidentType.SCHEDULER_FAILURE
        elif check.check_type == OpsCheckType.QA_GATE: return OpsIncidentType.QA_GATE_BLOCKED
        return OpsIncidentType.UNKNOWN

    def create_from_check_result(self, check: OpsCheckResult, save: bool = False) -> OpsIncident | None:
        if check.status in (OpsStatus.PASS, OpsStatus.SKIPPED): return None
        return self.create_incident(incident_type=self.incident_type_from_check(check), title=f"Check Failed: {check.module_name}", description=check.message, severity=check.severity, related_check_ids=[check.check_id], save=save)

    def list_incidents(self, status: OpsStatus | None = None, limit: int = 1000) -> list[OpsIncident]:
        return self.store.load_incidents(status=status, limit=limit)

    def get_incident(self, incident_id: str) -> OpsIncident | None:
        return self.store.get_incident(incident_id)

    def resolve_incident(self, incident_id: str, resolution_note: str, confirm: bool = False) -> OpsIncident:
        requires_confirm = getattr(self.settings, "OPS_INCIDENT_RESOLVE_REQUIRES_CONFIRM", True) if self.settings else True
        if not confirm and requires_confirm: raise OpsIncidentError("Incident resolution requires explicit confirmation (confirm=True).")
        inc = self.get_incident(incident_id)
        if not inc: raise OpsIncidentError(f"Incident {incident_id} not found.")

        resolved_inc = inc.model_copy()
        resolved_inc.status = OpsStatus.PASS
        resolved_inc.resolved_at = datetime.datetime.now()
        resolved_inc.resolution_note = resolution_note
        self.store.append_incident(resolved_inc)
        return resolved_inc
