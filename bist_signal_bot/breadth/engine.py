import time
from datetime import datetime
from typing import Any

from bist_signal_bot.breadth.models import (
    BreadthAnalysisRequest, BreadthAnalysisResult, BreadthSnapshot,
    CrossSectionalRankItem, SectorRotationScore
)
from bist_signal_bot.breadth.calculator import BreadthCalculator
from bist_signal_bot.breadth.relative_strength import RelativeStrengthCalculator
from bist_signal_bot.breadth.sector_rotation import SectorRotationAnalyzer
from bist_signal_bot.breadth.ranking import CrossSectionalRanker
from bist_signal_bot.breadth.regime import BreadthRegimeClassifier
from bist_signal_bot.breadth.storage import BreadthStore
from dataclasses import dataclass

@dataclass
class BreadthEngineConfig:
    data_service: Any
    sector_classifier: Any = None
    fundamental_engine: Any = None
    calculator: BreadthCalculator = None
    relative_strength_calculator: RelativeStrengthCalculator = None
    sector_rotation_analyzer: SectorRotationAnalyzer = None
    ranker: CrossSectionalRanker = None
    regime_classifier: BreadthRegimeClassifier = None
    store: BreadthStore = None
    settings: Any = None

class BreadthEngine:
    def __init__(self, config: BreadthEngineConfig):
        self.data_service = config.data_service
        self.sector_classifier = config.sector_classifier
        self.fundamental_engine = config.fundamental_engine
        self.calculator = config.calculator or BreadthCalculator(config.settings)
        self.relative_strength_calculator = config.relative_strength_calculator or RelativeStrengthCalculator(config.settings)
        self.sector_rotation_analyzer = config.sector_rotation_analyzer or SectorRotationAnalyzer(config.settings)
        self.ranker = config.ranker or CrossSectionalRanker(config.settings)
        self.regime_classifier = config.regime_classifier or BreadthRegimeClassifier(config.settings)
        self.store = config.store or BreadthStore(settings=config.settings)
        self.settings = config.settings

    def analyze(self, request: BreadthAnalysisRequest) -> BreadthAnalysisResult:
        start_time = time.time()

        # 1. Load data
        data_by_symbol = {}
        for sym in request.symbols:
            try:
                df = self.data_service.get_historical_data(sym, request.timeframe, source=request.source)
                if df is not None and not df.empty:
                    data_by_symbol[sym] = df
            except Exception:
                pass

        benchmark_data = None
        if request.benchmark_symbol:
            try:
                benchmark_data = self.data_service.get_historical_data(request.benchmark_symbol, request.timeframe, source=request.source)
            except Exception:
                pass

        sectors = {}
        if self.sector_classifier:
            try:
                # Mock sector fetch
                for sym in request.symbols:
                    sectors[sym] = "UNKNOWN"
            except Exception:
                pass

        fundamentals = {}
        if self.fundamental_engine and request.include_fundamentals:
            try:
                # Mock fundamentals fetch
                pass
            except Exception:
                pass

        # 2. Calculate Snapshot
        snapshot = self.calculator.calculate_snapshot(data_by_symbol, request)

        # 3. Relative Strength
        rs_scores = []
        if request.include_relative_strength:
            rs_scores = self.relative_strength_calculator.calculate_scores(data_by_symbol, benchmark_data, sectors, snapshot.as_of_date)

        # 4. Sector Rotation
        sector_scores = []
        if request.include_sector_rotation and rs_scores:
            sector_scores = self.sector_rotation_analyzer.calculate_sector_rotation(rs_scores, sectors, fundamentals)

        # 5. Cross Sectional Ranking
        ranking = []
        if rs_scores:
            ranking = self.ranker.rank_symbols(rs_scores, fundamentals)

        # 6. Regime
        regime = self.regime_classifier.classify(snapshot, sector_scores)
        snapshot.status = regime.status

        # 7. Store
        output_files = {}
        result = BreadthAnalysisResult(
            request=request,
            snapshot=snapshot,
            relative_strength_scores=rs_scores,
            sector_rotation_scores=sector_scores,
            cross_sectional_ranking=ranking,
            regime=regime,
            elapsed_seconds=time.time() - start_time
        )

        if request.save_snapshot:
            output_files = self.store.save_result(result)
            result.output_files = {k: str(v) for k, v in output_files.items()}

        return result

    def latest_snapshot(self) -> BreadthSnapshot | None:
        return self.store.load_latest_snapshot()

    def leaders(self, top_n: int = 20) -> list[CrossSectionalRankItem]:
        ranking = self.store.load_latest_ranking()
        if ranking:
            return self.ranker.top_leaders(ranking, top_n)
        return []

    def laggards(self, bottom_n: int = 20) -> list[CrossSectionalRankItem]:
        ranking = self.store.load_latest_ranking()
        if ranking:
            return self.ranker.bottom_laggards(ranking, bottom_n)
        return []

    def sector_rotation(self, top_n: int = 10) -> list[SectorRotationScore]:
        # Helper to load from store not fully implemented, returning empty list for mock
        return []

    def build_feature_snapshot(self, symbol: str, as_of_date: datetime) -> dict[str, Any]:
        snapshot = self.latest_snapshot()
        if not snapshot:
            return {}

        return {
            "breadth_status_code": snapshot.status.value,
            "breadth_composite_score": snapshot.composite_score
        }

    @classmethod
    def from_settings(cls, settings: Any) -> "BreadthEngine":
        from bist_signal_bot.data.data_service import MarketDataService
        from bist_signal_bot.data.mock_provider import MockMarketDataProvider
        data_service = MarketDataService(provider=MockMarketDataProvider())
        config = BreadthEngineConfig(
            data_service=data_service,
            settings=settings
        )
        return cls(config)
