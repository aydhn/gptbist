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

    # Shared strategy engine (scanner and paper engines both depend on it)
    strategy_engine = None
    try:
        from bist_signal_bot.strategies.engine import StrategyEngine
        strategy_engine = StrategyEngine(settings=settings)
    except ImportError:
        pass

    # Scanner engine
    scanner_engine = None
    try:
        from bist_signal_bot.scanner.engine import SignalScannerEngine, SignalScannerDependencies
        scanner_engine = SignalScannerEngine(deps=SignalScannerDependencies(
            data_service=data_service,
            strategy_engine=strategy_engine,
            settings=settings,
        ))
    except ImportError:
        class MockScanner:
            def scan(self, *args, **kwargs): return {"mock_scan": True}
        scanner_engine = MockScanner()

    # Paper trading engine (research-only simulation; no real orders)
    paper_engine = None
    try:
        from bist_signal_bot.paper.engine import PaperTradingEngine
        from bist_signal_bot.paper.ledger import PaperLedgerStore
        paper_engine = PaperTradingEngine(
            ledger_store=PaperLedgerStore(settings),
            strategy_engine=strategy_engine,
            data_service=data_service,
            settings=settings,
        )
    except ImportError:
        class MockPaper:
            def run(self, *args, **kwargs): return {"mock_paper": True}
        paper_engine = MockPaper()

    # Market regime engine (REGIME_ANALYSIS pipeline step)
    regime_engine = None
    try:
        from bist_signal_bot.regime.engine import RegimeEngine
        regime_engine = RegimeEngine.from_settings(settings)
    except ImportError:
        regime_engine = None

    # ML inference is opt-in and requires an explicitly registered model.
    ml_inference_engine = None
    model_id = getattr(settings, "ML_INFERENCE_DEFAULT_MODEL_ID", "")
    if getattr(settings, "RUNTIME_USE_ML_FILTER", False) and model_id:
        try:
            from bist_signal_bot.ml.inference.engine import MLInferenceEngine
            ml_inference_engine = MLInferenceEngine.from_settings(settings)
        except ImportError:
            ml_inference_engine = None

    return RuntimeOrchestrator(
        scanner_engine=scanner_engine,
        paper_engine=paper_engine,
        regime_engine=regime_engine,
        ml_inference_engine=ml_inference_engine,
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
