import os
from pathlib import Path

def get_monitoring_dir(settings=None) -> Path:
    # Use environment base dir or default to local data/
    base = Path(os.environ.get("BIST_DATA_DIR", "data"))
    d = base / "monitoring"
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_metrics_path() -> Path:
    d = get_monitoring_dir() / "metrics"
    d.mkdir(parents=True, exist_ok=True)
    return d / "monitoring_metrics.jsonl"

def get_snapshots_path() -> Path:
    d = get_monitoring_dir() / "snapshots"
    d.mkdir(parents=True, exist_ok=True)
    return d / "monitoring_snapshots.jsonl"

def get_decay_path() -> Path:
    d = get_monitoring_dir() / "decay"
    d.mkdir(parents=True, exist_ok=True)
    return d / "performance_decay_findings.jsonl"

def get_champion_challenger_path() -> Path:
    d = get_monitoring_dir() / "champion_challenger"
    d.mkdir(parents=True, exist_ok=True)
    return d / "champion_challenger_comparisons.jsonl"

def get_alerts_path() -> Path:
    d = get_monitoring_dir() / "alerts"
    d.mkdir(parents=True, exist_ok=True)
    return d / "monitoring_alerts.jsonl"

def get_watchlist_path() -> Path:
    d = get_monitoring_dir() / "watchlist"
    d.mkdir(parents=True, exist_ok=True)
    return d / "monitoring_watchlist.jsonl"

def get_report_dir(date_str: str) -> Path:
    d = get_monitoring_dir() / "reports" / date_str
    d.mkdir(parents=True, exist_ok=True)
    return d
