from bist_signal_bot.reports.scheduler import ReportScheduleHelper

def test_should_generate_daily():
    helper = ReportScheduleHelper()
    assert helper.should_generate_daily()

def test_should_generate_weekly():
    helper = ReportScheduleHelper()
    assert helper.should_generate_weekly()
