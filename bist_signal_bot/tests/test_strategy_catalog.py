import pytest
from bist_signal_bot.strategy_registry.catalog import StrategyCatalogScanner
from bist_signal_bot.strategy_registry.models import StrategyDefinition

class MockStrategy:
    strategy_name = "mock_strat"
    version = "1.2.0"
    family = "MOMENTUM"
    default_parameters = {"period": 14}

def test_catalog_scanner_definition_from_class():
    scanner = StrategyCatalogScanner()
    defn = scanner.definition_from_strategy_class(MockStrategy)

    assert defn.strategy_name == "mock_strat"
    assert defn.version == "1.2.0"
    assert defn.family.value == "MOMENTUM"
    assert defn.default_parameters == {"period": 14}

class MockFallbackStrategy:
    pass

def test_catalog_scanner_fallback_definition():
    scanner = StrategyCatalogScanner()
    defn = scanner.definition_from_strategy_class(MockFallbackStrategy)

    assert defn.strategy_name == "MockFallbackStrategy"
    assert defn.version == "1.0.0"
    assert defn.family.value == "UNKNOWN"
    assert defn.default_parameters == {}

def test_detect_missing_registry_entries(monkeypatch):
    scanner = StrategyCatalogScanner()

    def mock_scan():
        return [
            StrategyDefinition(strategy_id="1", strategy_name="strat_A", display_name="A", version="1", family="UNKNOWN", status="CANDIDATE"),
            StrategyDefinition(strategy_id="2", strategy_name="strat_B", display_name="B", version="1", family="UNKNOWN", status="CANDIDATE")
        ]

    monkeypatch.setattr(scanner, "scan_available_strategies", mock_scan)

    existing = [StrategyDefinition(strategy_id="1", strategy_name="strat_A", display_name="A", version="1", family="UNKNOWN", status="CANDIDATE")]

    missing = scanner.detect_missing_registry_entries(existing)
    assert len(missing) == 1
    assert missing[0].strategy_name == "strat_B"
