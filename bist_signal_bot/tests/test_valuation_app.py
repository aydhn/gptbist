from bist_signal_bot.app.valuation_app import (
    create_valuation_scorer,
    create_valuation_risk_engine,
    create_valuation_linker,
    create_valuation_store,
    create_valuation_market_input_builder,
    create_valuation_multiple_calculator,
    create_valuation_band_analyzer,
    create_peer_valuation_comparator
)
from bist_signal_bot.valuation.scoring import ValuationScorer
from bist_signal_bot.valuation.risk import ValuationRiskEngine
from bist_signal_bot.valuation.linking import ValuationLinker
from bist_signal_bot.valuation.storage import ValuationStore
from bist_signal_bot.valuation.market_inputs import ValuationMarketInputBuilder
from bist_signal_bot.valuation.multiples import ValuationMultipleCalculator
from bist_signal_bot.valuation.bands import ValuationBandAnalyzer
from bist_signal_bot.valuation.peer_compare import PeerValuationComparator
from pathlib import Path
from unittest.mock import patch
import sys

class MockSettings:
    pass

def test_create_valuation_scorer():
    scorer = create_valuation_scorer()
    assert isinstance(scorer, ValuationScorer)

def test_create_valuation_scorer_with_settings():
    settings = MockSettings()
    scorer = create_valuation_scorer(settings=settings)
    assert isinstance(scorer, ValuationScorer)
    assert scorer.settings is settings

def test_create_valuation_risk_engine():
    engine = create_valuation_risk_engine()
    assert isinstance(engine, ValuationRiskEngine)
    assert isinstance(engine.scorer, ValuationScorer)

def test_create_valuation_risk_engine_with_settings():
    settings = MockSettings()
    engine = create_valuation_risk_engine(settings=settings)
    assert isinstance(engine, ValuationRiskEngine)
    assert engine.settings is settings
    assert isinstance(engine.scorer, ValuationScorer)

def test_create_valuation_linker():
    linker = create_valuation_linker()
    assert isinstance(linker, ValuationLinker)

def test_create_valuation_linker_with_settings():
    settings = MockSettings()
    linker = create_valuation_linker(settings=settings)
    assert isinstance(linker, ValuationLinker)

def test_create_valuation_store():
    store = create_valuation_store()
    assert isinstance(store, ValuationStore)

def test_create_valuation_store_with_settings_and_basedir():
    settings = MockSettings()
    base_dir = Path("/tmp/test_val_store")
    store = create_valuation_store(settings=settings, base_dir=base_dir)
    assert isinstance(store, ValuationStore)
    assert store.settings is settings
    assert store.base_dir == base_dir

def test_create_valuation_market_input_builder():
    builder = create_valuation_market_input_builder()
    assert isinstance(builder, ValuationMarketInputBuilder)

def test_create_valuation_market_input_builder_with_settings():
    settings = MockSettings()
    builder = create_valuation_market_input_builder(settings=settings)
    assert isinstance(builder, ValuationMarketInputBuilder)
    assert builder.settings is settings

def test_create_valuation_multiple_calculator():
    calc = create_valuation_multiple_calculator()
    assert isinstance(calc, ValuationMultipleCalculator)

def test_create_valuation_multiple_calculator_with_settings():
    settings = MockSettings()
    calc = create_valuation_multiple_calculator(settings=settings)
    assert isinstance(calc, ValuationMultipleCalculator)
    assert calc.settings is settings

def test_create_valuation_band_analyzer():
    analyzer = create_valuation_band_analyzer()
    assert isinstance(analyzer, ValuationBandAnalyzer)

def test_create_valuation_band_analyzer_with_settings():
    settings = MockSettings()
    analyzer = create_valuation_band_analyzer(settings=settings)
    assert isinstance(analyzer, ValuationBandAnalyzer)
    assert analyzer.settings is settings

def test_create_peer_valuation_comparator():
    comparator = create_peer_valuation_comparator()
    assert isinstance(comparator, PeerValuationComparator)

def test_create_peer_valuation_comparator_with_settings():
    settings = MockSettings()
    comparator = create_peer_valuation_comparator(settings=settings)
    assert isinstance(comparator, PeerValuationComparator)
    assert comparator.settings is settings

def test_create_valuation_market_input_builder_import_error():
    with patch.dict('sys.modules', {'bist_signal_bot.app.instruments_app': None}):
        builder = create_valuation_market_input_builder()
        assert isinstance(builder, ValuationMarketInputBuilder)
        assert builder.instrument_master is None

def test_create_peer_valuation_comparator_import_error():
    with patch.dict('sys.modules', {'bist_signal_bot.app.instruments_app': None}):
        comparator = create_peer_valuation_comparator()
        assert isinstance(comparator, PeerValuationComparator)
        assert comparator.instrument_master is None

def test_create_valuation_linker_import_error():
    with patch.dict('sys.modules', {'bist_signal_bot.app.financials_app': None}):
        linker = create_valuation_linker()
        assert isinstance(linker, ValuationLinker)
        assert linker.financials_engine is None

def test_create_valuation_market_input_builder_success():
    class MockInstrumentMaster: pass
    class MockFinancialEngine: pass
    class MockDataService: pass

    # Mock the imports used in create_valuation_market_input_builder
    import types
    mock_instruments_app = types.ModuleType('bist_signal_bot.app.instruments_app')
    mock_instruments_app.create_instrument_master = lambda s: MockInstrumentMaster()

    mock_financials_app = types.ModuleType('bist_signal_bot.app.financials_app')
    mock_financials_app.create_financial_engine = lambda s: MockFinancialEngine()

    mock_data_app = types.ModuleType('bist_signal_bot.app.data_app')
    mock_data_app.create_market_data_service = lambda s: MockDataService()

    with patch.dict(sys.modules, {
        'bist_signal_bot.app.instruments_app': mock_instruments_app,
        'bist_signal_bot.app.financials_app': mock_financials_app,
        'bist_signal_bot.app.data_app': mock_data_app,
    }):
         builder = create_valuation_market_input_builder()
         assert isinstance(builder.instrument_master, MockInstrumentMaster)
         assert isinstance(builder.financials_engine, MockFinancialEngine)
         assert isinstance(builder.data_service, MockDataService)

def test_create_peer_valuation_comparator_success():
    class MockInstrumentMaster: pass
    import types
    mock_instruments_app = types.ModuleType('bist_signal_bot.app.instruments_app')
    mock_instruments_app.create_instrument_master = lambda s: MockInstrumentMaster()

    with patch.dict(sys.modules, {
        'bist_signal_bot.app.instruments_app': mock_instruments_app
    }):
         comparator = create_peer_valuation_comparator()
         assert isinstance(comparator.instrument_master, MockInstrumentMaster)

def test_create_valuation_linker_success():
    class MockFinancialEngine: pass
    import types
    mock_financials_app = types.ModuleType('bist_signal_bot.app.financials_app')
    mock_financials_app.create_financial_engine = lambda s: MockFinancialEngine()
    with patch.dict(sys.modules, {
        'bist_signal_bot.app.financials_app': mock_financials_app
    }):
         linker = create_valuation_linker()
         assert isinstance(linker.financials_engine, MockFinancialEngine)

def test_create_valuation_risk_engine_with_settings_and_basedir():
    settings = MockSettings()
    base_dir = Path("/tmp/test_val_risk_engine")
    engine = create_valuation_risk_engine(settings=settings, base_dir=base_dir)
    assert isinstance(engine, ValuationRiskEngine)
    assert engine.settings is settings
    assert isinstance(engine.scorer, ValuationScorer)
