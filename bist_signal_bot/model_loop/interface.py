"""Stable contract of the intraday model loop (research/paper only; no orders).

Other components (drift monitor, lifecycle, runtime guard) code against these types only.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

NO_ORDER = "No real order sent."


class TrainedModelInfo(BaseModel):
    model_id: str
    kind: str                       # 'hgb' | 'logreg'
    interval: str
    trained_through: str            # ISO date/time of the last data point used
    n_events: int
    oos_metrics: Dict[str, Any] = Field(default_factory=dict)
    gate_verdict: str = "INSUFFICIENT_DATA"   # CANDIDATE | REJECTED | INSUFFICIENT_DATA
    artifact_path: str = ""
    registry_status: str = ""       # never a champion/production status
    warnings: list = Field(default_factory=list)
    disclaimer: str = NO_ORDER


ModelTrainerFn = Callable[..., TrainedModelInfo]


@runtime_checkable
class TrainerProtocol(Protocol):
    def train(self, as_of) -> TrainedModelInfo: ...

    def latest_oos_net_sharpe(self, model_id: str) -> Optional[float]: ...
