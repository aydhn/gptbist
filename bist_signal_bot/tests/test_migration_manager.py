import pytest
from bist_signal_bot.maintenance.migration import MigrationManager

def test_migration_manager_plan_no_op(tmp_path):
    manager = MigrationManager(tmp_path)

    # Defaults to 1.0.0, current is 1.0.0
    plan = manager.plan_migration()
    assert plan.status.value == "NOT_REQUIRED"
    assert len(plan.steps) == 0

def test_migration_manager_requires_confirm(tmp_path):
    manager = MigrationManager(tmp_path)
    plan = manager.plan_migration(to_version="1.0.1")

    assert plan.status.value == "PLANNED"

    with pytest.raises(Exception) as excinfo:
        manager.apply_migration(plan, confirm=False)
    assert "confirm" in str(excinfo.value).lower()
