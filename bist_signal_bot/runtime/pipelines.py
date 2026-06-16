from typing import List

from bist_signal_bot.runtime.models import RuntimePipelineConfig, RuntimeJobType
from bist_signal_bot.core.exceptions import RuntimeValidationError

class RuntimePipelineBuilder:

    @staticmethod
    def build_scan_request(config: RuntimePipelineConfig):
        """Build a real ScanRequest from the runtime config (the scanner expects a
        ScanRequest object, not a dict)."""
        from bist_signal_bot.scanner.models import ScanRequest, ScanUniverseMode
        try:
            universe_mode = ScanUniverseMode(config.universe_mode)
        except (ValueError, TypeError):
            universe_mode = ScanUniverseMode.SYMBOLS
        return ScanRequest(
            strategy_name=config.strategy_name,
            universe_mode=universe_mode,
            symbols=list(config.symbols or []),
            watchlist_name=config.watchlist_name,
            group_name=config.group_name,
            source=config.source,
            top_n=config.top_n,
            use_trade_risk=config.use_trade_risk,
            use_portfolio_risk=config.use_portfolio_risk,
            continue_on_error=True,
        )

    @staticmethod
    def build_paper_request(config: RuntimePipelineConfig, symbols: List[str]) -> dict:
        return {
            "symbols": symbols,
            "strategy": config.strategy_name,
            "source": config.source
        }

    @staticmethod
    def build_runtime_pipeline_steps(config: RuntimePipelineConfig) -> List[RuntimeJobType]:
        steps = [RuntimeJobType.HEALTHCHECK]
        steps.append(RuntimeJobType.DATA_REFRESH)
        steps.append(RuntimeJobType.SIGNAL_SCAN)

        if config.use_regime_filter:
            steps.append(RuntimeJobType.REGIME_ANALYSIS)
        if config.use_ml_filter:
            steps.append(RuntimeJobType.ML_INFERENCE)

        # Risk and Portfolio Risk usually inside scanner, but can be separate steps

        if config.use_paper and not config.dry_run:
            steps.append(RuntimeJobType.PAPER_RUN)

        if config.send_telegram:
            steps.append(RuntimeJobType.TELEGRAM_SUMMARY)

        steps.append(RuntimeJobType.CLEANUP)
        return steps

    @staticmethod
    def validate_pipeline_config(config: RuntimePipelineConfig) -> None:
        if not config.strategy_name:
            raise RuntimeValidationError("strategy_name cannot be empty.")
        if config.source not in ["mock", "local"]:
            raise RuntimeValidationError("source must be 'mock' or 'local'.")
        if config.top_n <= 0:
            raise RuntimeValidationError("top_n must be positive.")
        if config.use_ml_filter and not config.ml_model_id:
            raise RuntimeValidationError("ml_model_id is required when use_ml_filter is True.")
        if config.use_paper and config.dry_run:
            # We don't fail, we just note it or let builder skip
            pass