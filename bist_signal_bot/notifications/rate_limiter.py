from datetime import datetime, timezone


class NotificationRateLimiter:
    def __init__(self, min_interval_seconds: float = 1.0, error_cooldown_seconds: float = 300.0):
        self.min_interval_seconds = min_interval_seconds
        self.error_cooldown_seconds = error_cooldown_seconds

        self._last_sent: dict[str, datetime] = {}
        self._last_error_sent: dict[str, datetime] = {}

    def _get_now(self, now: datetime | None) -> datetime:
        return now if now is not None else datetime.now(timezone.utc)

    def can_send(self, key: str | None = None, now: datetime | None = None) -> bool:
        if not key:
            key = "global"

        current_time = self._get_now(now)
        last_sent = self._last_sent.get(key)

        if not last_sent:
            return True

        delta = (current_time - last_sent).total_seconds()
        return delta >= self.min_interval_seconds

    def mark_sent(self, key: str | None = None, now: datetime | None = None) -> None:
        if not key:
            key = "global"
        self._last_sent[key] = self._get_now(now)

    def can_send_error(self, error_key: str, now: datetime | None = None) -> bool:
        current_time = self._get_now(now)
        last_sent = self._last_error_sent.get(error_key)

        if not last_sent:
            return True

        delta = (current_time - last_sent).total_seconds()
        return delta >= self.error_cooldown_seconds

    def mark_error_sent(self, error_key: str, now: datetime | None = None) -> None:
        self._last_error_sent[error_key] = self._get_now(now)
