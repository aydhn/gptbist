import argparse
import json
from bist_signal_bot.app.plugins_app import (
    create_plugin_contract_registry, create_plugin_discovery_engine,
    create_safe_plugin_loader, create_plugin_validator, create_plugin_test_harness,
    create_plugin_governance_engine, create_plugin_store, create_plugin_hook_registry
)
from bist_signal_bot.plugins.models import PluginRegistryReport, PluginExecutionMode
from bist_signal_bot.plugins.reporting import format_plugin_registry_report_markdown
from datetime import datetime
from pathlib import Path

def setup_parser(subparsers):
    parser = subparsers.add_parser("plugins", help="Manage local plugins architecture")
    subs = parser.add_subparsers(dest="plugin_command")

    # contracts
    c_parser = subs.add_parser("contracts", help="List plugin contracts")
    c_parser.add_argument("--json", action="store_true", help="Output JSON")

    # discover
    d_parser = subs.add_parser("discover", help="Discover plugins")
    d_parser.add_argument("--dir", help="Specific directory to discover")
    d_parser.add_argument("--json", action="store_true", help="Output JSON")

    # list
    l_parser = subs.add_parser("list", help="List discovered plugins")
    l_parser.add_argument("--kind", help="Filter by kind")
    l_parser.add_argument("--json", action="store_true", help="Output JSON")

    # show
    s_parser = subs.add_parser("show", help="Show plugin details")
    s_parser.add_argument("plugin", help="Plugin ID")
    s_parser.add_argument("--json", action="store_true", help="Output JSON")

    # validate
    v_parser = subs.add_parser("validate", help="Validate plugin")
    v_parser.add_argument("--plugin", help="Plugin ID")
    v_parser.add_argument("--dir", help="Directory path to validate")
    v_parser.add_argument("--json", action="store_true", help="Output JSON")

    # test
    t_parser = subs.add_parser("test", help="Test plugin in dry-run mode")
    t_parser.add_argument("--plugin", required=True, help="Plugin ID")
    t_parser.add_argument("--dry-run", action="store_true", help="Force dry-run")
    t_parser.add_argument("--json", action="store_true", help="Output JSON")

    # load
    load_parser = subs.add_parser("load", help="Load plugin metadata")
    load_parser.add_argument("--plugin", required=True, help="Plugin ID")
    load_parser.add_argument("--metadata-only", action="store_true")
    load_parser.add_argument("--dry-run", action="store_true")
    load_parser.add_argument("--json", action="store_true", help="Output JSON")

    # hooks
    h_parser = subs.add_parser("hooks", help="List hook registrations")
    h_parser.add_argument("--kind", help="Hook kind")
    h_parser.add_argument("--json", action="store_true", help="Output JSON")

    # governance
    g_parser = subs.add_parser("governance", help="Show governance assessment")
    g_parser.add_argument("--plugin", required=True, help="Plugin ID")
    g_parser.add_argument("--json", action="store_true", help="Output JSON")

    # report
    r_parser = subs.add_parser("report", help="Generate plugin registry report")
    r_parser.add_argument("--latest", action="store_true")
    r_parser.add_argument("--json", action="store_true", help="Output JSON")

    # recent
    rc_parser = subs.add_parser("recent", help="List recent plugin activities")
    rc_parser.add_argument("--limit", type=int, default=10)
    rc_parser.add_argument("--json", action="store_true")

    # config
    cfg_parser = subs.add_parser("config", help="Show plugin configuration")
    cfg_parser.add_argument("--json", action="store_true", help="Output JSON")

def get_manifest_by_id(plugin_id):
    engine = create_plugin_discovery_engine()
    manifests = engine.discover()
    for m in manifests:
        if m.plugin_id == plugin_id:
            return m
    return None

def _handle_contracts(args):
    reg = create_plugin_contract_registry()
    contracts = reg.default_contracts()
    if args.json:
        print(json.dumps([c.model_dump(mode='json') for c in contracts], indent=2))
    else:
        for c in contracts:
            print(f"Contract: {c.contract_id} ({c.kind.value}) v{c.version}")

def _handle_discover(args):
    engine = create_plugin_discovery_engine()
    dirs = [Path(args.dir)] if args.dir else None
    manifests = engine.discover(dirs)
    if args.json:
        print(json.dumps([m.model_dump(mode='json') for m in manifests], indent=2))
    else:
        print(f"Discovered {len(manifests)} plugins.")
        for m in manifests:
            print(f"- {m.plugin_id} ({m.kind.value})")

def _handle_list(args):
    engine = create_plugin_discovery_engine()
    manifests = engine.discover()
    if getattr(args, "kind", None):
        manifests = [m for m in manifests if m.kind.value == args.kind]
    if args.json:
        print(json.dumps([m.model_dump(mode='json') for m in manifests], indent=2))
    else:
        for m in manifests:
            print(f"{m.plugin_id} [{m.kind.value}] - Enabled: {m.enabled}")

