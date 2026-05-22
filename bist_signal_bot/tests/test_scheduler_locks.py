import pytest
from bist_signal_bot.scheduler.locks import SchedulerLockManager

def test_scheduler_lock_acquire_release(tmp_path):
    mgr = SchedulerLockManager(data_dir=tmp_path)

    assert mgr.acquire_lock("test_lock", 60) is True
    assert mgr.is_locked("test_lock") is True

    assert mgr.acquire_lock("test_lock", 60) is False # already locked

    assert mgr.release_lock("test_lock") is True
    assert mgr.is_locked("test_lock") is False
