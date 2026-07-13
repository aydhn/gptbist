import time
import hashlib
from datetime import datetime
from typing import Any
import pandas as pd
import numpy as np

from bist_signal_bot.benchmarks.base import BaseBenchmarkStrategy
from bist_signal_bot.benchmarks.models import (
    BenchmarkCategory,
    BenchmarkSpec,
    BenchmarkRequest,
    BenchmarkExecutionResult,
    BenchmarkSignal,
    BenchmarkPositionIntent,
    BenchmarkStatus
)

class BuyAndHoldBenchmark(BaseBenchmarkStrategy):
    def __init__(self):
        super().__init__(BenchmarkSpec(
            name="buy_and_hold",
            display_name="Buy and Hold",
            category=BenchmarkCategory.BUY_AND_HOLD,
            description="Reference strategy that holds a long position continuously.",
            required_columns=["close"],
            default_params={"weight": 1.0, "min_rows": 2},
            min_rows=2
        ))

    def generate(self, data: pd.DataFrame | None, request: BenchmarkRequest, params: dict[str, Any]) -> BenchmarkExecutionResult:
        start_time = time.time()
        issues = []
        signals = []

        symbol = request.symbol
        if not symbol:
            issues.append("Symbol is required for buy_and_hold benchmark")
            return BenchmarkExecutionResult(request=request, status=BenchmarkStatus.FAILED, issues=issues)

        if len(data) < params["min_rows"]:
            issues.append(f"Not enough data. Minimum required is {params['min_rows']}")
            return BenchmarkExecutionResult(request=request, status=BenchmarkStatus.FAILED, issues=issues)

        try:
            latest_bar = data.iloc[-1]
            reference_price = float(latest_bar["close"])
            signal_time = pd.to_datetime(data.index[-1]).to_pydatetime() if isinstance(data.index, pd.DatetimeIndex) else None

            signal = BenchmarkSignal(
                symbol=symbol,
                benchmark_name=self.spec.name,
                intent=BenchmarkPositionIntent.LONG,
                score=50.0,
                weight=params["weight"],
                reference_price=reference_price,
                signal_bar_timestamp=signal_time,
                reasons=["Buy-and-hold benchmark reference."]
            )
            signals.append(signal)
            status = BenchmarkStatus.SUCCESS
        except Exception as e:
            issues.append(f"Error generating signal: {str(e)}")
            status = BenchmarkStatus.FAILED

        return BenchmarkExecutionResult(
            request=request,
            status=status,
            signals=signals,
            issues=issues,
            elapsed_seconds=time.time() - start_time
        )


class CashBenchmark(BaseBenchmarkStrategy):
    def __init__(self):
        super().__init__(BenchmarkSpec(
            name="cash",
            display_name="Cash",
            category=BenchmarkCategory.CASH,
            description="Reference strategy representing holding 100% cash.",
            required_columns=[],
            default_params={"cash_weight": 1.0},
            min_rows=1
        ))

    def generate(self, data: pd.DataFrame | None, request: BenchmarkRequest, params: dict[str, Any]) -> BenchmarkExecutionResult:
        start_time = time.time()

        symbol = request.symbol or "CASH"

        signal = BenchmarkSignal(
            symbol=symbol,
            benchmark_name=self.spec.name,
            intent=BenchmarkPositionIntent.FLAT,
            score=50.0,
            weight=params["cash_weight"],
            reference_price=1.0,
            reasons=["Cash benchmark reference."]
        )

        return BenchmarkExecutionResult(
            request=request,
            status=BenchmarkStatus.SUCCESS,
            signals=[signal],
            elapsed_seconds=time.time() - start_time
        )


