from datetime import UTC, datetime, timedelta

from bist_signal_bot.notifications.rate_limiter import NotificationRateLimiter


def test_rate_limiter_allows_first_message():
    limiter = NotificationRateLimiter()
    now = datetime.now(UTC)
    assert limiter.can_send("test_key", now) is True

def test_rate_limiter_blocks_early_second_message():
    limiter = NotificationRateLimiter(min_interval_seconds=10.0)
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    limiter.mark_sent("test_key", now)

    # 5 seconds later
    later = now + timedelta(seconds=5)
    assert limiter.can_send("test_key", later) is False

def test_rate_limiter_allows_second_message_after_cooldown():
    limiter = NotificationRateLimiter(min_interval_seconds=10.0)
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    limiter.mark_sent("test_key", now)

    # 15 seconds later
    later = now + timedelta(seconds=15)
    assert limiter.can_send("test_key", later) is True

def test_error_cooldown_blocks_frequent_errors():
    limiter = NotificationRateLimiter(error_cooldown_seconds=300.0)
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    assert limiter.can_send_error("ValueError", now) is True
    limiter.mark_error_sent("ValueError", now)

    # 60 seconds later (blocked)
    later1 = now + timedelta(seconds=60)
    assert limiter.can_send_error("ValueError", later1) is False

    # 301 seconds later (allowed)
    later2 = now + timedelta(seconds=301)
    assert limiter.can_send_error("ValueError", later2) is True
