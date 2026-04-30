import html
from typing import Any

from bist_signal_bot.notifications.models import NotificationMessage


class NotificationFormatter:
    def __init__(self, parse_mode: str = "HTML", timezone_str: str = "Europe/Istanbul"):
        self.parse_mode = parse_mode.upper()
        self.timezone_str = timezone_str

    def _escape(self, text: str) -> str:
        if self.parse_mode == "HTML":
            return html.escape(str(text))
        return str(text)

    def format_message(self, message: NotificationMessage) -> str:
        """Formats a NotificationMessage to a string suitable for Telegram."""
        lines = []

        # Title
        title_escaped = self._escape(message.title)
        lines.append(f"<b>[{message.level.value}] {title_escaped}</b>")
        lines.append("")

        # Symbol if present
        if message.symbol:
            lines.append(f"Sembol: {self._escape(message.symbol)}")

        # Type
        lines.append(f"Tip: {message.notification_type.value}")

        # Time
        time_str = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"Zaman: {time_str} UTC")

        lines.append("")
        lines.append("Detay:")
        lines.append(self._escape(message.body))

        if message.metadata:
            lines.append("")
            lines.append("Ek:")
            for k, v in message.metadata.items():
                lines.append(f"{self._escape(k)}={self._escape(str(v))}")

        return "\n".join(lines)

    def format_healthcheck(self, summary: dict[str, Any]) -> str:
        """Formats healthcheck dict into a short readable text."""
        lines = [
            "<b>[INFO] Healthcheck Raporu</b>",
            "",
            f"App: {self._escape(summary.get('app_name', 'BIST Signal Bot'))}",
            f"Env: {self._escape(summary.get('environment', 'N/A'))}",
            f"Python: {self._escape(summary.get('python_version', 'N/A'))}"
        ]

        features = summary.get("features", {})
        if features:
            lines.append("")
            lines.append("Özellikler:")
            for k, v in features.items():
                lines.append(f"- {self._escape(k)}: {self._escape(str(v))}")

        notifications = summary.get("notifications", {})
        if notifications:
            lines.append("")
            lines.append("Bildirimler:")
            for k, v in notifications.items():
                lines.append(f"- {self._escape(k)}: {self._escape(str(v))}")

        return "\n".join(lines)

    def format_error(self, error: Exception, context: dict[str, Any] | None = None) -> str:
        """Formats an error message safely."""
        error_type = type(error).__name__
        error_msg = str(error)

        lines = [
            "<b>[ERROR] Sistem Hatası</b>",
            "",
            f"Tip: {self._escape(error_type)}",
            f"Mesaj: {self._escape(error_msg)}"
        ]

        if context:
            lines.append("")
            lines.append("Bağlam:")
            for k, v in context.items():
                lines.append(f"{self._escape(k)}={self._escape(str(v))}")

        return "\n".join(lines)

    def split_message(self, text: str, max_length: int = 3900) -> list[str]:
        """Splits text to fit Telegram message limits."""
        if not text:
            return []

        if len(text) <= max_length:
            return [text]

        parts = []
        current_part = ""

        lines = text.split("\n")

        for line in lines:
            if len(line) > max_length:
                if current_part:
                    parts.append(current_part)
                    current_part = ""

                for i in range(0, len(line), max_length):
                    parts.append(line[i:i + max_length])
                continue

            if len(current_part) + len(line) + 1 <= max_length:
                if current_part:
                    current_part += "\n" + line
                else:
                    current_part = line
            else:
                parts.append(current_part)
                current_part = line

        if current_part:
            parts.append(current_part)

        return parts

    @staticmethod
    def mask_secret(value: str, visible_prefix: int = 4, visible_suffix: int = 4) -> str:
        """Masks a secret string."""
        if not value:
            return ""
        if len(value) <= visible_prefix + visible_suffix:
            return "***"

        return f"{value[:visible_prefix]}***{value[-visible_suffix:]}"

    def format_download_summary(self, result: Any) -> str:
        """Formats a BatchDownloadResult into a Telegram message."""
        lines = [
            "<b>BIST Bot Veri İndirme Özeti</b>",
            "",
            f"Provider: {self._escape(result.provider)}",
            f"Timeframe: {self._escape(result.timeframe)}",
            f"Period: {self._escape(result.period or 'N/A')}",
            f"İstenen: {result.requested_count}",
            f"Başarılı: {result.success_count}",
            f"Başarısız: {result.failed_count}",
            f"Refresh: {'true' if result.refresh else 'false'}",
            f"Save: {'true' if result.save else 'false'}"
        ]

        failed = result.failed_symbols()
        if failed:
            lines.append("")
            lines.append("Başarısız semboller:")
            for sym in failed:
                # Find the error message
                err = "Bilinmeyen hata"
                for res in result.results:
                    if res.symbol == sym and res.error:
                        err = res.error
                        break
                lines.append(f"- {self._escape(sym)}: {self._escape(err)}")

        return "\n".join(lines)

    def format_cleaning_report(self, report: Any) -> str:
        """Formats a CleaningReport into a Telegram message."""
        lines = [
            "<b>BIST Bot Veri Temizleme Özeti</b>",
            "",
            f"Sembol: {self._escape(report.symbol)}",
            f"Timeframe: {self._escape(report.timeframe)}",
            f"Durum: {report.status.value}",
            f"Girdi satır: {report.input_rows}",
            f"Çıktı satır: {report.output_rows}",
            f"Silinen satır: {report.dropped_rows}",
            f"Doldurulan değer: {report.filled_values}",
            f"Aykırı işaretlenen: {report.flagged_outliers}",
            f"Backtest kullanılabilir: {'true' if report.usable_for_backtest else 'false'}",
            f"ML kullanılabilir: {'true' if report.usable_for_ml else 'false'}"
        ]
        return "\n".join(lines)
