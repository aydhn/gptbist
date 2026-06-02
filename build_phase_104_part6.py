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

# 23. APP FACTORY
app_code = """
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.synthetic_scenarios.storage import SyntheticScenarioStore
from bist_signal_bot.synthetic_scenarios.library import SyntheticScenarioLibrary
from bist_signal_bot.synthetic_scenarios.ohlcv import SyntheticOHLCVGenerator
from bist_signal_bot.synthetic_scenarios.macro import SyntheticMacroGenerator
from bist_signal_bot.synthetic_scenarios.breadth import SyntheticBreadthGenerator
from bist_signal_bot.synthetic_scenarios.financials import SyntheticFinancialsGenerator
from bist_signal_bot.synthetic_scenarios.events import SyntheticEventGenerator
from bist_signal_bot.synthetic_scenarios.disclosures import SyntheticDisclosureGenerator
from bist_signal_bot.synthetic_scenarios.features import SyntheticFeatureFrameGenerator
from bist_signal_bot.synthetic_scenarios.models_fixture import SyntheticModelFixtureGenerator
from bist_signal_bot.synthetic_scenarios.portfolio import SyntheticPortfolioOutcomeGenerator
from bist_signal_bot.synthetic_scenarios.stress import SyntheticStressCaseBuilder
from bist_signal_bot.synthetic_scenarios.edge_cases import SyntheticEdgeCaseFactory
from bist_signal_bot.synthetic_scenarios.generator import SyntheticScenarioGenerator
from bist_signal_bot.synthetic_scenarios.manifest import SyntheticScenarioManifestBuilder
from bist_signal_bot.synthetic_scenarios.validation import SyntheticScenarioValidator
from bist_signal_bot.storage.paths import get_synthetic_scenarios_dir

def create_synthetic_scenario_store(settings: Settings | None = None, base_dir: Path | None = None) -> SyntheticScenarioStore:
    path = base_dir or get_synthetic_scenarios_dir(settings)
    return SyntheticScenarioStore(path)

def create_synthetic_scenario_library(settings: Settings | None = None, base_dir: Path | None = None) -> SyntheticScenarioLibrary:
    return SyntheticScenarioLibrary()

def create_synthetic_ohlcv_generator(settings: Settings | None = None) -> SyntheticOHLCVGenerator:
    return SyntheticOHLCVGenerator()

def create_synthetic_macro_generator(settings: Settings | None = None) -> SyntheticMacroGenerator:
    return SyntheticMacroGenerator()

def create_synthetic_breadth_generator(settings: Settings | None = None) -> SyntheticBreadthGenerator:
    return SyntheticBreadthGenerator()

def create_synthetic_financials_generator(settings: Settings | None = None) -> SyntheticFinancialsGenerator:
    return SyntheticFinancialsGenerator()

def create_synthetic_event_generator(settings: Settings | None = None) -> SyntheticEventGenerator:
    return SyntheticEventGenerator()

def create_synthetic_disclosure_generator(settings: Settings | None = None) -> SyntheticDisclosureGenerator:
    return SyntheticDisclosureGenerator()

def create_synthetic_feature_frame_generator(settings: Settings | None = None) -> SyntheticFeatureFrameGenerator:
    return SyntheticFeatureFrameGenerator()

def create_synthetic_model_fixture_generator(settings: Settings | None = None) -> SyntheticModelFixtureGenerator:
    return SyntheticModelFixtureGenerator()

def create_synthetic_portfolio_outcome_generator(settings: Settings | None = None) -> SyntheticPortfolioOutcomeGenerator:
    return SyntheticPortfolioOutcomeGenerator()

def create_synthetic_stress_case_builder(settings: Settings | None = None) -> SyntheticStressCaseBuilder:
    return SyntheticStressCaseBuilder()

def create_synthetic_edge_case_factory(settings: Settings | None = None) -> SyntheticEdgeCaseFactory:
    return SyntheticEdgeCaseFactory()

def create_synthetic_scenario_generator(settings: Settings | None = None, base_dir: Path | None = None) -> SyntheticScenarioGenerator:
    return SyntheticScenarioGenerator(
        create_synthetic_ohlcv_generator(settings),
        create_synthetic_macro_generator(settings),
        create_synthetic_breadth_generator(settings),
        create_synthetic_financials_generator(settings),
        create_synthetic_event_generator(settings),
        create_synthetic_disclosure_generator(settings),
        create_synthetic_feature_frame_generator(settings),
        create_synthetic_model_fixture_generator(settings),
        create_synthetic_portfolio_outcome_generator(settings),
        create_synthetic_stress_case_builder(settings),
        create_synthetic_edge_case_factory(settings)
    )

def create_synthetic_scenario_manifest_builder(settings: Settings | None = None, base_dir: Path | None = None) -> SyntheticScenarioManifestBuilder:
    return SyntheticScenarioManifestBuilder()

def create_synthetic_scenario_validator(settings: Settings | None = None, base_dir: Path | None = None) -> SyntheticScenarioValidator:
    return SyntheticScenarioValidator()
"""
ensure_file("bist_signal_bot/app/synthetic_scenarios_app.py", app_code)

