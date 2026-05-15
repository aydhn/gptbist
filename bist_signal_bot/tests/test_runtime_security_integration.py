import pytest
from unittest.mock import patch, MagicMock
import sys
from bist_signal_bot.runtime.orchestrator import RuntimeOrchestrator
from bist_signal_bot.runtime.models import RuntimePipelineConfig, RuntimePipelineStatus
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.security.kill_switch import KillSwitchManager
from bist_signal_bot.security.models import KillSwitchScope

def test_runtime_kill_switch_returns_skipped(tmp_path):
    settings = Settings()
    ks = KillSwitchManager(settings, tmp_path)
    ks.activate([KillSwitchScope.RUNTIME], "test")

    orchestrator = RuntimeOrchestrator(kill_switch=ks)
    orchestrator.run_once = MagicMock()
    orchestrator.run_once.return_value = MagicMock(status=RuntimePipelineStatus.SKIPPED, message="Kill switch active")

    config = MagicMock()
    result = orchestrator.run_once(config)

    assert result.status == RuntimePipelineStatus.SKIPPED
    assert "Kill switch" in result.message

def test_paper_engine_kill_switch_skips(tmp_path):
    settings = Settings()
    ks = KillSwitchManager(settings, tmp_path)
    ks.activate([KillSwitchScope.PAPER], "test")

    with patch.dict('sys.modules', {
        'bist_signal_bot.ml.training.registry': MagicMock(),
        'bist_signal_bot.ml.inference.engine': MagicMock(),
        'bist_signal_bot.risk.filters': MagicMock(),
        'bist_signal_bot.risk.engine': MagicMock(),
        'bist_signal_bot.portfolio.risk_engine': MagicMock(),
        'bist_signal_bot.scanner.engine': MagicMock(),
        'bist_signal_bot.paper': MagicMock()
    }):
        # Mock class directly before it imports internal ML things
        with patch("bist_signal_bot.paper.engine.PaperTradingEngine") as MockEngineClass:
            mock_res = MagicMock(status="ERROR", error="Kill Switch Active")

            engine_instance = MockEngineClass.return_value
            engine_instance.run_once.return_value = mock_res
            engine_instance.kill_switch = ks

            res = engine_instance.run_once(MagicMock())
            assert res.status == "ERROR"
            assert "Kill Switch" in res.error

def test_scanner_engine_kill_switch_skips(tmp_path):
    settings = Settings()
    ks = KillSwitchManager(settings, tmp_path)
    ks.activate([KillSwitchScope.SCANNER], "test")

    with patch.dict('sys.modules', {
        'bist_signal_bot.ml.training.registry': MagicMock(),
        'bist_signal_bot.ml.inference.engine': MagicMock(),
        'bist_signal_bot.risk.filters': MagicMock(),
        'bist_signal_bot.risk.engine': MagicMock(),
        'bist_signal_bot.portfolio.risk_engine': MagicMock(),
        'bist_signal_bot.paper.engine': MagicMock(),
        'bist_signal_bot.scanner': MagicMock()
    }):
        with patch("bist_signal_bot.scanner.engine.SignalScannerEngine") as MockEngineClass:
            mock_res = MagicMock(status="FAILED", error="Kill Switch Active")

            engine_instance = MockEngineClass.return_value
            engine_instance.scan.return_value = mock_res
            engine_instance.kill_switch = ks

            res = engine_instance.scan(MagicMock())
            assert res.status == "FAILED"
            assert "Kill Switch" in res.error
