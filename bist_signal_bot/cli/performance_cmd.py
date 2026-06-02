import argparse
from typing import Any

def setup_performance_parser(subparsers: Any) -> None:
    perf_parser = subparsers.add_parser("performance", help="Performance and optimization tools")
    perf_subs = perf_parser.add_subparsers(dest="perf_cmd")

    prof_cmd = perf_subs.add_parser("profile", help="Profile a module or command")
    prof_cmd.add_argument("--module", help="Module to profile")
    prof_cmd.add_argument("--command", help="Command to profile")
    prof_cmd.add_argument("--dry-run", action="store_true")
    prof_cmd.add_argument("--json", action="store_true")

    bench_cmd = perf_subs.add_parser("benchmark", help="Run performance benchmarks")
    bench_cmd.add_argument("--scenario", help="Scenario to run")
    bench_cmd.add_argument("--all", action="store_true")
    bench_cmd.add_argument("--save", action="store_true")
    bench_cmd.add_argument("--json", action="store_true")

    budgets_cmd = perf_subs.add_parser("budgets", help="Show resource budgets")
    budgets_cmd.add_argument("--json", action="store_true")

    cache_cmd = perf_subs.add_parser("cache", help="Manage local cache")
    cache_subs = cache_cmd.add_subparsers(dest="cache_cmd")
    c_list = cache_subs.add_parser("list")
    c_list.add_argument("--namespace")
    c_list.add_argument("--json", action="store_true")
    c_inv = cache_subs.add_parser("invalidate")
    c_inv.add_argument("--namespace")
    c_inv.add_argument("--dry-run", action="store_true")
    c_inv.add_argument("--confirm", action="store_true")
    c_inv.add_argument("--json", action="store_true")

    bottleneck_cmd = perf_subs.add_parser("bottlenecks", help="Analyze bottlenecks")
    bottleneck_cmd.add_argument("--json", action="store_true")

    regression_cmd = perf_subs.add_parser("regressions", help="Detect performance regressions")
    regression_cmd.add_argument("--json", action="store_true")

    report_cmd = perf_subs.add_parser("report", help="Generate performance report")
    report_cmd.add_argument("--latest", action="store_true")
    report_cmd.add_argument("--json", action="store_true")

    recent_cmd = perf_subs.add_parser("recent", help="Show recent performance data")
    recent_cmd.add_argument("--limit", type=int, default=10)
    recent_cmd.add_argument("--json", action="store_true")

    config_cmd = perf_subs.add_parser("config", help="Show performance config")
    config_cmd.add_argument("--json", action="store_true")

def handle_performance_command(args: Any) -> None:
    print(f"Executing performance command: {args.perf_cmd}")
    # Minimal stub to make CLI commands not crash
