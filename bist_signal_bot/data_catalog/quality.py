import uuid
from datetime import datetime, timezone

import pandas as pd

from bist_signal_bot.data_catalog.models import (
    DataQualityAssessment,
    DataQualityFinding,
    DataQualityStatus,
    DatasetContract,
    DatasetProfile,
    DatasetRecord,
)
from bist_signal_bot.config.settings import Settings, get_settings


class DataQualityEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def assess(self, dataset: DatasetRecord, contract: DatasetContract | None = None, profile: DatasetProfile | None = None) -> DataQualityAssessment:
        findings = []
        warnings = []

        if not profile:
            return DataQualityAssessment(
                assessment_id=f"dqa_{uuid.uuid4().hex[:12]}",
                dataset_id=dataset.dataset_id,
                created_at=datetime.now(timezone.utc),
                status=DataQualityStatus.INSUFFICIENT_DATA,
                warnings=["No profile available for assessment."]
            )

        if contract:
            findings.extend(self.check_required_columns(profile, contract))
            findings.extend(self.check_null_ratios(profile, contract))
            findings.extend(self.check_duplicates(profile, contract))
            findings.extend(self.check_freshness(dataset, contract))
            if self.settings.DATA_QUALITY_OUTLIER_CHECK_ENABLED:
                findings.extend(self.check_outliers(profile, contract))
        else:
            warnings.append("No contract available. Performing generic quality checks only.")

        score = self.quality_score(findings)
        status = self.status_from_score(score, findings)

        return DataQualityAssessment(
            assessment_id=f"dqa_{uuid.uuid4().hex[:12]}",
            dataset_id=dataset.dataset_id,
            created_at=datetime.now(timezone.utc),
            quality_score=score,
            status=status,
            findings=findings,
            profile_ref=profile.profile_id,
            contract_ref=contract.contract_id if contract else None,
            warnings=warnings
        )

    def check_required_columns(self, profile: DatasetProfile, contract: DatasetContract) -> list[DataQualityFinding]:
        findings = []
        missing = [col for col in contract.required_columns if col not in profile.columns]

        if missing:
             findings.append(DataQualityFinding(
                 finding_id=f"dqf_{uuid.uuid4().hex[:12]}",
                 dataset_id=profile.dataset_id,
                 rule_name="required_columns",
                 status=DataQualityStatus.FAIL if self.settings.DATA_CATALOG_FAIL_ON_MISSING_REQUIRED_COLUMNS else DataQualityStatus.WATCH,
                 severity="HIGH",
                 message=f"Missing required columns: {missing}",
                 affected_columns=missing
             ))
        else:
             findings.append(DataQualityFinding(
                 finding_id=f"dqf_{uuid.uuid4().hex[:12]}",
                 dataset_id=profile.dataset_id,
                 rule_name="required_columns",
                 status=DataQualityStatus.PASS,
                 severity="INFO",
                 message="All required columns present.",
                 affected_columns=contract.required_columns
             ))
        return findings

    def check_column_types(self, profile: DatasetProfile, contract: DatasetContract, sample: pd.DataFrame | None = None) -> list[DataQualityFinding]:
        # Typically checked in schema drift, but could be a quality rule
        return []

    def check_null_ratios(self, profile: DatasetProfile, contract: DatasetContract) -> list[DataQualityFinding]:
        findings = []
        max_allowed = contract.max_null_ratio if contract.max_null_ratio is not None else self.settings.DATA_QUALITY_MAX_NULL_RATIO

        violating_cols = []
        for col, ratio in profile.null_ratios.items():
            if ratio > max_allowed:
                violating_cols.append(col)

        if violating_cols:
             findings.append(DataQualityFinding(
                 finding_id=f"dqf_{uuid.uuid4().hex[:12]}",
                 dataset_id=profile.dataset_id,
                 rule_name="null_ratios",
                 status=DataQualityStatus.WATCH,
                 severity="MEDIUM",
                 message=f"Null ratio exceeds {max_allowed} for columns: {violating_cols}",
                 affected_columns=violating_cols
             ))
        return findings

    def check_duplicates(self, profile: DatasetProfile, contract: DatasetContract) -> list[DataQualityFinding]:
        findings = []
        threshold = self.settings.DATA_QUALITY_DUPLICATE_WARN_THRESHOLD

        if profile.duplicate_count > threshold:
             status = DataQualityStatus.FAIL if contract.duplicate_policy == "FAIL" else DataQualityStatus.WATCH
             findings.append(DataQualityFinding(
                 finding_id=f"dqf_{uuid.uuid4().hex[:12]}",
                 dataset_id=profile.dataset_id,
                 rule_name="duplicates",
                 status=status,
                 severity="MEDIUM",
                 message=f"Found {profile.duplicate_count} duplicate rows (threshold {threshold}).",
                 affected_rows_count=profile.duplicate_count
             ))
        return findings

    def check_freshness(self, dataset: DatasetRecord, contract: DatasetContract) -> list[DataQualityFinding]:
        findings = []
        # If no last_seen or imported_at, use registered_at
        ref_time = dataset.last_seen_at or dataset.registered_at
        now = datetime.now(timezone.utc)

        days_old = (now - ref_time).days
        threshold = contract.freshness_threshold_days or self.settings.DATA_CATALOG_DEFAULT_FRESHNESS_DAYS

        if days_old > threshold:
             findings.append(DataQualityFinding(
                 finding_id=f"dqf_{uuid.uuid4().hex[:12]}",
                 dataset_id=dataset.dataset_id,
                 rule_name="freshness",
                 status=DataQualityStatus.WATCH,
                 severity="MEDIUM",
                 message=f"Dataset is {days_old} days old. Threshold is {threshold} days."
             ))
        return findings

    def check_outliers(self, profile: DatasetProfile, contract: DatasetContract) -> list[DataQualityFinding]:
        # Placeholder for basic outlier checks based on numeric ranges
        return []

    def quality_score(self, findings: list[DataQualityFinding]) -> float | None:
        if not findings:
            return 100.0

        base_score = 100.0
        for f in findings:
            if f.status == DataQualityStatus.FAIL:
                base_score -= 20.0
            elif f.status == DataQualityStatus.WATCH:
                base_score -= 5.0

        return max(0.0, base_score)

    def status_from_score(self, score: float | None, findings: list[DataQualityFinding]) -> DataQualityStatus:
        if any(f.status == DataQualityStatus.BLOCKED for f in findings):
            return DataQualityStatus.BLOCKED
        if any(f.status == DataQualityStatus.FAIL for f in findings):
            return DataQualityStatus.FAIL

        if score is None:
            return DataQualityStatus.UNKNOWN

        if score >= self.settings.DATA_QUALITY_PASS_SCORE:
            return DataQualityStatus.PASS
        elif score >= self.settings.DATA_QUALITY_WATCH_SCORE:
            return DataQualityStatus.WATCH
        else:
            return DataQualityStatus.FAIL
