import pytest
from bist_signal_bot.final_audit.freeze import HardeningFreezeManager
from bist_signal_bot.final_audit.release_candidate import ReleaseCandidateBuilder

def test_hardening_freeze_manager_dry_run():
    builder = ReleaseCandidateBuilder()
    cand = builder.build_candidate()

    manager = HardeningFreezeManager()
    freeze = manager.create_freeze(cand, confirm=False)
    assert not freeze.frozen
    assert not freeze.config_snapshot_ref

def test_hardening_freeze_manager_confirm():
    builder = ReleaseCandidateBuilder()
    cand = builder.build_candidate()

    manager = HardeningFreezeManager()
    freeze = manager.create_freeze(cand, confirm=True)
    assert freeze.frozen
    assert freeze.config_snapshot_ref