def _handle_show(args):
    m = get_manifest_by_id(args.plugin)
    if not m:
        print(f"Plugin {args.plugin} not found.")
        return
    if getattr(args, "json", False):
        print(json.dumps(m.model_dump(mode='json'), indent=2))
    else:
        print(f"ID: {m.plugin_id}\nName: {m.name}\nKind: {m.kind.value}\nDescription: {m.description}")

def _handle_validate(args):
    validator = create_plugin_validator()
    if getattr(args, "dir", None):
        from bist_signal_bot.app.plugins_app import create_plugin_manifest_parser
        p = Path(args.dir) / "plugin.json"
        if p.exists():
            m = create_plugin_manifest_parser().parse_manifest(p)
        else:
            print("No plugin.json found in dir.")
            return
    else:
        m = get_manifest_by_id(getattr(args, "plugin", ""))

    if not m:
        print("Plugin not found.")
        return

    res = validator.validate_plugin(m)
    if getattr(args, "json", False):
        print(json.dumps(res.model_dump(mode='json'), indent=2))
    else:
        print(f"Validation for {m.plugin_id}: {res.status.value}")
        for f in res.findings:
            print(f" - {f}")

def _handle_test(args):
    m = get_manifest_by_id(args.plugin)
    if not m:
        print("Plugin not found.")
        return
    harness = create_plugin_test_harness()
    res = harness.run_plugin_tests(m, dry_run=True)
    if getattr(args, "json", False):
        print(json.dumps(res.model_dump(mode='json'), indent=2))
    else:
        print(f"Test Status: {res.status.value} (Passed: {res.tests_passed}, Failed: {res.tests_failed})")

def _handle_load(args):
    m = get_manifest_by_id(args.plugin)
    if not m:
        print("Plugin not found.")
        return
    loader = create_safe_plugin_loader()
    mode = PluginExecutionMode.SAFE_METADATA_ONLY
    if getattr(args, "dry_run", False):
        mode = PluginExecutionMode.DRY_RUN

    res = loader.load_plugin(m, mode=mode)
    if getattr(args, "json", False):
        print(json.dumps(res.model_dump(mode='json'), indent=2))
    else:
        print(f"Load Status: {res.status.value} - {res.execution_mode.value}")

def _handle_hooks(args):
    engine = create_plugin_discovery_engine()
    hook_reg = create_plugin_hook_registry()
    for m in engine.discover():
        hook_reg.register_hooks_from_manifest(m)

    if getattr(args, "kind", None):
        hooks = hook_reg.hooks_for_kind(args.kind) # Actually expects enum but for CLI string is used, will just summarize
        summary = {"count": len(hooks)}
    else:
        summary = hook_reg.hook_summary()

    if getattr(args, "json", False):
        print(json.dumps(summary, indent=2))
    else:
        print(f"Hooks: {summary}")

def _handle_governance(args):
    m = get_manifest_by_id(args.plugin)
    if not m:
        print("Plugin not found.")
        return
    gov = create_plugin_governance_engine()
    res = gov.assess_plugin(m)
    if getattr(args, "json", False):
        print(json.dumps(res.model_dump(mode='json'), indent=2))
    else:
        print(f"Governance Status: {res.status.value}")
        if res.blocked_reasons:
            print("Blocked reasons:")
            for r in res.blocked_reasons:
                print(f" - {r}")

def _handle_report(args):
    engine = create_plugin_discovery_engine()
    gov = create_plugin_governance_engine()
    manifests = engine.discover()

    report = PluginRegistryReport(
        report_id="rep_1",
        generated_at=datetime.now(),
        manifests=manifests,
        governance_assessments=[gov.assess_plugin(m) for m in manifests]
    )

    if getattr(args, "json", False):
        print(json.dumps(report.model_dump(mode='json'), indent=2))
    else:
        print(format_plugin_registry_report_markdown(report))

def _handle_recent(args):
    print(json.dumps([]) if getattr(args, "json", False) else "No recent activity (mock).")

def _handle_config(args):
    from bist_signal_bot.config.settings import get_settings
    s = get_settings()
    cfg = {k: v for k, v in s.__dict__.items() if "PLUGIN" in k}
    if getattr(args, "json", False):
        print(json.dumps(cfg, indent=2))
    else:
        for k, v in cfg.items():
            print(f"{k}: {v}")

def handle(args):
    handlers = {
        "contracts": _handle_contracts,
        "discover": _handle_discover,
        "list": _handle_list,
        "show": _handle_show,
        "validate": _handle_validate,
        "test": _handle_test,
        "load": _handle_load,
        "hooks": _handle_hooks,
        "governance": _handle_governance,
        "report": _handle_report,
        "recent": _handle_recent,
        "config": _handle_config,
    }

    handler = handlers.get(args.plugin_command)
    if handler:
        handler(args)
    else:
        print(f"Unknown plugin command: {args.plugin_command}")

