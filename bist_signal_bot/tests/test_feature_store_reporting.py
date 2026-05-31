from bist_signal_bot.feature_store.reporting import format_feature_store_report_markdown
from bist_signal_bot.feature_store.models import FeatureStoreReport
from datetime import datetime, timezone

def test_feature_store_reporting():
    report = FeatureStoreReport(report_id="1", generated_at=datetime.now(timezone.utc))
    md = format_feature_store_report_markdown(report)
    assert "Feature Store Report" in md
    assert report.disclaimer in md
