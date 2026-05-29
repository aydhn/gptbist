import pytest
from bist_signal_bot.app.context_fusion_app import create_context_fusion_engine
from bist_signal_bot.config.settings import Settings

def test_context_fusion_engine_build_snapshot(tmp_path):
    settings = Settings(CONTEXT_FUSION_SAVE_RESULTS=False)
    engine = create_context_fusion_engine(settings, base_dir=tmp_path)
    payload = {"symbol": "ASELS", "strategy_name": "test", "signal_id": "1", "direction": "LONG", "score": 80.0}
    snap = engine.build_snapshot_for_signal(payload, save=False)
    assert snap.symbol == "ASELS"
    assert snap.composite_score is not None

def test_context_fusion_engine_build_report(tmp_path):
    settings = Settings(CONTEXT_FUSION_SAVE_RESULTS=False)
    engine = create_context_fusion_engine(settings, base_dir=tmp_path)
    report = engine.build_report()
    assert report is not None