class EqualWeightBenchmark(BaseBenchmarkStrategy):
    def __init__(self):
        super().__init__(BenchmarkSpec(
            name="equal_weight",
            display_name="Equal Weight",
            category=BenchmarkCategory.EQUAL_WEIGHT,
            description="Reference strategy that holds an equal-weighted portfolio.",
            required_columns=["close"],
            default_params={"total_weight": 1.0, "min_symbols": 1},
            supports_portfolio=True
        ))

    def generate(self, data: pd.DataFrame | None, request: BenchmarkRequest, params: dict[str, Any]) -> BenchmarkExecutionResult:
        start_time = time.time()
        issues = []
        signals = []

        symbols = request.symbols or ([request.symbol] if request.symbol else [])
        if not symbols:
            issues.append("Symbols are required for equal_weight benchmark")
            return BenchmarkExecutionResult(request=request, status=BenchmarkStatus.FAILED, issues=issues)

        if len(symbols) < params["min_symbols"]:
            issues.append(f"Not enough symbols. Minimum required is {params['min_symbols']}")
            return BenchmarkExecutionResult(request=request, status=BenchmarkStatus.FAILED, issues=issues)

        weight_per_symbol = params["total_weight"] / len(symbols)

        try:
            reference_price = None
            signal_time = None
            if data is not None and not data.empty:
                reference_price = float(data.iloc[-1]["close"]) if "close" in data.columns else None
                signal_time = pd.to_datetime(data.index[-1]).to_pydatetime() if isinstance(data.index, pd.DatetimeIndex) else None

            for symbol in symbols:
                signal = BenchmarkSignal(
                    symbol=symbol,
                    benchmark_name=self.spec.name,
                    intent=BenchmarkPositionIntent.LONG,
                    score=50.0,
                    weight=weight_per_symbol,
                    reference_price=reference_price if request.symbol == symbol else None,
                    signal_bar_timestamp=signal_time,
                    reasons=["Equal-weight benchmark reference."]
                )
                signals.append(signal)
            status = BenchmarkStatus.SUCCESS
        except Exception as e:
            issues.append(f"Error generating signal: {str(e)}")
            status = BenchmarkStatus.FAILED

        return BenchmarkExecutionResult(
            request=request,
            status=status,
            signals=signals,
            issues=issues,
            elapsed_seconds=time.time() - start_time
        )


class MovingAverageBenchmark(BaseBenchmarkStrategy):
    def __init__(self):
        super().__init__(BenchmarkSpec(
            name="moving_average_benchmark",
            display_name="Moving Average Benchmark",
            category=BenchmarkCategory.TREND,
            description="Reference strategy based on Simple Moving Average.",
            required_columns=["close"],
            default_params={"window": 200, "long_when_above": True},
            min_rows=200
        ))

    def generate(self, data: pd.DataFrame | None, request: BenchmarkRequest, params: dict[str, Any]) -> BenchmarkExecutionResult:
        start_time = time.time()
        issues = []
        signals = []

        symbol = request.symbol
        if not symbol:
            issues.append("Symbol is required for moving_average_benchmark")
            return BenchmarkExecutionResult(request=request, status=BenchmarkStatus.FAILED, issues=issues)

        window = int(params["window"])
        if len(data) < window:
            issues.append(f"Not enough data. Minimum required is {window}")
            return BenchmarkExecutionResult(request=request, status=BenchmarkStatus.FAILED, issues=issues)

        try:
            sma = data["close"].rolling(window=window).mean()
            latest_close = float(data.iloc[-1]["close"])
            latest_sma = float(sma.iloc[-1])
            signal_time = pd.to_datetime(data.index[-1]).to_pydatetime() if isinstance(data.index, pd.DatetimeIndex) else None

            is_above = latest_close > latest_sma
            long_cond = is_above if params["long_when_above"] else not is_above

            intent = BenchmarkPositionIntent.LONG if long_cond else BenchmarkPositionIntent.FLAT

            # Simple score: distance from SMA
            dist_pct = abs(latest_close - latest_sma) / latest_sma
            score = min(50.0 + (dist_pct * 100), 100.0) if long_cond else min(50.0 - (dist_pct * 100), 100.0)
            score = max(0.0, score)

            reason = f"Close ({latest_close:.2f}) is {'above' if is_above else 'below'} SMA{window} ({latest_sma:.2f})"

            signal = BenchmarkSignal(
                symbol=symbol,
                benchmark_name=self.spec.name,
                intent=intent,
                score=score,
                weight=1.0 if intent == BenchmarkPositionIntent.LONG else 0.0,
                reference_price=latest_close,
                signal_bar_timestamp=signal_time,
                reasons=[f"Moving Average Benchmark reference: {reason}"]
            )
            signals.append(signal)
            status = BenchmarkStatus.SUCCESS
        except Exception as e:
            issues.append(f"Error generating signal: {str(e)}")
            status = BenchmarkStatus.FAILED

        return BenchmarkExecutionResult(
            request=request,
            status=status,
            signals=signals,
            issues=issues,
            elapsed_seconds=time.time() - start_time
        )


