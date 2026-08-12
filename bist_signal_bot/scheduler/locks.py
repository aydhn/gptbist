import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SchedulerLockManager:
    def __init__(self, data_dir: Path | str = "data"):
        self.lock_dir = Path(data_dir) / "scheduler" / "locks"
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}

    def _get_lock_path(self, lock_name: str) -> Path:
        # Sanitize lock name slightly
        safe_name = "".join(c if c.isalnum() else "_" for c in lock_name)
        return self.lock_dir / f"{safe_name}.lock"

    def _get_expires_at(self, lock_path: Path) -> datetime:
        try:
            mtime = lock_path.stat().st_mtime
            if lock_path in self._cache and self._cache[lock_path][0] == mtime:
                return self._cache[lock_path][1]

            with open(lock_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            created_at = datetime.fromisoformat(data['created_at'])
            ttl = data['ttl_seconds']
            expires_at = created_at + timedelta(seconds=ttl)

            self._cache[lock_path] = (mtime, expires_at)
            return expires_at
        except Exception:
            self._cache.pop(lock_path, None)
            raise

    def acquire_lock(self, lock_name: str, ttl_seconds: int) -> bool:
        lock_path = self._get_lock_path(lock_name)
        now = datetime.utcnow()

        # Check if exists and valid
        if lock_path.exists():
            try:
                expires_at = self._get_expires_at(lock_path)
                if now < expires_at:
                    return False # Still locked
            except (json.JSONDecodeError, KeyError, ValueError):
                pass # Invalid lock file, we will overwrite
            except Exception:
                pass

        # Create or overwrite lock
        lock_data = {
            'pid': os.getpid(),
            'created_at': now.isoformat(),
            'ttl_seconds': ttl_seconds
        }

        try:
            # Simple atomic-ish write (better would be using open with O_CREAT|O_EXCL but this is local MVP)
            # Actually, let's try a safer approach if possible, but standard write is okay for local non-concurrent
            with open(lock_path, 'w', encoding='utf-8') as f:
                json.dump(lock_data, f)
            # clear cache since we updated the file
            self._cache.pop(lock_path, None)
            return True
        except Exception as e:
            logger.error(f"Failed to acquire lock {lock_name}: {e}")
            return False

    def release_lock(self, lock_name: str) -> bool:
        lock_path = self._get_lock_path(lock_name)
        if lock_path.exists():
            try:
                lock_path.unlink()
                self._cache.pop(lock_path, None)
                return True
            except Exception as e:
                logger.error(f"Failed to release lock {lock_name}: {e}")
                return False
        return True # already released

    def is_locked(self, lock_name: str) -> bool:
        lock_path = self._get_lock_path(lock_name)
        if not lock_path.exists():
            return False

        try:
            expires_at = self._get_expires_at(lock_path)
            return datetime.utcnow() < expires_at
        except Exception:
            return False # Invalid lock is considered unlocked

    def cleanup_expired_locks(self) -> int:
        cleaned = 0
        now = datetime.utcnow()
        for lock_file in self.lock_dir.glob("*.lock"):
            try:
                expires_at = self._get_expires_at(lock_file)
                if now >= expires_at:
                    lock_file.unlink()
                    self._cache.pop(lock_file, None)
                    cleaned += 1
            except Exception:
                # Corrupted lock file, just delete it
                try:
                    lock_file.unlink()
                    self._cache.pop(lock_file, None)
                    cleaned += 1
                except Exception:
                    pass
        return cleaned