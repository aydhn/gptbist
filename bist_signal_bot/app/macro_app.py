from pathlib import Path
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.macro.storage import MacroStore
from bist_signal_bot.macro.importer import MacroSeriesImporter
from bist_signal_bot.macro.series import MacroSeriesService
from bist_signal_bot.macro.proxies import MacroProxyRegistry
from bist_signal_bot.macro.returns import MacroReturnCalculator
from bist_signal_bot.macro.correlation import MacroCorrelationAnalyzer
from bist_signal_bot.macro.sensitivity import MacroSensitivityEngine
from bist_signal_bot.macro.regime import MacroRegimeClassifier
from bist_signal_bot.macro.stress import MacroStressEngine
from bist_signal_bot.macro.intermarket import IntermarketContextAnalyzer
from bist_signal_bot.macro.linking import MacroLinker

def create_macro_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MacroStore:
    return MacroStore(settings, base_dir)

def create_macro_proxy_registry(settings: Optional[Settings] = None) -> MacroProxyRegistry:
    return MacroProxyRegistry(settings)

def create_macro_series_importer(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MacroSeriesImporter:
    store = create_macro_store(settings, base_dir)
    registry = create_macro_proxy_registry(settings)
    return MacroSeriesImporter(store, registry, settings)

def create_macro_series_service(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MacroSeriesService:
    store = create_macro_store(settings, base_dir)
    registry = create_macro_proxy_registry(settings)
    return MacroSeriesService(store, registry, settings)

def create_macro_return_calculator(settings: Optional[Settings] = None) -> MacroReturnCalculator:
    registry = create_macro_proxy_registry(settings)
    return MacroReturnCalculator(registry, settings)

def create_macro_correlation_analyzer(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MacroCorrelationAnalyzer:
    store = create_macro_store(settings, base_dir)
    registry = create_macro_proxy_registry(settings)
    return MacroCorrelationAnalyzer(store, registry, settings)

def create_macro_sensitivity_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MacroSensitivityEngine:
    store = create_macro_store(settings, base_dir)
    registry = create_macro_proxy_registry(settings)
    analyzer = create_macro_correlation_analyzer(settings, base_dir)
    return MacroSensitivityEngine(store, analyzer, registry, settings)

def create_macro_regime_classifier(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MacroRegimeClassifier:
    store = create_macro_store(settings, base_dir)
    registry = create_macro_proxy_registry(settings)
    return MacroRegimeClassifier(store, registry, settings)

def create_macro_stress_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MacroStressEngine:
    classifier = create_macro_regime_classifier(settings, base_dir)
    return MacroStressEngine(classifier, settings)

def create_intermarket_context_analyzer(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> IntermarketContextAnalyzer:
    store = create_macro_store(settings, base_dir)
    return IntermarketContextAnalyzer(store, settings)

def create_macro_linker(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> MacroLinker:
    return MacroLinker(settings)
