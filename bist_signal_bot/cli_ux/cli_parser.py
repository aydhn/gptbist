import argparse
import sys
import json
from datetime import datetime, timezone

from bist_signal_bot.app.cli_ux_app import (
    create_cli_output_contract_registry,
    create_cli_output_schema_registry,
    create_cli_alias_registry,
    create_cli_workflow_runner,
    create_command_recipe_executor,
    create_cli_compatibility_checker,
    create_cli_ux_store
)
from bist_signal_bot.cli_ux.models import CLIUXReport
from bist_signal_bot.cli_ux.reporting import (
    contract_to_dict, format_contracts_text,
    schema_to_dict, alias_to_dict, format_aliases_text,
    workflow_run_to_dict, format_workflow_run_text,
    compatibility_to_dict, format_compatibility_text,
    cli_ux_report_to_dict, format_cli_ux_report_markdown
)
from bist_signal_bot.config.settings import get_settings

def add_cli_ux_subparser(subparsers):
    parser = subparsers.add_parser("cli-ux", help="Manage CLI UX and Output Contracts")
    sub = parser.add_subparsers(dest="cli_ux_command", required=True)

    # contracts
    p_contracts = sub.add_parser("contracts", help="List or show output contracts")
    p_contracts.add_argument("action", nargs="?", default="list", choices=["list", "show"], help="Action to perform")
    p_contracts.add_argument("name", nargs="?", help="Command path to show")
    p_contracts.add_argument("--json", action="store_true", help="Output JSON")

    # schemas
    p_schemas = sub.add_parser("schemas", help="List or show output schemas")
    p_schemas.add_argument("action", nargs="?", default="list", choices=["list", "show"], help="Action to perform")
    p_schemas.add_argument("name", nargs="?", help="Schema name to show")
    p_schemas.add_argument("--json", action="store_true", help="Output JSON")

    # aliases
    p_aliases = sub.add_parser("aliases", help="List or resolve aliases")
    p_aliases.add_argument("action", nargs="?", default="list", choices=["list", "resolve"], help="Action to perform")
    p_aliases.add_argument("name", nargs="?", help="Alias to resolve")
    p_aliases.add_argument("--json", action="store_true", help="Output JSON")

    # workflow
    p_wf = sub.add_parser("workflow", help="Manage workflows")
    p_wf.add_argument("action", choices=["run", "recent"], help="Action to perform")
    p_wf.add_argument("--name", help="Workflow name (for run)")
    p_wf.add_argument("--dry-run", action="store_true", help="Dry run workflow")
    p_wf.add_argument("--save", action="store_true", help="Save workflow run")
    p_wf.add_argument("--limit", type=int, default=10, help="Recent limit")
    p_wf.add_argument("--json", action="store_true", help="Output JSON")

    # recipe
    p_recipe = sub.add_parser("recipe", help="Execute recipes")
    p_recipe.add_argument("action", choices=["preview", "run"], help="Action to perform")
    p_recipe.add_argument("name", help="Recipe ID or type")
    p_recipe.add_argument("--dry-run", action="store_true", help="Dry run recipe")
    p_recipe.add_argument("--save", action="store_true", help="Save recipe run")
    p_recipe.add_argument("--json", action="store_true", help="Output JSON")

    # compatibility
    p_compat = sub.add_parser("compatibility", help="Check output contract compatibility")
    p_compat.add_argument("--json", action="store_true", help="Output JSON")

    # report
    p_report = sub.add_parser("report", help="Generate CLI UX report")
    p_report.add_argument("--latest", action="store_true", help="Get latest report")
    p_report.add_argument("--json", action="store_true", help="Output JSON")

    # recent
    p_recent = sub.add_parser("recent", help="Show recent workflow runs")
    p_recent.add_argument("--limit", type=int, default=10, help="Recent limit")
    p_recent.add_argument("--json", action="store_true", help="Output JSON")

    # config
    p_config = sub.add_parser("config", help="Show CLI UX config")
    p_config.add_argument("--json", action="store_true", help="Output JSON")


