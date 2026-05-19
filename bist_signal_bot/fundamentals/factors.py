from datetime import datetime
from typing import Optional, List
from bist_signal_bot.fundamentals.models import FundamentalRatioSnapshot, FactorScore, FactorGroup
class FactorScorer:
    def score_symbol(self, symbol: str, ratio_snapshot: FundamentalRatioSnapshot, peer_snapshots: Optional[List[FundamentalRatioSnapshot]] = None) -> List[FactorScore]:
        return [FactorScore(symbol, ratio_snapshot.as_of_date, ratio_snapshot.available_at, FactorGroup.COMPOSITE, 60.0)]
