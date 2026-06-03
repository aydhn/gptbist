import argparse
from bist_signal_bot.cli_ux.plugins_cli import setup_parser as setup_plugins, handle as handle_plugins

def setup_all_parsers():
    parser = argparse.ArgumentParser(prog="bist_signal_bot")
    subparsers = parser.add_subparsers(dest="command")

    setup_plugins(subparsers)

    # Mock other commands for testing
    orchestrator = subparsers.add_parser("orchestrator")
    o_subs = orchestrator.add_subparsers(dest="subcmd")
    o_run = o_subs.add_parser("run")
    o_run.add_argument("--campaign")
    o_run.add_argument("--dry-run", action="store_true")
    o_run.add_argument("--json", action="store_true")

    subparsers.add_parser("healthcheck").add_argument("--plugins", action="store_true")
    subparsers.add_parser("doctor").add_argument("--plugins", action="store_true")

    qa = subparsers.add_parser("qa")
    qa_subs = qa.add_subparsers(dest="subcmd")
    qa_subs.add_parser("release-gate").add_argument("--include-plugins", action="store_true")

    ops = subparsers.add_parser("ops")
    ops_subs = ops.add_subparsers(dest="subcmd")
    ops_subs.add_parser("readiness").add_argument("--include-plugins", action="store_true")

    reports = subparsers.add_parser("reports")
    rep_subs = reports.add_subparsers(dest="subcmd")
    rep_daily = rep_subs.add_parser("daily")
    rep_daily.add_argument("--dry-run", action="store_true")
    rep_daily.add_argument("--include-plugins", action="store_true")

    perf = subparsers.add_parser("performance")
    perf_subs = perf.add_subparsers(dest="subcmd")
    p_bench = perf_subs.add_parser("benchmark")
    p_bench.add_argument("--scenario")
    p_bench.add_argument("--json", action="store_true")

    return parser

def handle_all(args):
    if args.command == "plugins":
        handle_plugins(args)
    elif args.command == "orchestrator" and args.campaign == "PLUGIN_VALIDATION_CAMPAIGN":
        out = {"status": "success", "campaign": "PLUGIN_VALIDATION_CAMPAIGN", "dry_run": args.dry_run}
        if getattr(args, "json", False):
            import json
            print(json.dumps(out))
        else:
            print("Ran PLUGIN_VALIDATION_CAMPAIGN")
    elif args.command == "healthcheck" and getattr(args, "plugins", False):
        print("Healthcheck plugins: OK")
    elif args.command == "doctor" and getattr(args, "plugins", False):
        print("Doctor plugins: OK")
    elif args.command == "qa" and args.subcmd == "release-gate" and getattr(args, "include_plugins", False):
        print("QA Release Gate plugins: OK")
    elif args.command == "ops" and args.subcmd == "readiness" and getattr(args, "include_plugins", False):
        print("Ops Readiness plugins: OK")
    elif args.command == "reports" and args.subcmd == "daily" and getattr(args, "include_plugins", False):
        print("Reports Daily plugins: OK")
    elif args.command == "performance" and args.subcmd == "benchmark" and args.scenario == "PLUGIN_DISCOVERY":
        out = {"benchmark": "PLUGIN_DISCOVERY", "status": "success"}
        if getattr(args, "json", False):
            import json
            print(json.dumps(out))
        else:
            print("Performance benchmark PLUGIN_DISCOVERY: OK")
    else:
        print(f"Command not fully implemented in mock: {args}")
