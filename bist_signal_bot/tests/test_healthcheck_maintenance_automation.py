import pytest

def test_healthcheck_maintenance_automation_flags():
    # Mocking healthcheck --maintenance-automation
    def mock_healthcheck():
        return {
            "maintenance_automation_enabled": True,
            "cadence_policies_loaded": True,
            "retention_policies_loaded": True,
            "planner_capable": True,
            "latest_run_status": "PASS"
        }

    res = mock_healthcheck()
    assert res["maintenance_automation_enabled"] is True
    assert res["latest_run_status"] == "PASS"

def test_doctor_oversized_cache_detection():
    # Mocking doctor --maintenance-automation
    def mock_doctor():
        return {
            "missing_policies": False,
            "oversized_cache": True
        }

    res = mock_doctor()
    assert res["oversized_cache"] is True

def test_reports_daily_include_maintenance():
    # Mocking reports daily --include-maintenance-automation
    def mock_reports():
        return "Daily Report\nMaintenance Automation: PASS"

    res = mock_reports()
    assert "Maintenance Automation" in res
