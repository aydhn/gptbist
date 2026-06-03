from datetime import datetime, timezone
from bist_signal_bot.explainability.reporting import format_explainability_report_markdown
from bist_signal_bot.explainability.models import ExplainabilityReport

def test_explainability_report_markdown():
    rep = ExplainabilityReport(
        report_id="r1",
        generated_at=datetime.now(timezone.utc),
        disclaimer="My disclaimer"
    )
    md = format_explainability_report_markdown(rep)
    assert "# Explainability Report" in md
    assert "My disclaimer" in md
