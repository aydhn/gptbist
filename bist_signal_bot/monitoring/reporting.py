from typing import Any, List
import pandas as pd
from bist_signal_bot.monitoring.models import (
    MonitoringSnapshot, DiagnosticCheckResult, MonitoringAlert,
    MonitoringMetric, SelfHealingResult
)

def monitoring_snapshot_to_dict(snapshot: MonitoringSnapshot) -> dict[str, Any]:
    return snapshot.model_dump(mode="json")

def diagnostic_checks_to_dataframe(checks: List[DiagnosticCheckResult]) -> pd.DataFrame:
    if not checks:
        return pd.DataFrame()

    data = [
        {
            "check_name": c.check_name,
            "component": c.component.value,
            "status": c.status.value,
            "severity": c.severity.value,
            "message": c.message,
            "generated_at": c.generated_at
        } for c in checks
    ]
    return pd.DataFrame(data)

def alerts_to_dataframe(alerts: List[MonitoringAlert]) -> pd.DataFrame:
    if not alerts:
        return pd.DataFrame()

    data = [
        {
            "alert_id": a.alert_id,
            "timestamp": a.timestamp,
            "component": a.component.value,
            "severity": a.severity.value,
            "status": a.status.value,
            "title": a.title,
            "count": a.count,
            "first_seen": a.first_seen_at
        } for a in alerts
    ]
    return pd.DataFrame(data)

def metrics_to_dataframe(metrics: List[MonitoringMetric]) -> pd.DataFrame:
    if not metrics:
        return pd.DataFrame()

    data = [
        {
            "metric_id": m.metric_id,
            "timestamp": m.timestamp,
            "component": m.component.value,
            "name": m.name,
            "type": m.metric_type.value,
            "value": m.value,
            "unit": m.unit
        } for m in metrics
    ]
    return pd.DataFrame(data)

def format_monitoring_snapshot_text(snapshot: MonitoringSnapshot) -> str:
    lines = [
        "BIST Signal Bot Monitoring Status",
        "=" * 40,
        f"Generated At: {snapshot.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"Overall Health: {snapshot.overall_health.value}",
        ""
    ]

    if snapshot.active_alerts:
        lines.append(f"Active Alerts ({len(snapshot.active_alerts)}):")
        for a in snapshot.active_alerts:
            lines.append(f"  - [{a.severity.value}] {a.title} ({a.count}x)")
        lines.append("")

    if snapshot.issues:
        lines.append("Issues:")
        for issue in snapshot.issues:
            lines.append(f"  - {issue}")
        lines.append("")

    lines.extend([
        "-" * 40,
        snapshot.disclaimer
    ])

    return "\n".join(lines)

def format_monitoring_report_markdown(snapshot: MonitoringSnapshot) -> str:
    lines = [
        "# BIST Signal Bot Monitoring Report",
        f"**Generated At:** {snapshot.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"**Overall Health:** {snapshot.overall_health.value}",
        "",
        "## Active Alerts",
    ]

    if snapshot.active_alerts:
        for a in snapshot.active_alerts:
            lines.append(f"- **[{a.severity.value}] {a.title}** (Count: {a.count}, Status: {a.status.value})")
            lines.append(f"  - {a.message}")
    else:
        lines.append("*No active alerts.*")

    lines.append("")
    lines.append("## Diagnostic Checks")
    if snapshot.diagnostics:
        for c in snapshot.diagnostics:
            emoji = "✅" if c.status.value == "PASS" else ("⚠️" if c.status.value == "WARN" else "❌")
            lines.append(f"- {emoji} **{c.check_name}**: {c.status.value} - {c.message}")
    else:
        lines.append("*No diagnostics available.*")

    lines.extend([
        "",
        "---",
        f"_{snapshot.disclaimer}_"
    ])

    return "\n".join(lines)

def format_alert_text(alert: MonitoringAlert) -> str:
    lines = [
        "BIST Bot Monitoring Alert",
        "",
        f"Severity: {alert.severity.value}",
        f"Component: {alert.component.value}",
        f"Title: {alert.title}",
        f"Message: {alert.message}",
        "",
        "Bu operasyonel monitoring uyarısıdır.",
        "Yatırım tavsiyesi değildir.",
        "Gerçek emir gönderilmedi."
    ]
    return "\n".join(lines)

def format_self_healing_result_text(result: SelfHealingResult) -> str:
    lines = [
        "BIST Bot Self-Healing Result",
        "=" * 40,
        f"Generated At: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"Actions Executed: {result.executed_count}",
        f"Success: {result.success_count}",
        f"Failed: {result.failed_count}",
        f"Skipped: {result.skipped_count}",
        ""
    ]

    if result.actions:
        lines.append("Actions Details:")
        for action in result.actions:
            status = "SUCCESS" if action.success else ("FAILED" if action.executed else "SKIPPED")
            lines.append(f"  - [{status}] {action.action_type.value}: {action.description}")
            if action.message:
                lines.append(f"    Note: {action.message}")

    lines.extend([
        "",
        "-" * 40,
        result.disclaimer
    ])
    return "\n".join(lines)
