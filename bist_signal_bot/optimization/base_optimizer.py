from abc import ABC, abstractmethod

class BaseOptimizer(ABC):
    """
    Abstract base class for strategy parameter optimizers.
    """

    @abstractmethod
    def optimize(self):
        """Run parameter optimization."""
        raise NotImplementedError("optimize method must be implemented.")
