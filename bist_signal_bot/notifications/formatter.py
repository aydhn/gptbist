
from bist_signal_bot.review_workflow.models import ReviewCase, ReviewChecklistItem, DecisionJournalEntry, ReviewSignoffRequest, ReviewWorkflowReport
from typing import Any


from bist_signal_bot.reports.models import GeneratedReport, TelegramDigest
from ..research.models import ResearchRun, ResearchComparisonReport, AttributionReport, SignalJournalEntry
import html
from typing import Any

from bist_signal_bot.notifications.models import NotificationMessage
from bist_signal_bot.security.claims_guard import UnsafeClaimGuard
from bist_signal_bot.security.redaction import SecretRedactor
from bist_signal_bot.config.settings import settings as default_settings



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
    def format_model_record(self, model: Any) -> str:
        return f"BIST Bot Model Registry Özeti\n\nModel: {model.model_name}\nVersion: {model.version}\nStatus: {model.status.value}\n\nBu çıktı yerel model yönetişimi özetidir.\nYatırım tavsiyesi değildir.\nİşlem uygunluğu anlamına gelmez.\nGerçek emir gönderilmedi."


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



    def format_telegram_command_result(self, result: Any) -> str:
        text = f"Command Result: {result.status.value}\n"
        text += f"Elapsed: {result.elapsed_seconds:.2f}s\n"
        text += f"\n{result.response_text}"
        return self._escape(text)

    def format_notification_message(self, message: Any) -> str:
        text = f"[{message.priority.value}] {message.title}\n"
        text += f"{message.body}"
        return self._escape(text)

    def format_digest_result(self, result: Any) -> str:
        text = f"=== {result.title} ===\n"
        text += f"{result.body}"
        return self._escape(text)

    def format_telegram_status_summary(self, stats: dict[str, Any]) -> str:
        text = "Telegram Center Status\n"
        for k, v in stats.items():
            text += f"• {k}: {v}\n"
        return self._escape(text)

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

    def format_scenario_result(self, result: 'ScenarioResult') -> str:
        from bist_signal_bot.scenarios.reporting import format_scenario_result_text
        return format_scenario_result_text(result)

    def format_golden_comparison(self, result: 'GoldenComparisonResult') -> str:
        from bist_signal_bot.scenarios.reporting import format_golden_comparison_text
        return format_golden_comparison_text(result)

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

    def format_paper_run_result(self, result: Any) -> str:
        lines = [
            "<b>BIST Bot Paper Trading Özeti</b>",
            "",
            f"Account: {self._escape(result.account.account_id)}",
            f"Signals: {len(result.signals)}",
            f"Paper Orders: {len(result.orders)}",
            f"Paper Fills: {len(result.fills)}",
            f"Cash: {result.account.cash:,.2f} TRY",
            f"Equity: {result.account.equity:,.2f} TRY",
            f"Open Positions: {len(result.positions)}",
            "",
            "<i>Bu bir paper trading simülasyonudur.</i>",
            "<i>Yatırım tavsiyesi değildir.</i>",
            "<i>Gerçek emir gönderilmedi.</i>"
        ]

        text = "\n".join(lines)
        forbidden_phrases = ["kesin al", "kesin sat", "garanti getiri", "risksiz", "yüzde yüz"]
        for p in forbidden_phrases:
            if p in text.lower():
                 return "<b>[WARNING]</b>\nPaper çıktısında yasaklı ifade saptandı. İçerik gizlendi."

        return text

    def format_paper_fill(self, fill: Any) -> str:
        lines = [
            "<b>BIST Bot Paper Simulated Fill</b>",
            "",
            f"Sembol: {self._escape(fill.symbol)}",
            f"Yön: {self._escape(fill.side.value)}",
            f"Miktar: {fill.quantity}",
            f"Gerçekleşen Fiyat: {fill.fill_price:,.2f}",
            f"Efektif Fiyat: {fill.effective_price:,.2f}",
            f"Toplam Maliyet: {fill.total_cost:,.2f} TRY",
            "",
            "<i>Simülasyon. Gerçek emir gönderilmedi.</i>"
        ]
        return "\n".join(lines)

    def format_paper_status(self, state: Any) -> str:
        lines = [
            "<b>BIST Bot Paper Account Status</b>",
            "",
            f"Account ID: {self._escape(state.account.account_id)}",
            f"Status: {state.account.status.value}",
            f"Cash: {state.account.cash:,.2f} TRY",
            f"Equity: {state.account.equity:,.2f} TRY",
            f"Open Positions: {len(state.open_positions())}",
            "",
            "<i>Simülasyon. Gerçek portföy değildir.</i>"
        ]
        return "\n".join(lines)

    def format_scan_report(self, report: Any) -> str:
        lines = [
            "<b>BIST Bot Sinyal Tarama Özeti</b>",
            "",
            f"Strateji: {self._escape(report.request.strategy_name)}",
            f"Taranan: {report.total_symbols}",
            f"Geçen: {report.passed_count}",
            f"Reddedilen: {report.rejected_count}",
            f"Filtrelenen: {report.filtered_count}",
            f"Hata: {report.error_count}",
            ""
        ]

        top = report.top_candidates(report.request.top_n)
        if top:
            lines.append("<b>Top Adaylar:</b>")
            for r in top:
                sig_dir = r.signal.direction.value if r.signal else "N/A"
                final_score = r.risk_decision.final_score if r.risk_decision and r.risk_decision.final_score else (r.signal.score if r.signal and r.signal.score else 0)
                lines.append(f"{r.rank}. {self._escape(r.symbol)} — Final Score: {final_score:.1f} — Status: {r.status.value}")
        else:
            lines.append("Geçen aday bulunamadı.")

        lines.extend([
            "",
            "<i>Bu çıktı araştırma amaçlı sinyal taramasıdır.</i>",
            "<i>Yatırım tavsiyesi değildir.</i>",
            "<i>Gerçek emir gönderilmedi.</i>"
        ])

        text = "\n".join(lines)

        forbidden_phrases = ["kesin al", "kesin sat", "garanti getiri", "risksiz", "yüzde yüz"]
        for p in forbidden_phrases:
            if p in text.lower():
                 return "<b>[WARNING]</b>\nTarama çıktısında yasaklı ifade saptandı. İçerik gizlendi."

        return text

    def format_scan_top_candidates(self, report: Any, limit: int = 5) -> str:
        # Alias or similar behavior
        return self.format_scan_report(report)

    def format_optimization_result(self, result: Any) -> str:
        summary = result.summary()
        lines = [
            "<b>BIST Bot Optimization Özeti</b>",
            "",
            f"Sembol: {self._escape(result.symbol)}",
            f"Strateji: {self._escape(result.strategy_name)}",
            f"Method: {self._escape(result.method.value)}",
            f"Objective: {self._escape(result.objective.value)}",
            f"Trial: {result.total_trials_run}",
            f"Best Score: {summary.get('best_score', 'N/A')}",
            f"Best Params: {self._escape(str(summary.get('best_params')))}"
        ]

        if result.best_trial and result.best_trial.performance_report:
             pr = result.best_trial.performance_report
             lines.append(f"Best Return: {pr.return_metrics.total_return_pct:.2f}%" if pr.return_metrics.total_return_pct is not None else "Best Return: N/A")
             lines.append(f"Max DD: {pr.risk_metrics.max_drawdown_pct:.2f}%" if pr.risk_metrics.max_drawdown_pct is not None else "Max DD: N/A")
             lines.append(f"Sharpe: {pr.risk_adjusted_metrics.sharpe_ratio:.2f}" if pr.risk_adjusted_metrics.sharpe_ratio is not None else "Sharpe: N/A")

        lines.extend([
            "",
            "<i>Bu çıktı geçmiş veri optimizasyon araştırmasıdır.</i>",
            "<i>Gelecek performans garantisi değildir.</i>",
            "<i>Yatırım tavsiyesi değildir.</i>",
            "<i>Gerçek emir gönderilmedi.</i>"
        ])

        text = "\n".join(lines)

        forbidden_phrases = ["kesin al", "kesin sat", "garanti getiri", "risksiz", "yüzde yüz"]
        for p in forbidden_phrases:
            if p in text.lower():
                 return "<b>[WARNING]</b>\nOptimizasyon çıktısında yasaklı ifade saptandı. İçerik gizlendi."

        return text

    def format_walk_forward_optimization_result(self, result: Any) -> str:
        summary = result.summary()
        lines = [
            "<b>BIST Bot WF Optimization Özeti</b>",
            "",
            f"Sembol: {self._escape(result.symbol)}",
            f"Strateji: {self._escape(result.strategy_name)}",
            f"Splits: {len(result.split_results)}",
            f"Status: {self._escape(result.status.value)}",
            f"Stability: {summary.get('parameter_stability_score', 0):.1f}%",
            f"Mean OOS Return: {summary.get('mean_oos_return_pct')}",
            f"Positive OOS Pct: {summary.get('positive_oos_split_pct')}",
        ]

        lines.extend([
            "",
            "<i>Bu çıktı geçmiş veri optimizasyon araştırmasıdır.</i>",
            "<i>Gelecek performans garantisi değildir.</i>",
            "<i>Yatırım tavsiyesi değildir.</i>",
            "<i>Gerçek emir gönderilmedi.</i>"
        ])

        text = "\n".join(lines)

        forbidden_phrases = ["kesin al", "kesin sat", "garanti getiri", "risksiz", "yüzde yüz"]
        for p in forbidden_phrases:
            if p in text.lower():
                 return "<b>[WARNING]</b>\nOptimizasyon çıktısında yasaklı ifade saptandı. İçerik gizlendi."

        return text

