from pathlib import Path
from typing import Optional

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.storage.paths import get_valuation_dir
from bist_signal_bot.valuation.storage import ValuationStore
from bist_signal_bot.valuation.market_inputs import ValuationMarketInputBuilder
from bist_signal_bot.valuation.multiples import ValuationMultipleCalculator
from bist_signal_bot.valuation.bands import ValuationBandAnalyzer
from bist_signal_bot.valuation.peer_compare import PeerValuationComparator
from bist_signal_bot.valuation.scoring import ValuationScorer
from bist_signal_bot.valuation.risk import ValuationRiskEngine
from bist_signal_bot.valuation.linking import ValuationLinker

def create_valuation_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ValuationStore:
    settings = settings or get_settings()
    base_dir = base_dir or get_valuation_dir(settings)
    return ValuationStore(settings=settings, base_dir=base_dir)

def create_valuation_market_input_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ValuationMarketInputBuilder:
    settings = settings or get_settings()

    # Resolving dependencies lazily to avoid circular imports where possible
    try:
        from bist_signal_bot.app.instruments_app import create_instrument_master
        from bist_signal_bot.app.financials_app import create_financial_engine
        from bist_signal_bot.app.data_app import create_market_data_service

        im = create_instrument_master(settings)
        fe = create_financial_engine(settings)
        ds = create_market_data_service(settings)
    except ImportError:
        im = None
        fe = None
        ds = None

    return ValuationMarketInputBuilder(settings=settings, data_service=ds, financials_engine=fe, instrument_master=im)

def create_valuation_multiple_calculator(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ValuationMultipleCalculator:
    settings = settings or get_settings()
    return ValuationMultipleCalculator(settings=settings)

def create_valuation_band_analyzer(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ValuationBandAnalyzer:
    settings = settings or get_settings()
    return ValuationBandAnalyzer(settings=settings)

def create_peer_valuation_comparator(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> PeerValuationComparator:
    settings = settings or get_settings()
    try:
        from bist_signal_bot.app.instruments_app import create_instrument_master
        im = create_instrument_master(settings)
    except ImportError:
        im = None
    return PeerValuationComparator(settings=settings, instrument_master=im)

def create_valuation_scorer(settings: Optional[Settings] = None) -> ValuationScorer:
    settings = settings or get_settings()
    return ValuationScorer(settings=settings)

def create_valuation_risk_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ValuationRiskEngine:
    settings = settings or get_settings()
    scorer = create_valuation_scorer(settings)
    return ValuationRiskEngine(settings=settings, scorer=scorer)

def create_valuation_linker(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ValuationLinker:
    settings = settings or get_settings()
    try:
        from bist_signal_bot.app.financials_app import create_financial_engine
        fe = create_financial_engine(settings)
    except ImportError:
        fe = None
    # Add other mock engines here if needed
    return ValuationLinker(financials_engine=fe)
