import uuid
from typing import Any, Optional

from bist_signal_bot.performance.models import (
    PerformanceProfile,
    PerformanceStatus,
    ResourceBudget,
    ResourceKind,
    ResourceMeasurement,
)
from bist_signal_bot.core.exceptions import BistSignalBotError

class ResourceBudgetError(BistSignalBotError):
    pass

class ResourceBudgetManager:
    def __init__(self, settings: Any = None, base_dir: Any = None):
        self.settings = settings
        self.base_dir = base_dir

        self.default_runtime = 60.0
        self.default_memory = 2048.0
        self.default_disk = 1024.0

        if self.settings:
            self.default_runtime = getattr(self.settings, "PERFORMANCE_DEFAULT_MAX_RUNTIME_SECONDS", self.default_runtime)
            self.default_memory = getattr(self.settings, "PERFORMANCE_DEFAULT_MAX_MEMORY_MB", self.default_memory)
            self.default_disk = getattr(self.settings, "PERFORMANCE_DEFAULT_MAX_DISK_MB", self.default_disk)

    def default_budgets(self) -> list[ResourceBudget]:
        modules = [
            "bootstrap",
            "qa",
            "ops",
            "docs_hub",
            "data_catalog",
            "feature_store",
            "model_registry",
            "monitoring",
            "leaderboard",
            "research_orchestrator",
            "final_audit",
            "final_handoff",
            "reports"
        ]

        budgets = []
        for m in modules:
            budgets.append(
                ResourceBudget(
                    budget_id=str(uuid.uuid4()),
                    module_name=m,
                    max_runtime_seconds=self.default_runtime,
                    max_memory_mb=self.default_memory,
                    max_disk_mb=self.default_disk,
                    status=PerformanceStatus.PASS
                )
            )

        return budgets

    def budget_for_module(self, module_name: str) -> Optional[ResourceBudget]:
        budgets = self.default_budgets()
        for b in budgets:
            if b.module_name == module_name:
                return b
        return None

    def evaluate_profile(self, profile: PerformanceProfile, budget: Optional[ResourceBudget] = None) -> list[ResourceMeasurement]:
        budget = budget or self.budget_for_module(profile.module_name)
        if not budget:
            return profile.resources

        evaluated = []
        for res in profile.resources:
            new_res = res.model_copy()

            if res.resource_kind == ResourceKind.RUNTIME and budget.max_runtime_seconds and res.value:
                new_res.threshold = budget.max_runtime_seconds
                if res.value > budget.max_runtime_seconds:
                    new_res.status = PerformanceStatus.SLOW
                    new_res.warnings.append(f"Runtime {res.value}s exceeds budget {budget.max_runtime_seconds}s")

            elif res.resource_kind == ResourceKind.MEMORY and budget.max_memory_mb and res.value:
                new_res.threshold = budget.max_memory_mb
                if res.value > budget.max_memory_mb:
                    new_res.status = PerformanceStatus.FAIL
                    new_res.warnings.append(f"Memory {res.value}MB exceeds budget {budget.max_memory_mb}MB")

            elif res.resource_kind == ResourceKind.DISK and budget.max_disk_mb and res.value:
                new_res.threshold = budget.max_disk_mb
                if res.value > budget.max_disk_mb:
                    new_res.status = PerformanceStatus.FAIL
                    new_res.warnings.append(f"Disk {res.value}MB exceeds budget {budget.max_disk_mb}MB")

            evaluated.append(new_res)

        return evaluated

    def validate_budget(self, budget: ResourceBudget) -> list[str]:
        errors = []
        if budget.max_runtime_seconds is not None and budget.max_runtime_seconds <= 0:
            errors.append("max_runtime_seconds must be positive")
        if budget.max_memory_mb is not None and budget.max_memory_mb <= 0:
            errors.append("max_memory_mb must be positive")
        if budget.max_disk_mb is not None and budget.max_disk_mb <= 0:
            errors.append("max_disk_mb must be positive")
        if budget.max_rows is not None and budget.max_rows <= 0:
            errors.append("max_rows must be positive")
        if budget.max_cache_age_seconds is not None and budget.max_cache_age_seconds <= 0:
            errors.append("max_cache_age_seconds must be positive")
        return errors

    def classify_budget_status(self, measurements: list[ResourceMeasurement]) -> PerformanceStatus:
        statuses = [m.status for m in measurements]
        if PerformanceStatus.FAIL in statuses:
            return PerformanceStatus.FAIL
        if PerformanceStatus.SLOW in statuses:
            return PerformanceStatus.SLOW
        if PerformanceStatus.WATCH in statuses:
            return PerformanceStatus.WATCH
        return PerformanceStatus.PASS
