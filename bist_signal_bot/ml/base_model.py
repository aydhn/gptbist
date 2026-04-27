from abc import ABC, abstractmethod

class BaseMLModel(ABC):
    """
    Abstract base class for Machine Learning models.
    """

    @abstractmethod
    def train(self, X, y):
        """Train the ML model."""
        raise NotImplementedError("train method must be implemented.")

    @abstractmethod
    def predict(self, X):
        """Generate predictions."""
        raise NotImplementedError("predict method must be implemented.")
