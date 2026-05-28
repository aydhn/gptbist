from bist_signal_bot.factors.reporting import format_factor_report_markdown, FactorReport
def test_format_report():
    r = FactorReport(report_id='1')
    res = format_factor_report_markdown(r)
    assert '# Factor Report' in res
