
import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional
from bist_signal_bot.performance.models import CacheEntry, CacheLookupResult, CacheStatus

class LocalCacheManager:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir
        self._memory_store = {}

    def build_key(self, namespace: str, inputs: dict[str, Any]) -> str:
        s = json.dumps(inputs, sort_keys=True)
        return hashlib.md5(s.encode()).hexdigest()

    def get(self, namespace: str, key: str) -> CacheLookupResult:
        full_key = f"{namespace}:{key}"
        if full_key in self._memory_store:
            entry = self._memory_store[full_key]
            if self.is_stale(entry):
                return CacheLookupResult(lookup_id=uuid.uuid4().hex, key=key, namespace=namespace, status=CacheStatus.STALE, entry=entry)
            return CacheLookupResult(lookup_id=uuid.uuid4().hex, key=key, namespace=namespace, status=CacheStatus.HIT, entry=entry)
        return CacheLookupResult(lookup_id=uuid.uuid4().hex, key=key, namespace=namespace, status=CacheStatus.MISS)

    def put(self, namespace: str, key: str, payload: dict[str, Any], ttl_seconds: Optional[int] = None, confirm: bool = False) -> CacheEntry:
        full_key = f"{namespace}:{key}"
        entry = CacheEntry(
            cache_id=uuid.uuid4().hex,
            key=key,
            namespace=namespace,
            path=f"/fake/path/{full_key}",
            created_at=datetime.now(timezone.utc),
            status=CacheStatus.HIT
        )
        if confirm:
            self._memory_store[full_key] = entry
        return entry

    def invalidate(self, namespace: str, key: Optional[str] = None, confirm: bool = False) -> list[CacheEntry]:
        if not confirm:
            return []
        invalidated = []
        keys_to_delete = []
        for k, v in self._memory_store.items():
            if k.startswith(f"{namespace}:"):
                if key is None or k == f"{namespace}:{key}":
                    invalidated.append(v)
                    keys_to_delete.append(k)
        for k in keys_to_delete:
            del self._memory_store[k]
        return invalidated

    def list_entries(self, namespace: Optional[str] = None) -> list[CacheEntry]:
        res = []
        for k, v in self._memory_store.items():
            if namespace is None or k.startswith(f"{namespace}:"):
                res.append(v)
        return res

    def is_stale(self, entry: CacheEntry) -> bool:
        if entry.expires_at and datetime.now(timezone.utc) > entry.expires_at:
            return True
        return False

    def checksum_payload(self, payload: dict[str, Any]) -> str:
        return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
