import json
from pathlib import Path
from typing import Optional
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.research_lab.models import ResearchLabPolicy
from bist_signal_bot.core.exceptions import ResearchLabValidationError

class ResearchLabPolicyManager:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def default_policy(self) -> ResearchLabPolicy:
        s = self.settings

        try:
            from bist_signal_bot.app.config_registry_app import create_config_registry
            registry = create_config_registry(s)

            # Using defaults/overrides from registry if present
            max_jobs = registry.get_record("RESEARCH_LAB_MAX_JOBS")
            if max_jobs:
                setattr(s, "RESEARCH_LAB_MAX_JOBS_PER_BATCH", max_jobs.value)
        except Exception:
            pass

        return ResearchLabPolicy(
            max_jobs_per_batch=getattr(s, "RESEARCH_LAB_MAX_JOBS_PER_BATCH", 20),
            max_parallel_jobs=getattr(s, "RESEARCH_LAB_MAX_PARALLEL_JOBS", 1),
            max_runtime_seconds_per_job=getattr(s, "RESEARCH_LAB_MAX_RUNTIME_SECONDS_PER_JOB", 900),
            max_runtime_seconds_per_batch=getattr(s, "RESEARCH_LAB_MAX_RUNTIME_SECONDS_PER_BATCH", 3600),
            max_memory_mb=getattr(s, "RESEARCH_LAB_MAX_MEMORY_MB", 4096),
            allow_network=getattr(s, "RESEARCH_LAB_ALLOW_NETWORK", False),
            allow_telegram=getattr(s, "RESEARCH_LAB_ALLOW_TELEGRAM", False),
            allow_destructive=getattr(s, "RESEARCH_LAB_ALLOW_DESTRUCTIVE", False),
            require_confirm_for_heavy_jobs=getattr(s, "RESEARCH_LAB_REQUIRE_CONFIRM_FOR_HEAVY_JOBS", True),
            dedupe_window_hours=getattr(s, "RESEARCH_LAB_DEDUPE_WINDOW_HOURS", 24),
            default_max_retries=getattr(s, "RESEARCH_LAB_DEFAULT_MAX_RETRIES", 1),
            retry_backoff_seconds=getattr(s, "RESEARCH_LAB_RETRY_BACKOFF_SECONDS", 30)
        )

    def validate_policy(self, policy: ResearchLabPolicy) -> None:
        if policy.max_jobs_per_batch <= 0:
            raise ResearchLabValidationError("max_jobs_per_batch must be positive")
        if policy.max_parallel_jobs < 1:
            raise ResearchLabValidationError("max_parallel_jobs must be >= 1")
        if policy.max_runtime_seconds_per_job <= 0:
             raise ResearchLabValidationError("max_runtime_seconds_per_job must be positive")

        if policy.allow_network is not True and policy.allow_network is not False:
            policy.allow_network = False
        if policy.allow_telegram is not True and policy.allow_telegram is not False:
            policy.allow_telegram = False
        if policy.allow_destructive is not True and policy.allow_destructive is not False:
            policy.allow_destructive = False

    def load_policy(self, path: Optional[Path] = None) -> ResearchLabPolicy:
        if path and path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pol = ResearchLabPolicy(**data)
                    self.validate_policy(pol)
                    return pol
            except Exception:
                pass
        return self.default_policy()

    def save_policy(self, policy: ResearchLabPolicy, path: Optional[Path] = None, confirm: bool = False) -> Path:
        if not confirm:
            raise ResearchLabValidationError("Cannot save policy without explicit confirmation.")

        self.validate_policy(policy)

        if not path:
             from bist_signal_bot.storage.paths import get_research_lab_dir
             base_dir = get_research_lab_dir(self.settings) / "policy"
             base_dir.mkdir(parents=True, exist_ok=True)
             path = base_dir / "research_lab_policy.json"

        data = policy.dict(exclude={"metadata"})
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return path
