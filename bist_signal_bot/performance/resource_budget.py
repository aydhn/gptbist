from bist_signal_bot.performance.models import ResourceBudget, PerformanceStatus, ResourceMeasurement, ResourceKind

class ResourceBudgetManager:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def default_budgets(self) -> list[ResourceBudget]:
        modules = [
            "bootstrap", "qa", "ops", "docs_hub", "data_catalog", "feature_store",
            "model_registry", "monitoring", "leaderboard", "research_orchestrator",
            "final_audit", "final_handoff", "reports"
        ]
        return [
            ResourceBudget(
                budget_id=f"budget_{m}",
                module_name=m,
                max_runtime_seconds=60.0,
                max_memory_mb=2048.0,
                max_disk_mb=1024.0,
                max_rows=100000,
                status=PerformanceStatus.PASS
            ) for m in modules
        ]

    def budget_for_module(self, module_name: str) -> ResourceBudget | None:
        budgets = self.default_budgets()
        for b in budgets:
            if b.module_name == module_name:
                return b
        return None

    def evaluate_profile(self, profile, budget: ResourceBudget | None = None) -> list[ResourceMeasurement]:
        b = budget or self.budget_for_module(profile.module_name)
        measurements = []
        if not b:
            return measurements
        # Example evaluation
        total_runtime = sum(t.elapsed_seconds or 0 for t in profile.timings)
        status = PerformanceStatus.PASS
        if b.max_runtime_seconds and total_runtime > b.max_runtime_seconds:
            status = PerformanceStatus.SLOW

        # Simplified implementation
        return measurements

    def validate_budget(self, budget: ResourceBudget) -> list[str]:
        warnings = []
        if budget.max_runtime_seconds is not None and budget.max_runtime_seconds <= 0:
            warnings.append("max_runtime_seconds must be positive")
        if budget.max_memory_mb is not None and budget.max_memory_mb <= 0:
            warnings.append("max_memory_mb must be positive")
        return warnings

    def classify_budget_status(self, measurements: list[ResourceMeasurement]) -> PerformanceStatus:
        if any(m.status == PerformanceStatus.FAIL for m in measurements):
            return PerformanceStatus.FAIL
        if any(m.status in [PerformanceStatus.SLOW, PerformanceStatus.DEGRADED] for m in measurements):
            return PerformanceStatus.SLOW
        return PerformanceStatus.PASS
