
from bist_signal_bot.app.healthcheck import check_report_templates_health

def test_check_report_templates_health():
    res = check_report_templates_health()
    assert res["report_templates_enabled"] is True
    assert res["latest_validation_status"] == "PASS"
