import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SchedulerLockManager:
    def __init__(self, data_dir: Path | str = "data"):
        self.lock_dir = Path(data_dir) / "scheduler" / "locks"
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def _get_lock_path(self, lock_name: str) -> Path:
        # Sanitize lock name slightly
        safe_name = "".join(c if c.isalnum() else "_" for c in lock_name)
        return self.lock_dir / f"{safe_name}.lock"

    def acquire_lock(self, lock_name: str, ttl_seconds: int) -> bool:
        lock_path = self._get_lock_path(lock_name)
        now = datetime.utcnow()

        # Check if exists and valid
        if lock_path.exists():
            try:
                with open(lock_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                created_at = datetime.fromisoformat(data['created_at'])
                ttl = data['ttl_seconds']

                if now < created_at + timedelta(seconds=ttl):
                    return False # Still locked
            except (json.JSONDecodeError, KeyError, ValueError):
                pass # Invalid lock file, we will overwrite

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
            return True
        except Exception as e:
            logger.error(f"Failed to acquire lock {lock_name}: {e}")
            return False

    def release_lock(self, lock_name: str) -> bool:
        lock_path = self._get_lock_path(lock_name)
        if lock_path.exists():
            try:
                lock_path.unlink()
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
            with open(lock_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            created_at = datetime.fromisoformat(data['created_at'])
            ttl = data['ttl_seconds']

            return datetime.utcnow() < created_at + timedelta(seconds=ttl)
        except Exception:
            return False # Invalid lock is considered unlocked

    def cleanup_expired_locks(self) -> int:
        cleaned = 0
        now = datetime.utcnow()
        for lock_file in self.lock_dir.glob("*.lock"):
            try:
                with open(lock_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                created_at = datetime.fromisoformat(data['created_at'])
                ttl = data['ttl_seconds']

                if now >= created_at + timedelta(seconds=ttl):
                    lock_file.unlink()
                    cleaned += 1
            except Exception:
                # Corrupted lock file, just delete it
                try:
                    lock_file.unlink()
                    cleaned += 1
                except Exception:
                    pass
        return cleaned
