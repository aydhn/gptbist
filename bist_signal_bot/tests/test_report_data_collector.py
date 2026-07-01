from bist_signal_bot.reports.collector import ReportDataCollector
from bist_signal_bot.reports.models import ReportConfig

def test_collector_returns_bundle():
    collector = ReportDataCollector()
    config = ReportConfig()
    bundle = collector.collect(config)
    assert bundle.report_type == config.report_type
    assert isinstance(bundle.source_summaries, dict)

def test_collect_model_registry_report_skipped():
    class MockSettings:
        REPORT_INCLUDE_MODEL_REGISTRY = False

    collector = ReportDataCollector()
    collector.settings = MockSettings()

    result = collector.collect_model_registry_report()
    assert result == {"status": "SKIPPED"}

def test_collect_model_registry_report_error(monkeypatch):
    class MockSettings:
        REPORT_INCLUDE_MODEL_REGISTRY = True

    def mock_create(*args, **kwargs):
        raise ValueError("Failed to create registry")

    monkeypatch.setattr('bist_signal_bot.app.model_registry_app.create_local_model_registry', mock_create)

    collector = ReportDataCollector()
    collector.settings = MockSettings()

    result = collector.collect_model_registry_report()
    assert "error" in result
    assert "Failed to create registry" in result["error"]

def test_collect_model_registry_report_success(monkeypatch):
    class MockSettings:
        REPORT_INCLUDE_MODEL_REGISTRY = True

    class MockStatus:
        def __init__(self, value):
            self.value = value

    class MockModel:
        def __init__(self, status_val):
            self.status = MockStatus(status_val)

    class MockRegistry:
        def list_models(self):
            return [
                MockModel("ACTIVE_RESEARCH"),
                MockModel("ACTIVE_RESEARCH"),
                MockModel("CANDIDATE"),
                MockModel("BLOCKED_LEAKAGE"),
                MockModel("ARCHIVED")
            ]

    def mock_create(*args, **kwargs):
        return MockRegistry()

    monkeypatch.setattr('bist_signal_bot.app.model_registry_app.create_local_model_registry', mock_create)

    collector = ReportDataCollector()
    collector.settings = MockSettings()

    result = collector.collect_model_registry_report()

    assert "error" not in result
    assert result["total_models"] == 5
    assert result["active_research"] == 2
    assert result["candidate"] == 1
    assert result["blocked"] == 1
