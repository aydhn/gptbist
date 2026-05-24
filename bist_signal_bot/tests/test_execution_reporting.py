import pytest
from bist_signal_bot.execution_sim.reporting import format_execution_report_markdown
from bist_signal_bot.execution_sim.models import ExecutionQualityReport
import uuid

def test_reporting_formatting():
    report = ExecutionQualityReport(
        report_id=str(uuid.uuid4()), symbol="ASELS", strategy_name=None, fills=[],
        total_orders=1, filled_orders=1, partial_orders=0, not_filled_orders=0,
        gross_pnl=0, net_pnl=0, total_cost=0, average_slippage_bps=0, average_total_cost_bps=0, fill_rate_pct=100.0
    )
    txt = format_execution_report_markdown(report)
    assert "Execution Quality Report" in txt
    assert "**Disclaimer**" in txt
