from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Signal(BaseModel):
    """
    Data model representing a trading signal.
    """
    symbol: str
    timestamp: datetime
    action: str  # 'BUY', 'SELL', 'HOLD'
    price: float
    strategy_name: str
    score: Optional[float] = None
    metadata: Optional[dict] = None
