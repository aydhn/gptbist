from pathlib import Path
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.runtime.orchestrator import RuntimeOrchestrator
from bist_signal_bot.runtime.models import RuntimePipelineConfig, RuntimeScheduleConfig
from bist_signal_bot.app.bootstrap import bootstrap_app

def create_runtime_orchestrator(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> RuntimeOrchestrator:
    # Use real bootstrap to fetch existing engines properly, without assuming missing modules like Cleaner/Normalizer
    app_context = bootstrap_app()
    settings = settings or app_context.settings

    data_service = app_context.data_service

    # Placeholder missing engines for now to allow orchestration structure.
    # Phase 39 establishes the orchestrator *structure*. The specific engine classes
    # like ScannerEngine, RegimeEngine are instantiated where available.

    # Try importing Scanner Engine
    scanner_engine = None
    try:
        from bist_signal_bot.scanner.engine import SignalScannerEngine
        scanner_engine = SignalScannerEngine(data_service=data_service, settings=settings)
    except ImportError:
        class MockScanner:
            def scan(self, *args, **kwargs): return {"mock_scan": True}
        scanner_engine = MockScanner()

    # Try importing Paper Engine
    paper_engine = None
    try:
        from bist_signal_bot.paper.engine import PaperTradingEngine
        paper_engine = PaperTradingEngine(settings=settings)
    except ImportError:
        class MockPaper:
            def run(self, *args, **kwargs): return {"mock_paper": True}
        paper_engine = MockPaper()

    return RuntimeOrchestrator(
        scanner_engine=scanner_engine,
        paper_engine=paper_engine,
        notifier=app_context.notifier,
        settings=settings
    )

def create_runtime_pipeline_config_from_settings(settings: Settings) -> RuntimePipelineConfig:
    orchestrator = RuntimeOrchestrator(settings=settings)
    return orchestrator.build_default_pipeline_config()

def create_runtime_schedule_config_from_settings(settings: Settings) -> RuntimeScheduleConfig:
    from bist_signal_bot.runtime.scheduler import RuntimeScheduler
    scheduler = RuntimeScheduler(orchestrator=None, settings=settings)
    return scheduler.build_default_schedule_config()