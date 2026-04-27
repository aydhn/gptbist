from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    """

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on the provided data.
        Returns the data dataframe with an appended signal column.
        """
        raise NotImplementedError("generate_signals must be implemented by subclasses.")
