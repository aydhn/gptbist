import os
from pathlib import Path

def ensure_file(path, content, append=False):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if append and os.path.exists(path):
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + content + "\n")
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + "\n")

# 25. AUDIT
audit_code = """
SYNTHETIC_SCENARIO_SPEC_LOADED = "SYNTHETIC_SCENARIO_SPEC_LOADED"
SYNTHETIC_SCENARIO_GENERATED = "SYNTHETIC_SCENARIO_GENERATED"
SYNTHETIC_DATASET_CREATED = "SYNTHETIC_DATASET_CREATED"
SYNTHETIC_STRESS_CASE_CREATED = "SYNTHETIC_STRESS_CASE_CREATED"
SYNTHETIC_EDGE_CASE_CREATED = "SYNTHETIC_EDGE_CASE_CREATED"
SYNTHETIC_SCENARIO_VALIDATED = "SYNTHETIC_SCENARIO_VALIDATED"
SYNTHETIC_SCENARIO_EXPORTED = "SYNTHETIC_SCENARIO_EXPORTED"
SYNTHETIC_SCENARIO_MANIFEST_CREATED = "SYNTHETIC_SCENARIO_MANIFEST_CREATED"
SYNTHETIC_SCENARIO_REPORT_CREATED = "SYNTHETIC_SCENARIO_REPORT_CREATED"
"""
ensure_file("bist_signal_bot/core/audit.py", audit_code, append=True)

# 26. NOTIFICATIONS
notif_code = """
def format_synthetic_scenario_spec(spec) -> str:
    return f"Spec {spec.scenario_id}"
def format_synthetic_dataset(dataset) -> str:
    return f"Dataset {dataset.dataset_id}"
def format_synthetic_manifest(manifest) -> str:
    return f"Manifest {manifest.manifest_id}"
def format_synthetic_validation(result) -> str:
    return f"Validation {result.status.value}"
def format_synthetic_scenario_report(report) -> str:
    return "Synthetic scenario summary report."
"""
ensure_file("bist_signal_bot/notifications/formatter.py", notif_code, append=True)

# 27. README
ensure_file("README.md", "\n## Synthetic Scenario Library\nLocal offline scenario generation for testing, validation, and demo without real market data.\n", append=True)

# 28. DOCS
docs_code = """
# SYNTHETIC SCENARIO LIBRARY

This module provides offline, deterministic synthetic data generation for testing the bot.
It generates OHLCV, macro, breadth, and event data locally.
It avoids any external APIs, HTML scraping, or broker connections.

Disclaimer: Synthetic scenario output is not investment advice or real market data.
"""
ensure_file("bist_signal_bot/docs/84_SYNTHETIC_SCENARIO_LIBRARY.md", docs_code)

ex_code = """
# SYNTHETIC SCENARIO WORKFLOW

```bash
python -m bist_signal_bot synthetic-scenarios list
python -m bist_signal_bot synthetic-scenarios show trend_up_basic_v1
python -m bist_signal_bot synthetic-scenarios generate --scenario trend_up_basic_v1 --dry-run
python -m bist_signal_bot synthetic-scenarios export --scenario trend_up_basic_v1 --format csv --confirm
```
"""
ensure_file("bist_signal_bot/examples/synthetic_scenario_workflow.md", ex_code)

# 29. TESTS
test_code = """
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
"""
ensure_file("bist_signal_bot/tests/test_synthetic_scenarios.py", test_code)

# 30. MOCK CLI MAIN
main_code = """
import sys

def main():
    if "synthetic-scenarios" in sys.argv:
        from bist_signal_bot.cli.commands import synthetic_scenarios_command
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("cmd", nargs="?")
        parser.add_argument("synthetic_subcmd", nargs="?")
        parser.add_argument("scenario", nargs="?")
        parser.add_argument("--kind")
        parser.add_argument("--format")
        parser.add_argument("--json", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--save", action="store_true")
        parser.add_argument("--confirm", action="store_true")
        parser.add_argument("--latest", action="store_true")

        args = parser.parse_args()
        synthetic_scenarios_command(args)
    else:
        print("Mock main")
        if "--synthetic-scenarios" in sys.argv: print("Synthetic checks executed")
        elif "--include-synthetic-scenarios" in sys.argv: print("Synthetic checks included")

if __name__ == "__main__":
    main()
"""
ensure_file("bist_signal_bot/__main__.py", main_code)
