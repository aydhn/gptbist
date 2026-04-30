from abc import ABC, abstractmethod
from typing import Any, Dict, List
import pandas as pd
from .models import IndicatorSpec
from bist_signal_bot.core.exceptions import IndicatorCalculationError, IndicatorValidationError

class BaseIndicator(ABC):
    def __init__(self, spec: IndicatorSpec):
        self.spec = spec

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        """Validates that the input data and parameters meet the indicator's requirements."""
        # Check required columns
        for col in self.spec.required_columns:
            if col not in data.columns:
                raise IndicatorValidationError(f"Required column '{col}' missing for {self.spec.name}")

        # We can also check row counts here if needed, but warning/reporting might be better handled by the engine.
        pass

    @abstractmethod
    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        """Abstract method to implement the indicator logic.
        Must return a new DataFrame containing only the calculated output columns.
        """
        pass

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        """Returns the list of output column names based on the parameters."""
        return [self.build_column_name(col, params) for col in self.spec.output_columns]

    def build_column_name(self, base: str, params: Dict[str, Any]) -> str:
        """Helper to build consistent column names based on parameters."""
        # Simple strategy: append values of integer or float parameters that aren't the base itself
        parts = [base]
        # Try to extract the most relevant parameters to append based on what's common in indicators.
        # This can be overridden by specific indicators if they have complex naming needs.
        for k, v in params.items():
            if isinstance(v, (int, float)):
                 parts.append(str(v).replace('.', '_'))
        return "_".join(parts)

    def __call__(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        """Callable interface to execute the indicator."""
        # Merge default params with provided params
        merged_params = self.spec.default_params.copy()
        merged_params.update(params)

        try:
            self.validate_input(data, merged_params)
            # Ensure we don't mutate input
            result = self.calculate(data.copy(), **merged_params)
            return result
        except IndicatorValidationError:
            raise
        except Exception as e:
            raise IndicatorCalculationError(f"Error calculating {self.spec.name}: {str(e)}") from e
