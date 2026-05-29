import uuid
from typing import Any
from bist_signal_bot.bootstrap.models import RunProfile, RunProfileName

class RunProfileRegistry:
    def __init__(self, settings=None):
        self.settings = settings
        self.profiles = {p.name: p for p in self.default_profiles()}

    def default_profiles(self) -> list[RunProfile]:
        return [
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.MINIMAL,
                title="Minimal Research",
                description="Basic scan and signal generation.",
                enabled_modules=["scanner", "signals", "reports_basic"],
                disabled_modules=["context", "scheduler"]
            ),
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.STANDARD,
                title="Standard Research",
                description="Core signals, risk, basic context fusion.",
                enabled_modules=["scanner", "signals", "risk", "calibration", "context_fusion_light", "review_workflow", "reports"]
            ),
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.FULL_RESEARCH,
                title="Full Research",
                description="All modules active.",
                enabled_modules=["scanner", "signals", "risk", "events", "disclosures", "financials", "factors", "macro", "context_fusion", "review_workflow", "portfolio", "reports"]
            ),
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.QA,
                title="QA Testing",
                description="Testing profile with synthetic fixtures.",
                enabled_modules=["qa", "synthetic_fixtures", "release_gate"],
                env_overrides={"NO_EXTERNAL_CALLS": "true"}
            ),
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.DEMO,
                title="Offline Demo",
                description="Offline synthetic demo workflow.",
                enabled_modules=["offline_synthetic", "demo_workflow", "reports_dry_run"],
                env_overrides={"NO_EXTERNAL_CALLS": "true"}
            ),
            RunProfile(
                profile_id=str(uuid.uuid4()),
                name=RunProfileName.SAFE_MAINTENANCE,
                title="Safe Maintenance",
                description="Operations, backup/restore dry runs.",
                enabled_modules=["ops", "backup", "restore", "doctor", "healthcheck"],
                disabled_modules=["scanner"]
            )
        ]

    def get_profile(self, name: RunProfileName | str) -> RunProfile | None:
        if isinstance(name, str):
            try:
                name = RunProfileName(name)
            except ValueError:
                return None
        return self.profiles.get(name)

    def profile_env(self, profile: RunProfile) -> dict[str, str]:
        return profile.env_overrides

    def validate_profile(self, profile: RunProfile) -> list[str]:
        warnings = []
        if not profile.title:
            warnings.append("Profile title is empty.")
        for k, v in profile.env_overrides.items():
            if "SECRET" in k.upper() or "TOKEN" in k.upper() or "KEY" in k.upper():
                warnings.append(f"Secret detected in env override: {k}")
            if k.upper() in ["ENABLE_BROKER", "LIVE_TRADING"] and str(v).lower() == "true":
                warnings.append(f"BLOCK: Profile enables broker/live trading: {k}")
        return warnings

    def safe_profile_summary(self, profile: RunProfile) -> dict[str, Any]:
        return {
            "name": profile.name,
            "title": profile.title,
            "enabled": profile.enabled_modules,
            "overrides": {k: "***" if "SECRET" in k else v for k, v in profile.env_overrides.items()}
        }