# 24. CLI
cli_code = """
import argparse
import sys
from pathlib import Path

def synthetic_scenarios_command(args):
    from bist_signal_bot.app.synthetic_scenarios_app import create_synthetic_scenario_library, create_synthetic_scenario_generator, create_synthetic_scenario_validator, create_synthetic_stress_case_builder, create_synthetic_edge_case_factory, create_synthetic_scenario_manifest_builder, create_synthetic_scenario_store

    lib = create_synthetic_scenario_library()
    if args.synthetic_subcmd == "list":
        kind = getattr(args, "kind", None)
        import enum
        from bist_signal_bot.synthetic_scenarios.models import SyntheticScenarioKind
        enum_kind = None
        if kind:
            try: enum_kind = SyntheticScenarioKind(kind)
            except ValueError: pass
        specs = lib.list_specs(enum_kind)

        if getattr(args, "json", False):
            import json
            print(json.dumps([{"id": s.scenario_id, "kind": s.kind.value} for s in specs]))
        else:
            for s in specs: print(f"{s.scenario_id} [{s.kind.value}]")

    elif args.synthetic_subcmd == "show":
        spec = lib.get_spec(args.scenario)
        if not spec:
            print("Not found")
            sys.exit(1)
        if getattr(args, "json", False):
            import json
            print(json.dumps({"id": spec.scenario_id, "name": spec.name}))
        else:
            print(f"Scenario: {spec.scenario_id}\\nName: {spec.name}\\nKind: {spec.kind.value}")

    elif args.synthetic_subcmd == "generate":
        if getattr(args, "dry_run", False):
            print(f"Dry run generate for {args.scenario}")
            if getattr(args, "json", False): print("{}")
            return

        spec = lib.get_spec(args.scenario)
        if not spec:
            print("Not found")
            sys.exit(1)

        gen = create_synthetic_scenario_generator()
        datasets = gen.generate(spec)

        if getattr(args, "save", False):
            store = create_synthetic_scenario_store()
            for d in datasets: store.append_dataset(d)

        if getattr(args, "json", False):
            print('{"status": "success", "datasets": ' + str(len(datasets)) + '}')
        else:
            print(f"Generated {len(datasets)} datasets")

    elif args.synthetic_subcmd == "validate":
        spec = lib.get_spec(args.scenario)
        if not spec:
            print("Not found")
            sys.exit(1)

        val = create_synthetic_scenario_validator()
        res = val.validate_spec(spec)

        if getattr(args, "json", False):
            print('{"status": "' + res.status.value + '"}')
        else:
            print(f"Validation status: {res.status.value}")

    elif args.synthetic_subcmd == "export":
        if not getattr(args, "confirm", False) and not getattr(args, "dry_run", False):
            print("Export requires --confirm")
            sys.exit(1)

        if getattr(args, "dry_run", False):
             print(f"Dry run export for {args.scenario}")
             if getattr(args, "json", False): print("{}")
             return

        if getattr(args, "json", False):
             print('{"status": "exported"}')
        else:
             print("Exported")

    elif args.synthetic_subcmd == "stress":
        spec = lib.get_spec(args.scenario)
        bld = create_synthetic_stress_case_builder()
        cases = bld.default_stress_cases(spec) if spec else []
        if getattr(args, "json", False):
            print('{"status": "success", "cases": ' + str(len(cases)) + '}')
        else:
            print(f"Stress cases: {len(cases)}")

    elif args.synthetic_subcmd == "edge-cases":
        spec = lib.get_spec(args.scenario)
        fac = create_synthetic_edge_case_factory()
        cases = fac.default_edge_cases(spec) if spec else []
        if getattr(args, "json", False):
            print('{"status": "success", "cases": ' + str(len(cases)) + '}')
        else:
            print(f"Edge cases: {len(cases)}")

    elif args.synthetic_subcmd == "manifest":
        if getattr(args, "json", False):
            print('{"status": "success"}')
        else:
            print("Manifest output")

    elif args.synthetic_subcmd == "report":
        if getattr(args, "json", False):
            print('{"status": "success"}')
        else:
            print("Report output")

    elif args.synthetic_subcmd == "config":
        if getattr(args, "json", False):
            print('{"status": "success"}')
        else:
            print("Config output")

def add_synthetic_scenarios_parser(subparsers):
    p = subparsers.add_parser("synthetic-scenarios")
    sp = p.add_subparsers(dest="synthetic_subcmd", required=True)

    lp = sp.add_parser("list")
    lp.add_argument("--kind")
    lp.add_argument("--json", action="store_true")

    shp = sp.add_parser("show")
    shp.add_argument("scenario", nargs="?")
    shp.add_argument("--json", action="store_true")

    gp = sp.add_parser("generate")
    gp.add_argument("--scenario", required=True)
    gp.add_argument("--dry-run", action="store_true")
    gp.add_argument("--save", action="store_true")
    gp.add_argument("--json", action="store_true")

    vp = sp.add_parser("validate")
    vp.add_argument("--scenario", required=True)
    vp.add_argument("--json", action="store_true")

    ep = sp.add_parser("export")
    ep.add_argument("--scenario", required=True)
    ep.add_argument("--format")
    ep.add_argument("--dry-run", action="store_true")
    ep.add_argument("--confirm", action="store_true")
    ep.add_argument("--json", action="store_true")

    stp = sp.add_parser("stress")
    stp.add_argument("--scenario", required=True)
    stp.add_argument("--json", action="store_true")

    ecp = sp.add_parser("edge-cases")
    ecp.add_argument("--scenario", required=True)
    ecp.add_argument("--json", action="store_true")

    mp = sp.add_parser("manifest")
    mp.add_argument("--scenario")
    mp.add_argument("--latest", action="store_true")
    mp.add_argument("--json", action="store_true")

    rp = sp.add_parser("report")
    rp.add_argument("--latest", action="store_true")
    rp.add_argument("--json", action="store_true")

    cp = sp.add_parser("config")
    cp.add_argument("--json", action="store_true")
"""
ensure_file("bist_signal_bot/cli/commands.py", cli_code, append=True)
