import json
import uuid
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Dict, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import RuntimeLockError
from bist_signal_bot.storage.paths import get_runtime_dir

class RuntimeLockManager:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or get_runtime_dir(self.settings)
        self.lock_file = self.base_dir / self.settings.RUNTIME_LOCK_FILE_NAME
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

    def acquire(self, lock_id: Optional[str] = None, ttl_seconds: Optional[int] = None) -> str:
        if self.is_locked():
            if self.settings.RUNTIME_CLEAR_STALE_LOCK and self.clear_stale_lock(ttl_seconds or self.settings.RUNTIME_LOCK_TTL_SECONDS):
                pass # Cleared, proceed
            else:
                raise RuntimeLockError(f"Cannot acquire lock, another process holds it. File: {self.lock_file}")

        lock_id = lock_id or str(uuid.uuid4())
        lock_data = {
            "lock_id": lock_id,
            "acquired_at": datetime.utcnow().isoformat(),
            "pid": 0 # Not using os.getpid() for simplicity in this mock, but normally yes
        }

        # Atomic write approximation for local testing
        tmp_file = self.lock_file.with_suffix('.tmp')
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(lock_data, f)
        tmp_file.replace(self.lock_file)

        return lock_id

    def release(self, lock_id: str) -> None:
        data = self.read_lock()
        if not data:
            return # Already released or doesn't exist

        if data.get("lock_id") != lock_id:
            raise RuntimeLockError(f"Cannot release lock with invalid lock_id: {lock_id}. Held by: {data.get('lock_id')}")

        try:
            self.lock_file.unlink()
        except FileNotFoundError:
            pass

    def is_locked(self) -> bool:
        return self.lock_file.exists()

    def read_lock(self) -> Optional[Dict[str, Any]]:
        try:
            if self.lock_file.exists():
                with open(self.lock_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def clear_stale_lock(self, ttl_seconds: int) -> bool:
        data = self.read_lock()
        if not data:
            return True

        try:
            acquired = datetime.fromisoformat(data["acquired_at"])
            age = (datetime.utcnow() - acquired).total_seconds()
            if age > ttl_seconds:
                self.lock_file.unlink(missing_ok=True)
                return True
        except Exception:
            self.lock_file.unlink(missing_ok=True)
            return True

        return False

    @contextmanager
    def with_lock(self, lock_id: Optional[str] = None, ttl_seconds: Optional[int] = None):
        l_id = self.acquire(lock_id, ttl_seconds)
        try:
            yield l_id
        finally:
            self.release(l_id)
