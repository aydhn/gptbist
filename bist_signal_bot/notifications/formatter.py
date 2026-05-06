import html
from typing import Any

from bist_signal_bot.notifications.models import NotificationMessage



from bist_signal_bot.costs.models import RoundTripCostBreakdown, TransactionCostBreakdown

def format_transaction_cost_breakdown(cost: TransactionCostBreakdown) -> str:
    amount = f"{cost.gross_notional:,.2f}" if cost.gross_notional > 0 else "N/A"
    total_cost_fmt = f"{cost.total_cost:,.2f}"

    msg = f"BIST Bot Maliyet Tahmini\n\n"
    msg += f"Sembol: {cost.input.symbol}\n"
    msg += f"Yön: {cost.side.value}\n"
    msg += f"Tutar: {amount} TRY\n"
    msg += f"Komisyon: {cost.commission.commission_amount:,.2f} TRY\n"
    msg += f"Slippage: {cost.slippage.slippage_total_amount:,.2f} TRY ({cost.slippage.slippage_bps:.2f} bps)\n"
    msg += f"Spread: {cost.spread.spread_total_amount:,.2f} TRY ({cost.spread.spread_bps:.2f} bps)\n"
    msg += f"Toplam Maliyet: {total_cost_fmt} TRY ({cost.total_cost_bps:.2f} bps)\n"
    msg += f"Efektif Fiyat: {cost.effective_price:,.2f}\n\n"
    msg += "Bu yalnızca tahmini işlem maliyetidir.\n"
    msg += "Yatırım tavsiyesi değildir.\n"
    msg += "Emir gönderilmedi."

    return msg

def format_round_trip_cost_breakdown(cost: RoundTripCostBreakdown) -> str:
    msg = f"BIST Bot Round-Trip Maliyet Tahmini\n\n"
    msg += f"Sembol: {cost.entry_cost.input.symbol}\n"
    msg += f"Miktar: {cost.entry_cost.input.quantity}\n"
    msg += f"Toplam Maliyet: {cost.total_cost:,.2f} TRY ({cost.total_cost_bps:.2f} bps)\n"
    msg += f"Breakeven (Başa Baş): {cost.breakeven_move_pct:.2f}%\n\n"
    msg += "Bu yalnızca tahmini işlem maliyetidir.\n"
    msg += "Yatırım tavsiyesi değildir.\n"
    msg += "Emir gönderilmedi."

    return msg

class NotificationFormatter:

    def format_risk_decision(self, decision) -> str:
        lines = [
            "🛡 <b>BIST Bot Risk Değerlendirme Özeti</b>\n",
            f"<b>Sembol:</b> {decision.signal.symbol}",
            f"<b>Strateji:</b> {decision.signal.strategy_name}",
            f"<b>Risk Durumu:</b> {decision.status.value}"
        ]

        if decision.position_size:
            lines.append(f"<b>Pozisyon Tutarı:</b> {decision.position_size.final_notional:.2f} TL")
            lines.append(f"<b>Adet:</b> {decision.position_size.quantity}")

        if decision.stop_target:
            lines.append(f"<b>Entry Ref:</b> {decision.stop_target.entry_price:.2f}")
            if decision.stop_target.stop_price:
                lines.append(f"<b>Stop Ref:</b> {decision.stop_target.stop_price:.2f}")
            if decision.stop_target.target_price:
                lines.append(f"<b>Target Ref:</b> {decision.stop_target.target_price:.2f}")
            if decision.stop_target.risk_reward:
                lines.append(f"<b>Risk/Reward:</b> {decision.stop_target.risk_reward:.2f}")

        if decision.estimated_total_cost:
            lines.append(f"<b>Tahmini Maliyet:</b> {decision.estimated_total_cost:.2f} TL")

        lines.append("\n⚠️ <i>Bu çıktı risk araştırma çıktısıdır.\nYatırım tavsiyesi değildir.\nEmir gönderilmedi.</i>")
        return "\n".join(lines)

    def format_risk_batch_result(self, batch) -> str:
        lines = [
            "🛡 <b>Toplu Risk Değerlendirmesi</b>\n",
            f"<b>İstenen:</b> {batch.requested_count}",
            f"<b>Onaylanan:</b> {batch.approved_count}",
            f"<b>Reddedilen:</b> {batch.rejected_count}",
            f"<b>Düşürülen:</b> {batch.reduced_count}",
            f"<b>Sadece İzleme:</b> {batch.watch_only_count}",
            "\n⚠️ <i>Risk araştırma çıktısıdır. Yatırım tavsiyesi değildir.</i>"
        ]
        return "\n".join(lines)

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


    def format_adjustment_report(self, report: Any) -> str:
        lines = [
            "<b>BIST Bot Veri Düzeltme (Adjustment) Özeti</b>",
            "",
            f"Sembol: {self._escape(report.symbol)}",
            f"Timeframe: {self._escape(report.timeframe)}",
            f"Durum: {report.status.value}",
            f"Politika: {report.policy.value}",
            f"Girdi satır: {report.input_rows}",
            f"Çıktı satır: {report.output_rows}",
            f"Kullanılabilir aksiyon: {report.actions_available}",
            f"Uygulanan aksiyon: {report.actions_applied}",
            f"Sorun (Issue) sayısı: {report.issue_count()}"
        ]
        if report.volume_adjusted:
            lines.append("Hacim düzeltmesi: Uygulandı")

        return "\n".join(lines)

    def format_corporate_action_validation(self, report: Any) -> str:
        lines = [
            "<b>BIST Bot Kurumsal Aksiyon Doğrulama Raporu</b>",
            "",
            f"Toplam aksiyon: {report.total_actions}",
            f"Geçerli: {report.valid_actions}",
            f"Geçersiz: {report.invalid_actions}",
            f"Kopya (Duplicate): {report.duplicate_actions}",
            f"Durum: {'BAŞARILI' if report.passed else 'BAŞARISIZ'}"
        ]

        if report.issues:
            lines.append("")
            lines.append("Detaylar:")
            for issue in report.issues[:5]:  # limit to first 5
                lines.append(f"- [{issue.severity}] {self._escape(issue.symbol or 'N/A')}: {self._escape(issue.message)}")
            if len(report.issues) > 5:
                lines.append(f"...ve {len(report.issues) - 5} sorun daha.")

        return "\n".join(lines)


    def format_volatility_feature_summary(self, result: Any, symbol: str | None = None, level: str | None = None) -> str:
        lines = [
            "<b>BIST Bot Volatilite Feature Özeti</b>",
            "",
            f"Sembol: {self._escape(symbol or 'Bilinmiyor')}",
            f"Seviye: {self._escape(level or 'Bilinmiyor')}",
            f"İstenen: {result.requested_count}",
            f"Başarılı: {result.success_count}",
            f"Başarısız: {result.failed_count}",
        ]

        if result.success_count > 0:
            lines.append(f"Üretilen kolon: {len(result.output_data.columns)}")

        return "\n".join(lines)


    def format_pattern_feature_summary(self, result: Any, symbol: str | None = None, level: str | None = None) -> str:
        lines = [
            "<b>BIST Bot Pattern Feature Özeti</b>",
            "",
            f"Sembol: {self._escape(symbol or 'Bilinmiyor')}",
            f"Seviye: {self._escape(level or 'Bilinmiyor')}",
            f"İstenen: {result.requested_count}",
            f"Başarılı: {result.success_count}",
            f"Başarısız: {result.failed_count}",
        ]

        if result.success_count > 0:
            lines.append(f"Üretilen kolon: {len(result.output_data.columns)}")

        return "\n".join(lines)


    def format_pattern_feature_summary(self, result: Any, symbol: str | None = None, level: str | None = None) -> str:
        lines = [
            "<b>BIST Bot Pattern Feature Özeti</b>",
            "",
            f"Sembol: {self._escape(symbol or 'Bilinmiyor')}",
            f"Seviye: {self._escape(level or 'Bilinmiyor')}",
            f"İstenen: {result.requested_count}",
            f"Başarılı: {result.success_count}",
            f"Başarısız: {result.failed_count}",
        ]

        if result.success_count > 0:
            lines.append(f"Üretilen kolon: {len(result.output_data.columns)}")

        return "\n".join(lines)


