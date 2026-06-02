
import uuid
from bist_signal_bot.performance.models import ResourceBudget, PerformanceProfile, ResourceMeasurement, PerformanceStatus

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
        return [ResourceBudget(
            budget_id=f"budget_{m}",
            module_name=m,
            max_runtime_seconds=60.0,
            max_memory_mb=2048.0,
            status=PerformanceStatus.PASS
        ) for m in modules]

    def budget_for_module(self, module_name: str) -> ResourceBudget | None:
        budgets = self.default_budgets()
        for b in budgets:
            if b.module_name == module_name:
                return b
        return None

    def evaluate_profile(self, profile: PerformanceProfile, budget: ResourceBudget | None = None) -> list[ResourceMeasurement]:
        return []

    def validate_budget(self, budget: ResourceBudget) -> list[str]:
        errors = []
        if budget.max_runtime_seconds is not None and budget.max_runtime_seconds <= 0:
            errors.append("max_runtime_seconds must be positive")
        return errors

    def classify_budget_status(self, measurements: list[ResourceMeasurement]) -> PerformanceStatus:
        return PerformanceStatus.PASS
