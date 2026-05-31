from pathlib import Path
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