def format_divergence_result(result, symbol: str | None = None) -> str:
    sym = symbol or result.symbol
    lines = [
        "<b>BIST Bot Divergence Feature Özeti</b>",
        "",
        f"Sembol: {sym}",
        f"Pivot modu: {result.pivot_mode.value}",
        f"İndikatörler: {', '.join(result.requested_indicators)}",
        f"Tespit sayısı: {result.detected_count}",
        f"Bullish: {result.bullish_count()}",
        f"Bearish: {result.bearish_count()}",
        f"Strong: {result.strong_count()}",
        "",
        "<i>Bu çıktı sinyal/tavsiye değildir.</i>"
    ]
    return "\n".join(lines)

    def format_benchmark_result(self, result: Any) -> str:
        """Formats a BenchmarkExecutionResult into a Telegram message."""
        lines = [
            "<b>BIST Bot Benchmark Reference</b>",
            "",
            f"Sembol: {self._escape(result.request.symbol or 'N/A')}",
            f"Benchmark: {self._escape(result.request.benchmark_name)}",
        ]

        if result.signals:
            signal = result.signals[0]
            lines.append(f"Intent: {signal.intent.value}")
            lines.append(f"Score: {signal.score:.2f}")
            if signal.reference_price is not None:
                lines.append(f"Reference Price: {signal.reference_price:.2f}")

            if signal.reasons:
                lines.append(f"Reason: {self._escape(signal.reasons[0])}")

        lines.append("")
        lines.append("<i>Bu çıktı benchmark referansıdır.</i>")
        lines.append("<i>Yatırım tavsiyesi değildir. Emir gönderilmedi.</i>")

        # Primitive forbidden claim guard (full guard is handled by core but we double check representation)
        text = "\n".join(lines)
        forbidden_phrases = ["kesin al", "kesin sat", "garanti getiri", "risksiz", "yüzde yüz"]
        for p in forbidden_phrases:
            if p in text.lower():
                 return "<b>[WARNING]</b>\nBenchmark çıktısında yasaklı ifade saptandı. İçerik gizlendi."

        return text

    def format_benchmark_batch(self, batch: Any) -> str:
        """Formats a BenchmarkBatchResult into a Telegram message."""
        lines = [
            "<b>BIST Bot Benchmark Batch Özeti</b>",
            "",
            f"Benchmark: {self._escape(batch.benchmark_name)}",
            f"İstenen Sembol: {len(batch.requested_symbols)}",
            f"Başarılı Sinyal: {batch.success_count}",
            f"Başarısız Sembol/Run: {batch.failed_count}",
        ]

        lines.append("")
        lines.append("<i>Bu çıktı benchmark referansıdır.</i>")
        lines.append("<i>Yatırım tavsiyesi değildir. Emir gönderilmedi.</i>")

        text = "\n".join(lines)
        return text
