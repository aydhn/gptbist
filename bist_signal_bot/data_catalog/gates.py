import uuid
from datetime import datetime, timezone

from bist_signal_bot.data_catalog.models import (
    DataQualityAssessment,
    DataQualityGateResult,
    DataQualityStatus,
    SchemaDriftFinding,
)
from bist_signal_bot.config.settings import Settings, get_settings


class DataQualityGateEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def run_gate(
        self,
        assessment: DataQualityAssessment | None = None,
        drift_findings: list[SchemaDriftFinding] | None = None,
        dataset_id: str | None = None,
        gate_name: str = "default"
    ) -> DataQualityGateResult:

        required_score = self.settings.DATA_QUALITY_GATE_REQUIRED_SCORE

        if not self.settings.DATA_QUALITY_GATES_ENABLED:
            return DataQualityGateResult(
                gate_id=f"dqg_{uuid.uuid4().hex[:12]}",
                dataset_id=dataset_id,
                gate_name=gate_name,
                created_at=datetime.now(timezone.utc),
                status=DataQualityStatus.PASS,
                required_score=required_score,
                actual_score=assessment.quality_score if assessment else None,
                warnings=["Data quality gates are disabled by configuration."]
            )

        blockers = self.blocking_findings(assessment, drift_findings)
        status = self.status_from_assessment(assessment, required_score)

        if blockers:
             status = DataQualityStatus.BLOCKED

        actual_score = assessment.quality_score if assessment else None

        return DataQualityGateResult(
            gate_id=f"dqg_{uuid.uuid4().hex[:12]}",
            dataset_id=dataset_id,
            gate_name=gate_name,
            created_at=datetime.now(timezone.utc),
            status=status,
            required_score=required_score,
            actual_score=actual_score,
            blocking_findings=blockers
        )

    def run_all_gates(self) -> list[DataQualityGateResult]:
        return []

    def gate_for_module(self, module_name: str) -> DataQualityGateResult:
        return self.run_gate(gate_name=f"{module_name}_gate")

    def blocking_findings(self, assessment: DataQualityAssessment | None, drift_findings: list[SchemaDriftFinding] | None = None) -> list[str]:
        blockers = []
        if assessment:
            for f in assessment.findings:
                if f.status in (DataQualityStatus.FAIL, DataQualityStatus.BLOCKED):
                    blockers.append(f"Assessment Finding: {f.message}")

        if drift_findings and self.settings.DATA_QUALITY_GATE_BLOCK_ON_CRITICAL_SCHEMA_DRIFT:
             for d in drift_findings:
                 if d.severity == "HIGH":
                     blockers.append(f"Schema Drift: {d.message}")

        if not assessment and self.settings.DATA_QUALITY_GATE_BLOCK_ON_MISSING_REQUIRED_DATASET:
             blockers.append("Missing required dataset assessment.")

        return blockers

    def status_from_assessment(self, assessment: DataQualityAssessment | None, required_score: float | None) -> DataQualityStatus:
        if not assessment:
             return DataQualityStatus.UNKNOWN

        if assessment.status in (DataQualityStatus.FAIL, DataQualityStatus.BLOCKED):
             return assessment.status

        if required_score is not None and assessment.quality_score is not None:
             if assessment.quality_score < required_score:
                  return DataQualityStatus.FAIL

        return assessment.status
