import pytest
from bist_signal_bot.drift.engine import DriftEngine
from bist_signal_bot.drift.models import DriftAnalysisRequest, DriftDomain, DriftStatus
from bist_signal_bot.config.settings import Settings

def test_engine_analyze_mock():
    s = Settings()
    s.DRIFT_SAVE_RESULTS = False # Do not write to disk in simple unit test
    engine = DriftEngine.from_settings(s)

    req = DriftAnalysisRequest(
        domains=[DriftDomain.MODEL_SCORE, DriftDomain.SIGNAL_OUTCOME],
        save_output=False
    )
    res = engine.analyze(req)

    assert res.drift_id is not None
    assert len(res.model_results) == 1
    assert len(res.signal_decay_reports) == 1
    assert res.status != DriftStatus.UNKNOWN
