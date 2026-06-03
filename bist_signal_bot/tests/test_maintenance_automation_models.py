import pytest
from bist_signal_bot.maintenance_automation.models import MaintenanceAction, MaintenanceActionType

def test_maintenance_action_destructive_requires_confirm():
    action = MaintenanceAction(
        action_id="test_action",
        action_type=MaintenanceActionType.CUSTOM,
        name="Test",
        destructive=True,
        requires_confirm=False
    )
    errors = action.validate_action()
    assert len(errors) > 0
    assert "Destructive actions must require confirm." in errors[0]

def test_maintenance_action_unsafe_command_blocked():
    action = MaintenanceAction(
        action_id="test_unsafe",
        action_type=MaintenanceActionType.CUSTOM,
        name="Test Unsafe",
        command="python execute_broker_trade.py"
    )
    errors = action.validate_action()
    assert len(errors) > 0
    assert "broker" in errors[0].lower() or "live" in errors[0].lower() or "order" in errors[0].lower()

def test_maintenance_action_safe_command_passes():
    action = MaintenanceAction(
        action_id="test_safe",
        action_type=MaintenanceActionType.CUSTOM,
        name="Test Safe",
        command="python -m bist_signal_bot healthcheck"
    )
    errors = action.validate_action()
    assert len(errors) == 0
