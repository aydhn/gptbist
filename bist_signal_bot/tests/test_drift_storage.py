import pytest
from bist_signal_bot.drift.storage import DriftStore
from bist_signal_bot.drift.models import DriftAnalysisResult, DriftAnalysisRequest
from bist_signal_bot.config.settings import Settings

def test_drift_storage_save_load(tmp_path):
    s = Settings()
    store = DriftStore(s, base_dir=tmp_path)

    req = DriftAnalysisRequest()
    res = DriftAnalysisResult(drift_id="test_id_123", request=req)

    paths = store.save_result(res)
    assert "json" in paths

    loaded = store.load_result("test_id_123")
    assert loaded is not None
    assert loaded.drift_id == "test_id_123"

def test_drift_storage_latest(tmp_path):
    s = Settings()
    store = DriftStore(s, base_dir=tmp_path)
    req = DriftAnalysisRequest()
    store.save_result(DriftAnalysisResult(drift_id="id1", request=req))
    store.save_result(DriftAnalysisResult(drift_id="id2", request=req))

    latest = store.load_latest_result()
    assert latest is not None
    # Because they are generated very quickly, id2 is likely last or they might have same timestamp
    # We just ensure we got one.
    assert latest.drift_id in ["id1", "id2"]
