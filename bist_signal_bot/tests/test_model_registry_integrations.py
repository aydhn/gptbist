import pytest
from datetime import datetime, timezone
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.model_registry.models import ModelRecord, ModelKind, ModelRegistryStatus
from bist_signal_bot.ops.store_checks import StoreIntegrityChecker
from bist_signal_bot.reports.collector import ReportDataCollector

class DummyStore:
    def __init__(self):
        self.models = []
    def load_models(self, status=None, limit=1000): return self.models
    def get_model(self, m_id): return None
    def append_model(self, m): self.models.append(m)


def test_qa_release_gate_integration():
    settings = Settings()
    settings.QA_INCLUDE_MODEL_REGISTRY = False
    from bist_signal_bot.qa.release_gate import run_release_gate

    report = run_release_gate(include_model_registry=True, settings=settings)
    assert report.get("model_registry") is None

    # We can test logic without monkeypatching by letting it hit the try/except if we want, or just verify SKIPPED works.




def test_ops_store_check():
    # Since OpsStoreChecker initialization might have path_guard issues in the test environment
    # Let's just instantiate an empty mock and test the method
    settings = Settings()
    settings.ENABLE_MODEL_REGISTRY = False
    from bist_signal_bot.ops.store_checks import StoreIntegrityChecker
    checker = StoreIntegrityChecker.__new__(StoreIntegrityChecker)
    checker.settings = settings
    res = checker.check_model_registry_dirs()
    assert res["status"] == "SKIPPED"





def test_reports_collector():
    settings = Settings()
    settings.REPORT_INCLUDE_MODEL_REGISTRY = False

    from bist_signal_bot.reports.collector import ReportDataCollector
    collector = ReportDataCollector.__new__(ReportDataCollector)
    collector.settings = settings
    res = collector.collect_model_registry_report()
    assert res["status"] == "SKIPPED"
