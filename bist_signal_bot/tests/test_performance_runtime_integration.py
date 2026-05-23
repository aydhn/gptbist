import pytest
from bist_signal_bot.runtime.orchestrator import RuntimeOrchestrator
from bist_signal_bot.runtime.models import RuntimePipelineConfig
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.data_service import MarketDataService

def test_runtime_profile_generates_profile_id(tmp_path):
    settings = Settings(ENABLE_PERFORMANCE_PROFILING=True)
    orchestrator = RuntimeOrchestrator(settings)
    config = RuntimePipelineConfig(
        strategy_name="moving_average_trend",
        source="mock",
        profile_runtime=True
    )
    res = orchestrator.run_once(config)
    assert res is not None
    assert res.performance_profile_id is not None
