import pytest
from bist_signal_bot.context_fusion.reporting import format_context_fusion_report_markdown
from bist_signal_bot.context_fusion.models import ContextFusionReport
from datetime import datetime, timezone

def test_format_context_fusion_report_markdown():
    report = ContextFusionReport(
        report_id="1", generated_at=datetime.now(timezone.utc), snapshots=[], conflicts=[], evidence_gaps=[], key_findings=["Test finding"]
    )
    md = format_context_fusion_report_markdown(report)
    assert "Context Fusion Report" in md
    assert "Test finding" in md
