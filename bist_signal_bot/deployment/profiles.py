from typing import Any, Dict, List
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.deployment.models import DeploymentProfile, DeploymentProfileType

class DeploymentProfileManager:
    def default_profiles(self) -> List[DeploymentProfile]:
        return [
            DeploymentProfile(
                profile_id="prof_research_only",
                profile_type=DeploymentProfileType.RESEARCH_ONLY,
                name="RESEARCH_ONLY",
                description="Safest default. No broker, no real order, no telegram send. Scheduler dry-run.",
                settings_overrides={
                    "ALLOW_BROKER": False,
                    "FORCE_RESEARCH_ONLY": True,
                    "DISABLE_TELEGRAM_SEND": True,
                    "SCHEDULER_DRY_RUN_DEFAULT": True,
                    "ENABLE_PAPER_TRADING": False
                },
                safe_defaults=True,
                telegram_send_enabled=False,
                scheduler_dry_run=True,
                broker_enabled=False,
                real_order_enabled=False
            ),
            DeploymentProfile(
                profile_id="prof_paper_research",
                profile_type=DeploymentProfileType.PAPER_RESEARCH,
                name="PAPER_RESEARCH",
                description="Paper simulation enabled. No real order, no broker. Telegram dry-run.",
                settings_overrides={
                    "ALLOW_BROKER": False,
                    "FORCE_RESEARCH_ONLY": True,
                    "DISABLE_TELEGRAM_SEND": True,
                    "SCHEDULER_DRY_RUN_DEFAULT": True,
                    "ENABLE_PAPER_TRADING": True
                },
                safe_defaults=True,
                telegram_send_enabled=False,
                scheduler_dry_run=True,
                broker_enabled=False,
                real_order_enabled=False
            ),
            DeploymentProfile(
                profile_id="prof_telegram_dry_run",
                profile_type=DeploymentProfileType.TELEGRAM_DRY_RUN,
                name="TELEGRAM_DRY_RUN",
                description="Telegram commands dry-run. Send disabled. Unknown chat block.",
                settings_overrides={
                    "ALLOW_BROKER": False,
                    "FORCE_RESEARCH_ONLY": True,
                    "DISABLE_TELEGRAM_SEND": True,
                    "SCHEDULER_DRY_RUN_DEFAULT": True,
                    "ENABLE_TELEGRAM_CENTER": True
                },
                safe_defaults=True,
                telegram_send_enabled=False,
                scheduler_dry_run=True,
                broker_enabled=False,
                real_order_enabled=False
            ),
            DeploymentProfile(
                profile_id="prof_local_scheduler_dry_run",
                profile_type=DeploymentProfileType.LOCAL_SCHEDULER_DRY_RUN,
                name="LOCAL_SCHEDULER_DRY_RUN",
                description="Scheduler enabled. All jobs dry-run. No telegram send.",
                settings_overrides={
                    "ALLOW_BROKER": False,
                    "FORCE_RESEARCH_ONLY": True,
                    "DISABLE_TELEGRAM_SEND": True,
                    "SCHEDULER_DRY_RUN_DEFAULT": True,
                    "ENABLE_LOCAL_SCHEDULER": True
                },
                safe_defaults=True,
                telegram_send_enabled=False,
                scheduler_dry_run=True,
                broker_enabled=False,
                real_order_enabled=False
            ),
            DeploymentProfile(
                profile_id="prof_full_local_safe",
                profile_type=DeploymentProfileType.FULL_LOCAL_SAFE,
                name="FULL_LOCAL_SAFE",
                description="Research stack enabled. Paper simulation enabled. Scheduler safe. Telegram dry-run.",
                settings_overrides={
                    "ALLOW_BROKER": False,
                    "FORCE_RESEARCH_ONLY": True,
                    "DISABLE_TELEGRAM_SEND": True,
                    "SCHEDULER_DRY_RUN_DEFAULT": True,
                    "ENABLE_PAPER_TRADING": True,
                    "ENABLE_LOCAL_SCHEDULER": True,
                    "ENABLE_TELEGRAM_CENTER": True,
                    "GOVERNANCE_REQUIRE_RELEASE_GATE": True
                },
                safe_defaults=True,
                telegram_send_enabled=False,
                scheduler_dry_run=True,
                broker_enabled=False,
                real_order_enabled=False
            ),
            DeploymentProfile(
                profile_id="prof_development",
                profile_type=DeploymentProfileType.DEVELOPMENT,
                name="DEVELOPMENT",
                description="Test paths. Verbose logs. External sends disabled.",
                settings_overrides={
                    "ALLOW_BROKER": False,
                    "FORCE_RESEARCH_ONLY": True,
                    "DISABLE_TELEGRAM_SEND": True,
                    "SCHEDULER_DRY_RUN_DEFAULT": True,
                    "LOG_LEVEL": "DEBUG"
                },
                safe_defaults=True,
                telegram_send_enabled=False,
                scheduler_dry_run=True,
                broker_enabled=False,
                real_order_enabled=False
            )
        ]

    def get_profile(self, profile_type: DeploymentProfileType) -> DeploymentProfile:
        for profile in self.default_profiles():
            if profile.profile_type == profile_type:
                return profile
        # Fallback to custom / research_only
        return self.default_profiles()[0]

    def apply_profile_to_settings(self, profile: DeploymentProfile, settings: Settings) -> Dict[str, Any]:
        applied = {}
        for key, value in profile.settings_overrides.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
                applied[key] = value
        return applied

    def validate_profile(self, profile: DeploymentProfile) -> List[str]:
        errors = []
        if getattr(profile, "real_order_enabled", False):
            errors.append("Profile enables real orders, which is forbidden.")
        if getattr(profile, "broker_enabled", False):
            errors.append("Profile enables broker, which is forbidden.")
        if not profile.name:
            errors.append("Profile name cannot be empty.")
        if getattr(profile.settings_overrides, "ALLOW_BROKER", False):
            errors.append("ALLOW_BROKER override is True, which is forbidden.")
        return errors
