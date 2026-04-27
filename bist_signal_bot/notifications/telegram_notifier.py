from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.logging_setup import get_logger
from bist_signal_bot.notifications.formatter import NotificationFormatter
from bist_signal_bot.notifications.models import (
    NotificationLevel,
    NotificationMessage,
    NotificationType,
    TelegramSendResult,
)
from bist_signal_bot.notifications.rate_limiter import NotificationRateLimiter

logger = get_logger("bist_signal_bot.telegram_notifier")

class TelegramNotifier:
    def __init__(
        self,
        settings: Settings,
        formatter: NotificationFormatter | None = None,
        rate_limiter: NotificationRateLimiter | None = None,
    ):
        self.settings = settings
        self.formatter = formatter or NotificationFormatter(
            parse_mode=settings.TELEGRAM_PARSE_MODE,
            timezone_str=settings.DEFAULT_TIMEZONE
        )
        self.rate_limiter = rate_limiter or NotificationRateLimiter(
            min_interval_seconds=settings.TELEGRAM_RATE_LIMIT_SECONDS,
            error_cooldown_seconds=settings.TELEGRAM_ERROR_COOLDOWN_SECONDS
        )

    @property
    def enabled(self) -> bool:
        return self.settings.ENABLE_TELEGRAM

    @property
    def dry_run(self) -> bool:
        return self.settings.DRY_RUN

    @property
    def bot_token(self) -> str:
        return self.settings.TELEGRAM_BOT_TOKEN

    @property
    def chat_id(self) -> str:
        return self.settings.TELEGRAM_CHAT_ID

    @property
    def parse_mode(self) -> str:
        return self.settings.TELEGRAM_PARSE_MODE

    @property
    def timeout(self) -> int:
        return self.settings.TELEGRAM_SEND_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        return bool(self.enabled and self.bot_token and self.chat_id)

    def _send_raw_text(self, text: str) -> TelegramSendResult:
        # In this phase, we mock the real API call
        return TelegramSendResult(
            success=True,
            message_id="mock_id_123",
            sent_at=datetime.now(timezone.utc),
            dry_run=self.dry_run
        )

    def send(self, message: NotificationMessage) -> TelegramSendResult:
        if not self.is_configured():
            logger.debug("Telegram notification skipped: Not configured or disabled.")
            return TelegramSendResult(success=False, error="Telegram is not configured or disabled.")

        if message.level in (NotificationLevel.ERROR, NotificationLevel.CRITICAL) and message.dedup_key:
            if not self.rate_limiter.can_send_error(message.dedup_key):
                logger.debug(f"Telegram notification skipped: Error '{message.dedup_key}' is in cooldown.")
                return TelegramSendResult(success=False, error="Error message in cooldown.")

        if not self.rate_limiter.can_send():
            logger.warning("Telegram notification rate limit exceeded.")
            return TelegramSendResult(success=False, error="Rate limit exceeded.")

        formatted_text = self.formatter.format_message(message)
        parts = self.formatter.split_message(formatted_text, max_length=self.settings.TELEGRAM_MESSAGE_MAX_LENGTH)

        overall_success = True
        last_error = None
        last_message_id = None

        for part in parts:
            if self.dry_run:
                logger.info(f"DRY RUN - Telegram Message (Type: {message.notification_type}): {part[:50]}...")
                result = TelegramSendResult(success=True, dry_run=True, sent_at=datetime.now(timezone.utc))
            else:
                try:
                    result = self._send_raw_text(part)
                except Exception as e:
                    logger.error(f"TelegramSendError: Failed to send part: {type(e).__name__}")
                    result = TelegramSendResult(success=False, error=str(e), dry_run=False)

            if not result.success:
                overall_success = False
                last_error = result.error
            else:
                last_message_id = result.message_id

            self.rate_limiter.mark_sent()

        if overall_success and message.level in (NotificationLevel.ERROR, NotificationLevel.CRITICAL) and message.dedup_key:
            self.rate_limiter.mark_error_sent(message.dedup_key)

        return TelegramSendResult(
            success=overall_success,
            message_id=last_message_id,
            error=last_error,
            sent_at=datetime.now(timezone.utc),
            dry_run=self.dry_run
        )

    def send_text(
        self,
        title: str,
        body: str,
        level: NotificationLevel = NotificationLevel.INFO,
        notification_type: NotificationType = NotificationType.SYSTEM
    ) -> TelegramSendResult:
        msg = NotificationMessage(
            title=title,
            body=body,
            level=level,
            notification_type=notification_type
        )
        return self.send(msg)

    def send_healthcheck(self, summary: dict[str, Any]) -> TelegramSendResult:
        body = self.formatter.format_healthcheck(summary)
        msg = NotificationMessage(
            title="Healthcheck Raporu",
            body=body,
            level=NotificationLevel.INFO,
            notification_type=NotificationType.HEALTHCHECK
        )
        return self.send(msg)

    def send_error(self, error: Exception, context: dict[str, Any] | None = None) -> TelegramSendResult:
        body = self.formatter.format_error(error, context)
        dedup_key = type(error).__name__
        msg = NotificationMessage(
            title="Sistem Hatası",
            body=body,
            level=NotificationLevel.ERROR,
            notification_type=NotificationType.ERROR,
            dedup_key=dedup_key
        )
        return self.send(msg)

    @classmethod
    def from_settings(cls, settings: Settings) -> "TelegramNotifier":
        return cls(settings=settings)
