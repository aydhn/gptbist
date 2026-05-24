import uuid
from copy import deepcopy

from bist_signal_bot.config_registry.models import (
    ConfigChangeDecision,
    ConfigDiffItem,
    ConfigDiffResult,
    ConfigModule,
    ConfigSafetyLevel,
    ConfigValidationFinding,
    ConfigValidationStatus,
    FeatureFlagState,
    RuntimeProfile,
    RuntimeProfileType,
)


class RuntimeProfileManager:
    def __init__(self, store=None):
        self.store = store
        self._profiles: dict[RuntimeProfileType, RuntimeProfile] = {}
        self._current_profile: RuntimeProfile | None = None

    def default_profiles(self) -> list[RuntimeProfile]:
        profiles = [
            RuntimeProfile(
                profile_id=str(uuid.uuid4()),
                profile_type=RuntimeProfileType.RESEARCH_ONLY,
                name="Research Only",
                description="Strict research mode. No execution, dry runs enabled.",
                force_research_only=True,
                telegram_send_enabled=False,
                scheduler_dry_run=True,
                overrides={"LOG_LEVEL": "INFO"}
            ),
            RuntimeProfile(
                profile_id=str(uuid.uuid4()),
                profile_type=RuntimeProfileType.TELEGRAM_DRY_RUN,
                name="Telegram Dry Run",
                description="Tests telegram notifications locally.",
                force_research_only=True,
                telegram_send_enabled=True,
                scheduler_dry_run=True,
                feature_flags={"ENABLE_TELEGRAM_CENTER": FeatureFlagState.DRY_RUN}
            ),
            RuntimeProfile(
                profile_id=str(uuid.uuid4()),
                profile_type=RuntimeProfileType.FULL_LOCAL_SAFE,
                name="Full Local Safe",
                description="Local end-to-end simulation.",
                force_research_only=True,
                telegram_send_enabled=False,
                scheduler_dry_run=True
            )
        ]
        self._profiles = {p.profile_type: p for p in profiles}
        return profiles

    def get_profile(self, profile_type: RuntimeProfileType) -> RuntimeProfile:
        if not self._profiles:
            self.default_profiles()
        if profile_type not in self._profiles:
            raise ValueError(f"Unknown profile type: {profile_type}")
        return self._profiles[profile_type]

    def apply_profile(self, profile_type: RuntimeProfileType, confirm: bool = False) -> RuntimeProfile:
        if not confirm:
            raise ValueError("Applying a runtime profile requires confirmation")
        profile = self.get_profile(profile_type)
        self._current_profile = profile
        return profile

    def preview_profile(self, profile_type: RuntimeProfileType) -> ConfigDiffResult:
        from datetime import datetime, UTC
        profile = self.get_profile(profile_type)
        items = []
        for key, val in profile.overrides.items():
            items.append(ConfigDiffItem(
                key=key,
                change_type="CHANGED",
                old_value_redacted="<current>",
                new_value_redacted=str(val),
                safety_level=ConfigSafetyLevel.SAFE,
                decision=ConfigChangeDecision.ALLOW
            ))

        return ConfigDiffResult(
            diff_id=str(uuid.uuid4()),
            created_at=datetime.now(UTC),
            items=items,
            changed_count=len(items)
        )

    def validate_profile(self, profile: RuntimeProfile) -> list[ConfigValidationFinding]:
        findings = []
        if profile.broker_enabled or profile.real_order_enabled:
            findings.append(ConfigValidationFinding(
                finding_id=str(uuid.uuid4()),
                title="Invalid Profile Configuration",
                message="Profiles cannot enable broker or real orders",
                status=ConfigValidationStatus.FAIL,
                decision=ConfigChangeDecision.BLOCK_FORBIDDEN
            ))
        return findings
