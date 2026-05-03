from abc import ABC, abstractmethod
from typing import Any
import pandas as pd

from bist_signal_bot.benchmarks.models import (
    BenchmarkSpec,
    BenchmarkRequest,
    BenchmarkExecutionResult
)
from bist_signal_bot.core.exceptions import BenchmarkValidationError

class BaseBenchmarkStrategy(ABC):
    """Abstract base class for benchmark strategies."""

    def __init__(self, spec: BenchmarkSpec):
        self.spec = spec

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Validate and merge parameters with defaults."""
        merged_params = self.spec.default_params.copy()
        if params:
            for k, v in params.items():
                if k not in merged_params:
                    raise BenchmarkValidationError(f"Unknown parameter '{k}' for benchmark '{self.spec.name}'")
                merged_params[k] = v
        return merged_params

    def validate_data(self, data: pd.DataFrame | None, required_columns: list[str]) -> None:
        """Validate that input data contains required columns."""
        if required_columns and data is None:
            raise BenchmarkValidationError(f"Benchmark '{self.spec.name}' requires data but None was provided.")

        if data is not None:
            if data.empty:
                raise BenchmarkValidationError(f"Benchmark '{self.spec.name}' received empty DataFrame.")
            missing_cols = [col for col in required_columns if col not in data.columns]
            if missing_cols:
                raise BenchmarkValidationError(f"Data missing required columns for benchmark '{self.spec.name}': {missing_cols}")

    @abstractmethod
    def generate(self, data: pd.DataFrame | None, request: BenchmarkRequest, params: dict[str, Any]) -> BenchmarkExecutionResult:
        """Core logic to generate benchmark signals."""
        pass

    def run(self, data: pd.DataFrame | None, request: BenchmarkRequest, params: dict[str, Any] | None = None) -> BenchmarkExecutionResult:
        """Entry point for executing a benchmark strategy."""
        merged_params = self.validate_params(params or {})
        self.validate_data(data, self.spec.required_columns)

        # Ensure we don't mutate input data
        data_copy = data.copy() if data is not None else None

        return self.generate(data_copy, request, merged_params)
