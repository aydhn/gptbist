from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional
import pandas as pd
from bist_signal_bot.signals.models import SignalCandidate
from .models import RiskContext, RiskDecision, RiskBatchResult

class BaseRiskEngine(ABC):
    """
    Abstract base class for risk management engines.
    """

    @abstractmethod
    def evaluate_signal(self, signal: SignalCandidate, context: RiskContext, data: pd.DataFrame | None = None) -> RiskDecision:
        """Evaluate a single signal candidate."""
        pass

    @abstractmethod
    def evaluate_batch(self, signals: list[SignalCandidate], context: RiskContext, data_by_symbol: dict[str, pd.DataFrame] | None = None) -> RiskBatchResult:
        """Evaluate a batch of signal candidates."""
        pass

    @abstractmethod
    def build_default_context(self, equity: float | None = None, available_cash: float | None = None) -> RiskContext:
        """Build a default RiskContext."""
        pass
