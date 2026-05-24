import uuid
from bist_signal_bot.config_registry.models import (
    ConfigModule,
    ConfigSafetyLevel,
    ConfigValidationFinding,
    ConfigValidationStatus,
    ConfigChangeDecision,
    FeatureFlag,
    FeatureFlagState
)


class FeatureFlagManager:
    def __init__(self, store=None):
        self.store = store
        self._flags: dict[str, FeatureFlag] = {}

    def default_flags(self) -> list[FeatureFlag]:
        flags = [
            FeatureFlag(
                flag_id=str(uuid.uuid4()),
                key="ENABLE_SCANNER",
                module=ConfigModule.SCANNER,
                state=FeatureFlagState.ENABLED,
                default_state=FeatureFlagState.ENABLED,
                safety_level=ConfigSafetyLevel.SAFE,
                description="Enable generic scanner engine"
            ),
            FeatureFlag(
                flag_id=str(uuid.uuid4()),
                key="ENABLE_ENSEMBLE_ENGINE",
                module=ConfigModule.STRATEGY,
                state=FeatureFlagState.ENABLED,
                default_state=FeatureFlagState.ENABLED,
                safety_level=ConfigSafetyLevel.SAFE,
                description="Enable strategy ensemble"
            ),
            FeatureFlag(
                flag_id=str(uuid.uuid4()),
                key="ENABLE_TELEGRAM_CENTER",
                module=ConfigModule.TELEGRAM,
                state=FeatureFlagState.DRY_RUN,
                default_state=FeatureFlagState.DRY_RUN,
                safety_level=ConfigSafetyLevel.CAUTION,
                description="Enable Telegram notification center",
                requires_confirm=True
            ),
            FeatureFlag(
                flag_id=str(uuid.uuid4()),
                key="ENABLE_LOCAL_SCHEDULER",
                module=ConfigModule.SCHEDULER,
                state=FeatureFlagState.ENABLED,
                default_state=FeatureFlagState.ENABLED,
                safety_level=ConfigSafetyLevel.CAUTION,
                description="Enable local job scheduler"
            )
        ]
        self._flags = {f.key: f for f in flags}
        return flags

    def load_flags(self) -> list[FeatureFlag]:
        if not self._flags:
            self.default_flags()
        return list(self._flags.values())

    def get_flag(self, key: str) -> FeatureFlag | None:
        if not self._flags:
            self.load_flags()
        return self._flags.get(key)

    def set_flag(self, key: str, state: FeatureFlagState, confirm: bool = False) -> FeatureFlag:
        flag = self.get_flag(key)
        if not flag:
            raise ValueError(f"Unknown flag: {key}")

        if flag.requires_confirm and not confirm:
            raise ValueError(f"Flag {key} requires confirmation to change state")

        if flag.safety_level in [ConfigSafetyLevel.DANGEROUS, ConfigSafetyLevel.FORBIDDEN]:
             raise ValueError(f"Flag {key} has safety level {flag.safety_level} and cannot be modified dynamically")

        flag.state = state
        self._flags[key] = flag
        return flag

    def validate_flag_dependencies(self, flags: list[FeatureFlag]) -> list[ConfigValidationFinding]:
        findings = []
        flag_dict = {f.key: f for f in flags}

        # Simple hardcoded rules for now
        tele_flag = flag_dict.get("ENABLE_TELEGRAM_CENTER")
        if tele_flag and tele_flag.state == FeatureFlagState.ENABLED:
            findings.append(ConfigValidationFinding(
                finding_id=str(uuid.uuid4()),
                title="Telegram Enabled Warning",
                message="Telegram is fully enabled. Ensure bot token is set.",
                status=ConfigValidationStatus.WARN,
                decision=ConfigChangeDecision.WARN,
                key=tele_flag.key,
                module=tele_flag.module
            ))

        return findings
