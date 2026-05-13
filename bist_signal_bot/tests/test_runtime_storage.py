import pytest
from datetime import datetime
from bist_signal_bot.runtime.storage import RuntimeReportStore
from bist_signal_bot.runtime.models import RuntimePipelineResult, RuntimePipelineConfig, RuntimeTrigger, RuntimePipelineStatus

def test_report_store_save_files(tmp_path):
    store = RuntimeReportStore(base_dir=tmp_path)
    res = RuntimePipelineResult(
        run_id="run-1",
        trigger=RuntimeTrigger.TEST,
        config=RuntimePipelineConfig(strategy_name="test"),
        status=RuntimePipelineStatus.SUCCESS,
        started_at=datetime.utcnow()
    )

    paths = store.save_result(res, formats=["all"])
    assert "json" in paths
    assert "markdown" in paths
    assert "csv" in paths
    assert paths["json"].exists()
    assert paths["markdown"].exists()
