import hashlib
import json
import uuid
from datetime import datetime, timedelta, UTC
from typing import Any, Optional

from bist_signal_bot.performance.models import (
    CacheEntry,
    CacheLookupResult,
    CacheStatus,
)
from bist_signal_bot.core.exceptions import BistSignalBotError

class LocalCacheError(BistSignalBotError):
    pass

class LocalCacheManager:
    def __init__(self, settings: Any = None, base_dir: Any = None):
        self.settings = settings
        self.base_dir = base_dir

        self.enabled = True
        self.default_ttl = 86400
        self.requires_confirm = True

        if self.settings:
            self.enabled = getattr(self.settings, "PERFORMANCE_CACHE_ENABLED", self.enabled)
            self.default_ttl = getattr(self.settings, "PERFORMANCE_CACHE_DEFAULT_TTL_SECONDS", self.default_ttl)
            self.requires_confirm = getattr(self.settings, "PERFORMANCE_CACHE_REQUIRES_CONFIRM", self.requires_confirm)

        self._memory_store: dict[str, CacheEntry] = {}
        self._payload_store: dict[str, dict[str, Any]] = {}

    def build_key(self, namespace: str, inputs: dict[str, Any]) -> str:
        # Sort keys to ensure deterministic ordering
        sorted_inputs = {k: inputs[k] for k in sorted(inputs.keys())}
        json_str = json.dumps(sorted_inputs, sort_keys=True)
        return hashlib.sha256(f"{namespace}:{json_str}".encode()).hexdigest()

    def get(self, namespace: str, key: str) -> CacheLookupResult:
        lookup_id = str(uuid.uuid4())

        if not self.enabled:
            return CacheLookupResult(
                lookup_id=lookup_id,
                key=key,
                namespace=namespace,
                status=CacheStatus.DISABLED,
                reason="Cache is disabled"
            )

        full_key = f"{namespace}:{key}"
        entry = self._memory_store.get(full_key)

        if not entry:
            return CacheLookupResult(
                lookup_id=lookup_id,
                key=key,
                namespace=namespace,
                status=CacheStatus.MISS,
                reason="Not found in cache"
            )

        if self.is_stale(entry):
            entry.status = CacheStatus.STALE
            return CacheLookupResult(
                lookup_id=lookup_id,
                key=key,
                namespace=namespace,
                status=CacheStatus.STALE,
                entry=entry,
                reason="Cache entry is stale",
                warnings=["Recomputation recommended"]
            )

        return CacheLookupResult(
            lookup_id=lookup_id,
            key=key,
            namespace=namespace,
            status=CacheStatus.HIT,
            entry=entry,
            metadata={"payload": self._payload_store.get(full_key)}
        )

    def put(self, namespace: str, key: str, payload: dict[str, Any], ttl_seconds: Optional[int] = None, confirm: bool = False) -> CacheEntry:
        if not self.enabled:
            return CacheEntry(
                cache_id=str(uuid.uuid4()),
                key=key,
                namespace=namespace,
                path="",
                created_at=datetime.now(UTC),
                status=CacheStatus.DISABLED
            )

        if self.requires_confirm and not confirm:
            # Temporary cache write without confirm
            entry = CacheEntry(
                cache_id=str(uuid.uuid4()),
                key=key,
                namespace=namespace,
                path=f"/tmp/cache/{namespace}/{key}.json",
                created_at=datetime.now(UTC),
                status=CacheStatus.BYPASS,
                warnings=["Write bypassed due to lack of confirmation"]
            )
            return entry

        ttl = ttl_seconds or self.default_ttl
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ttl)

        checksum = self.checksum_payload(payload)
        payload_str = json.dumps(payload)
        size_bytes = len(payload_str.encode())

        entry = CacheEntry(
            cache_id=str(uuid.uuid4()),
            key=key,
            namespace=namespace,
            path=f"/data/cache/{namespace}/{key}.json", # Mock path
            created_at=now,
            expires_at=expires_at,
            checksum=checksum,
            status=CacheStatus.HIT,
            size_bytes=size_bytes
        )

        full_key = f"{namespace}:{key}"
        self._memory_store[full_key] = entry
        self._payload_store[full_key] = payload

        return entry

    def invalidate(self, namespace: str, key: Optional[str] = None, confirm: bool = False) -> list[CacheEntry]:
        invalidated = []

        if not confirm:
            return invalidated

        keys_to_remove = []
        for full_key, entry in self._memory_store.items():
            ns, k = full_key.split(":", 1)
            if ns == namespace and (key is None or k == key):
                keys_to_remove.append(full_key)
                entry.status = CacheStatus.INVALID
                invalidated.append(entry)

        for k in keys_to_remove:
            self._memory_store.pop(k, None)
            self._payload_store.pop(k, None)

        return invalidated

    def list_entries(self, namespace: Optional[str] = None) -> list[CacheEntry]:
        if not namespace:
            return list(self._memory_store.values())

        return [
            entry for full_key, entry in self._memory_store.items()
            if full_key.startswith(f"{namespace}:")
        ]

    def is_stale(self, entry: CacheEntry) -> bool:
        if entry.expires_at is None:
            return False
        return datetime.now(UTC) > entry.expires_at

    def checksum_payload(self, payload: dict[str, Any]) -> str:
        # Sort keys to ensure deterministic ordering
        sorted_payload = {k: payload[k] for k in sorted(payload.keys())}
        json_str = json.dumps(sorted_payload, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

