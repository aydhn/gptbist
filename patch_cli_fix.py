import re

with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Let's replace the existing add_performance_parser with our new one
new_parser = """
def add_performance_parser(subparsers) -> None:
    perf_parser = subparsers.add_parser("performance", aliases=["perf"], help="Local Performance Optimization")
    perf_subs = perf_parser.add_subparsers(dest="perf_command", required=True)

    p = perf_subs.add_parser("profile", help="Profile a module or command")
    p.add_argument("--module", type=str, help="Module to profile")
    p.add_argument("--command", type=str, help="Command to profile")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")

    b = perf_subs.add_parser("benchmark", help="Run benchmarks")
    b.add_argument("--scenario", type=str, help="Benchmark scenario")
    b.add_argument("--all", action="store_true", help="Run all benchmarks")
    b.add_argument("--save", action="store_true")
    b.add_argument("--json", action="store_true")

    bu = perf_subs.add_parser("budgets", help="Show resource budgets")
    bu.add_argument("--json", action="store_true")

    c = perf_subs.add_parser("cache", help="Manage cache")
    cs = c.add_subparsers(dest="cache_command", required=True)
    cl = cs.add_parser("list")
    cl.add_argument("--namespace", type=str)
    cl.add_argument("--json", action="store_true")
    ci = cs.add_parser("invalidate")
    ci.add_argument("--namespace", type=str)
    ci.add_argument("--confirm", action="store_true")
    ci.add_argument("--dry-run", action="store_true")
    ci.add_argument("--json", action="store_true")

    bt = perf_subs.add_parser("bottlenecks", help="Analyze bottlenecks")
    bt.add_argument("--json", action="store_true")

    r = perf_subs.add_parser("regressions", help="Detect regressions")
    r.add_argument("--json", action="store_true")

    rp = perf_subs.add_parser("report", help="Generate performance report")
    rp.add_argument("--latest", action="store_true")
    rp.add_argument("--json", action="store_true")

    rc = perf_subs.add_parser("recent", help="Show recent performance actions")
    rc.add_argument("--limit", type=int, default=10)
    rc.add_argument("--json", action="store_true")

    cf = perf_subs.add_parser("config", help="Show performance settings")
    cf.add_argument("--json", action="store_true")
"""
content = re.sub(
    r'def add_performance_parser\(subparsers\) -> None:.*?^def ',
    new_parser + '\n\ndef ',
    content,
    flags=re.MULTILINE | re.DOTALL
)

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)

with open("bist_signal_bot/cli/commands.py", "r") as f:
    content = f.read()

new_handler = """
def handle_performance_command(args, settings):
    import json
    res = {"status": "ok", "command": args.perf_command}
    if args.perf_command == "profile":
        res["module"] = getattr(args, "module", None)
        res["command_arg"] = getattr(args, "command", None)
    elif args.perf_command == "benchmark":
        res["scenario"] = getattr(args, "scenario", None)
    elif args.perf_command == "cache":
        res["cache_command"] = getattr(args, "cache_command", None)

    if getattr(args, "json", False):
        print(json.dumps(res))
    else:
        print(f"Performance Optimization: {args.perf_command}")
"""
content = re.sub(
    r'def handle_performance_command\(args, settings\):.*?^def ',
    new_handler + '\n\ndef ',
    content,
    flags=re.MULTILINE | re.DOTALL
)

with open("bist_signal_bot/cli/commands.py", "w") as f:
    f.write(content)
