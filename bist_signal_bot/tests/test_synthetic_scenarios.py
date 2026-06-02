
import pytest
from bist_signal_bot.synthetic_scenarios.models import SyntheticScenarioSpec, SyntheticScenarioKind, SyntheticOutputKind, SyntheticFrequency
from bist_signal_bot.synthetic_scenarios.library import SyntheticScenarioLibrary
from bist_signal_bot.synthetic_scenarios.ohlcv import SyntheticOHLCVGenerator
from bist_signal_bot.synthetic_scenarios.macro import SyntheticMacroGenerator
from bist_signal_bot.synthetic_scenarios.stress import SyntheticStressCaseBuilder
from bist_signal_bot.synthetic_scenarios.edge_cases import SyntheticEdgeCaseFactory
from bist_signal_bot.synthetic_scenarios.manifest import SyntheticScenarioManifestBuilder
from bist_signal_bot.synthetic_scenarios.validation import SyntheticScenarioValidator
from bist_signal_bot.synthetic_scenarios.storage import SyntheticScenarioStore
from pathlib import Path

def test_spec_normalize():
    spec = SyntheticScenarioSpec("test_1", "Test", SyntheticScenarioKind.TREND_UP, "Desc", ["asels", "thyao"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, [SyntheticOutputKind.OHLCV])
    assert spec.symbols == ["ASELS", "THYAO"]

def test_spec_invalid_dates():
    with pytest.raises(ValueError):
        SyntheticScenarioSpec("test_1", "Test", SyntheticScenarioKind.TREND_UP, "Desc", ["ASELS"], "2024-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, [SyntheticOutputKind.OHLCV])

def test_library_default():
    lib = SyntheticScenarioLibrary()
    assert len(lib.default_specs()) > 0

def test_library_get():
    lib = SyntheticScenarioLibrary()
    assert lib.get_spec("trend_up_basic_v1") is not None

def test_ohlcv_invariants():
    gen = SyntheticOHLCVGenerator()
    spec = SyntheticScenarioSpec("test_1", "Test", SyntheticScenarioKind.TREND_UP, "Desc", ["ASELS"], "2023-01-01", "2023-01-05", SyntheticFrequency.DAILY, 42, [SyntheticOutputKind.OHLCV])
    ds = gen.generate_ohlcv(spec)
    for row in ds.rows:
        assert row["high"] >= max(row["open"], row["close"])
        assert row["low"] <= min(row["open"], row["close"])
        assert row["volume"] >= 0

def test_macro_indicators():
    gen = SyntheticMacroGenerator()
    spec = SyntheticScenarioSpec("test_1", "Test", SyntheticScenarioKind.TREND_UP, "Desc", ["ASELS"], "2023-01-01", "2023-01-05", SyntheticFrequency.DAILY, 42, [SyntheticOutputKind.MACRO])
    ds = gen.generate_macro(spec)
    assert len(ds.rows) > 0

def test_stress_builder():
    bld = SyntheticStressCaseBuilder()
    spec = SyntheticScenarioSpec("test_1", "Test", SyntheticScenarioKind.TREND_UP, "Desc", ["ASELS"], "2023-01-01", "2023-01-05", SyntheticFrequency.DAILY, 42, [SyntheticOutputKind.MACRO])
    cases = bld.default_stress_cases(spec)
    assert len(cases) > 0

def test_edge_factory():
    fac = SyntheticEdgeCaseFactory()
    spec = SyntheticScenarioSpec("test_1", "Test", SyntheticScenarioKind.TREND_UP, "Desc", ["ASELS"], "2023-01-01", "2023-01-05", SyntheticFrequency.DAILY, 42, [SyntheticOutputKind.MACRO])
    cases = fac.default_edge_cases(spec)
    assert len(cases) > 0

def test_manifest_builder():
    mb = SyntheticScenarioManifestBuilder()
    spec = SyntheticScenarioSpec("test_1", "Test", SyntheticScenarioKind.TREND_UP, "Desc", ["ASELS"], "2023-01-01", "2023-01-05", SyntheticFrequency.DAILY, 42, [SyntheticOutputKind.MACRO])
    manifest = mb.build_manifest(spec, [])
    assert manifest.scenario_id == spec.scenario_id

def test_validator():
    val = SyntheticScenarioValidator()
    spec = SyntheticScenarioSpec("test_1", "Test", SyntheticScenarioKind.TREND_UP, "Desc", ["ASELS"], "2023-01-01", "2023-01-05", SyntheticFrequency.DAILY, 42, [SyntheticOutputKind.MACRO])
    res = val.validate_spec(spec)
    assert res.status.value == "PASS"

def test_storage(tmp_path):
    store = SyntheticScenarioStore(tmp_path)
    spec = SyntheticScenarioSpec("test_1", "Test", SyntheticScenarioKind.TREND_UP, "Desc", ["ASELS"], "2023-01-01", "2023-01-05", SyntheticFrequency.DAILY, 42, [SyntheticOutputKind.MACRO])
    store.save_specs([spec])
    assert (tmp_path / "specs" / "synthetic_specs.json").exists()
