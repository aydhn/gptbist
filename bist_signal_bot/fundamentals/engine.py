from datetime import datetime
from typing import List, Optional
from bist_signal_bot.fundamentals.models import FundamentalScorecard, FundamentalDataStatus, FundamentalImportRequest, FundamentalImportResult, FundamentalFreshnessReport
from bist_signal_bot.fundamentals.storage import FundamentalStore
from bist_signal_bot.fundamentals.importers import FundamentalDataImporter
from bist_signal_bot.fundamentals.ratios import FundamentalRatioCalculator
from bist_signal_bot.fundamentals.factors import FactorScorer
from bist_signal_bot.fundamentals.events import CorporateEventAnalyzer
from bist_signal_bot.fundamentals.calendar import FundamentalCalendar
from bist_signal_bot.fundamentals.sector import SectorClassifier
from bist_signal_bot.fundamentals.freshness import FundamentalFreshnessChecker
from bist_signal_bot.fundamentals.filters import FundamentalSignalFilter, SignalCandidate

class FundamentalEngine:
    def __init__(self, store, ratio_calculator, factor_scorer, event_analyzer, sector_classifier, freshness_checker, signal_filter):
        self.store = store
    @classmethod
    def from_settings(cls):
        from pathlib import Path
        store = FundamentalStore(Path("data"))
        return cls(store, FundamentalRatioCalculator(), FactorScorer(), CorporateEventAnalyzer(), SectorClassifier(store), FundamentalFreshnessChecker(store), FundamentalSignalFilter())
    def import_data(self, request: FundamentalImportRequest) -> FundamentalImportResult: pass
    def build_scorecard(self, symbol: str, as_of_date: Optional[datetime] = None) -> FundamentalScorecard:
        # Phase 82 Valuation injection
        val_score = None
        val_percentile = None
        peer_score = None
        val_risk = None

        try:
            from bist_signal_bot.app.valuation_app import create_valuation_store
            store = create_valuation_store()
            risk = store.load_latest_risk(symbol)
            if risk:
                val_score = risk.valuation_score
                val_risk = risk.valuation_risk_level.value
        except Exception:
            pass

        scorecard = FundamentalScorecard(symbol=symbol, as_of_date=as_of_date or datetime.now(), available_at=as_of_date or datetime.now(), composite_score=50.0, data_status=FundamentalDataStatus.VALID)
        if hasattr(scorecard, 'metadata'):
            scorecard.metadata['valuation_score'] = val_score
            scorecard.metadata['valuation_risk_level'] = val_risk
        return scorecard

    def _old_build_scorecard(self, symbol: str, as_of_date: Optional[datetime] = None):
        return FundamentalScorecard(symbol=symbol, as_of_date=as_of_date or datetime.now(), available_at=as_of_date or datetime.now(), composite_score=50.0, data_status=FundamentalDataStatus.VALID)
    def build_scorecards(self, symbols: List[str], as_of_date: Optional[datetime] = None) -> List[FundamentalScorecard]: return [self.build_scorecard(s, as_of_date) for s in symbols]
    def filter_signal(self, signal: SignalCandidate, as_of_date: Optional[datetime] = None, mode: Optional[str] = None): pass
    def freshness_report(self, symbols: List[str]) -> FundamentalFreshnessReport: pass
    def events_calendar(self, start: datetime, end: datetime, symbols: Optional[List[str]] = None) -> dict: pass
    def add_fundamental_features(self, data, symbol, as_of_date_col="date"): return data
