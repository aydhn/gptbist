from abc import ABC, abstractmethod
from typing import Any
import pandas as pd
from bist_signal_bot.patterns.models import PatternSpec
from bist_signal_bot.core.exceptions import PatternValidationError

class BasePatternDetector(ABC):
    def __init__(self):
        pass

    @property
    @abstractmethod
    def spec(self) -> PatternSpec:
        pass

    def validate_input(self, data: pd.DataFrame, params: dict[str, Any]) -> None:
        if len(data) < self.spec.min_rows:
            raise PatternValidationError(f"{self.spec.name} requires at least {self.spec.min_rows} rows, got {len(data)}")

        missing_cols = [col for col in self.spec.required_columns if col not in data.columns]
        if missing_cols:
            raise PatternValidationError(f"{self.spec.name} requires columns: {missing_cols}")

    def get_output_columns(self, params: dict[str, Any]) -> list[str]:
        cols = []
        for col in self.spec.output_columns:
            # Simple format replacement for known params
            formatted = col
            for k, v in params.items():
                formatted = formatted.replace(f"{{{k}}}", str(v))
            cols.append(formatted)
        return cols

    @abstractmethod
    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        pass

    def __call__(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        merged_params = {**self.spec.default_params, **params}
        self.validate_input(data, merged_params)
        return self.detect(data, **merged_params)
