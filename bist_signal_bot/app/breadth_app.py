from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.breadth.storage import BreadthStore
from bist_signal_bot.breadth.universe import BreadthUniverseBuilder
from bist_signal_bot.breadth.inputs import BreadthInputBuilder
from bist_signal_bot.breadth.advance_decline import AdvanceDeclineCalculator
from bist_signal_bot.breadth.participation import ParticipationAnalyzer
from bist_signal_bot.breadth.high_low import HighLowBreadthAnalyzer
from bist_signal_bot.breadth.volume_breadth import VolumeBreadthAnalyzer
from bist_signal_bot.breadth.sector_breadth import SectorBreadthAnalyzer
from bist_signal_bot.breadth.divergence import BreadthDivergenceDetector
from bist_signal_bot.breadth.regime import BreadthRegimeClassifier
from bist_signal_bot.breadth.scoring import BreadthScorer
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.instruments.master import InstrumentMaster

def create_breadth_store(settings: Settings | None = None, base_dir: Path | None = None) -> BreadthStore:
    return BreadthStore(settings=settings, base_dir=base_dir)

def create_breadth_universe_builder(settings: Settings | None = None, instrument_master: InstrumentMaster | None = None) -> BreadthUniverseBuilder:
    return BreadthUniverseBuilder(settings=settings, instrument_master=instrument_master)

def create_breadth_input_builder(settings: Settings | None = None, data_service: MarketDataService | None = None) -> BreadthInputBuilder:
    return BreadthInputBuilder(settings=settings, data_service=data_service)

def create_advance_decline_calculator(settings: Settings | None = None) -> AdvanceDeclineCalculator:
    return AdvanceDeclineCalculator(settings=settings)

def create_participation_analyzer(settings: Settings | None = None) -> ParticipationAnalyzer:
    return ParticipationAnalyzer(settings=settings)

def create_high_low_breadth_analyzer(settings: Settings | None = None) -> HighLowBreadthAnalyzer:
    return HighLowBreadthAnalyzer(settings=settings)

def create_volume_breadth_analyzer(settings: Settings | None = None) -> VolumeBreadthAnalyzer:
    return VolumeBreadthAnalyzer(settings=settings)

def create_sector_breadth_analyzer(settings: Settings | None = None) -> SectorBreadthAnalyzer:
    return SectorBreadthAnalyzer(settings=settings)

def create_breadth_divergence_detector(settings: Settings | None = None) -> BreadthDivergenceDetector:
    return BreadthDivergenceDetector(settings=settings)

def create_breadth_regime_classifier(settings: Settings | None = None) -> BreadthRegimeClassifier:
    return BreadthRegimeClassifier(settings=settings)

def create_breadth_scorer(settings: Settings | None = None) -> BreadthScorer:
    return BreadthScorer(settings=settings)
