import os

# Create monitoring reporting
with open("bist_signal_bot/monitoring/reporting.py", "w") as f:
    f.write('''import pandas as pd
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
''')

# Create monitoring app
with open("bist_signal_bot/app/monitoring_app.py", "w") as f:
    f.write('''from pathlib import Path
from typing import Optional
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_monitoring_dir
from bist_signal_bot.monitoring.storage import MonitoringStore
from bist_signal_bot.monitoring.metrics import MonitoringMetricCalculator
from bist_signal_bot.monitoring.collectors import MonitoringDataCollector
from bist_signal_bot.monitoring.decay import PerformanceDecayDetector
from bist_signal_bot.monitoring.champion_challenger import ChampionChallengerEngine
from bist_signal_bot.monitoring.health import MonitoringHealthEngine
from bist_signal_bot.monitoring.alerts import MonitoringAlertRouter
from bist_signal_bot.monitoring.escalation import MonitoringEscalationEngine
from bist_signal_bot.monitoring.watchlist import MonitoringWatchlistManager

def create_monitoring_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MonitoringStore:
    d = base_dir or get_monitoring_dir(settings)
    return MonitoringStore(d)

def create_monitoring_metric_calculator(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MonitoringMetricCalculator:
    return MonitoringMetricCalculator()

def create_monitoring_data_collector(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MonitoringDataCollector:
    return MonitoringDataCollector()

def create_performance_decay_detector(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> PerformanceDecayDetector:
    return PerformanceDecayDetector()

def create_champion_challenger_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ChampionChallengerEngine:
    return ChampionChallengerEngine()

def create_monitoring_health_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MonitoringHealthEngine:
    return MonitoringHealthEngine()

def create_monitoring_alert_router(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MonitoringAlertRouter:
    return MonitoringAlertRouter()

def create_monitoring_escalation_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MonitoringEscalationEngine:
    return MonitoringEscalationEngine()

def create_monitoring_watchlist_manager(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MonitoringWatchlistManager:
    return MonitoringWatchlistManager()
''')

# Update notifications/formatter.py
with open("bist_signal_bot/notifications/formatter.py", "a") as f:
    f.write('''
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
''')

print("Part 4 done")
