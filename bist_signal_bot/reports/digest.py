import logging
from typing import Any
from datetime import datetime
from bist_signal_bot.reports.models import GeneratedReport, TelegramDigest, ReportStatus
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.core.exceptions import ReportDigestError

class ReportDigestBuilder:
    def __init__(self, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)

    def build_telegram_digest(self, report: GeneratedReport, top_n: int = 5) -> TelegramDigest:
        message = f"BIST Bot Research Digest\nType: {report.report_type.value}\nStatus: {report.status.value}\n"

        # Take some top items logic
        top_items = []
        if report.sections:
            message += f"Sections: {len(report.sections)}\n"

        digest = TelegramDigest(
            digest_id=f"DIG-{report.report_id}",
            report_id=report.report_id,
            title=f"Digest for {report.title}",
            message=message[:self.settings.REPORT_DIGEST_MAX_CHARS],
            top_items=top_items,
            status=ReportStatus.SUCCESS
        )
        return digest

    def send_digest(self, digest: TelegramDigest, notifier: Any, confirm: bool = False) -> TelegramDigest:
        if not self.settings.REPORT_TELEGRAM_DIGEST_ENABLED:
            self.logger.warning("Telegram digest sending disabled.")
            digest.warnings.append("Telegram digest sending disabled.")
            return digest

        if self.settings.REPORT_TELEGRAM_REQUIRE_CONFIRM and not confirm:
            raise ReportDigestError("Confirmation required to send Telegram digest.")

        try:
            notifier.send_message(digest.message)
            digest.sent = True
            digest.sent_at = datetime.utcnow()
        except Exception as e:
            digest.status = ReportStatus.FAILED
            digest.warnings.append(str(e))
            self.logger.error(f"Failed to send digest: {e}")

        return digest

    def digest_from_runtime_result(self, runtime_result: Any) -> TelegramDigest:
        return TelegramDigest(digest_id="RT-DIGEST", title="Runtime Digest", message="Runtime details")

    def digest_from_scanner_summary(self, scanner_summary: dict[str, Any]) -> TelegramDigest:
        return TelegramDigest(digest_id="SCAN-DIGEST", title="Scanner Digest", message="Scanner details")
