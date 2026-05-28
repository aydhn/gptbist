
from pathlib import Path
from bist_signal_bot.factors.storage import FactorStore
from bist_signal_bot.factors.inputs import FactorInputBuilder
from bist_signal_bot.factors.library import FactorLibrary
from bist_signal_bot.factors.scoring import FactorScorer
from bist_signal_bot.factors.exposure import FactorExposureEngine
from bist_signal_bot.factors.sector_rotation import SectorRotationAnalyzer
from bist_signal_bot.factors.theme import ThemeExposureEngine
from bist_signal_bot.factors.crowding import FactorCrowdingAnalyzer
from bist_signal_bot.factors.attribution import FactorAttributionEngine

def create_factor_store(settings=None, base_dir=None) -> FactorStore: return FactorStore(settings, base_dir)
def create_factor_input_builder(settings=None, base_dir=None) -> FactorInputBuilder: return FactorInputBuilder(settings, base_dir)
def create_factor_library(settings=None) -> FactorLibrary: return FactorLibrary(settings)
def create_factor_scorer(settings=None) -> FactorScorer: return FactorScorer(settings)
def create_factor_exposure_engine(settings=None, base_dir=None) -> FactorExposureEngine: return FactorExposureEngine(settings, base_dir)
def create_sector_rotation_analyzer(settings=None, base_dir=None) -> SectorRotationAnalyzer: return SectorRotationAnalyzer(settings, base_dir)
def create_theme_exposure_engine(settings=None, base_dir=None) -> ThemeExposureEngine: return ThemeExposureEngine(settings, base_dir)
def create_factor_crowding_analyzer(settings=None) -> FactorCrowdingAnalyzer: return FactorCrowdingAnalyzer(settings)
def create_factor_attribution_engine(settings=None) -> FactorAttributionEngine: return FactorAttributionEngine(settings)
