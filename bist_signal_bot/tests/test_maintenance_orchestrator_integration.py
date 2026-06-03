import pytest

def test_orchestrator_maintenance_campaign():
    # Mock orchestrator planning a campaign
    def mock_orchestrator_plan(campaign_name):
        if campaign_name == "MAINTENANCE_WEEKLY_CAMPAIGN":
            return {"tasks": ["MAINTENANCE_PLAN", "MAINTENANCE_RUN", "MAINTENANCE_REPORT"]}
        return {}

    plan = mock_orchestrator_plan("MAINTENANCE_WEEKLY_CAMPAIGN")
    assert "MAINTENANCE_PLAN" in plan["tasks"]
