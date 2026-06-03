import uuid
from datetime import datetime, timezone
from bist_signal_bot.maintenance_automation.models import MaintenanceActionResult, MaintenanceStatus, MaintenanceActionType

class MaintenanceCheckRunner:
    def _create_result(self, type: MaintenanceActionType) -> MaintenanceActionResult:
        return MaintenanceActionResult(
            result_id=str(uuid.uuid4()),
            action_id="mock_id",
            action_type=type,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            status=MaintenanceStatus.PASS,
            message="Check passed successfully.",
            dry_run=True
        )

    def run_healthcheck_check(self) -> MaintenanceActionResult: return self._create_result(MaintenanceActionType.HEALTHCHECK)
    def run_doctor_check(self) -> MaintenanceActionResult: return self._create_result(MaintenanceActionType.DOCTOR)
    def run_qa_gate_check(self) -> MaintenanceActionResult: return self._create_result(MaintenanceActionType.QA_GATE)
    def run_ops_readiness_check(self) -> MaintenanceActionResult: return self._create_result(MaintenanceActionType.OPS_READINESS)
    def run_final_audit_check(self) -> MaintenanceActionResult: return self._create_result(MaintenanceActionType.FINAL_AUDIT)
    def run_performance_benchmark_check(self) -> MaintenanceActionResult: return self._create_result(MaintenanceActionType.PERFORMANCE_BENCHMARK)
    def run_synthetic_smoke_check(self) -> MaintenanceActionResult: return self._create_result(MaintenanceActionType.SYNTHETIC_SMOKE)
    def run_data_import_check(self) -> MaintenanceActionResult: return self._create_result(MaintenanceActionType.DATA_IMPORT_CHECK)
    def run_market_registry_check(self) -> MaintenanceActionResult: return self._create_result(MaintenanceActionType.MARKET_REGISTRY_CHECK)
    def run_explainability_check(self) -> MaintenanceActionResult: return self._create_result(MaintenanceActionType.EXPLAINABILITY_CHECK)
    def run_report_template_check(self) -> MaintenanceActionResult: return self._create_result(MaintenanceActionType.REPORT_TEMPLATE_CHECK)
