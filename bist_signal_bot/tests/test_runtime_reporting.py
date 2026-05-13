import pytest
from datetime import datetime
from bist_signal_bot.runtime.reporting import format_runtime_result_text
from bist_signal_bot.runtime.models import RuntimePipelineResult, RuntimePipelineConfig, RuntimeTrigger, RuntimePipelineStatus

def test_format_runtime_result_text():
    res = RuntimePipelineResult(
        run_id="run-1",
        trigger=RuntimeTrigger.TEST,
        config=RuntimePipelineConfig(strategy_name="test"),
        status=RuntimePipelineStatus.SUCCESS,
        started_at=datetime.utcnow()
    )

    text = format_runtime_result_text(res)
    assert "Run ID: run-1" in text
    assert "Status: SUCCESS" in text
    assert "No real order sent" in text
