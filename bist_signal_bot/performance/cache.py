import hashlib
import json
import datetime
from pathlib import Path
from typing import Any
from bist_signal_bot.performance.models import CacheEntry, CacheLookupResult, CacheStatus

class LocalCacheManager:
    def __init__(self, settings=None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir or Path("data/performance/cache")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.entries: dict[str, CacheEntry] = {}

    def build_key(self, namespace: str, inputs: dict[str, Any]) -> str:
        s = json.dumps(inputs, sort_keys=True)
        h = hashlib.sha256(s.encode()).hexdigest()
        return f"{namespace}_{h[:12]}"

    def get(self, namespace: str, key: str) -> CacheLookupResult:
        entry = self.entries.get(key)
        if not entry or entry.namespace != namespace:
            return CacheLookupResult(lookup_id=f"loc_{key}", key=key, namespace=namespace, status=CacheStatus.MISS)
        if self.is_stale(entry):
            return CacheLookupResult(lookup_id=f"loc_{key}", key=key, namespace=namespace, status=CacheStatus.STALE, entry=entry)
        return CacheLookupResult(lookup_id=f"loc_{key}", key=key, namespace=namespace, status=CacheStatus.HIT, entry=entry)

    def put(self, namespace: str, key: str, payload: dict[str, Any], ttl_seconds: int | None = None, confirm: bool = False) -> CacheEntry:
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(seconds=ttl_seconds) if ttl_seconds else None

        path = str(self.base_dir / f"{key}.json")
        if not confirm:
            path = "memory_only"

        entry = CacheEntry(
            cache_id=f"ce_{key}",
            key=key,
            namespace=namespace,
            path=path,
            created_at=now,
            expires_at=expires_at,
            checksum=self.checksum_payload(payload),
            status=CacheStatus.HIT
        )
        if confirm:
            self.entries[key] = entry
            with open(path, "w") as f:
                json.dump(payload, f)
        return entry

    def invalidate(self, namespace: str, key: str | None = None, confirm: bool = False) -> list[CacheEntry]:
        invalidated = []
        if not confirm:
            return invalidated

        keys_to_remove = [k for k, v in self.entries.items() if v.namespace == namespace and (key is None or k == key)]
        for k in keys_to_remove:
            entry = self.entries.pop(k)
            if entry.path != "memory_only":
                try:
                    Path(entry.path).unlink(missing_ok=True)
                except OSError:
                    pass
            entry.status = CacheStatus.INVALID
            invalidated.append(entry)
        return invalidated

    def list_entries(self, namespace: str | None = None) -> list[CacheEntry]:
        if namespace:
            return [e for e in self.entries.values() if e.namespace == namespace]
        return list(self.entries.values())

    def is_stale(self, entry: CacheEntry) -> bool:
        if not entry.expires_at:
            return False
        return datetime.datetime.now(datetime.timezone.utc) > entry.expires_at

    def checksum_payload(self, payload: dict[str, Any]) -> str:
        s = json.dumps(payload, sort_keys=True)
        return hashlib.md5(s.encode()).hexdigest()
