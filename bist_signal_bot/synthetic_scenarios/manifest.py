from datetime import timezone
from typing import Any

import uuid
from datetime import datetime
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticScenarioManifest

class SyntheticScenarioManifestBuilder:
    def dataset_refs(self, datasets: list[SyntheticDataset]) -> dict[str, str]:
        return {ds.dataset_id: ds.output_kind.value for ds in datasets}

    def row_counts(self, datasets: list[SyntheticDataset]) -> dict[str, int]:
        return {ds.dataset_id: ds.row_count for ds in datasets}

    def checksum_manifest(self, datasets: list[SyntheticDataset], output_paths: dict[str, str] | None = None) -> dict[str, str]:
        # Fake checksum for now
        return {ds.dataset_id: f"hash_{ds.dataset_id}" for ds in datasets}

    def validate_manifest(self, manifest: SyntheticScenarioManifest) -> list[str]:
        warnings = []
        if not manifest.dataset_refs: warnings.append("No datasets referenced")
        return warnings

    def build_manifest(self, spec: SyntheticScenarioSpec, datasets: list[SyntheticDataset], output_paths: dict[str, str] | None = None) -> SyntheticScenarioManifest:
        return SyntheticScenarioManifest(
            manifest_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            created_at=datetime.now(timezone.utc),
            spec=spec,
            dataset_refs=self.dataset_refs(datasets),
            output_paths=output_paths or {},
            checksum_manifest=self.checksum_manifest(datasets, output_paths),
            row_counts=self.row_counts(datasets),
            validation_status="PENDING"
        )
