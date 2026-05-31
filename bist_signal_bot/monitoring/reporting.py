from bist_signal_bot.monitoring.models import (
    MonitoringMetric, MonitoringSnapshot, PerformanceDecayFinding,
    ChampionChallengerComparison, MonitoringAlert, MonitoringWatchlistItem, MonitoringReport
)

def format_monitoring_report_markdown(report: MonitoringReport) -> str:
    md = [
        "# Research Monitoring Report",
        f"**Generated At:** {report.generated_at}",
        f"**Disclaimer:** {report.disclaimer}",
        "",
        "## Key Findings",
    ]

    for f in report.key_findings:
        md.append(f"- {f}")

    md.append("")
    md.append("## Alerts")
    if not report.alerts:
        md.append("No open alerts.")
    else:
        for a in report.alerts:
            md.append(f"- [{a.severity}] {a.title}: {a.message} (Ack: {a.acknowledged})")

    md.append("")
    md.append("## Watchlist")
    if not report.watchlist:
        md.append("No items on watchlist.")
    else:
        for w in report.watchlist:
            md.append(f"- {w.object_type.value} / {w.object_id}: {w.reason}")

    return "\n".join(md)

# Stub formats for other utilities, could be expanded.
def format_snapshot_text(snapshot: MonitoringSnapshot) -> str:
    return (
        f"Snapshot for {snapshot.object_type.value} {snapshot.object_id}\n"
        f"Status: {snapshot.status.value}\n"
        f"Health: {snapshot.health_score}\n"
        f"Findings: {', '.join(snapshot.key_findings)}\n"
        f"Disclaimer: {snapshot.disclaimer}"
    )
