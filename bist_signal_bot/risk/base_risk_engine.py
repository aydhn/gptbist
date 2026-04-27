from abc import ABC, abstractmethod

class BaseRiskEngine(ABC):
    """
    Abstract base class for risk management engines.
    """

    @abstractmethod
    def evaluate_risk(self, signal) -> bool:
        """Evaluate if a signal passes risk constraints."""
        raise NotImplementedError("evaluate_risk method must be implemented.")
