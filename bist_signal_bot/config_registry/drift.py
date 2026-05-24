import uuid
from datetime import datetime, UTC

from bist_signal_bot.config_registry.diff import ConfigDiffEngine
from bist_signal_bot.config_registry.models import (
    ConfigDiffResult,
    ConfigDriftResult,
    ConfigSafetyLevel,
    ConfigSnapshot,
    ConfigValidationStatus,
    FeatureFlagState,
)


class ConfigDriftDetector:
    def __init__(self, diff_engine: ConfigDiffEngine, store=None):
        self.diff_engine = diff_engine
        self.store = store

    def detect_drift(self, current: ConfigSnapshot, baseline: ConfigSnapshot | None = None) -> ConfigDriftResult:
        if not baseline and self.store:
            baseline = self.store.load_latest_snapshot()

        if not baseline:
            # First run, no baseline to drift from
            return ConfigDriftResult(
                drift_id=str(uuid.uuid4()),
                current_snapshot_id=current.snapshot_id,
                created_at=datetime.now(UTC),
                status=ConfigValidationStatus.PASS,
                drift_score=0.0
            )

        diff = self.diff_engine.diff_snapshots(baseline, current)
        score = self.calculate_drift_score(diff)

        unexpected_flags = self.unexpected_enabled_flags(current, baseline)
        missing_keys = self.missing_required_keys(current)
        unsafe = self.unsafe_changes(diff)

        # Basic drift status logic
        status = ConfigValidationStatus.PASS
        if score > 70.0 or unsafe:
             status = ConfigValidationStatus.FAIL
        elif score > 30.0 or unexpected_flags:
             status = ConfigValidationStatus.WARN

        return ConfigDriftResult(
            drift_id=str(uuid.uuid4()),
            current_snapshot_id=current.snapshot_id,
            baseline_snapshot_id=baseline.snapshot_id,
            created_at=datetime.now(UTC),
            status=status,
            drift_score=score,
            drift_items=diff.items,
            unexpected_enabled_flags=unexpected_flags,
            missing_required_keys=missing_keys,
            unsafe_changes=unsafe
        )

    def calculate_drift_score(self, diff: ConfigDiffResult) -> float:
        score = 0.0
        for item in diff.items:
            if item.safety_level == ConfigSafetyLevel.FORBIDDEN:
                score += 50.0
            elif item.safety_level == ConfigSafetyLevel.DANGEROUS:
                score += 20.0
            elif item.safety_level == ConfigSafetyLevel.SENSITIVE:
                score += 10.0
            elif item.safety_level == ConfigSafetyLevel.CAUTION:
                score += 5.0
            else:
                score += 1.0
        return min(100.0, score)

    def unexpected_enabled_flags(self, current: ConfigSnapshot, baseline: ConfigSnapshot | None = None) -> list[str]:
        unexpected = []
        baseline_flags = {f.key: f for f in baseline.flags} if baseline else {}

        for f in current.flags:
            if f.state == FeatureFlagState.ENABLED:
                if f.key not in baseline_flags or baseline_flags[f.key].state != FeatureFlagState.ENABLED:
                    unexpected.append(f.key)
        return unexpected

    def missing_required_keys(self, snapshot: ConfigSnapshot) -> list[str]:
        # Minimal placeholder. Real implementation would cross-check Schema definition required=True
        return []

    def unsafe_changes(self, diff: ConfigDiffResult) -> list[str]:
        unsafe = []
        for item in diff.items:
            if item.safety_level in [ConfigSafetyLevel.FORBIDDEN, ConfigSafetyLevel.DANGEROUS]:
                unsafe.append(item.key)
        return unsafe
