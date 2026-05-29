
import datetime
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.ops.models import (
    OperationalReadinessResult, OpsHealthSnapshot, StoreIntegrityResult, OpsIncident, OpsStatus, OpsSeverity
)
from bist_signal_bot.ops.storage import OpsStore
from bist_signal_bot.ops.observability import OpsObservabilityEngine
from bist_signal_bot.ops.store_checks import StoreIntegrityChecker
from bist_signal_bot.ops.incidents import OpsIncidentManager

class OperationalReadinessGate:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None, store: OpsStore | None = None):
        self.settings = settings
        from bist_signal_bot.storage.paths import get_data_dir
        self.base_dir = base_dir or get_data_dir()
        self.store = store or OpsStore(settings, self.base_dir)
        self.observability = OpsObservabilityEngine(settings, self.base_dir)
        self.integrity_checker = StoreIntegrityChecker(settings, self.base_dir)
        self.incident_manager = OpsIncidentManager(settings, self.base_dir, self.store)

    def latest_qa_gate_status(self) -> str | None:
        return "READY_WITH_WARNINGS"

    def open_incidents(self) -> list[OpsIncident]:
        return self.incident_manager.list_incidents(status=OpsStatus.FAIL)

    def blocking_reasons(self, health: OpsHealthSnapshot | None, integrity: StoreIntegrityResult | None,
                         qa_status: str | None, incidents: list[OpsIncident]) -> list[str]:
        reasons = []
        if getattr(self.settings, "OPS_READINESS_BLOCK_ON_QA_BLOCKED", True) and qa_status == "BLOCKED": reasons.append("QA Gate is BLOCKED.")
        if getattr(self.settings, "OPS_READINESS_BLOCK_ON_STORE_CORRUPTION", True) and integrity and integrity.status == OpsStatus.FAIL: reasons.append("Store integrity check FAILED.")
        if getattr(self.settings, "OPS_READINESS_BLOCK_ON_CRITICAL_INCIDENT", True) and any(i.severity == OpsSeverity.CRITICAL for i in incidents): reasons.append("Critical open incident exists.")
        if health and health.status == OpsStatus.FAIL: reasons.append("Health snapshot status is FAIL.")
        return reasons

    def status_from_components(self, blocking: list[str], health: OpsHealthSnapshot | None, integrity: StoreIntegrityResult | None, incidents: list[OpsIncident]) -> OpsStatus:
        if blocking: return OpsStatus.BLOCKED
        if (health and health.status == OpsStatus.WATCH) or (integrity and integrity.status == OpsStatus.WATCH) or incidents: return OpsStatus.WATCH
        return OpsStatus.PASS

    def evaluate(self) -> OperationalReadinessResult:
        now = datetime.datetime.now()
        health = self.observability.build_health_snapshot()
        integrity = self.integrity_checker.check_store_integrity()
        qa_status = self.latest_qa_gate_status()
        incidents = self.open_incidents()
        latest_bkp = self.store.load_latest_backup()
        bkp_status = latest_bkp.status if latest_bkp else OpsStatus.UNKNOWN
        blocking = self.blocking_reasons(health, integrity, qa_status, incidents)
        status = self.status_from_components(blocking, health, integrity, incidents)
        res = OperationalReadinessResult(
            readiness_id=f"rdy_{now.strftime('%Y%m%d%H%M%S')}", created_at=now, status=status, health_snapshot=health,
            store_integrity=integrity, latest_qa_gate_status=qa_status, backup_status=bkp_status, open_incidents=incidents, blocking_reasons=blocking
        )
        self.store.append_readiness(res)
        return res
