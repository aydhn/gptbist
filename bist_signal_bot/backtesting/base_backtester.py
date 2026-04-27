from abc import ABC, abstractmethod


class BaseBacktester(ABC):
    """
    Abstract base class for backtesting engines.
    """

    @abstractmethod
    def run(self):
        """Run the backtest."""
        raise NotImplementedError("run method must be implemented by subclasses.")
