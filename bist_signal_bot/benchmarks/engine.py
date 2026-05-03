import logging
import time
from typing import Any, Optional
import pandas as pd

from bist_signal_bot.benchmarks.registry import BenchmarkRegistry, create_default_benchmark_registry
from bist_signal_bot.benchmarks.models import (
    BenchmarkRequest,
    BenchmarkExecutionResult,
    BenchmarkBatchResult,
    BenchmarkStatus
)
from bist_signal_bot.data.models import MarketDataFrame, Timeframe
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.config.settings import Settings, settings as default_settings

class BenchmarkEngine:
    def __init__(
        self,
        registry: Optional[BenchmarkRegistry] = None,
        data_service: Optional[MarketDataService] = None,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.registry = registry or create_default_benchmark_registry()
        self.data_service = data_service
        self.settings = settings or default_settings
        self.logger = logger or logging.getLogger(__name__)

    def parse_params(self, raw: Optional[list[str]]) -> dict[str, Any]:
        """Parse raw param strings like ['window=200', 'lookback=60'] into a dict."""
        params = {}
        if not raw:
            return params

        for param_str in raw:
            try:
                if "=" not in param_str:
                    continue
                key, val = param_str.split("=", 1)
                key = key.strip()
                val = val.strip()

                # Attempt to cast
                try:
                    if "." in val:
                        params[key] = float(val)
                    else:
                        params[key] = int(val)
                except ValueError:
                    if val.lower() == "true":
                        params[key] = True
                    elif val.lower() == "false":
                        params[key] = False
                    else:
                        params[key] = val
            except Exception as e:
                self.logger.warning(f"Failed to parse benchmark parameter '{param_str}': {e}")

        return params

    def run_on_data(
        self,
        benchmark_name: str,
        symbol: str | None,
        data: MarketDataFrame | pd.DataFrame | None,
        params: dict[str, Any] | None = None,
        timeframe: str = "1d",
        symbols: list[str] | None = None
    ) -> BenchmarkExecutionResult:
        """Run a benchmark on already loaded data."""
        request = BenchmarkRequest(
            benchmark_name=benchmark_name,
            symbol=symbol,
            symbols=symbols or [],
            params=params or {},
            timeframe=timeframe
        )

        try:
            benchmark = self.registry.get(benchmark_name)

            # Extract underlying pandas DataFrame if MarketDataFrame
            df = data.data if isinstance(data, MarketDataFrame) else data

            return benchmark.run(df, request, params)
        except Exception as e:
            self.logger.error(f"Error running benchmark {benchmark_name}: {e}")
            return BenchmarkExecutionResult(
                request=request,
                status=BenchmarkStatus.FAILED,
                issues=[str(e)]
            )

    def run_for_symbol(
        self,
        benchmark_name: str,
        symbol: str,
        params: dict[str, Any] | None = None,
        timeframe: Timeframe = Timeframe.DAILY,
        period: str | None = None,
        refresh: bool = False
    ) -> BenchmarkExecutionResult:
        """Fetch data and run a benchmark for a single symbol."""
        if not self.data_service:
            raise RuntimeError("MarketDataService is required to run for symbol.")

        try:
            data = getattr(self.data_service, "get_ohlcv", getattr(self.data_service, "fetch_one"))(
                symbol=symbol,
                timeframe=timeframe,
                period=period or self.settings.DOWNLOAD_DEFAULT_PERIOD,

            )
            return self.run_on_data(
                benchmark_name=benchmark_name,
                symbol=symbol,
                data=data,
                params=params,
                timeframe=timeframe.value
            )
        except Exception as e:
            self.logger.error(f"Error fetching data or running benchmark for {symbol}: {e}")
            req = BenchmarkRequest(benchmark_name=benchmark_name, symbol=symbol, params=params or {})
            return BenchmarkExecutionResult(
                request=req,
                status=BenchmarkStatus.FAILED,
                issues=[f"Data fetch failed: {str(e)}"]
            )

    def run_batch(
        self,
        benchmark_name: str,
        symbols: list[str],
        params: dict[str, Any] | None = None,
        continue_on_error: bool = True
    ) -> BenchmarkBatchResult:
        """Run a benchmark across a batch of symbols."""
        start_time = time.time()
        results = []
        success_count = 0
        failed_count = 0

        try:
            benchmark = self.registry.get(benchmark_name)

            if benchmark.spec.supports_portfolio:
                # Portfolio-level benchmark (e.g. EqualWeight)
                req = BenchmarkRequest(
                    benchmark_name=benchmark_name,
                    symbols=symbols,
                    params=params or {}
                )

                # Fetch data for all symbols if needed (simplified for this phase)
                # For EqualWeight, we might only need the latest close, or we can just mock the data pass
                result = benchmark.run(pd.DataFrame({'close': [100.0]}), req, params) # Passing None as data for simplicity in this phase since EqualWeight might just generate intent without data if not provided
                results.append(result)
                if result.status == BenchmarkStatus.SUCCESS:
                    success_count += len(result.signals)
                else:
                    failed_count += 1
            else:
                # Individual benchmark run per symbol
                for symbol in symbols:
                    try:
                        res = self.run_for_symbol(benchmark_name, symbol, params)
                        results.append(res)
                        if res.status == BenchmarkStatus.SUCCESS:
                            success_count += 1
                        else:
                            failed_count += 1
                            if not continue_on_error:
                                break
                    except Exception as e:
                        failed_count += 1
                        self.logger.error(f"Failed to run benchmark for {symbol}: {e}")
                        if not continue_on_error:
                            break

        except Exception as e:
            self.logger.error(f"Error in run_batch: {e}")

        return BenchmarkBatchResult(
            benchmark_name=benchmark_name,
            requested_symbols=symbols,
            results=results,
            success_count=success_count,
            failed_count=failed_count,
            elapsed_seconds=time.time() - start_time
        )

    def run_default_benchmarks(
        self,
        symbol: str,
        data: MarketDataFrame | pd.DataFrame
    ) -> dict[str, BenchmarkExecutionResult]:
        """Run the default set of benchmarks for a symbol."""
        defaults_str = getattr(self.settings, "DEFAULT_BENCHMARKS", "buy_and_hold,moving_average_benchmark,naive_momentum,naive_volatility_filter")
        defaults = [b.strip() for b in defaults_str.split(",") if b.strip()]

        results = {}
        for b_name in defaults:
            if self.registry.exists(b_name):
                res = self.run_on_data(benchmark_name=b_name, symbol=symbol, data=data)
                results[b_name] = res
            else:
                self.logger.warning(f"Default benchmark '{b_name}' not found in registry.")

        # Always run deterministic random baseline if registered
        if self.registry.exists("deterministic_random_baseline") and "deterministic_random_baseline" not in defaults:
             res = self.run_on_data(benchmark_name="deterministic_random_baseline", symbol=symbol, data=data)
             results["deterministic_random_baseline"] = res

        return results


def benchmark_signal_to_candidate(signal: 'BenchmarkSignal') -> 'SignalCandidate':
    from bist_signal_bot.signals.models import SignalCandidate, SignalDirection

    direction = SignalDirection.UNKNOWN
    if signal.intent.value == "LONG":
        direction = SignalDirection.LONG
    elif signal.intent.value == "FLAT":
        direction = SignalDirection.FLAT
    elif signal.intent.value == "SHORT":
        direction = SignalDirection.SHORT

    return SignalCandidate(
        symbol=signal.symbol,
        strategy_name=signal.benchmark_name,
        timeframe="1d",
        direction=direction,
        score=signal.score,
        reference_price=signal.reference_price,
        signal_bar_timestamp=signal.signal_bar_timestamp,
        reasons=signal.reasons,
        metadata=signal.metadata,
        disclaimer=signal.disclaimer
    )
