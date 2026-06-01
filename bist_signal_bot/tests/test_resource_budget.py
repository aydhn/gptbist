import pytest
from bist_signal_bot.performance.resource_budget import ResourceBudgetManager
from bist_signal_bot.performance.models import ResourceBudget, PerformanceStatus

def test_resource_budget_validation():
    manager = ResourceBudgetManager()

    budget_ok = ResourceBudget(
        budget_id="1",
        module_name="test",
        max_runtime_seconds=10.0,
        status=PerformanceStatus.PASS
    )
    assert not manager.validate_budget(budget_ok)

    budget_bad = ResourceBudget(
        budget_id="2",
        module_name="test",
        max_runtime_seconds=-1.0,
        status=PerformanceStatus.PASS
    )
    errors = manager.validate_budget(budget_bad)
    assert len(errors) == 1
    assert "positive" in errors[0]

def test_resource_budget_defaults():
    manager = ResourceBudgetManager()
    budgets = manager.default_budgets()
    assert len(budgets) > 0
    names = [b.module_name for b in budgets]
    assert "feature_store" in names