class NaiveMomentumBenchmark(BaseBenchmarkStrategy):
    def __init__(self):
        super().__init__(BenchmarkSpec(
            name="naive_momentum",
            display_name="Naive Momentum",
            category=BenchmarkCategory.MOMENTUM,
            description="Reference strategy based on simple n-period return.",
            required_columns=["close"],
            default_params={"lookback": 60, "threshold": 0.0},
            min_rows=61
        ))

    def generate(self, data: pd.DataFrame | None, request: BenchmarkRequest, params: dict[str, Any]) -> BenchmarkExecutionResult:
        start_time = time.time()
        issues = []
        signals = []

        symbol = request.symbol
        if not symbol:
            issues.append("Symbol is required for naive_momentum benchmark")
            return BenchmarkExecutionResult(request=request, status=BenchmarkStatus.FAILED, issues=issues)

        lookback = int(params["lookback"])
        if len(data) <= lookback:
            issues.append(f"Not enough data. Minimum required is {lookback + 1}")
            return BenchmarkExecutionResult(request=request, status=BenchmarkStatus.FAILED, issues=issues)

        try:
            returns = data["close"].pct_change(periods=lookback)
            latest_return = float(returns.iloc[-1])
            latest_close = float(data.iloc[-1]["close"])
            signal_time = pd.to_datetime(data.index[-1]).to_pydatetime() if isinstance(data.index, pd.DatetimeIndex) else None

            threshold = float(params["threshold"])
            intent = BenchmarkPositionIntent.LONG if latest_return > threshold else BenchmarkPositionIntent.FLAT

            # Score based on momentum magnitude
            score = 50.0 + (latest_return * 100) # Simple linear scaling
            score = min(max(0.0, score), 100.0)

            reason = f"{lookback}-period return is {latest_return:.2%} (threshold: {threshold:.2%})"

            signal = BenchmarkSignal(
                symbol=symbol,
                benchmark_name=self.spec.name,
                intent=intent,
                score=score,
                weight=1.0 if intent == BenchmarkPositionIntent.LONG else 0.0,
                reference_price=latest_close,
                signal_bar_timestamp=signal_time,
                reasons=[f"Naive Momentum Benchmark reference: {reason}"]
            )
            signals.append(signal)
            status = BenchmarkStatus.SUCCESS
        except Exception as e:
            issues.append(f"Error generating signal: {str(e)}")
            status = BenchmarkStatus.FAILED

        return BenchmarkExecutionResult(
            request=request,
            status=status,
            signals=signals,
            issues=issues,
            elapsed_seconds=time.time() - start_time
        )


