from abc import ABC, abstractmethod
import pandas as pd

class BaseDataProvider(ABC):
    """
    Abstract base class for all data providers.
    Every data provider (e.g., Yahoo Finance, local CSV) should inherit from this.
    """

    @abstractmethod
    def fetch_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch historical data for a given symbol.
        """
        raise NotImplementedError("fetch_data must be implemented by subclasses.")
