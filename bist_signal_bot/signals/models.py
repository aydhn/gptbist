from datetime import datetime

from pydantic import BaseModel


class Signal(BaseModel):
    """
    Data model representing a trading signal.
    """
    symbol: str
    timestamp: datetime
    action: str  # 'BUY', 'SELL', 'HOLD'
    price: float
    strategy_name: str
    score: float | None = None
    metadata: dict | None = None
