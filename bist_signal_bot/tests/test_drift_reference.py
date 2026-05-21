import pytest
from bist_signal_bot.drift.reference import DriftReferenceManager
from bist_signal_bot.drift.models import DriftDomain, DriftReferenceWindow
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import DriftReferenceError

def test_reference_manager_build():
    rm = DriftReferenceManager(Settings())
    win = rm.build_reference_from_feature_store(DriftDomain.FEATURE, ["f1"])
    assert win.domain == DriftDomain.FEATURE
    assert "f1" in win.feature_names

def test_reference_save_no_confirm(tmp_path):
    s = Settings()
    s.DRIFT_REFERENCE_UPDATE_REQUIRES_CONFIRM = True
    rm = DriftReferenceManager(s, base_dir=tmp_path)
    win = rm.build_reference_from_research_ledger(DriftDomain.STRATEGY_PERFORMANCE)
    with pytest.raises(DriftReferenceError):
        rm.save_reference(win, confirm=False)

def test_reference_save_and_load(tmp_path):
    s = Settings()
    rm = DriftReferenceManager(s, base_dir=tmp_path)
    win = rm.build_reference_from_research_ledger(DriftDomain.STRATEGY_PERFORMANCE)
    rm.save_reference(win, confirm=True)

    loaded_win, _ = rm.load_reference(reference_id=win.reference_id)
    assert loaded_win is not None
    assert loaded_win.reference_id == win.reference_id
