from bist_signal_bot.monitoring.models import (
    MonitoringSnapshot, PerformanceDecayFinding, ChampionChallengerComparison,
    MonitoringAlert, MonitoringReport
)

def format_monitoring_snapshot(snapshot: MonitoringSnapshot) -> str:
    return (
        f"BIST Bot Research Monitoring Snapshot\n"
        f"Object: {snapshot.object_id} ({snapshot.object_type.value})\n"
        f"Status: {snapshot.status.value}\n"
        f"Health Score: {snapshot.health_score}\n\n"
        f"This output is local research performance metadata only.\n"
        f"It is not investment advice or permission to trade.\n"
        f"No real order was sent."
    )

def format_performance_decay_findings(findings: list[PerformanceDecayFinding]) -> str:
    if not findings:
        return "No performance decay findings."
    lines = ["BIST Bot Performance Decay Findings"]
    for f in findings:
        lines.append(f"- {f.metric_name}: {f.status.value} (Score: {f.decay_score})")
    lines.append("\nThis output is research-only metadata. It does not predict future returns.")
    return "\n".join(lines)

def format_champion_challenger(comparison: ChampionChallengerComparison) -> str:
    return (
        f"BIST Bot Champion/Challenger Comparison\n"
        f"Champion: {comparison.champion_id} | Challenger: {comparison.challenger_id}\n"
        f"Decision: {comparison.decision.value}\n\n"
        f"This comparison is local research governance metadata only."
    )

def format_monitoring_alert(alert: MonitoringAlert) -> str:
    return (
        f"BIST Bot Monitoring Alert [{alert.severity}]\n"
        f"Title: {alert.title}\n"
        f"Message: {alert.message}\n"
        f"Status: {alert.status.value}\n\n"
        f"This alert is local research review metadata only. Not a trading alert."
    )

def format_monitoring_report(report: MonitoringReport) -> str:
    return (
        f"BIST Bot Monitoring Report Summary\n"
        f"Generated At: {report.generated_at}\n"
        f"Snapshots: {len(report.snapshots)}\n"
        f"Decay Findings: {len(report.decay_findings)}\n"
        f"Alerts: {len(report.alerts)}\n\n"
        f"{report.disclaimer}"
    )

def format_monitoring_summary(object_id: str, status: str, health_score: float, decay_count: int, alert_count: int, watchlist: bool) -> str:
    return (
        f"BIST Bot Research Monitoring Özeti\n\n"
        f"Object: {object_id}\n"
        f"Status: {status}\n"
        f"Health Score: {health_score}\n"
        f"Decay Findings: {decay_count}\n"
        f"Open Alerts: {alert_count}\n"
        f"Watchlist: {'YES' if watchlist else 'NO'}\n\n"
        f"Bu çıktı yerel araştırma performans gözetimi özetidir.\n"
        f"Yatırım tavsiyesi değildir.\n"
        f"İşlem uygunluğu anlamına gelmez.\n"
        f"Gerçek emir gönderilmedi."
    )
