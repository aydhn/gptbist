from datetime import datetime, timedelta, UTC
import pytest
from bist_signal_bot.performance.cache import LocalCacheManager
from bist_signal_bot.performance.models import CacheStatus
import time

def test_local_cache_deterministic_key():
    manager = LocalCacheManager()

    k1 = manager.build_key("test", {"a": 1, "b": 2})
    k2 = manager.build_key("test", {"b": 2, "a": 1})

    assert k1 == k2

def test_local_cache_get_miss():
    manager = LocalCacheManager()
    result = manager.get("test", "nonexistent")
    assert result.status == CacheStatus.MISS

def test_local_cache_put_without_confirm():
    manager = LocalCacheManager()
    entry = manager.put("test", "k1", {"data": "test"}, confirm=False)
    assert entry.status == CacheStatus.BYPASS

    # Should not be in memory store
    result = manager.get("test", "k1")
    assert result.status == CacheStatus.MISS

def test_local_cache_put_with_confirm():
    manager = LocalCacheManager()
    entry = manager.put("test", "k1", {"data": "test"}, confirm=True)
    assert entry.status == CacheStatus.HIT

    result = manager.get("test", "k1")
    assert result.status == CacheStatus.HIT

def test_local_cache_stale_entry():
    manager = LocalCacheManager()
    # TTL 0 so it expires immediately
    entry = manager.put("test", "k1", {"data": "test"}, ttl_seconds=0, confirm=True)

    manager._memory_store['test:k1'].expires_at = datetime.now(UTC) - timedelta(seconds=1)

    result = manager.get("test", "k1")
    assert result.status == CacheStatus.STALE
