import uuid
import logging
from typing import Any, Optional

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.ensemble.models import SignalVote, SignalSourceType, SignalVoteDirection, EnsembleRequest
from bist_signal_bot.core.exceptions import EnsembleCollectionError

logger = logging.getLogger(__name__)

class SignalVoteCollector:
    def __init__(
        self,
        strategy_engine: Any = None,
        ml_engine: Any = None,
        regime_engine: Any = None,
        risk_engine: Any = None,
        fundamental_engine: Any = None,
        breadth_engine: Any = None,
        adaptive_engine: Any = None,
        settings: Optional[Settings] = None
    ):
        self.strategy_engine = strategy_engine
        self.ml_engine = ml_engine
        self.regime_engine = regime_engine
        self.risk_engine = risk_engine
        self.fundamental_engine = fundamental_engine
        self.breadth_engine = breadth_engine
        self.adaptive_engine = adaptive_engine
        self.settings = settings or get_settings()

    def collect_votes(self, symbol: str, request: EnsembleRequest) -> list[SignalVote]:
        votes = []

        # Strategies
        try:
            votes.extend(self.collect_strategy_votes(symbol, request))
        except Exception as e:
            logger.warning(f"Failed to collect strategy votes for {symbol}: {e}")
            votes.append(self._error_vote(symbol, SignalSourceType.STRATEGY, "StrategyEngine", str(e)))

        # Indicators & Patterns & Divergences
        try:
            votes.extend(self.collect_indicator_votes(symbol, request))
            votes.extend(self.collect_pattern_votes(symbol, request))
            votes.extend(self.collect_divergence_votes(symbol, request))
        except Exception as e:
            logger.warning(f"Failed to collect tech votes for {symbol}: {e}")

        # ML
        if getattr(request, "include_ml", True) and getattr(self.settings, "ENSEMBLE_INCLUDE_ML", True):
            try:
                ml_v = self.collect_ml_vote(symbol, request)
                if ml_v: votes.append(ml_v)
            except Exception as e:
                logger.warning(f"Failed to collect ML vote for {symbol}: {e}")

        # Regime
        if getattr(request, "include_regime", True) and getattr(self.settings, "ENSEMBLE_INCLUDE_REGIME", True):
            try:
                reg_v = self.collect_regime_vote(symbol, request)
                if reg_v: votes.append(reg_v)
            except Exception as e:
                logger.warning(f"Failed to collect Regime vote for {symbol}: {e}")

        # Risk
        if getattr(request, "include_risk", True) and getattr(self.settings, "ENSEMBLE_INCLUDE_RISK", True):
            try:
                risk_v = self.collect_risk_vote(symbol, request)
                if risk_v: votes.append(risk_v)
            except Exception as e:
                logger.warning(f"Failed to collect Risk vote for {symbol}: {e}")

        # Fundamentals
        if getattr(request, "include_fundamentals", True) and getattr(self.settings, "ENSEMBLE_INCLUDE_FUNDAMENTALS", True):
            try:
                fund_v = self.collect_fundamental_vote(symbol, request)
                if fund_v: votes.append(fund_v)
            except Exception as e:
                logger.warning(f"Failed to collect Fundamental vote for {symbol}: {e}")

        # Breadth
        if getattr(request, "include_breadth", True) and getattr(self.settings, "ENSEMBLE_INCLUDE_BREADTH", True):
            try:
                br_v = self.collect_breadth_vote(symbol, request)
                if br_v: votes.append(br_v)
            except Exception as e:
                logger.warning(f"Failed to collect Breadth vote for {symbol}: {e}")

        # Adaptive
        if getattr(request, "include_adaptive", True) and getattr(self.settings, "ENSEMBLE_INCLUDE_ADAPTIVE", True):
            try:
                ad_v = self.collect_adaptive_vote(symbol, request)
                if ad_v: votes.append(ad_v)
            except Exception as e:
                logger.warning(f"Failed to collect Adaptive vote for {symbol}: {e}")

        return votes

    def _error_vote(self, symbol: str, s_type: SignalSourceType, s_name: str, msg: str) -> SignalVote:
        return SignalVote(
            vote_id=str(uuid.uuid4())[:8],
            source_type=s_type,
            source_name=s_name,
            symbol=symbol,
            direction=SignalVoteDirection.UNKNOWN,
            score=50.0,
            confidence=0.0,
            weight=0.0,
            warnings=[f"Error collecting vote: {msg}"]
        )

    def collect_strategy_votes(self, symbol: str, request: EnsembleRequest) -> list[SignalVote]:
        if not self.strategy_engine:
            return []
        votes = []
        return votes

    def collect_indicator_votes(self, symbol: str, request: EnsembleRequest) -> list[SignalVote]:
        return []

    def collect_pattern_votes(self, symbol: str, request: EnsembleRequest) -> list[SignalVote]:
        return []

    def collect_divergence_votes(self, symbol: str, request: EnsembleRequest) -> list[SignalVote]:
        return []

    def collect_ml_vote(self, symbol: str, request: EnsembleRequest) -> Optional[SignalVote]:
        if not self.ml_engine: return None
        return None

    def collect_regime_vote(self, symbol: str, request: EnsembleRequest) -> Optional[SignalVote]:
        if not self.regime_engine: return None
        return None

    def collect_risk_vote(self, symbol: str, request: EnsembleRequest) -> Optional[SignalVote]:
        if not self.risk_engine: return None
        return None

    def collect_fundamental_vote(self, symbol: str, request: EnsembleRequest) -> Optional[SignalVote]:
        if not self.fundamental_engine: return None
        return None

    def collect_breadth_vote(self, symbol: str, request: EnsembleRequest) -> Optional[SignalVote]:
        if not self.breadth_engine: return None
        return None

    def collect_adaptive_vote(self, symbol: str, request: EnsembleRequest) -> Optional[SignalVote]:
        if not self.adaptive_engine: return None
        return None