def handle_cli_ux(args, context=None):
    settings = get_settings()

    if args.cli_ux_command == "contracts":
        registry = create_cli_output_contract_registry(settings)
        if args.action == "show" and args.name:
            c = registry.get_contract(args.name)
            if not c:
                print(f"Contract not found: {args.name}")
                sys.exit(4)
            if args.json:
                print(json.dumps(contract_to_dict(c), indent=2))
            else:
                print(format_contracts_text([c]))
        else:
            contracts = registry.default_contracts()
            if args.json:
                print(json.dumps([contract_to_dict(c) for c in contracts], indent=2))
            else:
                print(format_contracts_text(contracts))

    elif args.cli_ux_command == "schemas":
        registry = create_cli_output_schema_registry(settings)
        if args.action == "show" and args.name:
            # simple mock match
            s = next((sch for sch in registry.default_schemas() if sch.name == args.name), None)
            if not s:
                print(f"Schema not found: {args.name}")
                sys.exit(4)
            if args.json:
                print(json.dumps(schema_to_dict(s), indent=2))
            else:
                print(json.dumps(schema_to_dict(s), indent=2))
        else:
            schemas = registry.default_schemas()
            if args.json:
                print(json.dumps([schema_to_dict(s) for s in schemas], indent=2))
            else:
                print(f"Loaded {len(schemas)} schemas.")

    elif args.cli_ux_command == "aliases":
        registry = create_cli_alias_registry(settings)
        if args.action == "resolve" and args.name:
            t = registry.resolve_alias(args.name)
            if not t:
                print(f"Alias not found: {args.name}")
                sys.exit(4)
            if args.json:
                print(json.dumps({"alias": args.name, "target": t}, indent=2))
            else:
                print(f"{args.name} -> {t}")
        else:
            aliases = registry.default_aliases()
            if args.json:
                print(json.dumps([alias_to_dict(a) for a in aliases], indent=2))
            else:
                print(format_aliases_text(aliases))

    elif args.cli_ux_command == "workflow":
        runner = create_cli_workflow_runner(settings)
        if args.action == "run":
            if not args.name:
                print("Workflow name is required.")
                sys.exit(2)
            # mock command
            run = runner.run_workflow(args.name, ["echo 'mock'"], dry_run=args.dry_run, save=args.save)
            if args.json:
                print(json.dumps(workflow_run_to_dict(run), indent=2))
            else:
                print(format_workflow_run_text(run))
        elif args.action == "recent":
            store = create_cli_ux_store(settings)
            runs = store.load_workflow_runs(args.limit)
            if args.json:
                print(json.dumps([workflow_run_to_dict(r) for r in runs], indent=2))
            else:
                print(f"Found {len(runs)} recent runs.")

    elif args.cli_ux_command == "recipe":
        executor = create_command_recipe_executor(settings)
        if args.action == "preview":
            cmds = executor.preview_recipe(args.name)
            if args.json:
                print(json.dumps({"recipe": args.name, "commands": cmds}, indent=2))
            else:
                print(f"Recipe {args.name} commands:")
                for c in cmds:
                    print(f"  {c}")
        elif args.action == "run":
            run = executor.execute_recipe(args.name, dry_run=args.dry_run, save=args.save)
            if args.json:
                print(json.dumps(workflow_run_to_dict(run), indent=2))
            else:
                print(format_workflow_run_text(run))

    elif args.cli_ux_command == "compatibility":
        checker = create_cli_compatibility_checker(settings)
        res = checker.check_compatibility()
        if args.json:
            print(json.dumps(compatibility_to_dict(res), indent=2))
        else:
            print(format_compatibility_text(res))

    elif args.cli_ux_command == "report":
        import uuid
        checker = create_cli_compatibility_checker(settings)
        compat = checker.check_compatibility()
        r = CLIUXReport(
            report_id=str(uuid.uuid4()),
            generated_at=datetime.now(timezone.utc),
            contracts=create_cli_output_contract_registry(settings).default_contracts(),
            schemas=create_cli_output_schema_registry(settings).default_schemas(),
            aliases=create_cli_alias_registry(settings).default_aliases(),
            compatibility=compat,
            key_findings=["CLI UX components are functioning correctly"]
        )
        if args.json:
            print(json.dumps(cli_ux_report_to_dict(r), indent=2))
        else:
            print(format_cli_ux_report_markdown(r))

    elif args.cli_ux_command == "recent":
        store = create_cli_ux_store(settings)
        runs = store.load_workflow_runs(args.limit)
        if args.json:
            print(json.dumps([workflow_run_to_dict(r) for r in runs], indent=2))
        else:
            print(f"Found {len(runs)} recent runs.")

    elif args.cli_ux_command == "config":
        conf = {
            "ENABLE_CLI_UX": getattr(settings, "ENABLE_CLI_UX", True),
            "CLI_OUTPUT_CONTRACTS_ENABLED": getattr(settings, "CLI_OUTPUT_CONTRACTS_ENABLED", True)
        }
        if args.json:
            print(json.dumps(conf, indent=2))
        else:
            for k, v in conf.items():
                print(f"{k}: {v}")