class NaiveVolatilityFilterBenchmark(BaseBenchmarkStrategy):
    def __init__(self):
        super().__init__(BenchmarkSpec(
            name="naive_volatility_filter",
            display_name="Naive Volatility Filter",
            category=BenchmarkCategory.VOLATILITY,
            description="Reference strategy that stays flat in high volatility regimes.",
            required_columns=["close"],
            default_params={"vol_window": 20, "max_vol": 0.60, "annualization": 252},
            min_rows=21
        ))

    def generate(self, data: pd.DataFrame | None, request: BenchmarkRequest, params: dict[str, Any]) -> BenchmarkExecutionResult:
        start_time = time.time()
        issues = []
        signals = []

        symbol = request.symbol
        if not symbol:
            issues.append("Symbol is required for naive_volatility_filter benchmark")
            return BenchmarkExecutionResult(request=request, status=BenchmarkStatus.FAILED, issues=issues)

        vol_window = int(params["vol_window"])
        if len(data) <= vol_window:
            issues.append(f"Not enough data. Minimum required is {vol_window + 1}")
            return BenchmarkExecutionResult(request=request, status=BenchmarkStatus.FAILED, issues=issues)

        try:
            daily_returns = data["close"].pct_change()
            historical_vol = daily_returns.rolling(window=vol_window).std() * np.sqrt(params["annualization"])

            latest_vol = float(historical_vol.iloc[-1])
            latest_close = float(data.iloc[-1]["close"])
            signal_time = pd.to_datetime(data.index[-1]).to_pydatetime() if isinstance(data.index, pd.DatetimeIndex) else None

            max_vol = float(params["max_vol"])
            intent = BenchmarkPositionIntent.LONG if latest_vol <= max_vol else BenchmarkPositionIntent.FLAT

            # Lower volatility -> higher score
            score = 100.0 * (1.0 - min(latest_vol / (max_vol * 1.5), 1.0))
            score = min(max(0.0, score), 100.0)

            reason = f"{vol_window}-period annualized volatility is {latest_vol:.2%} (max allowed: {max_vol:.2%})"

            signal = BenchmarkSignal(
                symbol=symbol,
                benchmark_name=self.spec.name,
                intent=intent,
                score=score,
                weight=1.0 if intent == BenchmarkPositionIntent.LONG else 0.0,
                reference_price=latest_close,
                signal_bar_timestamp=signal_time,
                reasons=[f"Naive Volatility Filter Benchmark reference: {reason}"]
            )
            signals.append(signal)
            status = BenchmarkStatus.SUCCESS
        except Exception as e:
            issues.append(f"Error generating signal: {str(e)}")
            status = BenchmarkStatus.FAILED

        return BenchmarkExecutionResult(
            request=request,
            status=status,
            signals=signals,
            issues=issues,
            elapsed_seconds=time.time() - start_time
        )


class DeterministicRandomBaselineBenchmark(BaseBenchmarkStrategy):
    def __init__(self):
        super().__init__(BenchmarkSpec(
            name="deterministic_random_baseline",
            display_name="Deterministic Random Baseline",
            category=BenchmarkCategory.RANDOM_BASELINE,
            description="Sanity baseline producing deterministic random signals for comparison.",
            required_columns=["close"],
            default_params={"seed": 42, "long_probability": 0.5},
            min_rows=1
        ))

    def generate(self, data: pd.DataFrame | None, request: BenchmarkRequest, params: dict[str, Any]) -> BenchmarkExecutionResult:
        start_time = time.time()
        issues = []
        signals = []

        symbol = request.symbol
        if not symbol:
            issues.append("Symbol is required for deterministic_random_baseline")
            return BenchmarkExecutionResult(request=request, status=BenchmarkStatus.FAILED, issues=issues)

        try:
            latest_close = float(data.iloc[-1]["close"]) if data is not None and not data.empty and "close" in data.columns else None
            signal_time = pd.to_datetime(data.index[-1]).to_pydatetime() if data is not None and not data.empty and isinstance(data.index, pd.DatetimeIndex) else datetime(2025, 1, 1)

            # Deterministic hash based on symbol, timestamp, and seed
            seed = int(params["seed"])
            hash_input = f"{symbol}_{signal_time.isoformat()}_{seed}"
            hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

            # Map hash to a 0.0 - 1.0 probability
            rand_val = (hash_val % 10000) / 10000.0

            prob = float(params["long_probability"])
            intent = BenchmarkPositionIntent.LONG if rand_val < prob else BenchmarkPositionIntent.FLAT

            score = 100.0 * rand_val if intent == BenchmarkPositionIntent.LONG else 100.0 * (1.0 - rand_val)

            reason = f"Deterministic pseudo-random value {rand_val:.4f} vs threshold {prob:.4f}"

            signal = BenchmarkSignal(
                symbol=symbol,
                benchmark_name=self.spec.name,
                intent=intent,
                score=score,
                weight=1.0 if intent == BenchmarkPositionIntent.LONG else 0.0,
                reference_price=latest_close,
                signal_bar_timestamp=signal_time,
                reasons=[f"Random Baseline reference: {reason}"]
            )
            signals.append(signal)
            status = BenchmarkStatus.SUCCESS
        except Exception as e:
            issues.append(f"Error generating signal: {str(e)}")
            status = BenchmarkStatus.FAILED

        return BenchmarkExecutionResult(
            request=request,
            status=status,
            signals=signals,
            issues=issues,
            elapsed_seconds=time.time() - start_time
        )
