import time
from abc import ABC, abstractmethod
from typing import Any
import pandas as pd

from bist_signal_bot.core.exceptions import StrategyValidationError, StrategyExecutionError
from bist_signal_bot.strategies.context import StrategyContext
from bist_signal_bot.strategies.models import (
    StrategySpec,
    StrategyRequest,
    StrategyExecutionResult,
    StrategyExecutionIssue
)
from bist_signal_bot.signals.models import SignalCandidate, SignalStatus, SignalDirection, SignalStrength

class BaseStrategy(ABC):
    """
    Abstract base class for all signal bot strategies.
    Defines the standard lifecycle and data contract for strategy execution.
    """

    @property
    @abstractmethod
    def spec(self) -> StrategySpec:
        pass

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        final_params = dict(self.spec.default_params)
        if params:
            for k, v in params.items():
                if k not in final_params:
                    raise StrategyValidationError(f"Unknown parameter '{k}' for strategy '{self.spec.name}'")
                final_params[k] = v

        for param_spec in self.spec.parameters:
            name = param_spec.name
            val = final_params.get(name)

            if val is not None:
                if param_spec.min_value is not None and val < param_spec.min_value:
                    raise StrategyValidationError(f"Parameter '{name}' value {val} is less than minimum {param_spec.min_value}")
                if param_spec.max_value is not None and val > param_spec.max_value:
                    raise StrategyValidationError(f"Parameter '{name}' value {val} is greater than maximum {param_spec.max_value}")
                if param_spec.choices is not None and val not in param_spec.choices:
                    raise StrategyValidationError(f"Parameter '{name}' value {val} must be one of {param_spec.choices}")

        return final_params

    def validate_context(self, context: StrategyContext, params: dict[str, Any]) -> None:
        if len(context.data) < self.spec.min_rows:
            raise StrategyValidationError(
                f"Strategy '{self.spec.name}' requires at least {self.spec.min_rows} rows, "
                f"but got {len(context.data)} for {context.symbol}"
            )

        context.require_columns(self.spec.required_columns)
        context.require_columns(self.spec.required_features)

        if params.get("allow_short", False) and not self.spec.supports_short:
            raise StrategyValidationError(f"Strategy '{self.spec.name}' does not support short positions")

    def prepare_features(self, context: StrategyContext, params: dict[str, Any]) -> pd.DataFrame:
        return context.data.copy()

    @abstractmethod
    def generate_candidate(self, context: StrategyContext, params: dict[str, Any]) -> SignalCandidate | None:
        pass

    def build_signal_candidate(self, context: StrategyContext, direction: SignalDirection,
                              score: float = 0.0, strength: SignalStrength = SignalStrength.UNKNOWN,
                              reasons: list[Any] | None = None, risk_notes: list[Any] | None = None,
                              **kwargs: Any) -> SignalCandidate:
        disclaimer = "Research signal candidate only. Not investment advice. No order was sent."
        if context.settings:
            disclaimer = getattr(context.settings, "STRATEGY_CANDIDATE_DISCLAIMER", disclaimer)

        timestamp = None
        if context.latest_row is not None and hasattr(context.latest_row, "name"):
            if isinstance(context.latest_row.name, pd.Timestamp):
                timestamp = context.latest_row.name

        entry_price = context.get_latest_value("close")

        return SignalCandidate(
            symbol=context.symbol,
            strategy_name=self.spec.name,
            direction=direction,
            score=score,
            strength=strength,
            timeframe=context.timeframe,
            signal_bar_timestamp=timestamp,
            entry_reference_price=entry_price,
            reasons=reasons or [],
            risk_notes=risk_notes or [],
            disclaimer=disclaimer,
            **kwargs
        )

    def run(self, context: StrategyContext, params: dict[str, Any] | None = None) -> StrategyExecutionResult:
        start_time = time.time()
        issues = []

        request = StrategyRequest(
            strategy_name=self.spec.name,
            symbol=context.symbol,
            params=params or {},
            run_mode=context.run_mode,
            timeframe=context.timeframe
        )

        try:
            validated_params = self.validate_params(request.params)
            self.validate_context(context, validated_params)
            feature_df = self.prepare_features(context, validated_params)
            candidate = self.generate_candidate(context, validated_params)

            return StrategyExecutionResult(
                request=request,
                candidate=candidate,
                output_data=None,
                status="success",
                issues=issues,
                elapsed_seconds=time.time() - start_time
            )

        except StrategyValidationError as e:
            issues.append(StrategyExecutionIssue(
                strategy_name=self.spec.name,
                symbol=context.symbol,
                message=str(e),
                severity="warning"
            ))
            return StrategyExecutionResult(
                request=request,
                status="failed_validation",
                issues=issues,
                elapsed_seconds=time.time() - start_time
            )
        except Exception as e:
            issues.append(StrategyExecutionIssue(
                strategy_name=self.spec.name,
                symbol=context.symbol,
                message=f"Strategy execution error: {str(e)}",
                severity="error"
            ))
            return StrategyExecutionResult(
                request=request,
                status="error",
                issues=issues,
                elapsed_seconds=time.time() - start_time
            )
