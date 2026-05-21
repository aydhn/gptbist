from pathlib import Path
from bist_signal_bot.maintenance.models import RetentionPolicy, RetentionTarget
from bist_signal_bot.config.settings import get_settings

class RetentionPolicyManager:
    @staticmethod
    def default_policies() -> list[RetentionPolicy]:
        settings = get_settings()
        # Fallbacks in case settings are missing or not correctly mapping the exact names
        keep_min = getattr(settings, 'RETENTION_KEEP_MIN_COUNT', 10)
        return [
            RetentionPolicy(target=RetentionTarget.LOGS, keep_days=getattr(settings, 'RETENTION_LOGS_DAYS', 30), keep_min_count=keep_min),
            RetentionPolicy(target=RetentionTarget.REPORTS, keep_days=getattr(settings, 'RETENTION_REPORTS_DAYS', 180), keep_min_count=keep_min),
            RetentionPolicy(target=RetentionTarget.SCENARIOS, keep_days=getattr(settings, 'RETENTION_SCENARIOS_DAYS', 90), keep_min_count=keep_min),
            RetentionPolicy(target=RetentionTarget.STRESS_RESULTS, keep_days=getattr(settings, 'RETENTION_STRESS_DAYS', 180), keep_min_count=keep_min),
            RetentionPolicy(target=RetentionTarget.DRIFT_RESULTS, keep_days=getattr(settings, 'RETENTION_DRIFT_DAYS', 180), keep_min_count=keep_min),
            RetentionPolicy(target=RetentionTarget.RESEARCH_LAB_RUNS, keep_days=getattr(settings, 'RETENTION_RESEARCH_LAB_DAYS', 180), keep_min_count=keep_min),
            RetentionPolicy(target=RetentionTarget.TEMP, keep_days=getattr(settings, 'RETENTION_TEMP_DAYS', 7), keep_min_count=0),
            RetentionPolicy(target=RetentionTarget.SIGNALS, keep_days=getattr(settings, 'RETENTION_SIGNALS_DAYS', 365), keep_min_count=keep_min),
            RetentionPolicy(target=RetentionTarget.CACHE, keep_days=90, keep_min_count=keep_min),
            RetentionPolicy(target=RetentionTarget.RELEASE_RUNS, keep_days=180, keep_min_count=keep_min),
            RetentionPolicy(target=RetentionTarget.RESEARCH_LEDGER, keep_days=3650, keep_min_count=1, enabled=False), # default off
            RetentionPolicy(target=RetentionTarget.MARKET_DATA, keep_days=3650, keep_min_count=1, enabled=False), # default off
            RetentionPolicy(target=RetentionTarget.MODEL_ARTIFACTS, keep_days=3650, keep_min_count=1, enabled=False), # default off
        ]

    @staticmethod
    def load_policies(path: Path | None = None) -> list[RetentionPolicy]:
        if path and path.exists():
            import json
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return [RetentionPolicy.model_validate(p) for p in data]
            except Exception:
                pass
        return RetentionPolicyManager.default_policies()

    @staticmethod
    def save_policies(policies: list[RetentionPolicy], path: Path, confirm: bool = False) -> Path:
        if not confirm:
            raise ValueError("Confirm required to save policies")
        path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in policies], f, indent=2)
        return path

    @staticmethod
    def policy_for_target(target: RetentionTarget, policies: list[RetentionPolicy] | None = None) -> RetentionPolicy:
        policies = policies or RetentionPolicyManager.default_policies()
        for p in policies:
            if p.target == target:
                return p
        return RetentionPolicy(target=target, keep_days=30, keep_min_count=10)
