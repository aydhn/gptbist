import pandas as pd
from typing import Any, List, Dict
from bist_signal_bot.monitoring.models import MonitoringMetric, MonitoringSnapshot, PerformanceDecayFinding, ChampionChallengerComparison, MonitoringAlert, MonitoringWatchlistItem, MonitoringReport

def metric_to_dict(metric: MonitoringMetric) -> Dict[str, Any]:
    return metric.dict()

def snapshot_to_dict(snapshot: MonitoringSnapshot) -> Dict[str, Any]:
    return snapshot.dict()

def decay_finding_to_dict(finding: PerformanceDecayFinding) -> Dict[str, Any]:
    return finding.dict()

def champion_challenger_to_dict(comparison: ChampionChallengerComparison) -> Dict[str, Any]:
    return comparison.dict()

def alert_to_dict(alert: MonitoringAlert) -> Dict[str, Any]:
    return alert.dict()

def watchlist_item_to_dict(item: MonitoringWatchlistItem) -> Dict[str, Any]:
    return item.dict()

def monitoring_report_to_dict(report: MonitoringReport) -> Dict[str, Any]:
    return report.dict()

def metrics_to_dataframe(metrics: List[MonitoringMetric]) -> pd.DataFrame:
    return pd.DataFrame([m.dict() for m in metrics])

def snapshots_to_dataframe(snapshots: List[MonitoringSnapshot]) -> pd.DataFrame:
    return pd.DataFrame([s.dict() for s in snapshots])

def format_metric_text(metric: MonitoringMetric) -> str:
    return f"{metric.metric_name}: {metric.value}"

def format_snapshot_text(snapshot: MonitoringSnapshot) -> str:
    return f"Snapshot {snapshot.snapshot_id} - Health: {snapshot.health_score}"

def format_decay_findings_text(findings: List[PerformanceDecayFinding]) -> str:
    if not findings: return "No decay findings."
    return f"Found {len(findings)} decay issues."

def format_champion_challenger_text(comparison: ChampionChallengerComparison) -> str:
    return f"Champion vs Challenger: {comparison.decision.value}"

def format_alerts_text(alerts: List[MonitoringAlert]) -> str:
    if not alerts: return "No alerts."
    return f"Found {len(alerts)} alerts."

def format_watchlist_text(items: List[MonitoringWatchlistItem]) -> str:
    if not items: return "Watchlist empty."
    return f"Watchlist has {len(items)} items."

def format_monitoring_report_markdown(report: MonitoringReport) -> str:
    return f"""# Monitoring Report
Generated: {report.generated_at}

Disclaimer: {report.disclaimer}
"""

def render_monitoring_template(context: dict) -> dict:
    from bist_signal_bot.report_templates.models import RenderedReportSection, ReportValidationStatus
    return {
        "rendered_section_id": "sec_mon",
        "section_key": "monitoring",
        "title": "Monitoring Report",
        "content_markdown": "*Monitoring summary.*",
        "content_json": {"status": "PASS"},
        "status": ReportValidationStatus.PASS,
        "warnings": []
    }
