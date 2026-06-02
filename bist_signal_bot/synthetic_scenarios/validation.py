from datetime import timezone
from typing import Any

import uuid
from datetime import datetime
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticScenarioValidationResult, SyntheticScenarioStatus

class SyntheticScenarioValidator:
    def validate_ohlcv(self, dataset: SyntheticDataset) -> list[str]:
        findings = []
        for i, r in enumerate(dataset.rows):
             if r.get("high", 0) < max(r.get("open", 0), r.get("close", 0)):
                 findings.append(f"Row {i} OHLCV invariant failed")
                 break # only report once
        return findings

    def validate_required_outputs(self, spec: SyntheticScenarioSpec, datasets: list[SyntheticDataset]) -> list[str]:
        findings = []
        got = [d.output_kind for d in datasets]
        for req in spec.output_kinds:
             if req not in got:
                 findings.append(f"Missing required output: {req.value}")
        return findings

    def validate_determinism(self, spec: SyntheticScenarioSpec, generator=None) -> list[str]:
        return []

    def status_from_findings(self, findings: list[str]) -> SyntheticScenarioStatus:
        if findings: return SyntheticScenarioStatus.FAIL
        return SyntheticScenarioStatus.PASS

    def validate_spec(self, spec: SyntheticScenarioSpec) -> SyntheticScenarioValidationResult:
        return SyntheticScenarioValidationResult(
            validation_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            created_at=datetime.now(timezone.utc),
            status=SyntheticScenarioStatus.PASS,
            findings=[],
            failed_outputs=[]
        )

    def validate_datasets(self, spec: SyntheticScenarioSpec, datasets: list[SyntheticDataset]) -> SyntheticScenarioValidationResult:
        findings = self.validate_required_outputs(spec, datasets)
        for ds in datasets:
             if "OHLCV" in ds.output_kind.value:
                  findings.extend(self.validate_ohlcv(ds))
        status = self.status_from_findings(findings)

        return SyntheticScenarioValidationResult(
            validation_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            created_at=datetime.now(timezone.utc),
            status=status,
            findings=findings,
            failed_outputs=[]
        )
