import time
import logging
from typing import Any, List, Dict
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import StrategyExecutionError
from bist_signal_bot.data.models import MarketDataFrame
from bist_signal_bot.strategies.models import (
    StrategySpec,
    StrategyCategory,
    StrategyRunMode,
    StrategyExecutionResult,
    StrategyExecutionIssue
)
from bist_signal_bot.signals.models import StrategySignalBatch, SignalCandidate
from bist_signal_bot.strategies.registry import StrategyRegistry
from bist_signal_bot.ml.inference.engine import MLInferenceEngine
from bist_signal_bot.ml.inference.models import MLInferenceConfig, MLInferenceMode
from bist_signal_bot.ml.inference.models import MLFilterDecision
from bist_signal_bot.strategies.context import StrategyContext

class StrategyEngine:
    def __init__(
        self,
        registry: StrategyRegistry | None = None,
        data_service: Any | None = None,
        indicator_engine: Any | None = None,
        settings: Settings | None = None,
        logger: logging.Logger | None = None
    ):
        self.registry = registry
        self.ml_inference_engine = ml_inference_engine or get_registry()
        self.data_service = data_service
        self.indicator_engine = indicator_engine
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    def run_strategy_on_data(
        self,
        strategy_name: str,
        symbol: str,
        data: MarketDataFrame | pd.DataFrame,
        params: dict[str, Any] | None = None,
        run_mode: StrategyRunMode = StrategyRunMode.RESEARCH,
        timeframe: str = "1d"
    ) -> StrategyExecutionResult:
        try:
            strategy = self.registry.get(strategy_name)
        except Exception as e:
            return StrategyExecutionResult(
                request={"strategy_name": strategy_name, "symbol": symbol, "run_mode": run_mode}, # type: ignore
                status="error",
                issues=[StrategyExecutionIssue(strategy_name=strategy_name, symbol=symbol, message=str(e))]
            )

        df = data.data if hasattr(data, "data") else data
        market_data = data if hasattr(data, "data") else None

        try:
            context = StrategyContext(
                symbol=symbol,
                timeframe=timeframe,
                market_data=market_data,
                data=df,
                settings=self.settings,
                run_mode=run_mode
            )
        except Exception as e:
             return StrategyExecutionResult(
                request={"strategy_name": strategy_name, "symbol": symbol, "run_mode": run_mode}, # type: ignore
                status="error",
                issues=[StrategyExecutionIssue(strategy_name=strategy_name, symbol=symbol, message=str(e))]
            )

        return strategy.run(context, params)

    def run_strategy_for_symbol(
        self,
        strategy_name: str,
        symbol: str,
        params: dict[str, Any] | None = None,
        timeframe: str = "1d",
        period: str | None = None,
        refresh: bool = False
    ) -> StrategyExecutionResult:
        if not self.data_service:
            raise StrategyExecutionError("Data service is required to fetch data by symbol.")

        try:
            if hasattr(self.data_service, "get_ohlcv"):
                data = self.data_service.get_ohlcv(symbol, timeframe, period=period)
                if data is None:
                     raise StrategyExecutionError(f"Failed to fetch data for {symbol}")
            elif hasattr(self.data_service, "fetch_one"):
                data = self.data_service.fetch_one(symbol, timeframe)
            elif hasattr(self.data_service, "get_mock_data"):
                data = self.data_service.get_mock_data(symbol)
            else:
                raise StrategyExecutionError("Data service interface not recognized.")

            return self.run_strategy_on_data(strategy_name, symbol, data, params, timeframe=timeframe)

        except Exception as e:
             return StrategyExecutionResult(
                request={"strategy_name": strategy_name, "symbol": symbol}, # type: ignore
                status="error",
                issues=[StrategyExecutionIssue(strategy_name=strategy_name, symbol=symbol, message=f"Data fetch error: {str(e)}")]
            )

    def run_strategy_batch(
        self,
        strategy_name: str,
        symbols: list[str],
        params: dict[str, Any] | None = None,
        continue_on_error: bool = True
    ) -> StrategySignalBatch:
        start_time = time.time()
        candidates = []
        issues = []
        success = 0
        failed = 0

        for symbol in symbols:
            try:
                res = self.run_strategy_for_symbol(strategy_name, symbol, params)
                if res.status == "success":
                    success += 1
                    if res.candidate:
                        candidates.append(res.candidate)
                else:
                    failed += 1
                    for issue in res.issues:
                        issues.append(f"{symbol}: {issue.message}")
            except Exception as e:
                failed += 1
                issues.append(f"{symbol}: {str(e)}")
                if not continue_on_error:
                    break

        return StrategySignalBatch(
            strategy_name=strategy_name,
            symbol_count=len(symbols),
            candidates=candidates,
            success_count=success,
            failed_count=failed,
            issues=issues,
            elapsed_seconds=time.time() - start_time
        )

    def list_strategies(self, category: StrategyCategory | None = None) -> list[StrategySpec]:
        return self.registry.list_specs(category)

    def parse_params(self, raw: list[str] | None) -> dict[str, Any]:
        params = {}
        if not raw:
            return params

        for item in raw:
            if "=" not in item:
                self.logger.warning(f"Ignoring invalid param format (needs key=value): {item}")
                continue
            k, v = item.split("=", 1)
            k = k.strip()
            v = v.strip()

            if v.lower() == "true":
                params[k] = True
            elif v.lower() == "false":
                params[k] = False
            else:
                try:
                    if "." in v:
                        params[k] = float(v)
                    else:
                        params[k] = int(v)
                except ValueError:
                    params[k] = v

        return params
