from abc import ABC, abstractmethod
import pandas as pd

class BaseRegimeDetector(ABC):
    """
    Abstract base class for market regime detection (e.g., trend, ranging, volatile).
    """

    @abstractmethod
    def detect(self, data: pd.DataFrame) -> str:
        """Detect the market regime from data."""
        raise NotImplementedError("detect method must be implemented.")
