from typing import Tuple, List, Optional
from bist_signal_bot.fundamentals.models import FundamentalScorecard, FundamentalFilterDecision
class SignalCandidate:
    def __init__(self, symbol: str, score: float = 0.0, metadata: dict = None):
        self.symbol = symbol
        self.score = score
        self.metadata = metadata or {}
class FundamentalSignalFilter:
    def filter_signal(self, signal: SignalCandidate, scorecard: FundamentalScorecard, mode: str = "metadata_only") -> Tuple[FundamentalFilterDecision, SignalCandidate, List[str]]:
        signal.metadata['fundamental_composite_score'] = scorecard.composite_score
        if mode == "score_adjust": signal.score += 0.1
        return FundamentalFilterDecision.PASS, signal, []
