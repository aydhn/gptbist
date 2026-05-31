from bist_signal_bot.monitoring.storage import MonitoringStore
from bist_signal_bot.monitoring.metrics import MonitoringMetricCalculator
from bist_signal_bot.monitoring.collectors import MonitoringDataCollector
from bist_signal_bot.monitoring.decay import PerformanceDecayDetector
from bist_signal_bot.monitoring.champion_challenger import ChampionChallengerEngine
from bist_signal_bot.monitoring.health import MonitoringHealthEngine
from bist_signal_bot.monitoring.alerts import MonitoringAlertRouter
from bist_signal_bot.monitoring.escalation import MonitoringEscalationEngine
from bist_signal_bot.monitoring.watchlist import MonitoringWatchlistManager

def create_monitoring_store(settings=None, base_dir=None) -> MonitoringStore:
    return MonitoringStore()

def create_monitoring_metric_calculator(settings=None, base_dir=None) -> MonitoringMetricCalculator:
    return MonitoringMetricCalculator()

def create_monitoring_data_collector(settings=None, base_dir=None) -> MonitoringDataCollector:
    return MonitoringDataCollector()

def create_performance_decay_detector(settings=None, base_dir=None) -> PerformanceDecayDetector:
    # Use settings in real app
    return PerformanceDecayDetector()

def create_champion_challenger_engine(settings=None, base_dir=None) -> ChampionChallengerEngine:
    return ChampionChallengerEngine()

def create_monitoring_health_engine(settings=None, base_dir=None) -> MonitoringHealthEngine:
    return MonitoringHealthEngine()

def create_monitoring_alert_router(settings=None, base_dir=None) -> MonitoringAlertRouter:
    return MonitoringAlertRouter()

def create_monitoring_escalation_engine(settings=None, base_dir=None) -> MonitoringEscalationEngine:
    return MonitoringEscalationEngine()

def create_monitoring_watchlist_manager(settings=None, base_dir=None) -> MonitoringWatchlistManager:
    return MonitoringWatchlistManager()
