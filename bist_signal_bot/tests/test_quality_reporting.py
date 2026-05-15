import pytest
from bist_signal_bot.quality.models import QualityRunResult, QualityRunConfig, QualityCheckStatus
from bist_signal_bot.quality.reporting import format_quality_result_text

def test_format_quality_result_text():
    config = QualityRunConfig()
    result = QualityRunResult(run_id="test-123", config=config, status=QualityCheckStatus.PASS)
    text = format_quality_result_text(result)
    assert "test-123" in text
    assert "Status: PASS" in text
    assert "Quality gate output only." in text
