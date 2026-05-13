import pytest
import time
from bist_signal_bot.runtime.locks import RuntimeLockManager
from bist_signal_bot.core.exceptions import RuntimeLockError

def test_lock_manager_acquire_release(tmp_path):
    manager = RuntimeLockManager(base_dir=tmp_path)
    lock_id = manager.acquire()
    assert manager.is_locked()

    manager.release(lock_id)
    assert not manager.is_locked()

def test_lock_manager_acquire_already_locked(tmp_path):
    manager = RuntimeLockManager(base_dir=tmp_path)
    manager.settings.RUNTIME_CLEAR_STALE_LOCK = False
    manager.acquire()

    with pytest.raises(RuntimeLockError):
        manager.acquire()

def test_lock_manager_stale_clear(tmp_path):
    manager = RuntimeLockManager(base_dir=tmp_path)
    manager.acquire()

    # Force age by setting ttl to -1
    cleared = manager.clear_stale_lock(ttl_seconds=-1)
    assert cleared
    assert not manager.is_locked()
