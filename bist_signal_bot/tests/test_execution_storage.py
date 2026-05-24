import pytest
from bist_signal_bot.execution_sim.storage import ExecutionSimStore
from bist_signal_bot.execution_sim.models import ExecutionQualityReport
import uuid

def test_execution_sim_store_quality_report(tmp_path):
    store = ExecutionSimStore(base_dir=tmp_path)
    report = ExecutionQualityReport(
        report_id=str(uuid.uuid4()), symbol="ASELS", strategy_name=None, fills=[],
        total_orders=1, filled_orders=1, partial_orders=0, not_filled_orders=0,
        gross_pnl=0, net_pnl=0, total_cost=0, average_slippage_bps=0, average_total_cost_bps=0, fill_rate_pct=100.0
    )
    store.append_quality_report(report)
    loaded = store.load_latest_quality_report("ASELS")
    assert loaded is not None
    assert loaded.report_id == report.report_id