def format_ml_dataset_result(result) -> str:
    lines = [
        "BIST Bot ML Dataset Özeti",
        "",
        f"Sembol: {', '.join(result.request.symbols) if len(result.request.symbols) <= 5 else f'{len(result.request.symbols)} sembol'}",
        f"Satır: {result.row_count}",
        f"Feature: {result.feature_count}",
        f"Label: {result.label_count}",
        f"Task: {result.request.task_type.value}",
        f"Label Horizon: {result.request.label_config.horizon_bars}",
    ]
    if result.train_data is not None and result.test_data is not None:
        lines.append(f"Train/Test: {len(result.train_data)} / {len(result.test_data)}")

    lines.extend([
        "",
        "Bu çıktı ML veri seti araştırma çıktısıdır.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ])
    return "\n".join(lines)


def format_ml_train_result(result) -> str:
    from bist_signal_bot.ml.training.models import MLTrainResult
    res: MLTrainResult = result
    lines = [
        "🤖 <b>BIST Signal Bot ML Training</b>",
        f"<b>Status:</b> {res.status.value}",
        f"<b>Model:</b> {res.config.model_type.value}",
        f"<b>Task:</b> {res.config.task_type.value}",
        f"<b>Target:</b> {res.config.target_col}",
        f"<b>Train/Test:</b> {res.prepared_data_summary.get('train_rows', 0)} / {res.prepared_data_summary.get('test_rows', 0)}"
    ]
    if res.classification_metrics:
        m = res.classification_metrics
        lines.append(f"<b>Accuracy:</b> {m.accuracy:.4f}" if m.accuracy else "<b>Accuracy:</b> N/A")
        lines.append(f"<b>F1:</b> {m.f1:.4f}" if m.f1 else "<b>F1:</b> N/A")
        lines.append(f"<b>ROC AUC:</b> {m.roc_auc:.4f}" if m.roc_auc else "<b>ROC AUC:</b> N/A")
    elif res.regression_metrics:
        m = res.regression_metrics
        lines.append(f"<b>MAE:</b> {m.mae:.4f}" if m.mae else "<b>MAE:</b> N/A")
        lines.append(f"<b>R2:</b> {m.r2:.4f}" if m.r2 else "<b>R2:</b> N/A")

    if res.artifact and res.artifact.model_id:
        lines.append(f"<b>Model ID:</b> {res.artifact.model_id}")

    lines.append("")
    lines.append("<i>Bu çıktı ML araştırma çıktısıdır. Tahminler yatırım tavsiyesi değildir. Gerçek emir gönderilmedi.</i>")
    return "\n".join(lines)

def format_ml_prediction_result(result) -> str:
    from bist_signal_bot.ml.training.models import MLPredictionResult
    res: MLPredictionResult = result
    lines = [
        "🤖 <b>BIST Signal Bot ML Prediction</b>",
        f"<b>Model ID:</b> {res.model_id}",
        f"<b>Predictions:</b> {res.row_count}",
        f"<b>Generated:</b> {res.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC"
    ]
    if res.predictions:
        lines.append("")
        for p in res.predictions[:10]:
            val = f"{p.predicted_value:.4f}" if isinstance(p.predicted_value, float) else str(p.predicted_value)
            lines.append(f"• <b>{p.symbol}</b>: {val}")
        if len(res.predictions) > 10:
            lines.append(f"... ve {len(res.predictions) - 10} sembol daha")

    lines.append("")
    lines.append("<i>Bu çıktı ML araştırma çıktısıdır. Tahminler yatırım tavsiyesi değildir. Gerçek emir gönderilmedi.</i>")
    return "\n".join(lines)

def format_ml_inference_result(result) -> str:
    from bist_signal_bot.ml.inference.reporting import format_ml_inference_text
    return f"<b>BIST Bot ML Filter Özeti</b>\n\n<pre>{format_ml_inference_text(result)}</pre>"

def format_ml_signal_filter_result(result) -> str:
    from bist_signal_bot.ml.inference.reporting import format_ml_signal_filter_text
    return f"<b>BIST Bot ML Filter Özeti</b>\n\n<pre>{format_ml_signal_filter_text(result)}</pre>"

def format_ml_inference_batch_result(batch) -> str:
    from bist_signal_bot.ml.inference.reporting import format_ml_batch_text
    return f"<b>BIST Bot ML Filter Özeti</b>\n\n<pre>{format_ml_batch_text(batch)}</pre>"


from bist_signal_bot.runtime.models import RuntimePipelineResult, RuntimeJobResult

def format_runtime_pipeline_result(result: RuntimePipelineResult) -> str:
    lines = [
        "BIST Bot Runtime Özeti",
        f"Run ID: {result.run_id}",
        f"Durum: {result.status.value}",
        f"Strateji: {result.config.strategy_name}",
        f"Geçen: {result.elapsed_seconds:.2f}s",
        f"",
        "Bu çıktı otomatik araştırma/tarama çıktısıdır.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_runtime_job_result(result: RuntimeJobResult) -> str:
    return f"Job {result.job_type.value} -> {result.status.value} in {result.elapsed_seconds:.2f}s"

def format_runtime_failure(result: RuntimePipelineResult) -> str:
    return f"BIST Bot Runtime FAILED!\nRun ID: {result.run_id}\nStrategy: {result.config.strategy_name}"

# Wrapper to intercept and sanitize format function outputs
def _sanitize_output(text: str) -> str:
    if default_settings.SECURITY_SANITIZE_UNSAFE_CLAIMS:
        text = UnsafeClaimGuard.sanitize_text(text)
    if default_settings.SECURITY_REDACT_NOTIFICATIONS:
        text = SecretRedactor.redact_text(text)
    return text

_original_format_transaction_cost_breakdown = format_transaction_cost_breakdown
def format_transaction_cost_breakdown(cost: Any) -> str:
    return _sanitize_output(_original_format_transaction_cost_breakdown(cost))

_original_format_round_trip_cost_breakdown = format_round_trip_cost_breakdown
def format_round_trip_cost_breakdown(cost: Any) -> str:
    return _sanitize_output(_original_format_round_trip_cost_breakdown(cost))

def format_quality_run_result(result) -> str:
    from bist_signal_bot.quality.models import QualityRunResult, QualityCheckStatus
    if not isinstance(result, QualityRunResult):
        return str(result)

    summary = result.summary()

    lines = [
        "**BIST Bot Quality Gate Özeti**",
        "",
        f"**Status:** {result.status.value}",
        f"**Suite:** {result.config.suite.value}",
        f"**Gate:** {result.config.gate_level.value}",
        f"**Checks:** {summary['checks_total']}",
        f"**Failed:** {summary['checks_failed']}",
        f"**Warnings:** {summary['checks_warn']}",
    ]

    if result.coverage_summary:
        if result.coverage_summary.measured:
            lines.append(f"**Coverage:** {result.coverage_summary.total_coverage_pct}%")
        else:
            lines.append("**Coverage:** skipped")
    else:
        lines.append("**Coverage:** skipped")

    lines.extend([
        "",
        "Bu çıktı kalite kontrol raporudur.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ])

    return "\n".join(lines)

def format_quality_failure(result) -> str:
    lines = [
        "🚨 **BIST Bot Quality Gate FAILED** 🚨",
        "",
        format_quality_run_result(result),
        "",
        "**Failed Checks:**"
    ]
    for check in result.failed_checks():
        lines.append(f"- {check.check_name}: {check.message}")
    return "\n".join(lines)

def format_environment_doctor_report(report) -> str:
    lines = [
        "BIST Bot Environment Summary",
        f"Platform: {report.platform.name}",
        f"Python: {report.python_version}",
        f"Environment: {report.environment_type.name}",
        f"Status: {report.overall_status.name}",
        "",
        report.disclaimer
    ]
    return "\n".join(lines)

def format_release_bundle_result(result) -> str:
    lines = [
        "BIST Bot Release Summary",
        f"Release ID: {result.release_id}",
        f"Status: {result.status.name}",
        f"Format: {result.format.name}",
        f"Elapsed: {result.elapsed_seconds:.2f}s",
        "",
        result.disclaimer
    ]
    return "\n".join(lines)
    def format_docs_validation_report(self, report: Any) -> str:
        msg = "BIST Bot Docs Validation Özeti\n\n"
        msg += f"Status: {report.status.value}\n"
        msg += f"Checked Files: {report.checked_files}\n"
        msg += f"Findings: {len(report.findings)}\n"
        msg += f"Unsafe Claims: {report.unsafe_claims_found}\n"
        msg += f"Secrets: {report.secrets_found}\n"
        msg += f"Missing Pages: {len(report.missing_pages)}\n\n"
        msg += "Bu çıktı dokümantasyon doğrulama raporudur.\nYatırım tavsiyesi değildir.\nGerçek emir gönderilmedi."
        return msg

    def format_docs_generation_result(self, result: Any) -> str:
        msg = "BIST Bot Docs Generation Özeti\n\n"
        msg += f"Status: {result.status.value}\n"
        msg += f"Pages Created: {result.pages_created}\n\n"
        msg += "Bu çıktı dokümantasyon oluşturma raporudur.\nYatırım tavsiyesi değildir.\nGerçek emir gönderilmedi."
        return msg


def format_research_run(run: ResearchRun) -> str:
    lines = [
        "BIST Bot Research Ledger Özeti",
        "",
        f"Run Type: {run.run_type.value}",
        f"Strategy: {run.strategy_name or 'N/A'}",
        f"Symbols: {','.join(run.symbols) if run.symbols else 'N/A'}",
        f"Status: {run.status.value}",
        f"Metrics: {', '.join(f'{k}={v}' for k,v in run.metrics.items())}",
        f"Artifacts: {len(run.artifacts)}",
        "",
        "Bu çıktı araştırma kayıt özetidir.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_research_comparison(report: ResearchComparisonReport) -> str:
    lines = ["BIST Bot Research Comparison", "", f"Title: {report.title}", ""]
    for i in report.items[:5]:
        lines.append(f"{i.rank}. {i.label} -> {i.score}")
    lines.append("", "Yatırım tavsiyesi değildir. Gerçek emir gönderilmedi.")
    return "\n".join(lines)

def format_research_attribution(report: AttributionReport) -> str:
    lines = ["BIST Bot Research Attribution", "", f"Group By: {report.group_by.value}", ""]
    for b in report.buckets[:5]:
        wr = f"{b.win_rate:.1f}%" if b.win_rate else "N/A"
        lines.append(f"{b.group_key} -> Count: {b.count}, WinRate: {wr}")
    lines.append("", "Yatırım tavsiyesi değildir. Gerçek emir gönderilmedi.")
    return "\n".join(lines)

def format_signal_journal_summary(entries: list[SignalJournalEntry]) -> str:
    lines = ["BIST Bot Signal Journal Summary", ""]
    for e in entries[:5]:
        lines.append(f"{e.symbol} | {e.strategy_name} | {e.direction} -> {e.outcome.value}")
    lines.append("", "Yatırım tavsiyesi değildir. Gerçek emir gönderilmedi.")
    return "\n".join(lines)


    def format_generated_report(self, report: GeneratedReport) -> str:
        return f"Research Report: {report.title} [{report.status.value}]\nSections: {len(report.sections)}\nDisclaimer: {report.disclaimer}"

    def format_telegram_digest(self, digest: TelegramDigest) -> str:
        return digest.message

    def format_report_generation_failure(self, error: Any) -> str:
        return f"Report generation failed: {error}"


def format_release_readiness_report(report) -> str:
    lines = [
        "🚀 *BIST Bot Release Readiness*",
        f"Version: {report.config.version}",
        f"Stage: {report.config.stage.value}",
        f"Status: {report.status.value}",
        f"Score: {report.readiness_score:.1f}",
        f"Blockers: {len(report.blockers)}",
        f"Warnings: {report.warning_count}",
        "",
        "Bu çıktı release hazırlık raporudur.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_safe_launch_rehearsal(result) -> str:
    lines = [
        "🧪 *Safe Launch Rehearsal*",
        f"Profile: {result.profile.value}",
        f"Status: {result.status.value}",
        f"Steps: {len(result.steps)}",
        "",
        "Gerçek işlem yapılmadı."
    ]
    return "\n".join(lines)

def format_release_candidate_manifest(manifest) -> str:
    lines = [
        "📦 *Release Candidate Built*",
        f"Version: {manifest.version}",
        f"Stage: {manifest.stage.value}",
        f"Safe: {manifest.no_real_order_sent}",
        "",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_release_notes(notes) -> str:
    lines = [
        f"📄 *Release Notes: {notes.version}*",
        notes.summary,
        "",
        "Gerçek işlem yapılmadı."
    ]
    return "\n".join(lines)

def format_provider_response(response: Any) -> str:
    msg = f"Data Fetch: {response.status.value}\n"
    msg += f"Requested: {len(response.request.symbols)}, Fetched: {len(response.data_by_symbol)}\n"
    if response.warnings:
        msg += f"Warnings: {len(response.warnings)}\n"
    if response.errors:
        msg += f"Errors: {len(response.errors)}\n"
    return msg

def format_import_result(result: Any) -> str:
    msg = f"Data Import: {result.status.value}\n"
    msg += f"Symbol: {result.symbol}, Rows: {result.rows_imported}\n"
    if result.errors:
        msg += f"Errors: {result.errors}\n"
    return msg

def format_freshness_report(report: Any) -> str:
    msg = f"Data Freshness Check\n"
    msg += f"Fresh: {len(report.fresh_symbols)}, Stale: {len(report.stale_symbols)}, Missing: {len(report.missing_symbols)}\n"
    if report.warnings:
        msg += f"Warnings: {len(report.warnings)}\n"
    return msg

def format_data_comparison_report(report: Any) -> str:
    msg = f"Data Comparison: {report.symbol} ({report.status})\n"
    msg += f"Price Diffs: {report.price_diff_count}, Vol Diffs: {report.volume_diff_count}\n"
    if report.warnings:
         for w in report.warnings:
             msg += f"- {w}\n"
    return msg

def format_breadth_snapshot(snapshot) -> str:
    return f"""BIST Bot Breadth Özeti
Universe: {snapshot.universe_name}
Breadth Status: {snapshot.status.value}
Composite Score: {snapshot.composite_score:.1f}

Bu çıktı piyasa genişliği araştırma özetidir.
Yatırım tavsiyesi değildir.
Gerçek emir gönderilmedi."""

def format_breadth_analysis_result(result) -> str:
    return format_breadth_snapshot(result.snapshot)

def format_sector_rotation(scores) -> str:
    return "Sector Rotation calculated."

def format_relative_strength_leaders(scores) -> str:
    return "Relative Strength Leaders calculated."

    def format_research_portfolio_snapshot(self, snapshot: Any) -> str:
        lines = [
            "BIST Bot Research Portfolio Özeti",
            "",
            f"Snapshot: {snapshot.snapshot_id}",
            f"Items: {snapshot.item_count}",
            f"Method: {snapshot.allocation_method.value}",
            f"Total Research Weight: {snapshot.total_weight:.2%}"
        ]

        top_sector = None
        for exp in snapshot.exposures:
            if exp.group.value == "SECTOR":
                if not top_sector or exp.weight > top_sector.weight:
                    top_sector = exp

        if top_sector:
            lines.append(f"Top Sector Exposure: {top_sector.weight:.2%}")

        lines.append(f"Warnings: {len(snapshot.warnings)}")
        lines.append("")
        lines.append("Bu çıktı araştırma portföy sepeti özetidir.")
        lines.append("Yatırım tavsiyesi değildir.")
        lines.append("Gerçek emir gönderilmedi.")

        return "\n".join(lines)

    def format_rebalance_plan(self, plan: Any) -> str:
        lines = [
            "BIST Bot Research Portfolio Rebalance Özeti",
            "",
            f"Plan ID: {plan.plan_id}",
            f"Turnover: {plan.turnover_estimate:.2%}",
            f"Warnings: {len(plan.warnings)}",
            "",
            "Bu çıktı araştırma amaçlı rebalance deltalardır."
            "Yatırım tavsiyesi değildir.",
            "Gerçek emir gönderilmedi."
        ]
        return "\n".join(lines)

    def format_basket_simulation(self, result: Any) -> str:
        lines = [
            "BIST Bot Research Basket Simulation",
            "",
            f"Simulation ID: {result.simulation_id}",
            f"Return: {result.simulated_return_pct:.2f}%",
            "",
            "Bu çıktı geçmişe yönelik araştırma simülasyonudur.",
            "Gelecek performans garantisi vermez.",
            "Gerçek emir gönderilmedi."
        ]
        return "\n".join(lines)

# Drift formatting for notifications
def format_drift_analysis_result(result) -> str:
    from bist_signal_bot.drift.reporting import format_drift_result_text
    return format_drift_result_text(result)

def format_feature_drift_results(results) -> str:
    from bist_signal_bot.drift.reporting import format_feature_drift_text
    return format_feature_drift_text(results)

def format_model_drift_result(result) -> str:
    from bist_signal_bot.drift.reporting import format_model_drift_text
    return format_model_drift_text(result)

def format_signal_decay_report(report) -> str:
    return f"Signal Decay Status: {report.status.value}\nActions: {', '.join([a.value for a in report.recommended_actions])}"

def format_strategy_decay_report(report) -> str:
    return f"Strategy Decay Status: {report.status.value}\nScore: {report.decay_score:.2f}\nActions: {', '.join([a.value for a in report.recommended_actions])}"


def format_backup_result(result) -> str:
    lines = [
        "BIST Bot Maintenance Özeti",
        "",
        f"Backup: {result.status.value}",
        f"Included Files: {result.manifest.included_files}",
        f"Excluded Files: {result.manifest.excluded_files}",
        f"Verified: {'true' if result.verified else 'false'}",
        f"Warnings: {len(result.warnings)}",
        "",
        "Bu çıktı operasyonel bakım özetidir.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_restore_result(result) -> str:
    lines = [
        "BIST Bot Restore Özeti",
        "",
        f"Restore: {result.status.value}",
        f"Restored: {result.restored_files}",
        f"Blocked: {result.blocked_files}",
        "",
        "Bu çıktı operasyonel bakım özetidir.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_cleanup_result(result) -> str:
    lines = [
        "BIST Bot Cleanup Özeti",
        "",
        f"Cleanup: {result.status.value}",
        f"Deleted: {result.deleted_files}",
        f"Candidates: {len(result.candidates)}",
        "",
        "Bu çıktı operasyonel bakım özetidir.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_maintenance_doctor_report(report) -> str:
    lines = [
        "BIST Bot Doctor Özeti",
        "",
        f"Status: {report.status.value}",
        f"Missing Dirs: {len(report.missing_dirs)}",
        f"Corrupted: {len(report.corrupted_files)}",
        f"Secret Risks: {len(report.secret_risk_files)}",
        "",
        "Bu çıktı operasyonel bakım özetidir.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

    def format_audit_review_result(self, result: Any) -> str:
        lines = [
            "BIST Bot Governance Özeti",
            "",
            f"Status: {result.status.value}",
            f"Findings: {len(result.findings)}",
            f"Critical: {sum(1 for f in result.findings if f.severity.value in ('CRITICAL', 'HIGH'))}",
            f"Blocked: {result.blocked_count}",
            f"Warnings: {result.warning_count}",
            "",
            "Bu çıktı operasyonel governance özetidir.",
            "Yatırım tavsiyesi değildir.",
            "Gerçek emir gönderilmedi."
        ]
        return "\n".join(lines)

    def format_governance_gate_result(self, result: Any) -> str:
        lines = [
            "BIST Bot Governance Gate",
            f"Gate: {result.request.gate_name}",
            f"Decision: {result.decision.value}",
            "Gerçek emir gönderilmedi."
        ]
        return "\n".join(lines)

    def format_evidence_pack_manifest(self, manifest: Any) -> str:
        return f"Evidence Pack Created: {manifest.pack_name}\nNo real order sent."

    def format_compliance_attestation(self, attestation: Any) -> str:
        return f"Compliance Attestation: {attestation.status.value}\nNot investment advice."


def format_review_item(item) -> str:
    return f"[{item.symbol}] Review Item: {item.status.value}\n{item.summary}\n{item.disclaimer}"

def format_review_decision(decision) -> str:
    return f"Decision: {decision.decision_type.value}\nReason: {decision.reason}\n{decision.disclaimer}"

def format_review_inbox_summary(summary) -> str:
    lines = [
        "BIST Bot Analyst Review Özeti",
        "",
        f"New: {summary.new_count}",
        f"In Review: {summary.in_review_count}",
        f"Watch Only: {summary.watch_only_count}",
        f"Approved Research: {summary.approved_research_count}",
        f"Due Follow-ups: {summary.waiting_followup_count}",
        "",
        "Bu çıktı analist araştırma review özetidir.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_review_followups(items) -> str:
    if not items:
        return "No due follow-ups."
    lines = ["Due follow-ups:"]
    for i in items:
        lines.append(f"- {i.symbol}")
    return "\n".join(lines)

def format_knowledge_index_build(result: Any) -> str:
    return f"BIST Bot Knowledge Base\n\nIndex Status: {result.status.value}\nDocuments: {result.documents_indexed}\nChunks: {result.chunks_created}\n\nBu çıktı araştırma hafızası operasyon özetidir.\nYatırım tavsiyesi değildir.\nGerçek emir gönderilmedi."
# Scheduler Formatting
def format_scheduler_run_result(result) -> str:
    from bist_signal_bot.scheduler.reporting import format_scheduler_run_text
    return format_scheduler_run_text(result)

def format_due_job_result(result) -> str:
    from bist_signal_bot.scheduler.reporting import format_due_result_text
    return format_due_result_text(result)

def format_market_session_snapshot(snapshot) -> str:
    from bist_signal_bot.scheduler.reporting import format_market_session_text
    return format_market_session_text(snapshot)

def format_scheduled_job_run(run) -> str:
    return f"Job Run: {run.job_name} ({run.status.value})"

# Deployment Notification Formatters
def format_deployment_doctor(checks: list) -> str:
    msg = ["🛠️ **Deployment Doctor Summary**\n"]
    passed = sum(1 for c in checks if c.status.name == "PASS")
    total = len(checks)
    msg.append(f"Checks Passed: {passed}/{total}\n")
    for check in checks:
        if check.status.name != "PASS":
            msg.append(f"⚠️ {check.title}: {check.status.name}")
            if check.message:
                msg.append(f"   {check.message}")
    msg.append("\n_This output is for operational deployment guidance only._")
    return "\n".join(msg)

def format_first_run_result(result: Any) -> str:
    msg = [
        "🚀 **BIST Bot Deployment Özeti**\n",
        f"Profile: {result.profile.profile_type.name}",
        f"Environment: {result.status.name}"
    ]

    smoke_step = next((s for s in result.steps if s.step_type.name == "RUN_SMOKE_TESTS"), None)
    if smoke_step:
        msg.append(f"Smoke Test: {smoke_step.status.name}")

    msg.append(f"Scheduler Dry Run: {'Enabled' if result.profile.scheduler_dry_run else 'Disabled'}")
    msg.append(f"Telegram Send: {'Enabled' if result.profile.telegram_send_enabled else 'Disabled'}")
    msg.append(f"Broker: {'Enabled' if getattr(result.profile, 'broker_enabled', False) else 'Disabled'}")

    msg.append("\nBu çıktı operasyonel kurulum özetidir.")
    msg.append("Yatırım tavsiyesi değildir.")
    msg.append("Gerçek emir gönderilmedi.")

    return "\n".join(msg)

def format_smoke_test_result(result: Any) -> str:
    msg = [
        "💨 **Smoke Test Summary**\n",
        f"Status: {result.status.name}",
        f"Commands Tested: {len(result.commands_tested)}"
    ]
    if result.errors:
        msg.append("\nErrors:")
        for err in result.errors:
            msg.append(f"- {err}")
    msg.append("\n_Smoke test is operational only. No real order was sent._")
    return "\n".join(msg)

def format_operator_runbook_summary(runbook: Any) -> str:
    msg = [
        "📖 **Operator Runbook Generated**\n",
        f"Profile: {runbook.profile_type.name}",
        f"Sections: {len(runbook.sections)}"
    ]
    msg.append("\n_Operator runbook is operational guidance only. Not investment advice. No real order was sent._")
    return "\n".join(msg)

def format_config_validation_result(result) -> str:
    lines = [
        "**BIST Bot Config Registry Özeti**\n",
        f"Validation: {result.status.value}",
        f"Records Checked: {result.records_checked}",
        f"Warnings: {result.warning_count}",
        f"Blocked: {result.blocked_count}\n",
        f"Bu çıktı operasyonel config özetidir.",
        f"Yatırım tavsiyesi değildir.",
        f"Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_config_snapshot(snapshot) -> str:
    lines = [
        "**Config Snapshot Created**",
        f"ID: {snapshot.snapshot_id}",
        f"Profile: {snapshot.profile_type.value if snapshot.profile_type else 'None'}",
        f"Checksum: {snapshot.checksum_sha256[:8] if snapshot.checksum_sha256 else ''}"
    ]
    return "\n".join(lines)

def format_config_diff(diff) -> str:
    lines = [
        "**Config Diff**",
        f"Changed: {diff.changed_count}",
        f"Dangerous: {diff.dangerous_count}",
        f"Blocked: {diff.blocked_count}"
    ]
    return "\n".join(lines)

def format_config_drift(result) -> str:
    lines = [
        "**Config Drift Report**",
        f"Status: {result.status.value}",
        f"Score: {result.drift_score:.1f}"
    ]
    return "\n".join(lines)

def format_config_gate(result) -> str:
    lines = [
        "**Config Gate Result**",
        f"Gate: {result.request.gate_name}",
        f"Decision: {result.decision.value}",
        f"Blocked: {result.blocked}"
    ]
    return "\n".join(lines)

def format_strategy_validation_result(result) -> str:
    return f"Validation {result.status}"

def format_walk_forward_result(result) -> str:
    return f"WF {result.status}"

def format_overfit_diagnostics(result) -> str:
    return f"Overfit {result.status}"

def format_parameter_stability(result) -> str:
    return f"Stability {result.status}"

def format_cost_robustness(result) -> str:
    return f"Cost {result.status}"

def format_signal_explanation(explanation: Any) -> str:
    return "Signal Explanation Mock"

def format_evidence_card(card: Any) -> str:
    return "Evidence Card Mock"

def format_decision_trace(trace: Any) -> str:
    return "Decision Trace Mock"

def format_research_portfolio(portfolio: Any) -> str:
    lines = [
        f"BIST Bot Research Portfolio Ledger Özeti",
        "",
        f"Portfolio: {portfolio.name}",
        f"Status: {portfolio.status.value}",
        f"Initial Notional: {portfolio.initial_notional:,.2f} {portfolio.base_currency}"
    ]
    if portfolio.current_simulated_nav is not None:
        lines.append(f"Simulated NAV: {portfolio.current_simulated_nav:,.2f} {portfolio.base_currency}")
    lines.append("")
    lines.append("Bu çıktı araştırma amaçlı simülasyon özetidir.")
    lines.append("Yatırım tavsiyesi değildir.")
    lines.append("Gerçek emir gönderilmedi.")
    return "\n".join(lines)

def format_portfolio_valuation(snapshot: Any) -> str:
    lines = [
        f"BIST Bot Research Portfolio Ledger Özeti",
        "",
        f"Portfolio ID: {snapshot.portfolio_id}",
        f"Simulated NAV: {snapshot.simulated_nav:,.2f}"
    ]
    if snapshot.net_return_pct is not None:
        lines.append(f"Net Return: {snapshot.net_return_pct:.2f}%")
    if snapshot.total_cost_drag_pct is not None:
        lines.append(f"Cost Drag: {snapshot.total_cost_drag_pct:.2f}%")

    lines.append("")
    lines.append("Bu çıktı araştırma amaçlı simülasyon özetidir.")
    lines.append("Yatırım tavsiyesi değildir.")
    lines.append("Gerçek emir gönderilmedi.")
    return "\n".join(lines)

def format_portfolio_attribution(result: Any) -> str:
    lines = [
        f"BIST Bot Research Portfolio Ledger Özeti",
        "",
        f"Portfolio ID: {result.portfolio_id}"
    ]
    if result.top_positive_contributors:
        lines.append(f"Top Positive: {', '.join(result.top_positive_contributors)}")
    if result.top_negative_contributors:
        lines.append(f"Top Negative: {', '.join(result.top_negative_contributors)}")

    lines.append("")
    lines.append("Bu çıktı araştırma amaçlı simülasyon özetidir.")
    lines.append("Yatırım tavsiyesi değildir.")
    lines.append("Gerçek emir gönderilmedi.")
    return "\n".join(lines)

def format_portfolio_outcome(result: Any) -> str:
    lines = [
        f"BIST Bot Research Portfolio Ledger Özeti",
        "",
        f"Portfolio ID: {result.portfolio_id}",
        f"Horizon: {result.horizon_days} days",
        f"Label: {result.label.value}"
    ]
    if result.net_return_pct is not None:
        lines.append(f"Net Return: {result.net_return_pct:.2f}%")

    lines.append("")
    lines.append("Bu çıktı araştırma amaçlı simülasyon özetidir.")
    lines.append("Yatırım tavsiyesi değildir.")
    lines.append("Gerçek emir gönderilmedi.")
    return "\n".join(lines)

def format_portfolio_ledger_report(report: Any) -> str:
    lines = [
        f"BIST Bot Research Portfolio Ledger Raporu",
        "",
        f"Portfolios: {len(report.portfolios)}",
        f"Valuations: {len(report.valuations)}",
        f"Attributions: {len(report.attributions)}",
        ""
    ]
    for k in report.key_findings:
        lines.append(f"- {k}")

    lines.append("")
    lines.append("Bu çıktı araştırma amaçlı simülasyon özetidir.")
    lines.append("Yatırım tavsiyesi değildir.")
    lines.append("Gerçek emir gönderilmedi.")
    return "\n".join(lines)

    def format_whatif_run_result(self, result: Any) -> str:
        lines = [
            "BIST Bot What-If Özeti",
            f"Scenarios: {len(result.scenario_results)}",
            f"Run ID: {result.run_id}"
        ]
        if result.comparison:
            baseline = next((r for r in result.scenario_results if r.scenario.scenario_type.value == "BASELINE"), None)
            best_id = result.comparison.best_scenario_id
            worst_id = result.comparison.worst_scenario_id

            if baseline:
                lines.append(f"Baseline Net Quality: {baseline.estimated_net_quality_score}")

            worst = next((r for r in result.scenario_results if r.result_id == worst_id), None)
            if worst:
                lines.append(f"Worst Scenario Net Quality: {worst.estimated_net_quality_score}")
                lines.append(f"Key Warning: {worst.scenario.name} scenario reduces net quality materially.")

            if result.comparison.sensitivity_findings:
                most_sens = result.comparison.sensitivity_findings[0].assumption_type.value
                lines.append(f"Most Sensitive Assumption: {most_sens}")

        lines.extend([
            "",
            "Bu çıktı araştırma amaçlı varsayım analizi özetidir.",
            "Yatırım tavsiyesi değildir.",
            "Gerçek emir gönderilmedi."
        ])
        return "\n".join(lines)

    def format_whatif_comparison(self, result: Any) -> str:
        lines = [
            "What-If Comparison",
            f"Best: {result.best_scenario_id}",
            f"Worst: {result.worst_scenario_id}"
        ]
        return "\n".join(lines)

    def format_capital_scaling_result(self, result: Any) -> str:
        lines = [
            "Capital Scaling Result",
            f"Best Notional: {result.best_research_notional}"
        ]
        return "\n".join(lines)

    def format_policy_sandbox_result(self, result: Any) -> str:
        lines = [
            "Policy Sandbox",
            f"Tested Policy: {result.policy_name}"
        ]
        return "\n".join(lines)

def format_market_event(event: Any) -> str:
    msg = f"📅 **Market Event:** {event.title}\n"
    msg += f"• Date: {event.event_date.strftime('%Y-%m-%d')}\n"
    msg += f"• Type: {event.event_type.value}\n"
    msg += f"• Scope: {event.scope.value}\n"
    if event.symbol:
        msg += f"• Symbol: {event.symbol}\n"
    msg += f"• Severity: {event.severity.value}\n"
    msg += f"• Status: {event.status.value}\n"
    msg += "\n*This is an operational research metadata record. It is not investment advice. No real order was sent.*\n"
    return msg

def format_event_risk_assessment(assessment: Any) -> str:
    msg = f"⚠️ **BIST Bot Event Risk Özeti**\n\n"
    msg += f"Sembol: {assessment.symbol or 'Market-wide'}\n"
    if assessment.matching_events:
        msg += f"Yakın Event: {assessment.matching_events[0].title}\n"
    else:
        msg += "Yakın Event: None\n"

    window_status = "ACTIVE" if assessment.matching_windows else "NONE"
    msg += f"Event Window: {window_status}\n"
    msg += f"Risk Score: {assessment.risk_score or 0}\n"
    msg += f"Decision: {assessment.decision.value}\n\n"
    msg += "Bu çıktı araştırma amaçlı event risk özetidir.\nYatırım tavsiyesi değildir.\nGerçek emir gönderilmedi.\n"
    return msg

def format_event_calendar_snapshot(snapshot: Any) -> str:
    msg = f"🗓️ **Event Calendar Snapshot**\n"
    msg += f"• Total Events: {snapshot.events_count}\n"
    msg += f"• Upcoming: {snapshot.upcoming_count}\n"
    msg += f"• High Severity: {snapshot.high_severity_count}\n"
    msg += "\n*This snapshot is research-only metadata. No real orders were sent.*\n"
    return msg

def format_financial_statement(statement) -> str:
    return f"Statement: {statement.symbol} {statement.fiscal_year} {statement.fiscal_period}"

def format_financial_ratios(ratios) -> str:
    return f"Ratios for {len(ratios)} metrics"

def format_earnings_quality(assessment) -> str:
    return f"""
BIST Bot Finansal Özet

Sembol: {assessment.symbol}
Dönem: {assessment.fiscal_year}{assessment.fiscal_period}
Earnings Quality Score: {assessment.overall_quality_score}
Status: {assessment.status.value}

Bu çıktı araştırma amaçlı finansal tablo özetidir.
Yatırım tavsiyesi değildir.
Gerçek emir gönderilmedi.
"""

def format_financial_analysis_report(report) -> str:
    return f"Report for {report.symbol}"

def format_valuation_multiples(multiples: list) -> str:
    return "Valuation Multiples Summary..."

def format_valuation_risk(assessment: Any) -> str:
    # Stub format, real one uses proper values
    return "Valuation Risk Assessment Summary..."

def format_valuation_report(report: Any) -> str:
    return "Valuation Report Summary..."


def format_factor_summary():
    return '''BIST Bot Factor Özeti

Sembol: ASELS
Aggregate Factor Score: 68
Dominant Factors: MOMENTUM, QUALITY
Weak Factors: VALUE
Crowding: MEDIUM

Bu çıktı araştırma amaçlı faktör analizidir.
Yatırım tavsiyesi değildir.
Gerçek emir gönderilmedi.'''

from bist_signal_bot.breadth.models import AdvanceDeclineSummary, BreadthRegimeSnapshot, SectorBreadthSummary, BreadthReport

def format_breadth_regime(snapshot: BreadthRegimeSnapshot) -> str:
    msg = f"BIST Bot Breadth Regime\n\n"
    msg += f"Regime: {snapshot.label.value}\n"
    msg += f"Status: {snapshot.status.value}\n"
    msg += f"Breadth Score: {snapshot.breadth_score}\n"
    msg += f"Participation Score: {snapshot.participation_score}\n"
    msg += f"\nBu çıktı araştırma amaçlı piyasa iç yapı analizidir.\n"
    msg += f"Yatırım tavsiyesi değildir.\n"
    msg += f"Gerçek emir gönderilmedi.\n"
    return msg

def format_advance_decline(summary: AdvanceDeclineSummary) -> str:
    msg = f"BIST Bot Advance/Decline\n\n"
    msg += f"Advances: {summary.advances}\n"
    msg += f"Declines: {summary.declines}\n"
    msg += f"Unchanged: {summary.unchanged}\n"
    msg += f"AD Ratio: {summary.advance_decline_ratio}\n"
    msg += f"\nBu çıktı araştırma amaçlı piyasa iç yapı analizidir.\n"
    msg += f"Yatırım tavsiyesi değildir.\n"
    msg += f"Gerçek emir gönderilmedi.\n"
    return msg

def format_sector_breadth(summaries: list[SectorBreadthSummary]) -> str:
    msg = f"BIST Bot Sector Breadth\n\n"
    for s in summaries:
         msg += f"- {s.sector}: Score {s.sector_breadth_score}, AD {s.advance_percent}%\n"
    msg += f"\nBu çıktı araştırma amaçlı piyasa iç yapı analizidir.\n"
    msg += f"Yatırım tavsiyesi değildir.\n"
    msg += f"Gerçek emir gönderilmedi.\n"
    return msg

def format_breadth_report(report: BreadthReport) -> str:
    msg = f"BIST Bot Breadth Özeti\n\n"

    if report.regime:
        msg += f"Regime: {report.regime.label.value}\n"
        msg += f"Breadth Score: {report.regime.breadth_score}\n"

    if report.participation:
        msg += f"Participation Score: {report.participation.participation_score}\n"

    if report.advance_decline:
        msg += f"AD Ratio: {report.advance_decline.advance_decline_ratio}\n"

    if report.divergences:
        msg += f"Divergence Warning: Var ({len(report.divergences)})\n"
    else:
        msg += f"Divergence Warning: Yok\n"

    msg += f"\nBu çıktı araştırma amaçlı piyasa iç yapı analizidir.\n"
    msg += f"Yatırım tavsiyesi değildir.\n"
    msg += f"Gerçek emir gönderilmedi.\n"
    return msg


from bist_signal_bot.context_fusion.models import UnifiedContextSnapshot, ContextConflict, EvidenceGap, ContextFusionReport

def format_unified_context_snapshot(snapshot: UnifiedContextSnapshot) -> str:
    msg = "BIST Bot Unified Context Özeti\n\n"
    msg += f"Sembol: {snapshot.symbol}\n"
    if snapshot.composite_score:
        msg += f"Composite Research Score: {snapshot.composite_score.adjusted_score:.2f} ({snapshot.composite_score.final_status.value})\n"
    msg += f"Conflicts: {len(snapshot.conflicts)}\n"
    msg += f"Evidence Gaps: {len(snapshot.evidence_gaps)}\n"
    msg += f"Key Supports: {', '.join(snapshot.key_supports) if snapshot.key_supports else 'None'}\n"
    msg += f"Key Pressures: {', '.join(snapshot.key_pressures) if snapshot.key_pressures else 'None'}\n\n"
    msg += "Bu çıktı araştırma amaçlı birleşik bağlam özetidir.\nYatırım tavsiyesi değildir.\nGerçek emir gönderilmedi."
    return msg

def format_context_conflicts(conflicts: list[ContextConflict]) -> str:
    msg = "BIST Bot Context Conflicts\n\n"
    for c in conflicts:
        msg += f"[{c.severity.value}] {c.conflict_type.value}: {c.message}\n"
    return msg

def format_evidence_gaps(gaps: list[EvidenceGap]) -> str:
    msg = "BIST Bot Evidence Gaps\n\n"
    for g in gaps:
        msg += f"[{g.severity.value}] {g.gap_type.value} ({g.layer.value}): {g.message}\n"
    return msg

def format_context_fusion_report(report: ContextFusionReport) -> str:
    msg = f"BIST Bot Context Fusion Report ({report.generated_at.strftime('%Y-%m-%d')})\n\n"
    msg += f"Total Snapshots: {len(report.snapshots)}\n"
    msg += f"Total Conflicts: {len(report.conflicts)}\n"
    msg += f"Total Gaps: {len(report.evidence_gaps)}\n\n"
    for f in report.key_findings:
        msg += f"- {f}\n"
    msg += "\n" + report.disclaimer
    return msg


def format_review_case(case: ReviewCase) -> str:
    playbooks = ", ".join(case.playbook_ids) if case.playbook_ids else "None"
    return f'''BIST Bot Review Workflow Özeti

Case: {case.case_id}
Symbol: {case.symbol}
Priority: {case.priority.name}
Status: {case.status.name}
Playbooks: {playbooks}
Signoff: {case.signoff_status.name}
Disposition: {case.disposition.name}

Bu çıktı araştırma amaçlı analist inceleme özetidir.
Yatırım tavsiyesi değildir.
Gerçek emir gönderilmedi.'''

def format_review_checklist(items: list[ReviewChecklistItem]) -> str:
    return "Checklist summary"

def format_decision_journal(entries: list[DecisionJournalEntry]) -> str:
    return "Journal summary"

def format_review_signoff(signoff: ReviewSignoffRequest) -> str:
    return "Signoff summary"

def format_review_workflow_report(report: ReviewWorkflowReport) -> str:
    return "Report summary"

def format_qa_check_results(results: list) -> str: return "QA checks summary"
def format_smoke_test_results(results: list) -> str: return "Smoke tests summary"
def format_regression_matrix(result) -> str: return "Regression matrix summary"
def format_release_gate_result(result) -> str:
    return f"""BIST Bot QA / Release Gate Özeti
Decision: {result.decision.value}
Status: {result.status.value}
Checks: {len(result.check_results)}
Smoke Failures: {len([s for s in result.smoke_results if s.status == 'FAIL'])}
Blocking Reasons: {len(result.blocking_reasons)}
Warnings: {len(result.warnings)}

Bu çıktı yazılım kalite kontrol özetidir.
Yatırım tavsiyesi değildir.
Gerçek emir gönderilmedi."""
def format_qa_report(report) -> str: return "QA report summary"

def format_cli_workflow_run(run) -> str:
    return f"Workflow {run.workflow_name} completed with status {run.status.value}"

def format_cli_compatibility(result) -> str:
    return f"CLI Compatibility: {result.status.value}"

def format_cli_ux_report(report) -> str:
    return f"CLI UX Report Generated: {len(report.contracts)} contracts, {len(report.aliases)} aliases"

    def format_docs_index(self, index) -> str:
        return f"Docs Index Built: {index.total_pages} pages.\nLocal metadata only. No real orders sent."

    def format_docs_coverage(self, result) -> str:
        lines = [
            "BIST Bot Docs Hub Özeti",
            "",
            f"Docs Coverage: {result.coverage_score}",
            f"Missing Docs: {len(result.missing_docs)}",
            f"Commands Without Examples: {len(result.commands_without_examples)}",
            f"Unsafe Language Findings: {len(result.unsafe_language_findings)}",
            f"Handoff: {result.status.name}",
            "",
            "Bu çıktı yerel dokümantasyon kalite özetidir.",
            "Yatırım tavsiyesi değildir.",
            "Gerçek emir gönderilmedi."
        ]
        return "\n".join(lines)

    def format_mvp_handoff(self, manifest) -> str:
        return f"MVP Handoff Created: QA Status {manifest.qa_status}\nLocal metadata only. No real orders sent."

    def format_docs_hub_report(self, report) -> str:
        return f"Docs Hub Report Generated\nLocal metadata only. No real orders sent."

def format_dataset_record(record) -> str:
    return f"Dataset {record.name} ({record.dataset_kind.value}) Status: {record.status.value}"

def format_data_quality_assessment(assessment) -> str:
    return f"Data Quality [Score: {assessment.quality_score}] Status: {assessment.status.value}"

def format_schema_drift_findings(findings: list) -> str:
    return f"Schema Drift Findings: {len(findings)}"

def format_data_quality_gate(result) -> str:
    return f"Gate {result.gate_name} - Status: {result.status.value} (Score: {result.actual_score})"

def format_data_catalog_report(report) -> str:
    low_quality = len([a for a in report.assessments if a.status.value in ("FAIL", "BLOCKED")])
    stale = len([d for d in report.datasets if d.status.value == "STALE"])
    latest_gate = report.gates[0].status.value if report.gates else "UNKNOWN"
    return f"""BIST Bot Data Catalog Özeti

Datasets: {len(report.datasets)}
Low Quality: {low_quality}
Schema Drift: {len(report.drift_findings)}
Latest Gate: {latest_gate}
Stale Datasets: {stale}

Bu çıktı yerel veri yönetişimi özetidir.
Yatırım tavsiyesi değildir.
İşlem uygunluğu anlamına gelmez.
Gerçek emir gönderilmedi."""

def format_feature_store_report(report):
    return "Feature Store Report\n\nNot investment advice."

def format_feature_set(feature_set):
    return f"Feature Set: {feature_set.name}"

def format_feature_quality_assessment(assessment):
    return f"Quality: {assessment.status.value}"

def format_feature_drift_findings(findings):
    return f"Drift Findings: {len(findings)}"

def format_feature_leakage_findings(findings):
    return f"Leakage Findings: {len(findings)}"

# Monitoring Notification Formatter
def format_monitoring_snapshot(snapshot: 'MonitoringSnapshot') -> str:
    return f"Monitoring Snapshot: {snapshot.object_id} - {snapshot.status}"

def format_performance_decay_findings(findings: list) -> str:
    return f"Decay Findings: {len(findings)}"

def format_champion_challenger(comparison: 'ChampionChallengerComparison') -> str:
    return f"Champion/Challenger: {comparison.decision}"

def format_monitoring_alert(alert: 'MonitoringAlert') -> str:
    return f"Alert: {alert.title} - {alert.severity}"

def format_monitoring_report(report: 'MonitoringReport') -> str:
    return f"Monitoring Report: {len(report.snapshots)} snapshots"

def format_research_run_plan(plan) -> str:
    return f"BIST Bot Research Orchestrator Özeti\nCampaign: {plan.campaign_type.value}\nMode: {plan.execution_mode.value}\nStatus: {plan.status.value}\nTasks: {len(plan.tasks)}\n\nBu çıktı yerel araştırma workflow özetidir.\nYatırım tavsiyesi değildir.\nİşlem uygunluğu anlamına gelmez.\nGerçek emir gönderilmedi."

def format_research_run(run) -> str:
    return f"Research Run: {run.run_id}\nStatus: {run.status.value}\nTasks: {len(run.task_results)}\nDisclaimer: {run.disclaimer}"

def format_research_campaign(campaign) -> str:
    return f"Campaign: {campaign.name}\nType: {campaign.campaign_type.value}\nDisclaimer: {campaign.disclaimer}"

def format_research_run_manifest(manifest) -> str:
    return f"Manifest: {manifest.manifest_id}\nRun: {manifest.run_id}\nDisclaimer: {manifest.disclaimer}"

def format_research_orchestrator_report(report) -> str:
    return f"Report Generated: {report.generated_at}\nRuns: {len(report.runs)}\nDisclaimer: {report.disclaimer}"

    def format_final_acceptance_suite(self, suite: Any) -> str:
        lines = [
            f"BIST Bot Final Audit Acceptance: {suite.suite_id}",
            f"Status: {suite.status}",
            f"Total: {suite.total_count} | Pass: {suite.pass_count} | Fail: {suite.fail_count} | Blocked: {suite.blocked_count} | Watch: {suite.watch_count}",
            "",
            "Disclaimer:",
            suite.disclaimer
        ]
        return "\n".join(lines)

    def format_final_security_audit(self, result: Any) -> str:
        lines = [
            f"BIST Bot Final Security Audit: {result.audit_id}",
            f"Blocked Findings: {len(result.blocked_findings)}",
            "",
            "Disclaimer:",
            result.disclaimer
        ]
        return "\n".join(lines)

    def format_release_candidate_manifest(self, candidate: Any) -> str:
        lines = [
            f"BIST Bot Release Candidate: {candidate.candidate_id}",
            f"Stage: {candidate.stage}",
            "",
            "Disclaimer:",
            candidate.disclaimer
        ]
        return "\n".join(lines)

    def format_go_no_go_decision(self, decision: Any) -> str:
        lines = [
            f"BIST Bot Go/No-Go Decision: {decision.decision_id}",
            f"Decision: {decision.decision}",
            f"Status: {decision.status}",
            "",
            "Disclaimer:",
            decision.disclaimer
        ]
        return "\n".join(lines)

    def format_final_audit_report(self, report: Any) -> str:
        lines = [
            "BIST Bot Final Audit Report",
            f"Decision: {report.go_no_go.decision if report.go_no_go else 'UNKNOWN'}",
            f"Acceptance: {report.acceptance_suite.status if report.acceptance_suite else 'UNKNOWN'}",
            f"Security: {report.security_audit.safe_language_status if report.security_audit else 'UNKNOWN'}",
            "",
            "Bu çıktı yerel yazılım release governance özetidir.",
            "Yatırım tavsiyesi değildir.",
            "İşlem uygunluğu anlamına gelmez.",
            "Gerçek emir gönderilmedi."
        ]
        return "\n".join(lines)

def format_final_handoff_manifest(manifest: Any) -> str:
    lines = [
        "BIST Bot Final Handoff Özeti",
        "",
        f"Final Status: {manifest.final_status.value}",
        f"Go/No-Go: {manifest.go_no_go_decision or 'UNKNOWN'}",
        f"Modules: {len(manifest.module_summaries)}",
        f"Roadmap Items: {len(manifest.roadmap_items)}",
        f"Maintenance Tasks: {len(manifest.maintenance_tasks)}",
        "",
        "Bu çıktı yerel yazılım handoff özetidir.",
        "Yatırım tavsiyesi değildir.",
        "İşlem uygunluğu anlamına gelmez.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_final_release_pack(pack: Any) -> str:
    lines = [
        "BIST Bot Release Pack Özeti",
        "",
        f"Stage: {pack.stage.value}",
        f"Go/No-Go: {pack.go_no_go_decision or 'UNKNOWN'}",
        f"Included Docs: {len(pack.included_docs)}",
        f"Included Reports: {len(pack.included_reports)}",
        "",
        "Bu çıktı yerel yazılım artifact özetidir.",
        "Yatırım tavsiyesi değildir.",
        "İşlem uygunluğu anlamına gelmez.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_operator_playbook(playbook: Any) -> str:
    lines = [
        "BIST Bot Operator Playbook Özeti",
        "",
        f"Title: {playbook.title}",
        f"Daily Tasks: {len(playbook.daily_routine)}",
        f"Emergency Checks: {len(playbook.emergency_checks)}",
        "",
        "Bu çıktı yerel yazılım bakım yönergesidir.",
        "Yatırım tavsiyesi değildir.",
        "İşlem uygunluğu anlamına gelmez.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_post_release_roadmap(items: list) -> str:
    lines = [
        "BIST Bot Post-Release Roadmap Özeti",
        "",
        f"Total Items: {len(items)}",
        "",
        "Bu çıktı yerel yazılım yol haritasıdır.",
        "Yatırım tavsiyesi değildir.",
        "İşlem uygunluğu anlamına gelmez.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_final_handoff_report(report: Any) -> str:
    lines = [
        "BIST Bot Final Handoff Report",
        "",
        f"Status: {report.manifest.final_status.value if report.manifest else 'UNKNOWN'}",
        f"Pack Stage: {report.release_pack.stage.value if report.release_pack else 'UNKNOWN'}",
        "",
        "Bu çıktı yerel yazılım release documentation özetidir.",
        "Yatırım tavsiyesi değildir.",
        "İşlem uygunluğu anlamına gelmez.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

from bist_signal_bot.performance.models import (
    PerformanceProfile,
    BenchmarkResult,
    BottleneckFinding,
    PerformanceRegressionFinding,
    PerformanceReport,
)
from bist_signal_bot.performance.reporting import (
    format_profile_text,
    format_benchmark_text,
    format_bottlenecks_text,
    format_regressions_text,
    format_performance_report_markdown,
)

def format_performance_profile(profile: PerformanceProfile) -> str:
    return format_profile_text(profile)

def format_benchmark_result(result: BenchmarkResult) -> str:
    return format_benchmark_text(result)

def format_bottleneck_findings(findings: list[BottleneckFinding]) -> str:
    return format_bottlenecks_text(findings)

def format_performance_regressions(findings: list[PerformanceRegressionFinding]) -> str:
    return format_regressions_text(findings)

def format_performance_report(report: PerformanceReport) -> str:
    return format_performance_report_markdown(report)
