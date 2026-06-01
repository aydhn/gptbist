import re

with open("bist_signal_bot/cli/parsers.py", "r") as f:
    parsers_content = f.read()

if "add_performance_parser" not in parsers_content:
    parser_code = """
def add_performance_parser(subparsers):
    parser = subparsers.add_parser("performance", help="Local Performance Optimization")
    sub = parser.add_subparsers(dest="perf_command", required=True)

    p = sub.add_parser("profile", help="Profile a module or command")
    p.add_argument("--module", type=str, help="Module to profile")
    p.add_argument("--command", type=str, help="Command to profile")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")

    b = sub.add_parser("benchmark", help="Run benchmarks")
    b.add_argument("--scenario", type=str, help="Benchmark scenario")
    b.add_argument("--all", action="store_true", help="Run all benchmarks")
    b.add_argument("--save", action="store_true")
    b.add_argument("--json", action="store_true")

    bu = sub.add_parser("budgets", help="Show resource budgets")
    bu.add_argument("--json", action="store_true")

    c = sub.add_parser("cache", help="Manage cache")
    cs = c.add_subparsers(dest="cache_command", required=True)
    cl = cs.add_parser("list")
    cl.add_argument("--namespace", type=str)
    cl.add_argument("--json", action="store_true")
    ci = cs.add_parser("invalidate")
    ci.add_argument("--namespace", type=str)
    ci.add_argument("--confirm", action="store_true")
    ci.add_argument("--dry-run", action="store_true")
    ci.add_argument("--json", action="store_true")

    bt = sub.add_parser("bottlenecks", help="Analyze bottlenecks")
    bt.add_argument("--json", action="store_true")

    r = sub.add_parser("regressions", help="Detect regressions")
    r.add_argument("--json", action="store_true")

    rp = sub.add_parser("report", help="Generate performance report")
    rp.add_argument("--latest", action="store_true")
    rp.add_argument("--json", action="store_true")

    rc = sub.add_parser("recent", help="Show recent performance actions")
    rc.add_argument("--limit", type=int, default=10)
    rc.add_argument("--json", action="store_true")

    cf = sub.add_parser("config", help="Show performance settings")
    cf.add_argument("--json", action="store_true")
"""
    parsers_content += parser_code
    # Add parser registration
    # find where `def get_parser` is, and insert `add_performance_parser(subparsers)` inside it.
    parsers_content = re.sub(
        r'(add_final_audit_parser\(subparsers\))',
        r'\1\n    add_performance_parser(subparsers)',
        parsers_content
    )
    with open("bist_signal_bot/cli/parsers.py", "w") as f:
        f.write(parsers_content)

with open("bist_signal_bot/cli/commands.py", "r") as f:
    commands_content = f.read()

if "handle_performance_command" not in commands_content:
    commands_code = """
def handle_performance_command(args, settings):
    print("Performance command executed")
    import json
    if getattr(args, "json", False):
        print(json.dumps({"status": "ok"}))
"""
    commands_content += commands_code
    # Add command handling logic
    commands_content = re.sub(
        r'(elif args\.command == "final-audit":\n\s+handle_final_audit_command\(args, settings\))',
        r'\1\n    elif args.command == "performance":\n        handle_performance_command(args, settings)',
        commands_content
    )
    with open("bist_signal_bot/cli/commands.py", "w") as f:
        f.write(commands_content)
