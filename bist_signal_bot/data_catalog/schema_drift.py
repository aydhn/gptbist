import uuid

import pandas as pd

from bist_signal_bot.data_catalog.models import (
    DataQualityStatus,
    DatasetContract,
    DatasetProfile,
    DatasetRecord,
    SchemaDriftFinding,
    SchemaDriftType,
)
from bist_signal_bot.config.settings import Settings, get_settings


class SchemaDriftDetector:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def detect_drift(self, dataset: DatasetRecord, contract: DatasetContract, profile: DatasetProfile | None = None) -> list[SchemaDriftFinding]:
        if not profile:
            return []

        findings = []
        findings.extend(self.missing_columns(profile, contract))
        findings.extend(self.extra_columns(profile, contract))
        # Type and date format changes would ideally require the sample df
        return findings

    def missing_columns(self, profile: DatasetProfile, contract: DatasetContract) -> list[SchemaDriftFinding]:
        findings = []
        for col in contract.required_columns:
            if col not in profile.columns:
                findings.append(SchemaDriftFinding(
                    drift_id=f"drf_{uuid.uuid4().hex[:12]}",
                    dataset_id=profile.dataset_id,
                    contract_id=contract.contract_id,
                    drift_type=SchemaDriftType.MISSING_COLUMN,
                    column_name=col,
                    expected="Present",
                    actual="Missing",
                    severity="HIGH",
                    message=f"Required column '{col}' is missing."
                ))
        return findings

    def extra_columns(self, profile: DatasetProfile, contract: DatasetContract) -> list[SchemaDriftFinding]:
        findings = []
        expected_cols = set(contract.required_columns + contract.optional_columns)

        # If contract defines no columns at all, don't flag everything as extra
        if not expected_cols:
             return findings

        for col in profile.columns:
            if col not in expected_cols:
                findings.append(SchemaDriftFinding(
                    drift_id=f"drf_{uuid.uuid4().hex[:12]}",
                    dataset_id=profile.dataset_id,
                    contract_id=contract.contract_id,
                    drift_type=SchemaDriftType.EXTRA_COLUMN,
                    column_name=col,
                    expected="Not Present",
                    actual="Present",
                    severity="LOW",
                    message=f"Undocumented extra column '{col}' found."
                ))
        return findings

    def type_changes(self, profile: DatasetProfile, contract: DatasetContract, sample: pd.DataFrame | None = None) -> list[SchemaDriftFinding]:
        return []

    def date_format_changes(self, profile: DatasetProfile, contract: DatasetContract, sample: pd.DataFrame | None = None) -> list[SchemaDriftFinding]:
        return []

    def classify_drift(self, findings: list[SchemaDriftFinding]) -> DataQualityStatus:
        if not findings:
            return DataQualityStatus.PASS

        if any(f.severity == "HIGH" for f in findings):
            return DataQualityStatus.FAIL

        return DataQualityStatus.WATCH
