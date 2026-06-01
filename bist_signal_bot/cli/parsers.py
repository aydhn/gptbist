
def add_portfolio_construct_parser(subparsers):
    parser = subparsers.add_parser("portfolio-construct", help="Portfolio Construction Management")
    sub = parser.add_subparsers(dest="pc_command", required=True)

    b = sub.add_parser("build", help="Build a portfolio basket")
    b.add_argument("--symbols", nargs="+", default=[], help="Symbols to include")
    b.add_argument("--method", type=str, default="HYBRID", help="Weighting method")
    b.add_argument("--max-positions", type=int, default=10, help="Max positions")
    b.add_argument("--notional", type=float, default=100000.0, help="Portfolio notional")
    b.add_argument("--json", action="store_true", help="JSON output")

    c = sub.add_parser("compare", help="Compare weighting methods")
    c.add_argument("--symbols", nargs="+", default=[])
    c.add_argument("--methods", nargs="+", default=["EQUAL_WEIGHT", "SCORE_WEIGHTED", "HYBRID"])
    c.add_argument("--json", action="store_true", help="JSON output")

    r = sub.add_parser("rebalance", help="Rebalance simulation")
    r.add_argument("--latest", action="store_true", help="Use latest construction result")
    r.add_argument("--current-weights", type=str, help="Path to current weights CSV/JSON")
    r.add_argument("--json", action="store_true", help="JSON output")

    con = sub.add_parser("constraints", help="Check constraints")
    con.add_argument("--latest", action="store_true", help="Use latest construction result")
    con.add_argument("--json", action="store_true", help="JSON output")

    rb = sub.add_parser("risk-budget", help="Check risk budget")
    rb.add_argument("--latest", action="store_true", help="Use latest construction result")
    rb.add_argument("--json", action="store_true", help="JSON output")

    rep = sub.add_parser("report", help="Show portfolio construction report")
    rep.add_argument("--latest", action="store_true", help="Use latest construction result")
    rep.add_argument("--json", action="store_true", help="JSON output")

    rec = sub.add_parser("recent", help="List recent portfolio constructions")
    rec.add_argument("--limit", type=int, default=10, help="Max items")
    rec.add_argument("--json", action="store_true", help="JSON output")

    cfg = sub.add_parser("config", help="Show portfolio construction config")
    cfg.add_argument("--json", action="store_true", help="JSON output")

from bist_signal_bot.cli.explain import setup_parser as setup_explain_parser

def add_deploy_parser(subparsers):
    deploy_parser = subparsers.add_parser("deploy", help="Manage deployment")
    deploy_subs = deploy_parser.add_subparsers(dest="deploy_subcommand", required=True)

    dp_profiles = deploy_subs.add_parser("profiles")
    dp_profiles.add_argument("--json", action="store_true")

    dp_doctor = deploy_subs.add_parser("doctor")
    dp_doctor.add_argument("--deep", action="store_true")
    dp_doctor.add_argument("--json", action="store_true")

    dp_init = deploy_subs.add_parser("init-dirs")
    dp_init.add_argument("--dry-run", action="store_true")
    dp_init.add_argument("--confirm", action="store_true")
    dp_init.add_argument("--json", action="store_true")

    dp_env = deploy_subs.add_parser("env-template")
    dp_env.add_argument("--profile", type=str, default="RESEARCH_ONLY")
    dp_env.add_argument("--dry-run", action="store_true")
    dp_env.add_argument("--confirm", action="store_true")
    dp_env.add_argument("--output", type=str)

    dp_first = deploy_subs.add_parser("first-run")
    dp_first.add_argument("--profile", type=str, default="RESEARCH_ONLY")
    dp_first.add_argument("--dry-run", action="store_true")
    dp_first.add_argument("--confirm-write", action="store_true")
    dp_first.add_argument("--json", action="store_true")

    dp_smoke = deploy_subs.add_parser("smoke-test")
    dp_smoke.add_argument("--json", action="store_true")

    dp_rb = deploy_subs.add_parser("runbook")
    dp_rb.add_argument("--profile", type=str, default="RESEARCH_ONLY")
    dp_rb.add_argument("--output", type=str)

    dp_plat = deploy_subs.add_parser("platform-commands")
    dp_plat.add_argument("--platform", type=str)
    dp_plat.add_argument("--json", action="store_true")

    dp_latest = deploy_subs.add_parser("latest")
    dp_latest.add_argument("--json", action="store_true")

    dp_cfg = deploy_subs.add_parser("config")
    dp_cfg.add_argument("--json", action="store_true")



def add_data_v2_parser(subparsers):
    data_parser = subparsers.add_parser("data", help="Manage data import, update, freshness, lineage, and health.")
    data_subs = data_parser.add_subparsers(dest="data_command", required=True)

    import_parser = data_subs.add_parser("import", help="Import data from CSV or Parquet")
    import_parser.add_argument("--file", type=str, required=True, help="Path to file")
    import_parser.add_argument("--symbol", type=str, help="Symbol name")
    import_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    import_parser.add_argument("--delimiter", type=str, help="CSV delimiter")
    import_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing data")
    import_parser.add_argument("--json", action="store_true", help="Output JSON")

    update_parser = data_subs.add_parser("update", help="Perform incremental data update")
    update_parser.add_argument("--symbols", type=str, nargs="+", help="Symbols to update")
    update_parser.add_argument("--group", type=str, help="Symbol group to update")
    update_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    update_parser.add_argument("--provider-order", type=str, nargs="+", help="Provider order")
    update_parser.add_argument("--json", action="store_true", help="Output JSON")

    fetch_parser = data_subs.add_parser("fetch-v2", help="Fetch data using V2 router")
    fetch_parser.add_argument("--symbols", type=str, nargs="+", required=True, help="Symbols to fetch")
    fetch_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    fetch_parser.add_argument("--source", type=str, help="Specific provider source")
    fetch_parser.add_argument("--provider-order", type=str, nargs="+", help="Provider order")
    fetch_parser.add_argument("--json", action="store_true", help="Output JSON")

    fresh_parser = data_subs.add_parser("freshness", help="Check data freshness")
    fresh_parser.add_argument("--symbols", type=str, nargs="+", help="Symbols to check")
    fresh_parser.add_argument("--group", type=str, help="Symbol group to check")
    fresh_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    fresh_parser.add_argument("--max-age-hours", type=float, help="Max allowed age in hours")
    fresh_parser.add_argument("--json", action="store_true", help="Output JSON")

    lin_parser = data_subs.add_parser("lineage", help="View data lineage")
    lin_parser.add_argument("--symbol", type=str, help="Filter by symbol")
    lin_parser.add_argument("--json", action="store_true", help="Output JSON")

    ph_parser = data_subs.add_parser("provider-health", help="View provider health")
    ph_parser.add_argument("--json", action="store_true", help="Output JSON")

    comp_parser = data_subs.add_parser("compare", help="Compare data")
    comp_parser.add_argument("symbol", type=str, help="Symbol")
    comp_parser.add_argument("--left", type=str, required=True, help="Left")
    comp_parser.add_argument("--right", type=str, required=True, help="Right")
    comp_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    comp_parser.add_argument("--json", action="store_true", help="Output JSON")

    cfg_parser = data_subs.add_parser("config", help="Show config")
    cfg_parser.add_argument("--json", action="store_true", help="Output JSON")

def add_release_parser(subparsers):


    release_parser = subparsers.add_parser("release", help="Release Manager commands")
    release_subparsers = release_parser.add_subparsers(dest="release_command", help="Release sub-commands")

    check_parser = release_subparsers.add_parser("check", help="Run basic release checks")
    check_parser.add_argument("--profile", type=str, help="Release profile")
    check_parser.add_argument("--no-scenarios", action="store_true", help="Skip scenarios")
    check_parser.add_argument("--json", action="store_true", help="Output JSON")

    readiness_parser = release_subparsers.add_parser("readiness", help="Evaluate release readiness")
    readiness_parser.add_argument("--version", type=str, help="Target version")
    readiness_parser.add_argument("--require-acceptance", action="store_true", help="Require acceptance pass")
    readiness_parser.add_argument("--json", action="store_true", help="Output JSON")

    rehearse_parser = release_subparsers.add_parser("rehearse", help="Run safe launch rehearsal")
    rehearse_parser.add_argument("--profile", type=str, help="Release profile")
    rehearse_parser.add_argument("--json", action="store_true", help="Output JSON")

    candidate_parser = release_subparsers.add_parser("candidate", help="Build release candidate")
    candidate_parser.add_argument("--version", type=str, help="Target version")
    candidate_parser.add_argument("--run-rehearsal", action="store_true", help="Run rehearsal before building")
    candidate_parser.add_argument("--package", action="store_true", help="Build package")
    candidate_parser.add_argument("--confirm", action="store_true", help="Confirm destructive actions")
    candidate_parser.add_argument("--json", action="store_true", help="Output JSON")

    notes_parser = release_subparsers.add_parser("notes", help="Generate release notes")
    notes_parser.add_argument("--version", type=str, help="Target version")
    notes_parser.add_argument("--markdown", action="store_true", help="Output Markdown")
    notes_parser.add_argument("--json", action="store_true", help="Output JSON")

    compat_parser = release_subparsers.add_parser("compatibility", help="Run compatibility checks")
    compat_parser.add_argument("--json", action="store_true", help="Output JSON")

    recent_parser = release_subparsers.add_parser("recent", help="List recent release runs")
    recent_parser.add_argument("--limit", type=int, default=10, help="Max number of runs to list")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON")

    status_parser = release_subparsers.add_parser("status", help="Show current release status")
    status_parser.add_argument("--json", action="store_true", help="Output JSON")

    config_parser = release_subparsers.add_parser("config", help="Show release configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON")


def add_release_parser(subparsers):

    release_parser = subparsers.add_parser("release", help="Release Manager commands")
    release_subparsers = release_parser.add_subparsers(dest="release_command", help="Release sub-commands")

    check_parser = release_subparsers.add_parser("check", help="Run basic release checks")
    check_parser.add_argument("--profile", type=str, help="Release profile")
    check_parser.add_argument("--no-scenarios", action="store_true", help="Skip scenarios")
    check_parser.add_argument("--json", action="store_true", help="Output JSON")

    readiness_parser = release_subparsers.add_parser("readiness", help="Evaluate release readiness")
    readiness_parser.add_argument("--version", type=str, help="Target version")
    readiness_parser.add_argument("--require-acceptance", action="store_true", help="Require acceptance pass")
    readiness_parser.add_argument("--json", action="store_true", help="Output JSON")

    rehearse_parser = release_subparsers.add_parser("rehearse", help="Run safe launch rehearsal")
    rehearse_parser.add_argument("--profile", type=str, help="Release profile")
    rehearse_parser.add_argument("--json", action="store_true", help="Output JSON")

    candidate_parser = release_subparsers.add_parser("candidate", help="Build release candidate")
    candidate_parser.add_argument("--version", type=str, help="Target version")
    candidate_parser.add_argument("--run-rehearsal", action="store_true", help="Run rehearsal before building")
    candidate_parser.add_argument("--package", action="store_true", help="Build package")
    candidate_parser.add_argument("--confirm", action="store_true", help="Confirm destructive actions")
    candidate_parser.add_argument("--json", action="store_true", help="Output JSON")

    notes_parser = release_subparsers.add_parser("notes", help="Generate release notes")
    notes_parser.add_argument("--version", type=str, help="Target version")
    notes_parser.add_argument("--markdown", action="store_true", help="Output Markdown")
    notes_parser.add_argument("--json", action="store_true", help="Output JSON")

    compat_parser = release_subparsers.add_parser("compatibility", help="Run compatibility checks")
    compat_parser.add_argument("--json", action="store_true", help="Output JSON")

    recent_parser = release_subparsers.add_parser("recent", help="List recent release runs")
    recent_parser.add_argument("--limit", type=int, default=10, help="Max number of runs to list")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON")

    status_parser = release_subparsers.add_parser("status", help="Show current release status")
    status_parser.add_argument("--json", action="store_true", help="Output JSON")

    config_parser = release_subparsers.add_parser("config", help="Show release configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON")


def add_release_parser(subparsers):

    release_parser = subparsers.add_parser("release", help="Release Manager commands")
    release_subparsers = release_parser.add_subparsers(dest="release_command", help="Release sub-commands")

    check_parser = release_subparsers.add_parser("check", help="Run basic release checks")
    check_parser.add_argument("--profile", type=str, help="Release profile")
    check_parser.add_argument("--no-scenarios", action="store_true", help="Skip scenarios")
    check_parser.add_argument("--json", action="store_true", help="Output JSON")

    readiness_parser = release_subparsers.add_parser("readiness", help="Evaluate release readiness")
    readiness_parser.add_argument("--version", type=str, help="Target version")
    readiness_parser.add_argument("--require-acceptance", action="store_true", help="Require acceptance pass")
    readiness_parser.add_argument("--json", action="store_true", help="Output JSON")

    rehearse_parser = release_subparsers.add_parser("rehearse", help="Run safe launch rehearsal")
    rehearse_parser.add_argument("--profile", type=str, help="Release profile")
    rehearse_parser.add_argument("--json", action="store_true", help="Output JSON")

    candidate_parser = release_subparsers.add_parser("candidate", help="Build release candidate")
    candidate_parser.add_argument("--version", type=str, help="Target version")
    candidate_parser.add_argument("--run-rehearsal", action="store_true", help="Run rehearsal before building")
    candidate_parser.add_argument("--package", action="store_true", help="Build package")
    candidate_parser.add_argument("--confirm", action="store_true", help="Confirm destructive actions")
    candidate_parser.add_argument("--json", action="store_true", help="Output JSON")

    notes_parser = release_subparsers.add_parser("notes", help="Generate release notes")
    notes_parser.add_argument("--version", type=str, help="Target version")
    notes_parser.add_argument("--markdown", action="store_true", help="Output Markdown")
    notes_parser.add_argument("--json", action="store_true", help="Output JSON")

    compat_parser = release_subparsers.add_parser("compatibility", help="Run compatibility checks")
    compat_parser.add_argument("--json", action="store_true", help="Output JSON")

    recent_parser = release_subparsers.add_parser("recent", help="List recent release runs")
    recent_parser.add_argument("--limit", type=int, default=10, help="Max number of runs to list")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON")

    status_parser = release_subparsers.add_parser("status", help="Show current release status")
    status_parser.add_argument("--json", action="store_true", help="Output JSON")

    config_parser = release_subparsers.add_parser("config", help="Show release configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON")


def add_release_parser(subparsers):

    release_parser = subparsers.add_parser("release", help="Release Manager commands")
    release_subparsers = release_parser.add_subparsers(dest="release_command", help="Release sub-commands")

    check_parser = release_subparsers.add_parser("check", help="Run basic release checks")
    check_parser.add_argument("--profile", type=str, help="Release profile")
    check_parser.add_argument("--no-scenarios", action="store_true", help="Skip scenarios")
    check_parser.add_argument("--json", action="store_true", help="Output JSON")

    readiness_parser = release_subparsers.add_parser("readiness", help="Evaluate release readiness")
    readiness_parser.add_argument("--version", type=str, help="Target version")
    readiness_parser.add_argument("--require-acceptance", action="store_true", help="Require acceptance pass")
    readiness_parser.add_argument("--json", action="store_true", help="Output JSON")

    rehearse_parser = release_subparsers.add_parser("rehearse", help="Run safe launch rehearsal")
    rehearse_parser.add_argument("--profile", type=str, help="Release profile")
    rehearse_parser.add_argument("--json", action="store_true", help="Output JSON")

    candidate_parser = release_subparsers.add_parser("candidate", help="Build release candidate")
    candidate_parser.add_argument("--version", type=str, help="Target version")
    candidate_parser.add_argument("--run-rehearsal", action="store_true", help="Run rehearsal before building")
    candidate_parser.add_argument("--package", action="store_true", help="Build package")
    candidate_parser.add_argument("--confirm", action="store_true", help="Confirm destructive actions")
    candidate_parser.add_argument("--json", action="store_true", help="Output JSON")

    notes_parser = release_subparsers.add_parser("notes", help="Generate release notes")
    notes_parser.add_argument("--version", type=str, help="Target version")
    notes_parser.add_argument("--markdown", action="store_true", help="Output Markdown")
    notes_parser.add_argument("--json", action="store_true", help="Output JSON")

    compat_parser = release_subparsers.add_parser("compatibility", help="Run compatibility checks")
    compat_parser.add_argument("--json", action="store_true", help="Output JSON")

    recent_parser = release_subparsers.add_parser("recent", help="List recent release runs")
    recent_parser.add_argument("--limit", type=int, default=10, help="Max number of runs to list")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON")

    status_parser = release_subparsers.add_parser("status", help="Show current release status")
    status_parser.add_argument("--json", action="store_true", help="Output JSON")

    config_parser = release_subparsers.add_parser("config", help="Show release configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON")


def add_release_parser(subparsers):

    release_parser = subparsers.add_parser("release", help="Release Manager commands")
    release_subparsers = release_parser.add_subparsers(dest="release_command", help="Release sub-commands")

    check_parser = release_subparsers.add_parser("check", help="Run basic release checks")
    check_parser.add_argument("--profile", type=str, help="Release profile")
    check_parser.add_argument("--no-scenarios", action="store_true", help="Skip scenarios")
    check_parser.add_argument("--json", action="store_true", help="Output JSON")

    readiness_parser = release_subparsers.add_parser("readiness", help="Evaluate release readiness")
    readiness_parser.add_argument("--version", type=str, help="Target version")
    readiness_parser.add_argument("--require-acceptance", action="store_true", help="Require acceptance pass")
    readiness_parser.add_argument("--json", action="store_true", help="Output JSON")

    rehearse_parser = release_subparsers.add_parser("rehearse", help="Run safe launch rehearsal")
    rehearse_parser.add_argument("--profile", type=str, help="Release profile")
    rehearse_parser.add_argument("--json", action="store_true", help="Output JSON")

    candidate_parser = release_subparsers.add_parser("candidate", help="Build release candidate")
    candidate_parser.add_argument("--version", type=str, help="Target version")
    candidate_parser.add_argument("--run-rehearsal", action="store_true", help="Run rehearsal before building")
    candidate_parser.add_argument("--package", action="store_true", help="Build package")
    candidate_parser.add_argument("--confirm", action="store_true", help="Confirm destructive actions")
    candidate_parser.add_argument("--json", action="store_true", help="Output JSON")

    notes_parser = release_subparsers.add_parser("notes", help="Generate release notes")
    notes_parser.add_argument("--version", type=str, help="Target version")
    notes_parser.add_argument("--markdown", action="store_true", help="Output Markdown")
    notes_parser.add_argument("--json", action="store_true", help="Output JSON")

    compat_parser = release_subparsers.add_parser("compatibility", help="Run compatibility checks")
    compat_parser.add_argument("--json", action="store_true", help="Output JSON")

    recent_parser = release_subparsers.add_parser("recent", help="List recent release runs")
    recent_parser.add_argument("--limit", type=int, default=10, help="Max number of runs to list")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON")

    status_parser = release_subparsers.add_parser("status", help="Show current release status")
    status_parser.add_argument("--json", action="store_true", help="Output JSON")

    config_parser = release_subparsers.add_parser("config", help="Show release configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON")

import argparse

def add_portfolio_construct_parser(subparsers):
    parser = subparsers.add_parser("portfolio-construct", help="Portfolio Construction Management")
    sub = parser.add_subparsers(dest="pc_command", required=True)

    b = sub.add_parser("build", help="Build a portfolio basket")
    b.add_argument("--symbols", nargs="+", default=[], help="Symbols to include")
    b.add_argument("--method", type=str, default="HYBRID", help="Weighting method")
    b.add_argument("--max-positions", type=int, default=10, help="Max positions")
    b.add_argument("--notional", type=float, default=100000.0, help="Portfolio notional")
    b.add_argument("--json", action="store_true", help="JSON output")

    c = sub.add_parser("compare", help="Compare weighting methods")
    c.add_argument("--symbols", nargs="+", default=[])
    c.add_argument("--methods", nargs="+", default=["EQUAL_WEIGHT", "SCORE_WEIGHTED", "HYBRID"])
    c.add_argument("--json", action="store_true", help="JSON output")

    r = sub.add_parser("rebalance", help="Rebalance simulation")
    r.add_argument("--latest", action="store_true", help="Use latest construction result")
    r.add_argument("--current-weights", type=str, help="Path to current weights CSV/JSON")
    r.add_argument("--json", action="store_true", help="JSON output")

    con = sub.add_parser("constraints", help="Check constraints")
    con.add_argument("--latest", action="store_true", help="Use latest construction result")
    con.add_argument("--json", action="store_true", help="JSON output")

    rb = sub.add_parser("risk-budget", help="Check risk budget")
    rb.add_argument("--latest", action="store_true", help="Use latest construction result")
    rb.add_argument("--json", action="store_true", help="JSON output")

    rep = sub.add_parser("report", help="Show portfolio construction report")
    rep.add_argument("--latest", action="store_true", help="Use latest construction result")
    rep.add_argument("--json", action="store_true", help="JSON output")

    rec = sub.add_parser("recent", help="List recent portfolio constructions")
    rec.add_argument("--limit", type=int, default=10, help="Max items")
    rec.add_argument("--json", action="store_true", help="JSON output")

    cfg = sub.add_parser("config", help="Show portfolio construction config")
    cfg.add_argument("--json", action="store_true", help="JSON output")


def add_portfolio_construct_parser(subparsers):
    parser = subparsers.add_parser("portfolio-construct", help="Portfolio Construction Management")
    sub = parser.add_subparsers(dest="pc_command", required=True)

    b = sub.add_parser("build", help="Build a portfolio basket")
    b.add_argument("--symbols", nargs="+", default=[], help="Symbols to include")
    b.add_argument("--method", type=str, default="HYBRID", help="Weighting method")
    b.add_argument("--max-positions", type=int, default=10, help="Max positions")
    b.add_argument("--notional", type=float, default=100000.0, help="Portfolio notional")
    b.add_argument("--json", action="store_true", help="JSON output")

    c = sub.add_parser("compare", help="Compare weighting methods")
    c.add_argument("--symbols", nargs="+", default=[])
    c.add_argument("--methods", nargs="+", default=["EQUAL_WEIGHT", "SCORE_WEIGHTED", "HYBRID"])
    c.add_argument("--json", action="store_true", help="JSON output")

    r = sub.add_parser("rebalance", help="Rebalance simulation")
    r.add_argument("--latest", action="store_true", help="Use latest construction result")
    r.add_argument("--current-weights", type=str, help="Path to current weights CSV/JSON")
    r.add_argument("--json", action="store_true", help="JSON output")

    con = sub.add_parser("constraints", help="Check constraints")
    con.add_argument("--latest", action="store_true", help="Use latest construction result")
    con.add_argument("--json", action="store_true", help="JSON output")

    rb = sub.add_parser("risk-budget", help="Check risk budget")
    rb.add_argument("--latest", action="store_true", help="Use latest construction result")
    rb.add_argument("--json", action="store_true", help="JSON output")

    rep = sub.add_parser("report", help="Show portfolio construction report")
    rep.add_argument("--latest", action="store_true", help="Use latest construction result")
    rep.add_argument("--json", action="store_true", help="JSON output")

    rec = sub.add_parser("recent", help="List recent portfolio constructions")
    rec.add_argument("--limit", type=int, default=10, help="Max items")
    rec.add_argument("--json", action="store_true", help="JSON output")

    cfg = sub.add_parser("config", help="Show portfolio construction config")
    cfg.add_argument("--json", action="store_true", help="JSON output")



def add_portfolio_construct_parser(subparsers):
    parser = subparsers.add_parser("portfolio-construct", help="Portfolio Construction Management")
    sub = parser.add_subparsers(dest="pc_command", required=True)

    b = sub.add_parser("build", help="Build a portfolio basket")
    b.add_argument("--symbols", nargs="+", default=[], help="Symbols to include")
    b.add_argument("--method", type=str, default="HYBRID", help="Weighting method")
    b.add_argument("--max-positions", type=int, default=10, help="Max positions")
    b.add_argument("--notional", type=float, default=100000.0, help="Portfolio notional")
    b.add_argument("--json", action="store_true", help="JSON output")

    c = sub.add_parser("compare", help="Compare weighting methods")
    c.add_argument("--symbols", nargs="+", default=[])
    c.add_argument("--methods", nargs="+", default=["EQUAL_WEIGHT", "SCORE_WEIGHTED", "HYBRID"])
    c.add_argument("--json", action="store_true", help="JSON output")

    r = sub.add_parser("rebalance", help="Rebalance simulation")
    r.add_argument("--latest", action="store_true", help="Use latest construction result")
    r.add_argument("--current-weights", type=str, help="Path to current weights CSV/JSON")
    r.add_argument("--json", action="store_true", help="JSON output")

    con = sub.add_parser("constraints", help="Check constraints")
    con.add_argument("--latest", action="store_true", help="Use latest construction result")
    con.add_argument("--json", action="store_true", help="JSON output")

    rb = sub.add_parser("risk-budget", help="Check risk budget")
    rb.add_argument("--latest", action="store_true", help="Use latest construction result")
    rb.add_argument("--json", action="store_true", help="JSON output")

    rep = sub.add_parser("report", help="Show portfolio construction report")
    rep.add_argument("--latest", action="store_true", help="Use latest construction result")
    rep.add_argument("--json", action="store_true", help="JSON output")

    rec = sub.add_parser("recent", help="List recent portfolio constructions")
    rec.add_argument("--limit", type=int, default=10, help="Max items")
    rec.add_argument("--json", action="store_true", help="JSON output")

    cfg = sub.add_parser("config", help="Show portfolio construction config")
    cfg.add_argument("--json", action="store_true", help="JSON output")


from bist_signal_bot.cli.ensemble_commands import setup_ensemble_parser
from bist_signal_bot.cli.stress_cmd import add_stress_parsers

def add_costs_parser(subparsers):
    costs_parser = subparsers.add_parser(
        "costs",
        help="Estimate transaction costs, slippage, and spread."
    )
    costs_subparsers = costs_parser.add_subparsers(dest="costs_command", required=True)

    estimate_parser = costs_subparsers.add_parser("estimate", help="Estimate transaction cost for a single trade.")
    estimate_parser.add_argument("symbol", type=str, help="Symbol to estimate cost for (e.g. ASELS)")
    estimate_parser.add_argument("--side", type=str, required=True, choices=["BUY", "SELL"], help="Order side")
    estimate_parser.add_argument("--quantity", type=float, required=True, help="Quantity of shares")
    estimate_parser.add_argument("--price", type=float, required=True, help="Price per share")
    estimate_parser.add_argument("--avg-daily-volume", type=float, dest="avg_daily_volume", help="Average daily volume for slippage calculation")
    estimate_parser.add_argument("--avg-daily-turnover", type=float, dest="avg_daily_turnover", help="Average daily turnover for spread bucket calculation")
    estimate_parser.add_argument("--volatility", type=float, help="Volatility for slippage calculation")
    estimate_parser.add_argument("--scenario", type=str, choices=["OPTIMISTIC", "BASE", "CONSERVATIVE", "STRESS"], help="Cost scenario to use")
    estimate_parser.add_argument("--json", action="store_true", help="Output result as JSON")

    round_trip_parser = costs_subparsers.add_parser("round-trip", help="Estimate total round trip cost for an entry and exit.")
    round_trip_parser.add_argument("symbol", type=str, help="Symbol to estimate cost for (e.g. ASELS)")
    round_trip_parser.add_argument("--side", type=str, required=True, choices=["BUY", "SELL"], help="Entry order side")
    round_trip_parser.add_argument("--quantity", type=float, required=True, help="Quantity of shares")
    round_trip_parser.add_argument("--entry-price", type=float, dest="entry_price", required=True, help="Entry price per share")
    round_trip_parser.add_argument("--exit-price", type=float, dest="exit_price", required=True, help="Exit price per share")
    round_trip_parser.add_argument("--scenario", type=str, choices=["OPTIMISTIC", "BASE", "CONSERVATIVE", "STRESS"], help="Cost scenario to use")
    round_trip_parser.add_argument("--json", action="store_true", help="Output result as JSON")

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", None) is None:
        args.command = "healthcheck"
        args.json = False
        args.verbose = False
    return args

def add_backtest_parser(subparsers):
    add_optimize_parser(subparsers)
    parser_backtest = subparsers.add_parser("backtest", help="Backtest engine operations")
    backtest_subparsers = parser_backtest.add_subparsers(dest="backtest_cmd", required=True)

    # backtest run
    run_parser = backtest_subparsers.add_parser("run", help="Run backtest on a single symbol")
    run_parser.add_argument("symbol", type=str, help="Symbol to run backtest for")
    run_parser.add_argument("--strategy", type=str, required=True, help="Strategy name")
    run_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    run_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g., 1d)")
    run_parser.add_argument("--period", type=str, help="History period")
    run_parser.add_argument("--rows", type=int, help="Rows for mock data")
    run_parser.add_argument("--param", type=str, action="append", help="Strategy parameters")
    run_parser.add_argument("--initial-capital", type=float, help="Initial capital")
    run_parser.add_argument("--execution", type=str, choices=["NEXT_OPEN", "NEXT_CLOSE", "SAME_CLOSE_FOR_RESEARCH_ONLY"], help="Execution mode")
    run_parser.add_argument("--cost-scenario", type=str, choices=["OPTIMISTIC", "BASE", "CONSERVATIVE", "STRESS"], help="Cost scenario")
    run_parser.add_argument("--max-position-size-pct", type=float, help="Max position size percentage")
    run_parser.add_argument("--allow-short", action="store_true", help="Allow short trades")
    run_parser.add_argument("--no-costs", action="store_true", help="Disable commission and slippage")
    run_parser.add_argument("--save-results", action="store_true", help="Save backtest results")
    run_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    run_parser.add_argument("--use-risk-engine", action="store_true", help="Use risk engine")

    # backtest batch
    batch_parser = backtest_subparsers.add_parser("batch", help="Run backtest on multiple symbols")
    batch_parser.add_argument("--strategy", type=str, required=True, help="Strategy name")

    group = batch_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbols", type=str, nargs="+", help="List of symbols")
    group.add_argument("--all", action="store_true", help="Run on all symbols")
    group.add_argument("--group", type=str, help="Run on symbol group")

    batch_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    batch_parser.add_argument("--param", type=str, action="append", help="Strategy parameters")
    batch_parser.add_argument("--initial-capital", type=float, help="Initial capital")
    batch_parser.add_argument("--execution", type=str, choices=["NEXT_OPEN", "NEXT_CLOSE", "SAME_CLOSE_FOR_RESEARCH_ONLY"], help="Execution mode")
    batch_parser.add_argument("--cost-scenario", type=str, choices=["OPTIMISTIC", "BASE", "CONSERVATIVE", "STRESS"], help="Cost scenario")
    batch_parser.add_argument("--max-position-size-pct", type=float, help="Max position size percentage")
    batch_parser.add_argument("--allow-short", action="store_true", help="Allow short trades")
    batch_parser.add_argument("--no-costs", action="store_true", help="Disable commission and slippage")
    batch_parser.add_argument("--save-results", action="store_true", help="Save backtest results")
    batch_parser.add_argument("--json", action="store_true", help="Output in JSON format")

def add_validate_backtest_parser(subparsers):
    validate_parser = subparsers.add_parser("validate-backtest", help="Walk-forward analysis, robustness, and out-of-sample testing")
    validate_subparsers = validate_parser.add_subparsers(dest="validate_command", required=True)

    # train-test
    train_test_parser = validate_subparsers.add_parser("train-test", help="Run a single train/test split backtest")
    train_test_parser.add_argument("symbol", type=str, help="Symbol to test")
    train_test_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    train_test_parser.add_argument("--strategy", type=str, required=True, help="Strategy to test")
    train_test_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    train_test_parser.add_argument("--period", type=str, help="History period")
    train_test_parser.add_argument("--rows", type=int, help="Rows for mock data")
    train_test_parser.add_argument("--train-ratio", type=float, help="Train ratio (e.g. 0.7)")
    train_test_parser.add_argument("--compare-benchmark", type=str, help="Benchmark to compare against")
    train_test_parser.add_argument("--param", action="append", help="Strategy parameter key=value")
    train_test_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # walk-forward
    wf_parser = validate_subparsers.add_parser("walk-forward", help="Run walk-forward cross-validation")
    wf_parser.add_argument("symbol", type=str, help="Symbol to test")
    wf_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    wf_parser.add_argument("--strategy", type=str, required=True, help="Strategy to test")
    wf_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    wf_parser.add_argument("--period", type=str, help="History period")
    wf_parser.add_argument("--rows", type=int, help="Rows for mock data")
    wf_parser.add_argument("--train-window", type=int, help="Train window rows")
    wf_parser.add_argument("--test-window", type=int, help="Test window rows")
    wf_parser.add_argument("--step", type=int, help="Step rows")
    wf_parser.add_argument("--expanding", action="store_true", help="Use expanding window")
    wf_parser.add_argument("--max-splits", type=int, help="Maximum number of splits")
    wf_parser.add_argument("--save-report", action="store_true", help="Save reports to disk")
    wf_parser.add_argument("--format", type=str, choices=["json", "markdown", "csv", "all"], help="Report format to save")
    wf_parser.add_argument("--param", action="append", help="Strategy parameter key=value")
    wf_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # robustness
    rob_parser = validate_subparsers.add_parser("robustness", help="Run parameter robustness test")
    rob_parser.add_argument("symbol", type=str, help="Symbol to test")
    rob_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    rob_parser.add_argument("--strategy", type=str, required=True, help="Strategy to test")
    rob_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    rob_parser.add_argument("--period", type=str, help="History period")
    rob_parser.add_argument("--rows", type=int, help="Rows for mock data")
    rob_parser.add_argument("--param-range", action="append", required=True, help="Parameter range: name=val1,val2,val3")
    rob_parser.add_argument("--max-runs", type=int, help="Maximum number of robustness runs")
    rob_parser.add_argument("--json", action="store_true", help="Output in JSON format")


def add_telegram_center_parser(subparsers):
    add_disclosures_parser(subparsers)
    parser = subparsers.add_parser('telegram-center', help='Manage Telegram Command Center')
    subs = parser.add_subparsers(dest='telegram_subcommand', required=True)

    config_p = subs.add_parser('config', help='Show Telegram Center configuration summary')
    config_p.add_argument('--json', action='store_true', help='Output in JSON format')

    dry_run_p = subs.add_parser('dry-run', help='Simulate a Telegram command locally')
    dry_run_p.add_argument('command', help='The command text (e.g. "/status")')
    dry_run_p.add_argument('--json', action='store_true', help='Output in JSON format')

    route_p = subs.add_parser('route', help='Route a Telegram command')
    route_p.add_argument('command', help='The command text')
    route_p.add_argument('--chat-id', required=True, help='The origin chat ID')
    route_p.add_argument('--dry-run', action='store_true', help='Do not actually send response')
    route_p.add_argument('--json', action='store_true', help='Output in JSON format')

    inbox_p = subs.add_parser('inbox', help='Manage notification inbox')
    inbox_p.add_argument('--status', help='Filter by status (PENDING, SENT, FAILED, MUTED)')
    inbox_p.add_argument('--json', action='store_true', help='Output in JSON format')

    digest_p = subs.add_parser('digest', help='Generate and optionally send a digest')
    digest_p.add_argument('type', choices=['daily', 'weekly', 'runtime'], help='Digest type')
    digest_p.add_argument('--dry-run', action='store_true', help='Do not send, only generate')
    digest_p.add_argument('--json', action='store_true', help='Output in JSON format')

    test_p = subs.add_parser('send-test', help='Send a test message')
    test_p.add_argument('--dry-run', action='store_true')
    test_p.add_argument('--confirm', action='store_true')

    retry_p = subs.add_parser('retry-failed', help='Retry failed notifications')
    retry_p.add_argument('--limit', type=int, default=10)
    retry_p.add_argument('--dry-run', action='store_true')
    retry_p.add_argument('--json', action='store_true')

    recent_p = subs.add_parser('recent-commands', help='Show recently received commands')
    recent_p.add_argument('--limit', type=int, default=20)
    recent_p.add_argument('--json', action='store_true')

def add_signals_parser(subparsers):
    signals_parser = subparsers.add_parser("signals", help="Manage signal lifecycle and watchlist")
    signals_subparsers = signals_parser.add_subparsers(dest="signals_cmd", help="Signals sub-commands")

    list_p = signals_subparsers.add_parser("list", help="List tracked signals")
    list_p.add_argument("--state", type=str, help="Filter by state (e.g. ACTIVE, EXPIRED)")
    list_p.add_argument("--symbol", type=str, help="Filter by symbol")
    list_p.add_argument("--strategy", type=str, help="Filter by strategy")
    list_p.add_argument("--json", action="store_true", help="Output JSON")

    show_p = signals_subparsers.add_parser("show", help="Show signal details")
    show_p.add_argument("signal_id", type=str, help="Signal ID")
    show_p.add_argument("--events", action="store_true", help="Show lifecycle events")
    show_p.add_argument("--json", action="store_true", help="Output JSON")

    exp_p = signals_subparsers.add_parser("expire", help="Expire stale signals")
    exp_p.add_argument("--json", action="store_true", help="Output JSON")

    inv_p = signals_subparsers.add_parser("invalidate", help="Invalidate a signal manually")
    inv_p.add_argument("signal_id", type=str, help="Signal ID")
    inv_p.add_argument("--reason", type=str, required=True, help="Reason for invalidation")
    inv_p.add_argument("--confirm", action="store_true", help="Confirm invalidation")

    arc_p = signals_subparsers.add_parser("archive", help="Archive a signal manually")
    arc_p.add_argument("signal_id", type=str, help="Signal ID")
    arc_p.add_argument("--confirm", action="store_true", help="Confirm archive")

    wl_p = signals_subparsers.add_parser("watchlist", help="Show active watchlist")
    wl_p.add_argument("--symbol", type=str, help="Filter by symbol")
    wl_p.add_argument("--json", action="store_true", help="Output JSON")

    wla_p = signals_subparsers.add_parser("watchlist-add", help="Add a signal to watchlist")
    wla_p.add_argument("signal_id", type=str, help="Signal ID")
    wla_p.add_argument("--tag", type=str, help="Tag for watchlist entry")
    wla_p.add_argument("--confirm", action="store_true", help="Confirm add")

    wlr_p = signals_subparsers.add_parser("watchlist-remove", help="Remove from watchlist")
    wlr_p.add_argument("watchlist_id", type=str, help="Watchlist entry ID")
    wlr_p.add_argument("--confirm", action="store_true", help="Confirm remove")

    dedupe_p = signals_subparsers.add_parser("dedupe", help="Check signal deduplication")
    dedupe_p.add_argument("--symbol", type=str, required=True, help="Symbol to dedupe check")
    dedupe_p.add_argument("--json", action="store_true", help="Output JSON")

    sim_p = signals_subparsers.add_parser("simulate-exits", help="Simulate research exits")
    sim_p.add_argument("--symbol", type=str, help="Symbol to simulate")
    sim_p.add_argument("--state", type=str, help="State filter (e.g. ACTIVE)")
    sim_p.add_argument("--source", type=str, default="local_file", help="Data source")
    sim_p.add_argument("--json", action="store_true", help="Output JSON")

    out_p = signals_subparsers.add_parser("outcomes", help="Show signal outcomes")
    out_p.add_argument("--symbol", type=str, help="Filter by symbol")
    out_p.add_argument("--strategy", type=str, help="Filter by strategy")
    out_p.add_argument("--json", action="store_true", help="Output JSON")

    out_up_p = signals_subparsers.add_parser("outcome-update", help="Update manual outcome")
    out_up_p.add_argument("signal_id", type=str, help="Signal ID")
    out_up_p.add_argument("--outcome", type=str, required=True, help="Outcome state (e.g. HIT_RESEARCH_TARGET)")
    out_up_p.add_argument("--return-pct", type=float, help="Return percentage")
    out_up_p.add_argument("--confirm", action="store_true", help="Confirm update")

    sum_p = signals_subparsers.add_parser("summary", help="Show lifecycle summary")
    sum_p.add_argument("--json", action="store_true", help="Output JSON")

    pol_p = signals_subparsers.add_parser("policy", help="Show active alert policy")
    pol_p.add_argument("--json", action="store_true", help="Output JSON")

    cfg_p = signals_subparsers.add_parser("config", help="Show signals configuration")
    cfg_p.add_argument("--json", action="store_true", help="Output JSON")


def add_lab_parser(subparsers):
    lab_parser = subparsers.add_parser("lab", help="Research Lab automation (queue, batch, jobs)")
    lab_subs = lab_parser.add_subparsers(dest="lab_command", required=True)

    plan_parser = lab_subs.add_parser("plan", help="Generate a research batch plan")
    plan_parser.add_argument("plan_type", choices=["daily", "weekly", "adaptive", "drift"], help="Type of plan to generate")
    plan_parser.add_argument("--symbols", nargs="+", help="Symbols to include")
    plan_parser.add_argument("--strategies", nargs="+", help="Strategies to include")
    plan_parser.add_argument("--from-latest", action="store_true", help="Use latest adaptive/drift state")
    plan_parser.add_argument("--json", action="store_true", help="Output JSON")

    enqueue_parser = lab_subs.add_parser("enqueue", help="Enqueue jobs")
    enqueue_parser.add_argument("--plan", help="Plan ID to enqueue")
    enqueue_parser.add_argument("--job", help="Single job type to enqueue")
    enqueue_parser.add_argument("--symbol", help="Symbol for single job")
    enqueue_parser.add_argument("--strategy", help="Strategy for single job")
    enqueue_parser.add_argument("--json", action="store_true", help="Output JSON")

    run_parser = lab_subs.add_parser("run", help="Run batch jobs")
    run_parser.add_argument("--next", action="store_true", help="Run next ready jobs from queue")
    run_parser.add_argument("--plan", help="Run a specific plan immediately")
    run_parser.add_argument("--queued", action="store_true", help="Run all queued jobs")
    run_parser.add_argument("--limit", type=int, default=1, help="Max jobs to run")
    run_parser.add_argument("--confirm-heavy", action="store_true", help="Confirm running heavy jobs")
    run_parser.add_argument("--json", action="store_true", help="Output JSON")

    jobs_parser = lab_subs.add_parser("jobs", help="List jobs in queue")
    jobs_parser.add_argument("--status", help="Filter by status")
    jobs_parser.add_argument("--json", action="store_true", help="Output JSON")

    cancel_parser = lab_subs.add_parser("cancel", help="Cancel a job")
    cancel_parser.add_argument("job_id", help="Job ID to cancel")
    cancel_parser.add_argument("--confirm", action="store_true", help="Confirm cancellation", required=True)

    retry_parser = lab_subs.add_parser("retry", help="Retry a failed job")
    retry_parser.add_argument("job_id", help="Job ID to retry")
    retry_parser.add_argument("--confirm", action="store_true", help="Confirm retry", required=True)

    show_parser = lab_subs.add_parser("show", help="Show details of job/run/plan")
    show_parser.add_argument("type", choices=["job", "run", "plan"], help="Type of entity")
    show_parser.add_argument("id", help="Entity ID")
    show_parser.add_argument("--json", action="store_true", help="Output JSON")

    recent_parser = lab_subs.add_parser("recent", help="List recent batch runs")
    recent_parser.add_argument("--limit", type=int, default=10, help="Number of runs to show")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON")

    policy_parser = lab_subs.add_parser("policy", help="Show active research policy")
    policy_parser.add_argument("--json", action="store_true", help="Output JSON")

    config_parser = lab_subs.add_parser("config", help="Show lab config")
    config_parser.add_argument("--json", action="store_true", help="Output JSON")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bist_signal_bot",
        description="BIST Signal Bot CLI"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Format all output as JSON"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    from bist_signal_bot.cli.calibration_cli import setup_calibration_parser
    setup_explain_parser(subparsers)
    setup_calibration_parser(subparsers)
    add_portfolio_construct_parser(subparsers)
    try:
        add_docs_hub_parser(subparsers)
    except NameError:
        pass
    from bist_signal_bot.cli.portfolio_ledger_commands import setup_portfolio_ledger_parser
    setup_portfolio_ledger_parser(subparsers)
    add_telegram_center_parser(subparsers)

    # Portfolio Research Command
    portfolio_parser = subparsers.add_parser("portfolio-research", help="Manage research portfolio baskets and simulations")
    portfolio_subparsers = portfolio_parser.add_subparsers(dest="subcommand", help="Portfolio Research commands")

    # build
    build_parser = portfolio_subparsers.add_parser("build", help="Build a new research portfolio snapshot")
    build_parser.add_argument("--symbols", nargs="+", help="Specific symbols to include")
    build_parser.add_argument("--method", type=str, default="HYBRID", help="Allocation method")
    build_parser.add_argument("--max-items", type=int, default=10, help="Max items in basket")
    build_parser.add_argument("--include-watchlist", action="store_true", help="Include watchlist items")
    build_parser.add_argument("--include-ensemble", action="store_true", help="Include ensemble candidates")
    build_parser.add_argument("--save", action="store_true", help="Save the snapshot")
    build_parser.add_argument("--json", action="store_true", help="Output JSON")

    # exposure
    exposure_parser = portfolio_subparsers.add_parser("exposure", help="Show portfolio exposures")
    exposure_parser.add_argument("--snapshot", type=str, help="Snapshot ID to analyze")
    exposure_parser.add_argument("--group", type=str, default="SECTOR", help="Exposure group (SECTOR, STRATEGY, etc)")
    exposure_parser.add_argument("--json", action="store_true", help="Output JSON")

    # rebalance
    rebalance_parser = portfolio_subparsers.add_parser("rebalance", help="Create a rebalance plan")
    rebalance_parser.add_argument("--current", type=str, help="Current snapshot ID")
    rebalance_parser.add_argument("--method", type=str, default="HYBRID", help="Allocation method for target")
    rebalance_parser.add_argument("--json", action="store_true", help="Output JSON")

    # simulate
    simulate_parser = portfolio_subparsers.add_parser("simulate", help="Run a basket simulation")
    simulate_parser.add_argument("--snapshot", type=str, help="Snapshot ID to simulate")
    simulate_parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    simulate_parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    simulate_parser.add_argument("--latest", action="store_true", help="Use latest snapshot")
    simulate_parser.add_argument("--days", type=int, default=60, help="Lookback days if start/end not provided")
    simulate_parser.add_argument("--json", action="store_true", help="Output JSON")

    # show/latest/recent/config
    show_parser = portfolio_subparsers.add_parser("show", help="Show a specific snapshot")
    show_parser.add_argument("snapshot_id", type=str, help="Snapshot ID")
    show_parser.add_argument("--json", action="store_true", help="Output JSON")

    latest_parser = portfolio_subparsers.add_parser("latest", help="Show the latest snapshot")
    latest_parser.add_argument("--json", action="store_true", help="Output JSON")

    recent_parser = portfolio_subparsers.add_parser("recent", help="List recent snapshots")
    recent_parser.add_argument("--limit", type=int, default=10, help="Number of snapshots")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON")

    config_parser = portfolio_subparsers.add_parser("config", help="Show portfolio research configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON")

    healthcheck_parser = subparsers.add_parser("healthcheck", help="Check system components health")
    config_parser = subparsers.add_parser("config", help="View current configuration")
    config_parser.add_argument("--hide-secrets", action="store_true", default=True, help="Mask sensitive fields")
    config_parser.add_argument("--show-secrets", action="store_false", dest="hide_secrets", help="Show sensitive fields")

    symbols_parser = subparsers.add_parser("symbols", help="List default BIST seed symbol universe")
    validate_symbol_parser = subparsers.add_parser("validate-symbol", help="Validate a symbol format against BIST rules")
    validate_symbol_parser.add_argument("symbol", type=str, help="Symbol to validate")

    provider_status_parser = subparsers.add_parser("provider-status", help="Check market data provider status")
    storage_status_parser = subparsers.add_parser("storage-status", help="Check local storage status")
    calendar_parser = subparsers.add_parser("calendar-status", help="Check market calendar and session status")
    calendar_parser.add_argument("--at", type=str, help="ISO format datetime to check (default: now)")

    telegram_parser = subparsers.add_parser("telegram-test", help="Test Telegram configuration (dry-run by default)")
    telegram_parser.add_argument("--message", type=str, default="BIST Bot test mesajı", help="Message to send")
    telegram_parser.add_argument("--real", action="store_true", help="Send a real message if configured")

    mock_parser = subparsers.add_parser("mock-data", help="Generate mock market data for testing")
    mock_parser.add_argument("symbol", type=str, help="Symbol to generate data for")
    mock_parser.add_argument("--rows", type=int, default=252, help="Number of rows to generate")

    quality_parser = subparsers.add_parser("quality-demo", help="Generate mock data with synthetic errors to demonstrate quality checks")
    quality_parser.add_argument("symbol", type=str, help="Symbol to generate data for")
    quality_parser.add_argument("--rows", type=int, default=252, help="Number of rows")

    clean_parser = subparsers.add_parser("clean-data", help="Apply data cleaning policies to OHLCV data")
    clean_parser.add_argument("symbol", type=str, help="Symbol to clean")
    clean_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Source to read data from")
    clean_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")

    normalize_parser = subparsers.add_parser("normalize-data", help="Apply normalization to ensure proper column names and types")
    normalize_parser.add_argument("symbol", type=str, help="Symbol to normalize")
    normalize_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Source to read data from")
    normalize_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")

    adjust_parser = subparsers.add_parser("adjust-data", help="Apply price adjustments for corporate actions")
    adjust_parser.add_argument("symbol", type=str, help="Symbol to adjust")
    adjust_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Source to read data from")
    adjust_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")
    adjust_parser.add_argument("--policy", type=str, choices=["STRICT", "FLEXIBLE", "FLAG_ONLY"], default="FLEXIBLE", help="Adjustment Policy")

    ca_parser = subparsers.add_parser("corporate-actions", help="Manage corporate actions")
    ca_parser.add_argument("dummy", nargs="*")
    ca_subparsers = ca_parser.add_subparsers(dest="ca_command", required=True)

    ca_list_parser = ca_subparsers.add_parser("list", help="List all corporate actions for a symbol")
    ca_list_parser.add_argument("symbol", type=str, help="Symbol")
    ca_list_parser.add_argument("--verified-only", action="store_true", help="Show only verified actions")

    ca_add_parser = ca_subparsers.add_parser("add", help="Add a new corporate action")
    ca_add_parser.add_argument("symbol", type=str, help="Symbol")
    ca_add_parser.add_argument("--type", type=str, required=True, choices=["DIVIDEND", "STOCK_SPLIT"], help="Action type")
    ca_add_parser.add_argument("--ex-date", type=str, required=True, help="Ex-dividend date (YYYY-MM-DD)")
    ca_add_parser.add_argument("--value", type=float, required=True, help="Dividend amount or split ratio")
    ca_add_parser.add_argument("--verified", action="store_true", help="Mark as verified")

    ca_export_parser = ca_subparsers.add_parser("export", help="Export corporate actions")
    ca_export_parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Export format")
    ca_export_parser.add_argument("--output", type=str, required=True, help="Output file path")

    ind_calc_parser = subparsers.add_parser("indicators", help="Calculate technical indicators for a symbol")
    ind_calc_parser.add_argument("symbol", type=str, help="Symbol to calculate indicators for")
    ind_calc_parser.add_argument("--source", type=str, choices=["local", "mock"], default="mock", help="Data source")
    ind_calc_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    ind_calc_parser.add_argument("--indicators", type=str, help="Comma-separated list of indicators to calculate (e.g. sma_20,rsi_14)")
    ind_calc_parser.add_argument("--default-set", action="store_true", help="Calculate default indicator set")
    ind_calc_parser.add_argument("--rows", type=int, default=500, help="Number of rows for mock data")

    momentum_features_parser = subparsers.add_parser("momentum-features", help="Calculate comprehensive momentum features for a symbol")
    momentum_features_parser.add_argument("symbol", type=str, help="Symbol")
    momentum_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    momentum_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    momentum_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")

    trend_parser = subparsers.add_parser("trend-features", help="Calculate trend features for a symbol")
    trend_parser.add_argument("symbol", type=str, help="Symbol")
    trend_parser.add_argument("--source", type=str, choices=["local", "mock"], default="mock", help="Data source")
    trend_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    trend_parser.add_argument("--rows", type=int, default=500, help="Number of rows for mock data")
    trend_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")

    download_parser = subparsers.add_parser("download-data", help="Download OHLCV data from provider")
    download_subparsers = download_parser.add_subparsers(dest="download_command", required=True)

    download_single = download_subparsers.add_parser("single", help="Download data for a single symbol")
    download_single.add_argument("symbol", type=str, help="Symbol to download")
    download_single.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d, 1h)")
    download_single.add_argument("--period", type=str, default="2y", help="Period (e.g. 2y, max)")

    download_batch = download_subparsers.add_parser("batch", help="Download data for multiple symbols")
    download_batch.add_argument("--symbols", type=str, nargs="+", help="List of symbols to download")
    download_batch.add_argument("--all-active", action="store_true", help="Download for all active symbols in universe")
    download_batch.add_argument("--group", type=str, help="Download for a specific symbol group")
    download_batch.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    download_batch.add_argument("--period", type=str, default="2y", help="Period")

    version_parser = subparsers.add_parser("version", help="Show application version")
    diagnose_parser = subparsers.add_parser("diagnose", help="Run diagnostic checks on the environment")

    universe_parser = subparsers.add_parser("universe", help="Manage symbol universe")
    universe_subparsers = universe_parser.add_subparsers(dest="universe_command", required=True)

    init_parser = universe_subparsers.add_parser("init", help="Initialize default universe")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing universe")

    list_parser = universe_subparsers.add_parser("list", help="List symbols in universe")
    list_parser.add_argument("--active-only", action="store_true", help="Show only active symbols")
    list_parser.add_argument("--group", type=str, help="Filter by group")

    add_parser = universe_subparsers.add_parser("add", help="Add symbol to universe")
    add_parser.add_argument("symbol", type=str, help="Symbol to add")
    add_parser.add_argument("--name", type=str, help="Company name")
    add_parser.add_argument("--group", type=str, help="Symbol group")

    remove_parser = universe_subparsers.add_parser("remove", help="Remove symbol from universe")
    remove_parser.add_argument("symbol", type=str, help="Symbol to remove")

    update_parser = universe_subparsers.add_parser("update", help="Update symbol from data provider")
    update_parser.add_argument("--symbol", type=str, help="Specific symbol to update (optional)")

    export_parser = universe_subparsers.add_parser("export", help="Export universe data")
    export_parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Export format")
    export_parser.add_argument("--output", type=str, required=True, help="Output file path")

    patterns_parser = subparsers.add_parser("patterns", help="Manage and run pattern detection")
    patterns_subparsers = patterns_parser.add_subparsers(dest="patterns_command", required=True)

    p_list_parser = patterns_subparsers.add_parser("list", help="List registered pattern detectors")

    p_detect_parser = patterns_subparsers.add_parser("detect", help="Run pattern detection on a symbol")
    p_detect_parser.add_argument("symbol", type=str, help="Symbol to detect patterns for")
    p_detect_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    p_detect_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    p_detect_parser.add_argument("--patterns", type=str, help="Comma-separated list of patterns to detect")
    p_detect_parser.add_argument("--default-set", action="store_true", help="Run default pattern set")

    pattern_features_parser = subparsers.add_parser("pattern-features", help="Calculate comprehensive pattern features for a symbol")
    pattern_features_parser.add_argument("symbol", type=str, help="Symbol")
    pattern_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    pattern_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    pattern_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")

    volume_features_parser = subparsers.add_parser("volume-features", help="Calculate volume features for a symbol")
    volume_features_parser.add_argument("symbol", type=str, help="Symbol")
    volume_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    volume_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    volume_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")

    volatility_features_parser = subparsers.add_parser("volatility-features", help="Calculate volatility features for a symbol")
    volatility_features_parser.add_argument("symbol", type=str, help="Symbol")
    volatility_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    volatility_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    volatility_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")

    divergence_parser = subparsers.add_parser("divergence", help="Divergence detection operations")
    divergence_subparsers = divergence_parser.add_subparsers(dest="subcommand", required=True)

    div_detect_parser = divergence_subparsers.add_parser("detect", help="Detect divergences for a symbol")
    div_detect_parser.add_argument("symbol", help="Symbol to check")
    div_detect_parser.add_argument("--source", choices=["local", "mock"], default="local", help="Data source")
    div_detect_parser.add_argument("--timeframe", default="1d", help="Timeframe (e.g. 1d, 1h)")
    div_detect_parser.add_argument("--indicators", help="Comma separated indicators (e.g. rsi,macd_hist,obv)")
    div_detect_parser.add_argument("--pivot-mode", choices=["LOOKBACK_ONLY", "CONFIRMED_LAGGED"], default="LOOKBACK_ONLY", help="Pivot detection mode")
    div_detect_parser.add_argument("--lookback", type=int, help="Lookback window for pivots")
    div_detect_parser.add_argument("--min-distance", type=int, dest="min_pivot_distance", help="Min distance between pivots")
    div_detect_parser.add_argument("--max-distance", type=int, dest="max_pivot_distance", help="Max distance between pivots")
    div_detect_parser.set_defaults(include_hidden=True, include_regular=True)

    strategies_parser = subparsers.add_parser("strategies", help="Strategy engine operations")
    strategies_subparsers = strategies_parser.add_subparsers(dest="strategies_cmd", required=True)

    # strategies list
    strategies_subparsers.add_parser("list", help="List registered strategies")

    # strategies run
    run_strat_parser = strategies_subparsers.add_parser("run", help="Run a strategy on a single symbol")
    run_strat_parser.add_argument("strategy", type=str, help="Strategy name")
    run_strat_parser.add_argument("symbol", type=str, help="Symbol to run strategy for")
    run_strat_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    run_strat_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g., 1d, 1wk)")
    run_strat_parser.add_argument("--period", type=str, help="History period")
    run_strat_parser.add_argument("--rows", type=int, help="Rows for mock data")
    run_strat_parser.add_argument("--param", type=str, action="append", help="Strategy parameters (e.g., fast_window=10)")
    run_strat_parser.add_argument("--save-output", action="store_true", help="Save features and signals to CSV")
    run_strat_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # strategies batch
    batch_strat_parser = strategies_subparsers.add_parser("batch", help="Run a strategy on multiple symbols")
    batch_strat_parser.add_argument("strategy", type=str, help="Strategy name")

    group = batch_strat_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbols", type=str, nargs="+", help="List of symbols")
    group.add_argument("--all", action="store_true", help="Run on all symbols in universe")
    group.add_argument("--group", type=str, help="Run on a specific symbol group")

    batch_strat_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    batch_strat_parser.add_argument("--timeframe", type=str, help="Timeframe")
    batch_strat_parser.add_argument("--period", type=str, help="History period")
    batch_strat_parser.add_argument("--param", type=str, action="append", help="Strategy parameters")
    batch_strat_parser.add_argument("--min-score", type=float, help="Minimum signal score to report")
    batch_strat_parser.add_argument("--save-output", action="store_true", help="Save summary report to CSV/JSON")
    batch_strat_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    benchmarks_parser = subparsers.add_parser("benchmarks", help="Benchmark strategy operations")
    benchmarks_subparsers = benchmarks_parser.add_subparsers(dest="benchmarks_cmd", required=True)

    # benchmarks list
    benchmarks_subparsers.add_parser("list", help="List registered benchmarks")

    # benchmarks run
    run_bench_parser = benchmarks_subparsers.add_parser("run", help="Run a benchmark on a single symbol")
    run_bench_parser.add_argument("benchmark", type=str, help="Benchmark name")
    run_bench_parser.add_argument("symbol", type=str, help="Symbol to run benchmark for")
    run_bench_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    run_bench_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g., 1d)")
    run_bench_parser.add_argument("--period", type=str, help="History period")
    run_bench_parser.add_argument("--rows", type=int, help="Rows for mock data")
    run_bench_parser.add_argument("--param", type=str, action="append", help="Benchmark parameters")
    run_bench_parser.add_argument("--save-output", action="store_true", help="Save features and signals to CSV")
    run_bench_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # benchmarks batch
    batch_bench_parser = benchmarks_subparsers.add_parser("batch", help="Run a benchmark on multiple symbols")
    batch_bench_parser.add_argument("benchmark", type=str, help="Benchmark name")

    group = batch_bench_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbols", type=str, nargs="+", help="List of symbols")
    group.add_argument("--all", action="store_true", help="Run on all symbols in universe")
    group.add_argument("--group", type=str, help="Run on a specific symbol group")

    batch_bench_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    batch_bench_parser.add_argument("--timeframe", type=str, help="Timeframe")
    batch_bench_parser.add_argument("--period", type=str, help="History period")
    batch_bench_parser.add_argument("--param", type=str, action="append", help="Benchmark parameters")
    batch_bench_parser.add_argument("--save-output", action="store_true", help="Save summary report to CSV/JSON")
    batch_bench_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # benchmarks default
    default_bench_parser = benchmarks_subparsers.add_parser("default", help="Run default set of benchmarks on a symbol")
    default_bench_parser.add_argument("symbol", type=str, help="Symbol to run default benchmarks for")
    default_bench_parser.add_argument("--source", type=str, choices=["mock", "local"], default="local", help="Data source")
    default_bench_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    default_bench_parser.add_argument("--period", type=str, help="History period")
    default_bench_parser.add_argument("--rows", type=int, help="Rows for mock data")
    default_bench_parser.add_argument("--json", action="store_true", help="Output in JSON format")



    # Risk Engine commands
    risk_parser = subparsers.add_parser("risk", help="Risk engine operations")
    risk_subparsers = risk_parser.add_subparsers(dest="risk_cmd", required=True)

    # risk evaluate
    risk_eval_parser = risk_subparsers.add_parser("evaluate", help="Evaluate a strategy signal with the risk engine")
    risk_eval_parser.add_argument("symbol", type=str, help="Symbol to evaluate")
    risk_eval_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    risk_eval_parser.add_argument("--strategy", type=str, required=True, help="Strategy name")
    risk_eval_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    risk_eval_parser.add_argument("--rows", type=int, help="Rows for mock data")
    risk_eval_parser.add_argument("--param", type=str, action="append", help="Strategy parameters (e.g. key=val)")
    risk_eval_parser.add_argument("--equity", type=float, help="Account equity")
    risk_eval_parser.add_argument("--cash", type=float, help="Available cash")
    risk_eval_parser.add_argument("--daily-signal-count", type=int, help="Daily signal count")
    risk_eval_parser.add_argument("--open-position-count", type=int, help="Open position count")
    risk_eval_parser.add_argument("--portfolio-risk-pct", type=float, help="Current portfolio risk percent")
    risk_eval_parser.add_argument("--sizing", type=str, help="Position sizing method")
    risk_eval_parser.add_argument("--stop", type=str, help="Stop method")
    risk_eval_parser.add_argument("--target", type=str, help="Target method")
    risk_eval_parser.add_argument("--json", action="store_true", help="Output JSON")

    # risk size
    risk_size_parser = risk_subparsers.add_parser("size", help="Calculate position size")
    risk_size_parser.add_argument("symbol", type=str, help="Symbol to evaluate")
    risk_size_parser.add_argument("--side", type=str, required=True, choices=["LONG", "SHORT"], help="Trade side")
    risk_size_parser.add_argument("--entry", type=float, required=True, help="Entry price")
    risk_size_parser.add_argument("--stop", type=float, help="Stop price")
    risk_size_parser.add_argument("--target", type=float, help="Target price")
    risk_size_parser.add_argument("--equity", type=float, required=True, help="Account equity")
    risk_size_parser.add_argument("--method", type=str, help="Position sizing method")
    risk_size_parser.add_argument("--json", action="store_true", help="Output JSON")

    # risk stop-target
    risk_st_parser = risk_subparsers.add_parser("stop-target", help="Calculate stop/target reference")
    risk_st_parser.add_argument("symbol", type=str, help="Symbol to evaluate")
    risk_st_parser.add_argument("--side", type=str, required=True, choices=["LONG", "SHORT"], help="Trade side")
    risk_st_parser.add_argument("--entry", type=float, required=True, help="Entry price")
    risk_st_parser.add_argument("--atr", type=float, help="Optional ATR value for ATR-based methods")
    risk_st_parser.add_argument("--method-stop", type=str, help="Stop method")
    risk_st_parser.add_argument("--method-target", type=str, help="Target method")
    risk_st_parser.add_argument("--json", action="store_true", help="Output JSON")

    # risk config
    risk_cfg_parser = risk_subparsers.add_parser("config", help="Show risk configuration summary")
    risk_cfg_parser.add_argument("--json", action="store_true", help="Output JSON")

    add_costs_parser(subparsers)
    add_security_parser(subparsers)
    add_quality_parser(subparsers)

    add_validate_backtest_parser(subparsers)
    add_backtest_parser(subparsers)

    # SCAN
    scan_parser = subparsers.add_parser("scan", help="Signal Scanner v1")
    scan_sub = scan_parser.add_subparsers(dest="scan_command", required=True)

    scan_sym = scan_sub.add_parser("symbols", help="Scan explicit symbols")
    scan_sym.add_argument("symbols", nargs="+")
    scan_sym.add_argument("--source", default="mock")
    scan_sym.add_argument("--strategy", required=True)
    scan_sym.add_argument("--top", type=int, default=10)
    scan_sym.add_argument("--sort", default="FINAL_SCORE")
    scan_sym.add_argument("--no-portfolio-risk", action="store_true")
    scan_sym.add_argument("--json", action="store_true")

    scan_wl = scan_sub.add_parser("watchlist", help="Scan a watchlist")
    scan_wl.add_argument("watchlist")
    scan_wl.add_argument("--source", default="mock")
    scan_wl.add_argument("--strategy", required=True)
    scan_wl.add_argument("--save-report", action="store_true")
    scan_wl.add_argument("--telegram", action="store_true")

    scan_group = scan_sub.add_parser("group", help="Scan a group")
    scan_group.add_argument("group")
    scan_group.add_argument("--source", default="mock")
    scan_group.add_argument("--strategy", required=True)
    scan_group.add_argument("--top", type=int, default=10)

    scan_all = scan_sub.add_parser("all", help="Scan all active symbols")
    scan_all.add_argument("--source", default="mock")
    scan_all.add_argument("--strategy", required=True)
    scan_all.add_argument("--top", type=int, default=10)
    scan_all.add_argument("--save-report", action="store_true")

    scan_recent = scan_sub.add_parser("recent", help="List recent scans")
    scan_recent.add_argument("--limit", type=int, default=20)
    scan_recent.add_argument("--json", action="store_true")

    scan_config = scan_sub.add_parser("config", help="Show scanner config")
    scan_config.add_argument("--json", action="store_true")


    # Runtime Parser
    parser_runtime = subparsers.add_parser('runtime', help="Runtime orchestrator commands")
    runtime_subparsers = parser_runtime.add_subparsers(dest='runtime_command', required=True)

    # run-once
    parser_run_once = runtime_subparsers.add_parser('run-once', help="Run the pipeline once")
    parser_run_once.add_argument('--source', default='mock', help="Data source")
    parser_run_once.add_argument('--strategy', default='moving_average_trend', help="Strategy name")
    parser_run_once.add_argument('--group', help="Universe group")
    parser_run_once.add_argument('--symbols', nargs='+', help="Specific symbols")
    parser_run_once.add_argument('--ml-filter', action='store_true', help="Enable ML filter")
    parser_run_once.add_argument('--ml-model-id', help="ML model ID")
    parser_run_once.add_argument('--regime-filter', action='store_true', help="Enable regime filter")
    parser_run_once.add_argument('--paper', action='store_true', help="Enable paper trading")
    parser_run_once.add_argument('--telegram', action='store_true', help="Send Telegram summary")

    # dry-run
    parser_dry_run = runtime_subparsers.add_parser('dry-run', help="Dry run the pipeline")
    parser_dry_run.add_argument('--source', default='mock', help="Data source")
    parser_dry_run.add_argument('--strategy', default='moving_average_trend', help="Strategy name")
    parser_dry_run.add_argument('--symbols', nargs='+', help="Specific symbols")

    # loop
    parser_loop = runtime_subparsers.add_parser('loop', help="Run the pipeline in a loop")
    parser_loop.add_argument('--interval', type=int, default=60, help="Interval in minutes")
    parser_loop.add_argument('--max-iterations', type=int, default=0, help="Max iterations")
    parser_loop.add_argument('--run-immediately', action='store_true', help="Run immediately")
    parser_loop.add_argument('--source', default='mock', help="Data source")
    parser_loop.add_argument('--strategy', default='moving_average_trend', help="Strategy name")
    parser_loop.add_argument('--symbols', nargs='+', help="Specific symbols")

    # status
    parser_status = runtime_subparsers.add_parser('status', help="Show runtime status")

    # history
    parser_history = runtime_subparsers.add_parser('history', help="Show run history")
    parser_history.add_argument('--limit', type=int, default=10, help="Limit")

    # unlock
    parser_unlock = runtime_subparsers.add_parser('unlock', help="Unlock runtime")
    parser_unlock.add_argument('--stale-only', action='store_true', help="Only clear stale lock")
    parser_unlock.add_argument('--force', action='store_true', help="Force clear lock")
    parser_unlock.add_argument('--confirm', action='store_true', help="Confirm force clear")

    # reset-state
    parser_reset = runtime_subparsers.add_parser('reset-state', help="Reset runtime state")
    parser_reset.add_argument('--confirm', action='store_true', help="Confirm reset")

    # config
    parser_config = runtime_subparsers.add_parser('config', help="Show runtime config")
    setup_monitor_parser(subparsers)
    setup_package_parser(subparsers)
    add_performance_parser(subparsers)
    add_adaptive_parser(subparsers)
    add_signals_parser(subparsers)
    # Report parser
    parser_report = subparsers.add_parser("report", help="Manage research reports")
    report_subparsers = parser_report.add_subparsers(dest="report_command")

    # daily
    parser_daily = report_subparsers.add_parser("daily", help="Generate daily report")
    parser_daily.add_argument("--symbols", nargs="+", help="Symbols to include")
    parser_daily.add_argument("--format", help="Export format (e.g., markdown, json, all)")
    parser_daily.add_argument("--json", action="store_true", help="Output JSON directly")

    # weekly
    parser_weekly = report_subparsers.add_parser("weekly", help="Generate weekly report")
    parser_weekly.add_argument("--symbols", nargs="+", help="Symbols to include")
    parser_weekly.add_argument("--json", action="store_true", help="Output JSON directly")

    # runtime
    parser_runtime = report_subparsers.add_parser("runtime", help="Generate runtime report")
    parser_runtime.add_argument("--run-id", help="Specific runtime run ID")
    parser_runtime.add_argument("--json", action="store_true", help="Output JSON directly")

    # latest
    parser_latest = report_subparsers.add_parser("latest", help="Show latest report")
    parser_latest.add_argument("--type", help="Filter by report type (e.g., DAILY)")
    parser_latest.add_argument("--json", action="store_true", help="Output JSON directly")

    # digest
    parser_digest = report_subparsers.add_parser("digest", help="Generate report digest")
    parser_digest.add_argument("--type", help="Filter by report type")
    parser_digest.add_argument("--json", action="store_true", help="Output JSON directly")

    # send
    parser_send = report_subparsers.add_parser("send", help="Send report digest via Telegram")
    parser_send.add_argument("--latest", action="store_true", help="Send latest digest")
    parser_send.add_argument("--type", help="Filter by report type")
    parser_send.add_argument("--confirm", action="store_true", help="Confirm sending")

    # export
    parser_export = report_subparsers.add_parser("export", help="Export latest report")
    parser_export.add_argument("--latest", action="store_true", help="Export latest report")
    parser_export.add_argument("--format", required=True, help="Export format (html, pdf, markdown)")

    # recent
    parser_recent = report_subparsers.add_parser("recent", help="List recent reports")
    parser_recent.add_argument("--limit", type=int, default=10, help="Number of reports")
    parser_recent.add_argument("--json", action="store_true", help="Output JSON directly")

    # config
    parser_report_config = report_subparsers.add_parser("config", help="Show report config")
    parser_report_config.add_argument("--json", action="store_true", help="Output JSON directly")

    add_release_parser(subparsers)


    # Breadth commands
    breadth_parser = subparsers.add_parser("breadth", help="Market breadth and relative strength tools")
    breadth_subs = breadth_parser.add_subparsers(dest="breadth_command")

    # breadth snapshot
    b_snap = breadth_subs.add_parser("snapshot", help="Generate market breadth snapshot")
    b_snap.add_argument("--symbols", nargs="+", help="Symbols to analyze")
    b_snap.add_argument("--group", help="Universe group (e.g. LIQUID)")
    b_snap.add_argument("--benchmark", help="Benchmark symbol")
    b_snap.add_argument("--source", default="local_file", help="Data source")
    b_snap.add_argument("--save", action="store_true", help="Save snapshot")
    b_snap.add_argument("--json", action="store_true", help="Output JSON")

    # breadth relative-strength
    b_rs = breadth_subs.add_parser("relative-strength", help="Calculate relative strength")
    b_rs.add_argument("--symbols", nargs="+", help="Symbols to analyze")
    b_rs.add_argument("--group", help="Universe group")
    b_rs.add_argument("--benchmark", help="Benchmark symbol")
    b_rs.add_argument("--top", type=int, help="Top N")
    b_rs.add_argument("--json", action="store_true", help="Output JSON")

    # breadth sector-rotation
    b_sr = breadth_subs.add_parser("sector-rotation", help="Calculate sector rotation")
    b_sr.add_argument("--group", help="Universe group")
    b_sr.add_argument("--top", type=int, help="Top N")
    b_sr.add_argument("--json", action="store_true", help="Output JSON")

    # breadth rank
    b_rank = breadth_subs.add_parser("rank", help="Cross-sectional ranking")
    b_rank.add_argument("--symbols", nargs="+", help="Symbols")
    b_rank.add_argument("--group", help="Universe group")
    b_rank.add_argument("--top", type=int, help="Top N")
    b_rank.add_argument("--json", action="store_true", help="Output JSON")

    # breadth leaders
    b_lead = breadth_subs.add_parser("leaders", help="Show leaders")
    b_lead.add_argument("--top", type=int, default=20, help="Top N")
    b_lead.add_argument("--json", action="store_true", help="Output JSON")

    # breadth laggards
    b_lag = breadth_subs.add_parser("laggards", help="Show laggards")
    b_lag.add_argument("--bottom", type=int, default=20, help="Bottom N")
    b_lag.add_argument("--json", action="store_true", help="Output JSON")

    # breadth regime
    b_reg = breadth_subs.add_parser("regime", help="Show breadth regime")
    b_reg.add_argument("--group", help="Universe group")
    b_reg.add_argument("--json", action="store_true", help="Output JSON")

    # breadth recent
    b_rec = breadth_subs.add_parser("recent", help="List recent snapshots")
    b_rec.add_argument("--limit", type=int, default=10, help="Limit")
    b_rec.add_argument("--json", action="store_true", help="Output JSON")

    # breadth config
    b_conf = breadth_subs.add_parser("config", help="Show breadth config")
    b_conf.add_argument("--json", action="store_true", help="Output JSON")

    setup_ensemble_parser(subparsers)
    add_stress_parsers(subparsers)
    add_drift_parser(subparsers)
    add_lab_parser(subparsers)

    # KB Command
    kb_parser = subparsers.add_parser("kb", help="Knowledge Base operations")
    kb_subs = kb_parser.add_subparsers(dest="kb_cmd")

    # kb index
    kbi = kb_subs.add_parser("index", help="Build or update knowledge index")
    kbi.add_argument("--incremental", action="store_true", default=True)
    kbi.add_argument("--rebuild", action="store_true")
    kbi.add_argument("--confirm", action="store_true")
    kbi.add_argument("--use-embeddings", action="store_true")
    kbi.add_argument("--source", nargs="+")
    kbi.add_argument("--json", action="store_true")

    # kb search
    kbs = kb_subs.add_parser("search", help="Search knowledge base")
    kbs.add_argument("query")
    kbs.add_argument("--mode")
    kbs.add_argument("--symbol")
    kbs.add_argument("--source", nargs="+")
    kbs.add_argument("--json", action="store_true")

    # kb similar
    kbsim = kb_subs.add_parser("similar", help="Find similar cases")
    kbsim.add_argument("--symbol")
    kbsim.add_argument("--strategy")
    kbsim.add_argument("--text")
    kbsim.add_argument("--json", action="store_true")

    # kb cases
    kbc = kb_subs.add_parser("cases", help="Case history")
    kbc.add_argument("--symbol")
    kbc.add_argument("--strategy")
    kbc.add_argument("--json", action="store_true")

    # kb memory
    kbm = kb_subs.add_parser("memory", help="Memory cards")
    kbm.add_argument("--symbol")
    kbm.add_argument("--strategy")
    kbm.add_argument("--save", action="store_true")
    kbm.add_argument("--json", action="store_true")

    # kb show
    kbsh = kb_subs.add_parser("show", help="Show document")
    kbsh.add_argument("document_id")
    kbsh.add_argument("--chunks", action="store_true")
    kbsh.add_argument("--json", action="store_true")

    # kb stats
    kbst = kb_subs.add_parser("stats", help="Index stats")
    kbst.add_argument("--json", action="store_true")

    # kb clear-index
    kbcl = kb_subs.add_parser("clear-index", help="Clear index")
    kbcl.add_argument("--confirm", action="store_true")

    # kb config
    kbcf = kb_subs.add_parser("config", help="KB Config")
    kbcf.add_argument("--json", action="store_true")

    # Local Scheduler Module Phase 65
    scheduler_parser = subparsers.add_parser("scheduler", help="Manage scheduled jobs")
    scheduler_subs = scheduler_parser.add_subparsers(dest="subcommand", required=False) # allow fallback

    scheduler_subs.add_parser("list", help="List jobs")

    defaults_p = scheduler_subs.add_parser("defaults", help="Default jobs")
    defaults_p.add_argument("--create", action="store_true")
    defaults_p.add_argument("--confirm", action="store_true")

    scheduler_subs.add_parser("due", help="Find due jobs")

    run_due_p = scheduler_subs.add_parser("run-due", help="Run due jobs")
    run_due_p.add_argument("--dry-run", action="store_true")
    run_due_p.add_argument("--confirm", action="store_true")

    deploy_parser = subparsers.add_parser("deploy", help="Manage deployment")
    deploy_subs = deploy_parser.add_subparsers(dest="deploy_subcommand", required=True)

    dp_profiles = deploy_subs.add_parser("profiles")
    dp_profiles.add_argument("--json", action="store_true")

    dp_doctor = deploy_subs.add_parser("doctor")
    dp_doctor.add_argument("--deep", action="store_true")
    dp_doctor.add_argument("--json", action="store_true")

    dp_init = deploy_subs.add_parser("init-dirs")
    dp_init.add_argument("--dry-run", action="store_true")
    dp_init.add_argument("--confirm", action="store_true")
    dp_init.add_argument("--json", action="store_true")

    dp_env = deploy_subs.add_parser("env-template")
    dp_env.add_argument("--profile", type=str, default="RESEARCH_ONLY")
    dp_env.add_argument("--dry-run", action="store_true")
    dp_env.add_argument("--confirm", action="store_true")
    dp_env.add_argument("--output", type=str)

    dp_first = deploy_subs.add_parser("first-run")
    dp_first.add_argument("--profile", type=str, default="RESEARCH_ONLY")
    dp_first.add_argument("--dry-run", action="store_true")
    dp_first.add_argument("--confirm-write", action="store_true")
    dp_first.add_argument("--json", action="store_true")

    dp_smoke = deploy_subs.add_parser("smoke-test")
    dp_smoke.add_argument("--json", action="store_true")

    dp_rb = deploy_subs.add_parser("runbook")
    dp_rb.add_argument("--profile", type=str, default="RESEARCH_ONLY")
    dp_rb.add_argument("--output", type=str)

    dp_plat = deploy_subs.add_parser("platform-commands")
    dp_plat.add_argument("--platform", type=str)
    dp_plat.add_argument("--json", action="store_true")

    dp_latest = deploy_subs.add_parser("latest")
    dp_latest.add_argument("--json", action="store_true")

    dp_cfg = deploy_subs.add_parser("config")
    dp_cfg.add_argument("--json", action="store_true")


    p_inst = subparsers.add_parser("instruments", help="Instruments master operations")
    p_inst.add_argument("dummy", nargs="*") # to bypass argparse strictness and let click handle it

    # corporate-actions may already exist, let's safely add it only if it's missing
    if "corporate-actions" not in subparsers.choices:
        p_ca = subparsers.add_parser("corporate-actions", help="Corporate actions operations")
        p_ca.add_argument("dummy", nargs="*")
    else:
        # It exists, we just let it be. But wait, corporate-actions was already added natively?
        pass

    if "data-quality" not in subparsers.choices:
        p_dq = subparsers.add_parser("data-quality", help="Data quality operations")
        p_dq.add_argument("dummy", nargs="*")

    add_review_workflow_parser(subparsers)
    return parser


def add_paper_parser(subparsers: argparse._SubParsersAction) -> None:
    paper_parser = subparsers.add_parser("paper", help="Paper trading commands")
    paper_subparsers = paper_parser.add_subparsers(dest="paper_command", required=True)

    # Init
    init_parser = paper_subparsers.add_parser("init", help="Initialize a paper trading account")
    init_parser.add_argument("--account", help="Account ID to initialize")
    init_parser.add_argument("--cash", type=float, help="Initial cash amount")
    init_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing ledger")

    # Status
    status_parser = paper_subparsers.add_parser("status", help="Show paper account status")
    status_parser.add_argument("--account", help="Account ID")
    status_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Run-once
    run_parser = paper_subparsers.add_parser("run-once", help="Run a strategy and create paper orders")
    run_parser.add_argument("symbols", nargs="+", help="Symbols to run on")
    run_parser.add_argument("--account", help="Account ID")
    run_parser.add_argument("--source", choices=["mock", "local"], default="local", help="Data source")
    run_parser.add_argument("--strategy", required=True, help="Strategy name")
    run_parser.add_argument("--timeframe", default="1D", help="Timeframe (e.g., 1D, 1W)")
    run_parser.add_argument("--rows", type=int, default=500, help="Number of rows to fetch")
    run_parser.add_argument("--param", action="append", help="Strategy parameter (key=value)")
    run_parser.add_argument("--execution", default="LATEST_CLOSE_RESEARCH", help="Execution mode")
    run_parser.add_argument("--no-trade-risk", action="store_true", help="Disable trade-level risk engine")
    run_parser.add_argument("--no-portfolio-risk", action="store_true", help="Disable portfolio risk engine")
    run_parser.add_argument("--telegram-summary", action="store_true", help="Send summary to Telegram")
    run_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Positions
    pos_parser = paper_subparsers.add_parser("positions", help="List open positions")
    pos_parser.add_argument("--account", help="Account ID")
    pos_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Orders
    orders_parser = paper_subparsers.add_parser("orders", help="List orders")
    orders_parser.add_argument("--account", help="Account ID")
    orders_parser.add_argument("--status", help="Filter by order status")
    orders_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Fills
    fills_parser = paper_subparsers.add_parser("fills", help="List fills")
    fills_parser.add_argument("--account", help="Account ID")
    fills_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Trades
    trades_parser = paper_subparsers.add_parser("trades", help="List trades")
    trades_parser.add_argument("--account", help="Account ID")
    trades_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Close
    close_parser = paper_subparsers.add_parser("close", help="Close an open position")
    close_parser.add_argument("symbol", help="Symbol to close")
    close_parser.add_argument("--account", help="Account ID")
    close_parser.add_argument("--source", choices=["mock", "local"], default="local", help="Data source")
    close_parser.add_argument("--manual-price", type=float, help="Manual execution price")

    # Reset
    reset_parser = paper_subparsers.add_parser("reset", help="Reset a paper account")
    reset_parser.add_argument("--account", help="Account ID")
    reset_parser.add_argument("--cash", type=float, help="Initial cash amount after reset")
    reset_parser.add_argument("--confirm", action="store_true", help="Must confirm to reset")

    # Export
    export_parser = paper_subparsers.add_parser("export", help="Export ledger to CSV")
    export_parser.add_argument("--account", help="Account ID")

    # Config
    config_parser = paper_subparsers.add_parser("config", help="Show paper trading config")
    config_parser.add_argument("--json", action="store_true", help="Output JSON")

def add_optimize_parser(subparsers) -> None:
    add_ml_dataset_parser(subparsers)
    opt_parser = subparsers.add_parser("optimize", help="Strategy Optimizer commands")
    opt_subparsers = opt_parser.add_subparsers(dest="opt_command", required=True)

    # strategy
    s_parser = opt_subparsers.add_parser("strategy", help="Optimize strategy parameters")
    s_parser.add_argument("symbol")
    s_parser.add_argument("--source", choices=["local", "mock"], default="local")
    s_parser.add_argument("--strategy", required=True)
    s_parser.add_argument("--timeframe", default="1d")
    s_parser.add_argument("--rows", type=int, default=1000)
    s_parser.add_argument("--method", choices=["GRID_SEARCH", "RANDOM_SEARCH"])
    s_parser.add_argument("--objective", choices=["COMPOSITE", "SHARPE", "SORTINO", "CALMAR", "TOTAL_RETURN", "PROFIT_FACTOR", "MAX_DRAWDOWN"])
    s_parser.add_argument("--param-range", action="append", help="e.g. fast_window=10,20,30")
    s_parser.add_argument("--max-combinations", type=int)
    s_parser.add_argument("--seed", type=int)
    s_parser.add_argument("--top", type=int)
    s_parser.add_argument("--min-trades", type=int)
    s_parser.add_argument("--max-drawdown", type=float)
    s_parser.add_argument("--min-profit-factor", type=float)
    s_parser.add_argument("--require-positive-return", action="store_true")
    s_parser.add_argument("--compare-benchmark", action="store_true")
    s_parser.add_argument("--save-report", action="store_true")
    s_parser.add_argument("--format", default="all")
    s_parser.add_argument("--output-dir")
    s_parser.add_argument("--json", action="store_true")

    # walk-forward
    wf_parser = opt_subparsers.add_parser("walk-forward", help="Walk-forward optimization")
    wf_parser.add_argument("symbol")
    wf_parser.add_argument("--source", choices=["local", "mock"], default="local")
    wf_parser.add_argument("--strategy", required=True)
    wf_parser.add_argument("--timeframe", default="1d")
    wf_parser.add_argument("--rows", type=int, default=2000)
    wf_parser.add_argument("--method", choices=["WALK_FORWARD_GRID", "WALK_FORWARD_RANDOM"])
    wf_parser.add_argument("--objective", choices=["COMPOSITE", "SHARPE", "SORTINO", "TOTAL_RETURN"])
    wf_parser.add_argument("--param-range", action="append")
    wf_parser.add_argument("--max-combinations", type=int)
    wf_parser.add_argument("--train-window", type=int)
    wf_parser.add_argument("--test-window", type=int)
    wf_parser.add_argument("--step", type=int)
    wf_parser.add_argument("--max-splits", type=int)
    wf_parser.add_argument("--save-report", action="store_true")
    wf_parser.add_argument("--format", default="all")
    wf_parser.add_argument("--json", action="store_true")

    # search-space
    ss_parser = opt_subparsers.add_parser("search-space", help="Show default search space for a strategy")
    ss_parser.add_argument("--strategy", required=True)
    ss_parser.add_argument("--json", action="store_true")

    # recent
    r_parser = opt_subparsers.add_parser("recent", help="List recent optimizations")
    r_parser.add_argument("--limit", type=int, default=20)
    r_parser.add_argument("--json", action="store_true")

    # config
    c_parser = opt_subparsers.add_parser("config", help="Show optimization config")
    c_parser.add_argument("--json", action="store_true")

def add_ml_dataset_parser(subparsers):
    ml_parser = subparsers.add_parser("ml-dataset", help="ML dataset builder commands")
    ml_sub = ml_parser.add_subparsers(dest="ml_command")

    build_parser = ml_sub.add_parser("build", help="Build an ML dataset")
    build_parser.add_argument("symbols", nargs="+", help="Symbols to include")
    build_parser.add_argument("--source", choices=["mock", "local"], help="Data source")
    build_parser.add_argument("--timeframe", help="Timeframe")
    build_parser.add_argument("--rows", type=int, help="Number of rows")
    build_parser.add_argument("--period", help="Data period")
    build_parser.add_argument("--task", choices=["CLASSIFICATION", "REGRESSION"], help="Task type")
    build_parser.add_argument("--feature-level", choices=["basic", "advanced", "full"], help="Feature set level")
    build_parser.add_argument("--label-type", choices=["FORWARD_RETURN", "BINARY_DIRECTION", "MULTICLASS_DIRECTION", "THRESHOLD_EVENT"], help="Label type")
    build_parser.add_argument("--horizon", type=int, help="Label horizon bars")
    build_parser.add_argument("--pos-threshold", type=float, help="Positive threshold")
    build_parser.add_argument("--neg-threshold", type=float, help="Negative threshold")
    build_parser.add_argument("--include-mtf", action="store_true", help="Include MTF features")
    build_parser.add_argument("--include-raw-ohlcv", action="store_true", help="Include raw OHLCV")
    build_parser.add_argument("--no-trend", action="store_true", help="Exclude trend features")
    build_parser.add_argument("--no-momentum", action="store_true", help="Exclude momentum features")
    build_parser.add_argument("--no-volatility", action="store_true", help="Exclude volatility features")
    build_parser.add_argument("--no-volume", action="store_true", help="Exclude volume features")
    build_parser.add_argument("--no-patterns", action="store_true", help="Exclude pattern features")
    build_parser.add_argument("--no-divergence", action="store_true", help="Exclude divergence features")
    build_parser.add_argument("--split", choices=["none", "train-test"], help="Dataset split mode")
    build_parser.add_argument("--train-ratio", type=float, help="Train ratio (0-1)")
    build_parser.add_argument("--fill-method", choices=["none", "ffill", "bfill", "zero", "median"], help="Fill missing method")
    build_parser.add_argument("--drop-na-features", action="store_true", help="Drop rows with NA features")
    build_parser.add_argument("--save", action="store_true", help="Save dataset to store")
    build_parser.add_argument("--format", choices=["csv", "json", "parquet", "all"], help="Output format")
    build_parser.add_argument("--output-dir", help="Output directory")
    build_parser.add_argument("--json", action="store_true", help="Output JSON summary")

    schema_parser = ml_sub.add_parser("schema", help="Show ML dataset schema")
    schema_parser.add_argument("symbols", nargs="+", help="Symbols to check schema for")
    schema_parser.add_argument("--source", choices=["mock", "local"], help="Data source")
    schema_parser.add_argument("--json", action="store_true", help="Output JSON summary")

    recent_parser = ml_sub.add_parser("recent", help="List recent ML datasets")
    recent_parser.add_argument("--limit", type=int, default=10, help="Number of datasets to list")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON summary")

    config_parser = ml_sub.add_parser("config", help="Show ML dataset configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON summary")


def setup_ml_train_parser(subparsers):
    setup_monitor_parser(subparsers)
    ml_train_parser = subparsers.add_parser("ml-train", help="Train and evaluate ML models or generate predictions")
    ml_train_subparsers = ml_train_parser.add_subparsers(dest="ml_train_command", required=True)

    # train command
    train_parser = ml_train_subparsers.add_parser("train", help="Train an ML model")
    train_parser.add_argument("--dataset", type=str, help="Path to a pre-built feature dataset (CSV/Parquet)")
    train_parser.add_argument("--symbols", nargs="+", help="Symbols to build dataset for (if --dataset not provided)")
    train_parser.add_argument("--source", type=str, default="local", choices=["mock", "local"], help="Data source")
    train_parser.add_argument("--rows", type=int, help="Number of rows per symbol")
    train_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    train_parser.add_argument("--task", type=str, default="CLASSIFICATION", choices=["CLASSIFICATION", "REGRESSION"], help="ML task type")
    train_parser.add_argument("--model", type=str, help="Model type (e.g. RANDOM_FOREST_CLASSIFIER, LOGISTIC_REGRESSION, etc.)")
    train_parser.add_argument("--target", type=str, help="Target column name")
    train_parser.add_argument("--scaler", type=str, choices=["NONE", "STANDARD", "ROBUST", "MINMAX"], help="Scaler type")
    train_parser.add_argument("--imputer", type=str, choices=["NONE", "MEDIAN", "MEAN", "ZERO"], help="Imputer type")
    train_parser.add_argument("--train-ratio", type=float, help="Train/test split ratio (e.g. 0.7)")
    train_parser.add_argument("--seed", type=int, help="Random seed")
    train_parser.add_argument("--max-train-rows", type=int, help="Maximum number of train rows")
    train_parser.add_argument("--model-param", action="append", help="Model hyperparameter (key=value)")
    train_parser.add_argument("--save-model", action="store_true", help="Save the trained model to the registry")
    train_parser.add_argument("--save-report", action="store_true", help="Save the training report")
    train_parser.add_argument("--format", type=str, help="Report formats (json,markdown,csv,all)")
    train_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # predict command
    predict_parser = ml_train_subparsers.add_parser("predict", help="Generate predictions using a saved model")
    predict_parser.add_argument("--model-id", type=str, help="Model ID from the registry")
    predict_parser.add_argument("--model-path", type=str, help="Direct path to the model directory")
    predict_parser.add_argument("--dataset", type=str, help="Path to a pre-built feature dataset")
    predict_parser.add_argument("--symbols", nargs="+", help="Symbols to predict (fetches data dynamically)")
    predict_parser.add_argument("--source", type=str, default="local", choices=["mock", "local"], help="Data source")
    predict_parser.add_argument("--rows", type=int, help="Number of rows per symbol")
    predict_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe")
    predict_parser.add_argument("--all-rows", action="store_true", help="Predict for all rows instead of only the latest")
    predict_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # models command
    models_parser = ml_train_subparsers.add_parser("models", help="List saved ML models")
    models_parser.add_argument("--limit", type=int, default=20, help="Max number of models to list")
    models_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # show command
    show_parser = ml_train_subparsers.add_parser("show", help="Show details of a saved ML model")
    show_parser.add_argument("model_id", type=str, help="Model ID")
    show_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # delete command
    delete_parser = ml_train_subparsers.add_parser("delete", help="Delete a saved ML model")
    delete_parser.add_argument("model_id", type=str, help="Model ID")
    delete_parser.add_argument("--confirm", action="store_true", help="Confirm deletion", required=True)

    # config command
    config_parser = ml_train_subparsers.add_parser("config", help="Show ML training configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

def setup_monitor_parser(subparsers):
    monitor_parser = subparsers.add_parser("monitor", help="Monitoring and Self-Healing commands")
    monitor_subparsers = monitor_parser.add_subparsers(dest="monitor_command", required=True)

    # status command
    status_parser = monitor_subparsers.add_parser("status", help="Show overall monitoring status")
    status_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # heartbeat command
    hb_parser = monitor_subparsers.add_parser("heartbeat", help="Show or send heartbeats")
    hb_parser.add_argument("--component", type=str, help="Component to record heartbeat for")
    hb_parser.add_argument("--status", type=str, help="Health status (e.g. HEALTHY)")
    hb_parser.add_argument("--message", type=str, help="Heartbeat message")
    hb_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # diagnostics command
    diag_parser = monitor_subparsers.add_parser("diagnostics", help="Run diagnostic checks")
    diag_parser.add_argument("--save-report", action="store_true", help="Save the diagnostics report")
    diag_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # alerts command
    alerts_parser = monitor_subparsers.add_parser("alerts", help="List recent active alerts")
    alerts_parser.add_argument("--limit", type=int, default=20, help="Max number of alerts to list")
    alerts_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # test-alert command
    test_alert_parser = monitor_subparsers.add_parser("test-alert", help="Generate and optionally send a test alert")
    test_alert_parser.add_argument("--telegram", action="store_true", help="Actually send via Telegram if configured")

    # metrics command
    metrics_parser = monitor_subparsers.add_parser("metrics", help="List recent monitoring metrics")
    metrics_parser.add_argument("--limit", type=int, default=100, help="Max number of metrics to list")
    metrics_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    # repair command
    repair_parser = monitor_subparsers.add_parser("repair", help="Run self-healing actions")
    repair_parser.add_argument("--dry-run", action="store_true", help="Show suggested actions without running them")
    repair_parser.add_argument("--auto-safe", action="store_true", help="Run all safe auto-repair actions")
    repair_parser.add_argument("--clear-stale-lock", action="store_true", help="Clear stale runtime lock")
    repair_parser.add_argument("--reset-state", action="store_true", help="Reset stuck runtime state")
    repair_parser.add_argument("--confirm", action="store_true", help="Confirm destructive actions")

    # cleanup command
    cleanup_parser = monitor_subparsers.add_parser("cleanup", help="Cleanup old monitoring files")
    cleanup_parser.add_argument("--retention-days", type=int, default=30, help="Days to keep files")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    cleanup_parser.add_argument("--confirm", action="store_true", help="Confirm cleanup")

    # config command
    config_parser = monitor_subparsers.add_parser("config", help="Show monitoring configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

def add_security_parser(subparsers):
    security_parser = subparsers.add_parser("security", help="Manage security, secret hygiene, and kill-switches.")
    security_subparsers = security_parser.add_subparsers(dest="security_command", required=True)

    audit_parser = security_subparsers.add_parser("audit", help="Run a security configuration audit.")
    audit_parser.add_argument("--json", action="store_true", help="Output as JSON.")
    audit_parser.add_argument("--markdown", action="store_true", help="Output as Markdown.")

    preflight_parser = security_subparsers.add_parser("preflight", help="Run security preflight checks.")
    preflight_parser.add_argument("--runtime", action="store_true", help="Run runtime preflight.")
    preflight_parser.add_argument("--notification", action="store_true", help="Run notification preflight (dummy payload).")
    preflight_parser.add_argument("--json", action="store_true", help="Output as JSON.")

    redact_parser = security_subparsers.add_parser("redact", help="Test secret redaction on text.")
    redact_parser.add_argument("--text", required=True, type=str, help="Text to redact.")
    redact_parser.add_argument("--json", action="store_true", help="Output as JSON.")

    ks_parser = security_subparsers.add_parser("kill-switch", help="Manage operational kill switch.")
    ks_sub = ks_parser.add_subparsers(dest="ks_command", required=True)

    ks_sub.add_parser("status", help="Show kill switch status.")

    activate_parser = ks_sub.add_parser("activate", help="Activate the kill switch.")
    activate_parser.add_argument("--scope", type=str, default="ALL", help="Scope of the kill switch (e.g. ALL, RUNTIME, PAPER).")
    activate_parser.add_argument("--reason", type=str, required=True, help="Reason for activation.")

    deactivate_parser = ks_sub.add_parser("deactivate", help="Deactivate the kill switch.")
    deactivate_parser.add_argument("--confirm", action="store_true", help="Confirm deactivation.")

    scan_parser = security_subparsers.add_parser("scan-source", help="Scan source files for forbidden actions.")
    scan_parser.add_argument("--path", type=str, required=True, help="Path to scan.")
    scan_parser.add_argument("--json", action="store_true", help="Output as JSON.")

    config_parser = security_subparsers.add_parser("config", help="Dump safely redacted config.")
    config_parser.add_argument("--json", action="store_true", help="Output as JSON.")

def add_quality_parser(subparsers):
    quality_parser = subparsers.add_parser("quality", help="Run Quality Gate checks")
    quality_subparsers = quality_parser.add_subparsers(dest="quality_command", required=True)

    run_parser = quality_subparsers.add_parser("run", help="Run the full Quality Gate")
    run_parser.add_argument("--suite", type=str, help="QualitySuite to run (ALL, SMOKE, UNIT, SECURITY, FAST, etc.)")
    run_parser.add_argument("--gate", type=str, help="QualityGateLevel (RELAXED, STANDARD, STRICT, RELEASE)")
    run_parser.add_argument("--coverage", action="store_true", help="Force coverage run")
    run_parser.add_argument("--static", action="store_true", help="Force static analysis run")
    run_parser.add_argument("--type-check", action="store_true", help="Force type checking run")
    run_parser.add_argument("--regression-smoke", action="store_true", help="Force regression smoke test run")
    run_parser.add_argument("--save-report", action="store_true", help="Force saving report")
    run_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    smoke_parser = quality_subparsers.add_parser("smoke", help="Run only smoke checks")
    smoke_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    security_parser = quality_subparsers.add_parser("security", help="Run only security checks")
    security_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    imports_parser = quality_subparsers.add_parser("imports", help="Run only import checks")
    imports_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    coverage_parser = quality_subparsers.add_parser("coverage", help="Run only coverage checks")
    coverage_parser.add_argument("--threshold", type=float, help="Coverage threshold pct")
    coverage_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    regression_parser = quality_subparsers.add_parser("regression", help="Run only regression checks")
    regression_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    recent_parser = quality_subparsers.add_parser("recent", help="List recent quality runs")
    recent_parser.add_argument("--limit", type=int, default=20, help="Max runs to show")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    config_parser = quality_subparsers.add_parser("config", help="Show quality gate configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")


def setup_package_parser(subparsers):
    package_parser = subparsers.add_parser("package", help="Packaging and release tools")
    package_subparsers = package_parser.add_subparsers(dest="package_command")

    # doctor
    doctor_parser = package_subparsers.add_parser("doctor", help="Run environment doctor")
    doctor_parser.add_argument("--dependencies", action="store_true", help="Include dependency checks")
    doctor_parser.add_argument("--json", action="store_true", help="Output JSON format")

    # deps
    deps_parser = package_subparsers.add_parser("deps", help="Check dependencies")
    deps_parser.add_argument("--dev", action="store_true", help="Check dev dependencies")
    deps_parser.add_argument("--ml", action="store_true", help="Check ML dependencies")
    deps_parser.add_argument("--optional", action="store_true", help="Check optional dependencies")
    deps_parser.add_argument("--json", action="store_true", help="Output JSON format")

    # installers
    installers_parser = package_subparsers.add_parser("installers", help="Generate installer scripts")
    installers_parser.add_argument("--output", type=str, help="Output directory")
    installers_parser.add_argument("--json", action="store_true", help="Output JSON format")

    # manifest
    manifest_parser = package_subparsers.add_parser("manifest", help="Generate release manifest")
    manifest_parser.add_argument("--version", type=str, help="Release version")
    manifest_parser.add_argument("--json", action="store_true", help="Output JSON format")

    # release
    release_parser = package_subparsers.add_parser("release", help="Build release bundle")
    release_parser.add_argument("--manifest-only", action="store_true", help="Only build manifest")
    release_parser.add_argument("--zip", action="store_true", help="Build ZIP bundle")
    release_parser.add_argument("--version", type=str, help="Release version")
    release_parser.add_argument("--run-quality", action="store_true", help="Run quality gate before release")
    release_parser.add_argument("--json", action="store_true", help="Output JSON format")

    # recent
    recent_parser = package_subparsers.add_parser("recent", help="List recent releases")
    recent_parser.add_argument("--limit", type=int, default=10, help="Number of releases to list")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON format")

    # config
    config_parser = package_subparsers.add_parser("config", help="Show packaging configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON format")



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


def add_research_parser(subparsers) -> None:
    # Research commands
    research_parser = subparsers.add_parser("research", help="Manage research ledger, journals, comparisons, and attributions.")
    research_parser.add_argument("args", nargs=argparse.REMAINDER)

def add_adaptive_parser(subparsers) -> None:
    add_research_parser(subparsers)
    # Adaptive Commands
    adaptive_parser = subparsers.add_parser("adaptive", help="Adaptive Strategy Selection & Self-Tuning (Phase 46)")
    adaptive_subparsers = adaptive_parser.add_subparsers(dest="adaptive_command", help="Adaptive commands")

    # Recommend
    rec_parser = adaptive_subparsers.add_parser("recommend", help="Generate strategy recommendations")
    rec_parser.add_argument("--symbols", nargs="+", help="Symbols to analyze")
    rec_parser.add_argument("--strategies", nargs="+", help="Strategies to analyze")
    rec_parser.add_argument("--top", type=int, help="Number of top candidates to return")
    rec_parser.add_argument("--save-report", action="store_true", help="Save the recommendation report")
    rec_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # Symbol
    sym_parser = adaptive_subparsers.add_parser("symbol", help="Get recommendation for a specific symbol")
    sym_parser.add_argument("symbol", help="Symbol to analyze")
    sym_parser.add_argument("--strategies", nargs="+", help="Strategies to analyze")
    sym_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # Refresh Plan
    ref_parser = adaptive_subparsers.add_parser("refresh-plan", help="Generate refresh plan")
    ref_parser.add_argument("--symbols", nargs="+", help="Symbols to analyze")
    ref_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # Model Refresh
    mr_parser = adaptive_subparsers.add_parser("model-refresh", help="Generate model refresh recommendations")
    mr_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # Params
    params_parser = adaptive_subparsers.add_parser("params", help="Manage active parameters")
    params_parser.add_argument("--strategy", help="Filter by strategy")
    params_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # Apply Params
    ap_parser = adaptive_subparsers.add_parser("apply-params", help="Apply adaptive parameter updates")
    ap_parser.add_argument("--from-latest", action="store_true", help="Apply from latest recommendation")
    ap_parser.add_argument("--confirm", action="store_true", help="Confirm update")

    # Policy
    pol_parser = adaptive_subparsers.add_parser("policy", help="Show current adaptive policy")
    pol_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # Recent
    recent_parser = adaptive_subparsers.add_parser("recent", help="List recent recommendations")
    recent_parser.add_argument("--limit", type=int, default=10, help="Number of recent records to show")
    recent_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # Config
    cfg_parser = adaptive_subparsers.add_parser("config", help="Show adaptive engine config")
    cfg_parser.add_argument("--json", action="store_true", help="Output in JSON format")


def add_release_parser(subparsers):

    release_parser = subparsers.add_parser("release", help="Release Manager commands")
    release_subparsers = release_parser.add_subparsers(dest="release_command", help="Release sub-commands")

    # release check
    check_parser = release_subparsers.add_parser("check", help="Run basic release checks")
    check_parser.add_argument("--profile", type=str, help="Release profile")
    check_parser.add_argument("--no-scenarios", action="store_true", help="Skip scenarios")
    check_parser.add_argument("--json", action="store_true", help="Output JSON")

    # release readiness
    readiness_parser = release_subparsers.add_parser("readiness", help="Evaluate release readiness")
    readiness_parser.add_argument("--version", type=str, help="Target version")
    readiness_parser.add_argument("--require-acceptance", action="store_true", help="Require acceptance pass")
    readiness_parser.add_argument("--json", action="store_true", help="Output JSON")

    # release rehearse
    rehearse_parser = release_subparsers.add_parser("rehearse", help="Run safe launch rehearsal")
    rehearse_parser.add_argument("--profile", type=str, help="Release profile")
    rehearse_parser.add_argument("--json", action="store_true", help="Output JSON")

    # release candidate
    candidate_parser = release_subparsers.add_parser("candidate", help="Build release candidate")
    candidate_parser.add_argument("--version", type=str, help="Target version")
    candidate_parser.add_argument("--run-rehearsal", action="store_true", help="Run rehearsal before building")
    candidate_parser.add_argument("--package", action="store_true", help="Build package")
    candidate_parser.add_argument("--confirm", action="store_true", help="Confirm destructive actions (e.g. creating files)")
    candidate_parser.add_argument("--json", action="store_true", help="Output JSON")

    # release notes
    notes_parser = release_subparsers.add_parser("notes", help="Generate release notes")
    notes_parser.add_argument("--version", type=str, help="Target version")
    notes_parser.add_argument("--markdown", action="store_true", help="Output Markdown")
    notes_parser.add_argument("--json", action="store_true", help="Output JSON")

    # release compatibility
    compat_parser = release_subparsers.add_parser("compatibility", help="Run compatibility checks")
    compat_parser.add_argument("--json", action="store_true", help="Output JSON")

    # release recent
    recent_parser = release_subparsers.add_parser("recent", help="List recent release runs")
    recent_parser.add_argument("--limit", type=int, default=10, help="Max number of runs to list")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON")

    # release status
    status_parser = release_subparsers.add_parser("status", help="Show current release status")
    status_parser.add_argument("--json", action="store_true", help="Output JSON")

    # release config
    config_parser = release_subparsers.add_parser("config", help="Show release configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON")

def add_drift_parser(subparsers):
    drift_parser = subparsers.add_parser("drift", help="Drift, Model Decay & Calibration Monitoring")
    subs = drift_parser.add_subparsers(dest="subcommand", help="Drift subcommands")

    # snapshot
    snap_parser = subs.add_parser("snapshot", help="Generate a comprehensive drift snapshot")
    snap_parser.add_argument("--domains", nargs="+", help="Specific domains to analyze (FEATURE, MODEL_SCORE, etc.)")
    snap_parser.add_argument("--symbols", nargs="+", help="Optional specific symbols")
    snap_parser.add_argument("--save", action="store_true", help="Save the snapshot results to disk")
    snap_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # features
    feat_parser = subs.add_parser("features", help="Analyze feature drift")
    feat_parser.add_argument("--reference-days", type=int, default=90, help="Days for reference window")
    feat_parser.add_argument("--current-days", type=int, default=14, help="Days for current window")
    feat_parser.add_argument("--features", nargs="+", help="Specific feature names to analyze")
    feat_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # model
    model_parser = subs.add_parser("model", help="Analyze model score drift and prediction rates")
    model_parser.add_argument("--model-id", type=str, help="Specific model ID to analyze")
    model_parser.add_argument("--latest", action="store_true", help="Use latest model")
    model_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # calibration
    calib_parser = subs.add_parser("calibration", help="Generate model calibration report")
    calib_parser.add_argument("--model-id", type=str, help="Specific model ID to analyze")
    calib_parser.add_argument("--latest", action="store_true", help="Use latest model")
    calib_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # signals
    sig_parser = subs.add_parser("signals", help="Analyze signal decay")
    sig_parser.add_argument("--reference-days", type=int, default=90, help="Days for reference window")
    sig_parser.add_argument("--current-days", type=int, default=14, help="Days for current window")
    sig_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # strategy
    strat_parser = subs.add_parser("strategy", help="Analyze strategy decay")
    strat_parser.add_argument("strategy", type=str, help="Strategy name to analyze")
    strat_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # portfolio
    port_parser = subs.add_parser("portfolio", help="Analyze portfolio drift")
    port_parser.add_argument("--latest", action="store_true", help="Compare current to latest snapshot")
    port_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # reference
    ref_parser = subs.add_parser("reference", help="Manage drift reference windows")
    ref_subs = ref_parser.add_subparsers(dest="ref_subcommand")

    ref_list = ref_subs.add_parser("list", help="List reference windows")
    ref_list.add_argument("--json", action="store_true", help="Output JSON")

    ref_build = ref_subs.add_parser("build", help="Build a new reference window")
    ref_build.add_argument("--domain", type=str, required=True, help="Domain for reference")
    ref_build.add_argument("--days", type=int, default=90, help="Days of data")
    ref_build.add_argument("--confirm", action="store_true", help="Confirm the build (required)")

    ref_show = ref_subs.add_parser("show", help="Show reference window details")
    ref_show.add_argument("reference_id", type=str, help="Reference ID")
    ref_show.add_argument("--json", action="store_true", help="Output JSON")

    # latest
    lat_parser = subs.add_parser("latest", help="Show latest full drift snapshot")
    lat_parser.add_argument("--json", action="store_true", help="Output JSON")

    # recent
    rec_parser = subs.add_parser("recent", help="List recent drift snapshots")
    rec_parser.add_argument("--limit", type=int, default=10, help="Number of snapshots")
    rec_parser.add_argument("--json", action="store_true", help="Output JSON")

    # config
    cfg_parser = subs.add_parser("config", help="Show drift configuration")
    cfg_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Adding maintenance logic integration
    maintenance_parser = subparsers.add_parser('maintenance', help='Run maintenance operations (backup, restore, cleanup, doctor)')
    maintenance_parser.add_argument('subcommand', nargs='...', help='Maintenance subcommand (backup-create, restore, cleanup, doctor, etc)')

def add_governance_parser(subparsers):
    parser = subparsers.add_parser("governance", help="Manage governance, compliance, and audit operations")
    sub = parser.add_subparsers(dest="gov_command", required=True)

    # policy
    pol = sub.add_parser("policy", help="Show current governance policy")
    pol.add_argument("--json", action="store_true", help="Output as JSON")

    # policy-save
    pols = sub.add_parser("policy-save", help="Save default governance policy")
    pols.add_argument("--confirm", action="store_true", help="Confirm saving policy")

    # audit
    aud = sub.add_parser("audit", help="Run governance audit review")
    aud.add_argument("--domains", nargs="+", help="Specific domains to audit")
    aud.add_argument("--lookback-days", type=int, default=30, help="Lookback days")
    aud.add_argument("--json", action="store_true", help="Output as JSON")

    # gate
    gat = sub.add_parser("gate", help="Run a specific governance gate")
    gat.add_argument("gate_type", choices=["release", "runtime", "research-lab", "maintenance", "report"], help="Gate type")
    gat.add_argument("--json", action="store_true", help="Output as JSON")

    # evidence
    evi = sub.add_parser("evidence", help="Build evidence pack")
    evi.add_argument("--pack-name", default="evidence_pack", help="Name of the pack")
    evi.add_argument("--dry-run", action="store_true", help="Do not create archive")
    evi.add_argument("--confirm", action="store_true", help="Confirm archive creation if not dry-run")
    evi.add_argument("--json", action="store_true", help="Output as JSON")

    # attest
    att = sub.add_parser("attest", help="Generate compliance attestation")
    att.add_argument("--from-latest-review", action="store_true", help="Use latest review")
    att.add_argument("--json", action="store_true", help="Output as JSON")

    # latest
    lat = sub.add_parser("latest", help="Show latest audit review")
    lat.add_argument("--json", action="store_true", help="Output as JSON")

    # recent
    rec = sub.add_parser("recent", help="List recent reviews")
    rec.add_argument("--limit", type=int, default=10, help="Max reviews to list")
    rec.add_argument("--json", action="store_true", help="Output as JSON")

    # config
    cfg = sub.add_parser("config", help="Show governance config")
    cfg.add_argument("--json", action="store_true", help="Output as JSON")
def add_config_registry_parser(subparsers):
    parser = subparsers.add_parser("config-registry", help="Config Registry management")
    subparsers_config = parser.add_subparsers(dest="config_command", required=True)

    # list
    p_list = subparsers_config.add_parser("list", help="List config records")
    p_list.add_argument("--module", type=str, help="Filter by module")
    p_list.add_argument("--json", action="store_true", help="JSON output")

    # show
    p_show = subparsers_config.add_parser("show", help="Show specific config record")
    p_show.add_argument("key", type=str, help="Config key")
    p_show.add_argument("--json", action="store_true", help="JSON output")

    # validate
    p_validate = subparsers_config.add_parser("validate", help="Validate current config")
    p_validate.add_argument("--json", action="store_true", help="JSON output")

    # flags
    p_flags = subparsers_config.add_parser("flags", help="Show feature flags")
    p_flags.add_argument("--module", type=str, help="Filter by module")
    p_flags.add_argument("--json", action="store_true", help="JSON output")

    # profiles
    p_profiles = subparsers_config.add_parser("profiles", help="Show runtime profiles")
    p_profiles.add_argument("--json", action="store_true", help="JSON output")

    # profile-preview
    p_preview = subparsers_config.add_parser("profile-preview", help="Preview profile apply diff")
    p_preview.add_argument("profile_type", type=str, help="Profile type")
    p_preview.add_argument("--json", action="store_true", help="JSON output")

    # profile-apply
    p_apply = subparsers_config.add_parser("profile-apply", help="Apply a runtime profile")
    p_apply.add_argument("profile_type", type=str, help="Profile type")
    p_apply.add_argument("--confirm", action="store_true", help="Confirm apply")

    # snapshot
    p_snapshot = subparsers_config.add_parser("snapshot", help="Create a config snapshot")
    p_snapshot.add_argument("--profile", type=str, help="Profile type string")
    p_snapshot.add_argument("--json", action="store_true", help="JSON output")

    # diff
    p_diff = subparsers_config.add_parser("diff", help="Diff snapshots")
    p_diff.add_argument("--old", type=str, help="Old snapshot ID")
    p_diff.add_argument("--new", type=str, help="New snapshot ID")
    p_diff.add_argument("--current-against", type=str, help="Diff current against snapshot ID")
    p_diff.add_argument("--json", action="store_true", help="JSON output")

    # drift
    p_drift = subparsers_config.add_parser("drift", help="Detect config drift")
    p_drift.add_argument("--baseline", type=str, help="Baseline snapshot ID")
    p_drift.add_argument("--json", action="store_true", help="JSON output")

    # gate
    p_gate = subparsers_config.add_parser("gate", help="Run a config gate")
    p_gate.add_argument("gate_type", type=str, choices=["runtime", "release", "scheduler"], help="Gate type")
    p_gate.add_argument("--json", action="store_true", help="JSON output")

    # recent
    p_recent = subparsers_config.add_parser("recent", help="Show recent snapshots")
    p_recent.add_argument("--limit", type=int, default=10, help="Number of snapshots")
    p_recent.add_argument("--json", action="store_true", help="JSON output")

    # config
    p_config = subparsers_config.add_parser("config", help="Show safe redacted config summary")
    p_config.add_argument("--json", action="store_true", help="JSON output")

def add_execution_sim_parser(subparsers):
    add_portfolio_construct_parser(subparsers)
    try:
        add_docs_hub_parser(subparsers)
    except NameError:
        pass
    from bist_signal_bot.cli.portfolio_ledger_commands import setup_portfolio_ledger_parser
    setup_portfolio_ledger_parser(subparsers)
    p = subparsers.add_parser("execution-sim", help="Execution Simulation utilities")
    sp = p.add_subparsers(dest="exec_cmd")

    c = sp.add_parser("cost", help="Estimate transaction costs")
    c.add_argument("--symbol", type=str, required=True)
    c.add_argument("--side", type=str, required=True)
    c.add_argument("--price", type=float, required=True)
    c.add_argument("--quantity", type=float, required=True)
    c.add_argument("--json", action="store_true")

    l = sp.add_parser("liquidity", help="Analyze liquidity")
    l.add_argument("symbol", type=str)
    l.add_argument("--source", type=str, default="local_file")
    l.add_argument("--notional", type=float)
    l.add_argument("--json", action="store_true")

    s = sp.add_parser("slippage", help="Estimate slippage")
    s.add_argument("symbol", type=str)
    s.add_argument("--side", type=str, required=True)
    s.add_argument("--price", type=float, required=True)
    s.add_argument("--quantity", type=float, required=True)
    s.add_argument("--model", type=str)
    s.add_argument("--json", action="store_true")

    f = sp.add_parser("fill", help="Simulate a fill")
    f.add_argument("symbol", type=str)
    f.add_argument("--side", type=str, required=True)
    f.add_argument("--notional", type=float, required=True)
    f.add_argument("--order-type", type=str, default="NEXT_CLOSE")
    f.add_argument("--limit-price", type=float)
    f.add_argument("--json", action="store_true")

    sc = sp.add_parser("scenario", help="Run scenarios")
    sc.add_argument("symbol", type=str)
    sc.add_argument("--side", type=str, required=True)
    sc.add_argument("--notional", type=float, required=True)
    sc.add_argument("--json", action="store_true")

    q = sp.add_parser("quality", help="Execution quality report")
    q.add_argument("--symbol", type=str)
    q.add_argument("--json", action="store_true")

    r = sp.add_parser("recent", help="Recent simulated fills")
    r.add_argument("--symbol", type=str)
    r.add_argument("--json", action="store_true")

    cfg = sp.add_parser("config", help="Execution sim config")
    cfg.add_argument("--json", action="store_true")

def add_strategy_registry_parser(subparsers):
    add_portfolio_construct_parser(subparsers)
    try:
        add_docs_hub_parser(subparsers)
    except NameError:
        pass
    from bist_signal_bot.cli.portfolio_ledger_commands import setup_portfolio_ledger_parser
    setup_portfolio_ledger_parser(subparsers)
    add_portfolio_construct_parser(subparsers)
    try:
        add_docs_hub_parser(subparsers)
    except NameError:
        pass
    from bist_signal_bot.cli.portfolio_ledger_commands import setup_portfolio_ledger_parser
    setup_portfolio_ledger_parser(subparsers)
    registry_parser = subparsers.add_parser("strategy-registry", help="Manage Strategy Registry")
    reg_subs = registry_parser.add_subparsers(dest="registry_command")

    # List
    list_p = reg_subs.add_parser("list", help="List registered strategies")
    list_p.add_argument("--status", type=str, help="Filter by status")
    list_p.add_argument("--family", type=str, help="Filter by family")
    list_p.add_argument("--json", action="store_true", help="Output as JSON")

    # Show
    show_p = reg_subs.add_parser("show", help="Show strategy details")
    show_p.add_argument("strategy_name", type=str, help="Strategy name or ID")
    show_p.add_argument("--json", action="store_true", help="Output as JSON")

    # Sync Catalog
    sync_p = reg_subs.add_parser("sync-catalog", help="Sync strategies from catalog")
    sync_p.add_argument("--dry-run", action="store_true", help="Dry run only")
    sync_p.add_argument("--confirm", action="store_true", help="Confirm sync")

    # Evidence
    ev_p = reg_subs.add_parser("evidence", help="Show strategy evidence")
    ev_p.add_argument("strategy_name", type=str, help="Strategy name or ID")
    ev_p.add_argument("--json", action="store_true", help="Output as JSON")

    # Score
    sc_p = reg_subs.add_parser("score", help="Generate scorecard")
    sc_p.add_argument("strategy_name", type=str, help="Strategy name or ID")
    sc_p.add_argument("--save", action="store_true", help="Save the scorecard")
    sc_p.add_argument("--json", action="store_true", help="Output as JSON")

    # Gate
    gate_p = reg_subs.add_parser("gate", help="Evaluate quality gate")
    gate_p.add_argument("strategy_name", type=str, help="Strategy name or ID")
    gate_p.add_argument("--context", type=str, default="runtime", help="Gate context (scanner, ensemble, runtime)")
    gate_p.add_argument("--json", action="store_true", help="Output as JSON")

    # Promote
    prom_p = reg_subs.add_parser("promote", help="Promote strategy")
    prom_p.add_argument("strategy_name", type=str, help="Strategy name or ID")
    prom_p.add_argument("--to", required=True, type=str, help="Target status")
    prom_p.add_argument("--reason", required=True, type=str, help="Reason for promotion")
    prom_p.add_argument("--confirm", action="store_true", help="Confirm promotion")

    # Demote
    dem_p = reg_subs.add_parser("demote", help="Demote strategy")
    dem_p.add_argument("strategy_name", type=str, help="Strategy name or ID")
    dem_p.add_argument("--to", default="WATCH", type=str, help="Target status")
    dem_p.add_argument("--reason", required=True, type=str, help="Reason for demotion")
    dem_p.add_argument("--confirm", action="store_true", help="Confirm demotion")

    # Block
    blk_p = reg_subs.add_parser("block", help="Block strategy")
    blk_p.add_argument("strategy_name", type=str, help="Strategy name or ID")
    blk_p.add_argument("--reason", required=True, type=str, help="Reason for block")
    blk_p.add_argument("--confirm", action="store_true", help="Confirm block")

    # Events
    evt_p = reg_subs.add_parser("events", help="List lifecycle events")
    evt_p.add_argument("strategy_name", type=str, help="Strategy name or ID")
    evt_p.add_argument("--json", action="store_true", help="Output as JSON")

    # Snapshot
    snap_p = reg_subs.add_parser("snapshot", help="Create or show registry snapshot")
    snap_p.add_argument("--json", action="store_true", help="Output as JSON")

    # Report
    rep_p = reg_subs.add_parser("report", help="Generate strategy registry report")
    rep_p.add_argument("--latest", action="store_true", help="Use latest data")
    rep_p.add_argument("--json", action="store_true", help="Output as JSON")

    # Config
    cfg_p = reg_subs.add_parser("config", help="Show registry configuration")
    cfg_p.add_argument("--json", action="store_true", help="Output as JSON")

def setup_whatif_parser(subparsers):
    whatif_parser = subparsers.add_parser("what-if", help="What-If Scenario Lab commands")
    whatif_subs = whatif_parser.add_subparsers(dest="whatif_command")

    # run
    run_parser = whatif_subs.add_parser("run", help="Run what-if scenarios")
    run_parser.add_argument("--source", type=str, default="latest-portfolio-construction", help="Source type")
    run_parser.add_argument("--source-ref", type=str, help="Source reference ID")
    run_parser.add_argument("--symbols", nargs="+", help="Specific symbols to override")
    run_parser.add_argument("--strategy", type=str, help="Strategy to override")
    run_parser.add_argument("--json", action="store_true", help="Output JSON")

    # compare
    compare_parser = whatif_subs.add_parser("compare", help="Compare scenarios")
    compare_parser.add_argument("--latest", action="store_true", help="Compare latest run")
    compare_parser.add_argument("--run-id", type=str, help="Run ID to compare")
    compare_parser.add_argument("--json", action="store_true", help="Output JSON")

    # sensitivity
    sens_parser = whatif_subs.add_parser("sensitivity", help="Run sensitivity analysis")
    sens_parser.add_argument("--assumption", type=str, required=True, help="Assumption type")
    sens_parser.add_argument("--source", type=str, default="latest-portfolio-construction")
    sens_parser.add_argument("--json", action="store_true")

    # capital-scale
    cap_parser = whatif_subs.add_parser("capital-scale", help="Run capital scaling")
    cap_parser.add_argument("--notionals", nargs="+", type=float, help="List of notionals")
    cap_parser.add_argument("--source", type=str, default="latest-portfolio-construction")
    cap_parser.add_argument("--source-ref", type=str)
    cap_parser.add_argument("--json", action="store_true")

    # policy
    pol_parser = whatif_subs.add_parser("policy", help="Run policy sandbox")
    pol_parser.add_argument("--preset", type=str, required=True, help="Policy preset")
    pol_parser.add_argument("--json", action="store_true")

    # scenario
    scen_parser = whatif_subs.add_parser("scenario", help="Scenario management")
    scen_subs = scen_parser.add_subparsers(dest="scenario_command")
    scen_subs.add_parser("list")
    sh = scen_subs.add_parser("show")
    sh.add_argument("name", type=str)
    sh.add_argument("--json", action="store_true")

    # report
    rep_parser = whatif_subs.add_parser("report", help="View report")
    rep_parser.add_argument("--latest", action="store_true")
    rep_parser.add_argument("--run-id", type=str)
    rep_parser.add_argument("--json", action="store_true")

    # recent
    rec_parser = whatif_subs.add_parser("recent", help="List recent what-if runs")
    rec_parser.add_argument("--limit", type=int, default=10)
    rec_parser.add_argument("--json", action="store_true")

    # config
    conf_parser = whatif_subs.add_parser("config", help="View what-if config")
    conf_parser.add_argument("--json", action="store_true")

def add_disclosures_parser(subparsers):
    parser = subparsers.add_parser("disclosures", help="Manage Disclosure Intelligence")
    subs = parser.add_subparsers(dest="disc_command", required=True)

    imp = subs.add_parser("import", help="Import disclosures")
    imp.add_argument("--file", type=str)
    imp.add_argument("--folder", type=str)
    imp.add_argument("--confirm", action="store_true")
    imp.add_argument("--dry-run", action="store_true")
    imp.add_argument("--json", action="store_true")

    ls = subs.add_parser("list", help="List disclosures")
    ls.add_argument("--symbol", type=str)
    ls.add_argument("--type", type=str)
    ls.add_argument("--limit", type=int, default=50)
    ls.add_argument("--json", action="store_true")

    show = subs.add_parser("show", help="Show disclosure details")
    show.add_argument("disclosure_id", type=str)
    show.add_argument("--json", action="store_true")

    clf = subs.add_parser("classify", help="Classify disclosure")
    clf.add_argument("disclosure_id", type=str)
    clf.add_argument("--json", action="store_true")

    ext = subs.add_parser("extract", help="Extract events")
    ext.add_argument("disclosure_id", type=str)
    ext.add_argument("--create-event", action="store_true")
    ext.add_argument("--confirm", action="store_true")
    ext.add_argument("--json", action="store_true")

    ass = subs.add_parser("assess", help="Assess impact")
    ass.add_argument("disclosure_id", type=str)
    ass.add_argument("--json", action="store_true")

    dig = subs.add_parser("digest", help="Build digest")
    dig.add_argument("--symbol", type=str)
    dig.add_argument("--json", action="store_true")

    lnk = subs.add_parser("link-events", help="Link events")
    lnk.add_argument("disclosure_id", type=str)
    lnk.add_argument("--json", action="store_true")

    rep = subs.add_parser("report", help="Generate report")
    rep.add_argument("--latest", action="store_true")
    rep.add_argument("--json", action="store_true")

    rec = subs.add_parser("recent", help="Recent disclosures")
    rec.add_argument("--limit", type=int, default=10)
    rec.add_argument("--json", action="store_true")

    conf = subs.add_parser("config", help="Show config")
    conf.add_argument("--json", action="store_true")

def add_valuation_parser(subparsers):
    parser = subparsers.add_parser("valuation", help="Valuation Intelligence")
    sub = parser.add_subparsers(dest="val_command", required=True)

    c = sub.add_parser("compute", help="Compute valuation for a symbol")
    c.add_argument("symbol", type=str)
    c.add_argument("--save", action="store_true")
    c.add_argument("--json", action="store_true")

    s = sub.add_parser("show", help="Show valuation for a symbol")
    s.add_argument("symbol", type=str)
    s.add_argument("--json", action="store_true")

    m = sub.add_parser("multiples", help="Show multiples for a symbol")
    m.add_argument("symbol", type=str)
    m.add_argument("--metric", type=str)
    m.add_argument("--json", action="store_true")

    b = sub.add_parser("bands", help="Show valuation bands for a symbol")
    b.add_argument("symbol", type=str)
    b.add_argument("--metric", type=str)
    b.add_argument("--json", action="store_true")

    p = sub.add_parser("compare-peers", help="Compare peers for a symbol")
    p.add_argument("symbol", type=str)
    p.add_argument("--metric", type=str)
    p.add_argument("--json", action="store_true")

    r = sub.add_parser("risk", help="Show valuation risk for a symbol")
    r.add_argument("symbol", type=str)
    r.add_argument("--json", action="store_true")

    rep = sub.add_parser("report", help="Generate valuation report")
    rep.add_argument("--symbol", type=str)
    rep.add_argument("--json", action="store_true")

    rec = sub.add_parser("recent", help="Show recent valuations")
    rec.add_argument("--limit", type=int, default=10)
    rec.add_argument("--json", action="store_true")

    cfg = sub.add_parser("config", help="Show valuation config")
    cfg.add_argument("--json", action="store_true")

# Factors CLI parser will be registered here


def add_review_workflow_parser(subparsers):
    review_workflow_parser = subparsers.add_parser("review-workflow", help="Manage Analyst Review Workflow")
    rw_subparsers = review_workflow_parser.add_subparsers(dest="rw_command", help="Review workflow subcommands")

    rw_create = rw_subparsers.add_parser("create", help="Create review case")
    rw_create.add_argument("--symbol", help="Symbol to review")
    rw_create.add_argument("--strategy", help="Strategy name")
    rw_create.add_argument("--snapshot-id", help="Snapshot ID")
    rw_create.add_argument("--signal-id", help="Signal ID")
    rw_create.add_argument("--save", action="store_true", help="Save the case")
    rw_create.add_argument("--json", action="store_true", help="JSON output")

    rw_list = rw_subparsers.add_parser("list", help="List review cases")
    rw_list.add_argument("--status", help="Filter by status")
    rw_list.add_argument("--symbol", help="Filter by symbol")
    rw_list.add_argument("--json", action="store_true", help="JSON output")

    rw_show = rw_subparsers.add_parser("show", help="Show review case")
    rw_show.add_argument("case_id", help="Case ID")
    rw_show.add_argument("--json", action="store_true", help="JSON output")

    rw_checklist = rw_subparsers.add_parser("checklist", help="Show case checklist")
    rw_checklist.add_argument("case_id", help="Case ID")
    rw_checklist.add_argument("--json", action="store_true", help="JSON output")

    rw_journal = rw_subparsers.add_parser("journal", help="Manage decision journal")
    rw_journal.add_argument("case_id", help="Case ID")
    rw_journal.add_argument("--add-note", help="Note to append")
    rw_journal.add_argument("--actor", help="Actor adding note")
    rw_journal.add_argument("--json", action="store_true", help="JSON output")

    rw_disposition = rw_subparsers.add_parser("disposition", help="Set case disposition")
    rw_disposition.add_argument("case_id", help="Case ID")
    rw_disposition.add_argument("--set", help="Disposition to set")
    rw_disposition.add_argument("--note", help="Journal note")
    rw_disposition.add_argument("--json", action="store_true", help="JSON output")

    rw_signoff = rw_subparsers.add_parser("signoff", help="Manage signoffs")
    rw_signoff.add_argument("id", help="Case ID or Signoff ID")
    rw_signoff.add_argument("--request", action="store_true", help="Request signoff")
    rw_signoff.add_argument("--approve", action="store_true", help="Approve signoff")
    rw_signoff.add_argument("--reject", action="store_true", help="Reject signoff")
    rw_signoff.add_argument("--reason", help="Reason for request or rejection")
    rw_signoff.add_argument("--actor", help="Actor signing off")

    rw_data_actions = rw_subparsers.add_parser("data-actions", help="Manage data actions")
    rw_data_actions.add_argument("--case-id", help="Filter by case ID")
    rw_data_actions.add_argument("--resolve", help="Action ID to resolve")
    rw_data_actions.add_argument("--note", help="Resolution note")
    rw_data_actions.add_argument("--json", action="store_true", help="JSON output")

    rw_close = rw_subparsers.add_parser("close", help="Close case")
    rw_close.add_argument("case_id", help="Case ID")
    rw_close.add_argument("--disposition", help="Final disposition")
    rw_close.add_argument("--note", help="Closure note")
    rw_close.add_argument("--json", action="store_true", help="JSON output")

    rw_patterns = rw_subparsers.add_parser("patterns", help="Detect patterns")
    rw_patterns.add_argument("--symbol", help="Filter by symbol")
    rw_patterns.add_argument("--json", action="store_true", help="JSON output")

    rw_report = rw_subparsers.add_parser("report", help="Generate workflow report")
    rw_report.add_argument("--json", action="store_true", help="JSON output")

    rw_recent = rw_subparsers.add_parser("recent", help="Show recent cases")
    rw_recent.add_argument("--limit", type=int, default=10, help="Limit")
    rw_recent.add_argument("--json", action="store_true", help="JSON output")

    rw_config = rw_subparsers.add_parser("config", help="Show workflow config")
    rw_config.add_argument("--json", action="store_true", help="JSON output")

def add_docs_hub_parser(subparsers):
    parser = subparsers.add_parser("docs-hub", help="Documentation Hub")
    sub = parser.add_subparsers(dest="dh_command", required=True)

    idx = sub.add_parser("index", help="Index local documentation")
    idx.add_argument("--save", action="store_true", help="Save the index")
    idx.add_argument("--json", action="store_true", help="JSON output")

    src = sub.add_parser("search", help="Search local documentation")
    src.add_argument("query", type=str, help="Search query")
    src.add_argument("--audience", type=str, help="Audience filter")
    src.add_argument("--json", action="store_true", help="JSON output")

    show = sub.add_parser("show", help="Show document")
    show.add_argument("path", type=str, help="Path to document")
    show.add_argument("--json", action="store_true", help="JSON output")

    arch = sub.add_parser("architecture", help="Show architecture map")
    arch.add_argument("--mermaid", action="store_true", help="Mermaid output")
    arch.add_argument("--json", action="store_true", help="JSON output")

    cook = sub.add_parser("cookbook", help="Show command cookbook")
    cook.add_argument("--profile", type=str, help="Profile filter")
    cook.add_argument("--module", type=str, help="Module filter")
    cook.add_argument("--json", action="store_true", help="JSON output")

    tr = sub.add_parser("troubleshoot", help="Show troubleshooting KB")
    tr.add_argument("query", type=str, nargs="?", help="Search query")
    tr.add_argument("--json", action="store_true", help="JSON output")

    cov = sub.add_parser("coverage", help="Analyze documentation coverage")
    cov.add_argument("--json", action="store_true", help="JSON output")

    hand = sub.add_parser("handoff", help="Generate MVP handoff manifest")
    hand.add_argument("--save", action="store_true", help="Save handoff")
    hand.add_argument("--json", action="store_true", help="JSON output")

    rep = sub.add_parser("report", help="Generate Docs Hub report")
    rep.add_argument("--latest", action="store_true", help="Load latest report")
    rep.add_argument("--json", action="store_true", help="JSON output")

    rec = sub.add_parser("recent", help="Show recent docs hub actions")
    rec.add_argument("--limit", type=int, default=10, help="Max rows")
    rec.add_argument("--json", action="store_true", help="JSON output")

    cfg = sub.add_parser("config", help="Show docs hub configuration")
    cfg.add_argument("--json", action="store_true", help="JSON output")

def add_feature_store_parser(subparsers):
    parser = subparsers.add_parser("feature-store", help="Local Feature Store and Governance")
    sub = parser.add_subparsers(dest="feature_store_command", required=True)

    contracts = sub.add_parser("contracts", help="Manage feature contracts")
    contracts.add_argument("show", nargs="?", default=None)
    contracts.add_argument("show_contract", nargs="?", default=None)
    contracts.add_argument("--json", action="store_true")

    lst = sub.add_parser("list", help="List registered features")
    lst.add_argument("--kind", type=str, help="Filter by kind (e.g., TECHNICAL)")
    lst.add_argument("--json", action="store_true")

    sets = sub.add_parser("sets", help="Manage feature sets")
    sets.add_argument("show_set", nargs="?", type=str, help="Feature set name to show")
    sets.add_argument("--json", action="store_true")

    compute = sub.add_parser("compute", help="Compute features or feature sets")
    compute.add_argument("--symbol", type=str, help="Compute single feature for symbol")
    compute.add_argument("--feature", type=str, help="Feature name to compute")
    compute.add_argument("--symbols", type=str, nargs="+", help="Compute feature set for symbols")
    compute.add_argument("--set", type=str, help="Feature set name")
    compute.add_argument("--save", action="store_true")
    compute.add_argument("--json", action="store_true")

    serve = sub.add_parser("serve", help="Serve feature frames")
    serve.add_argument("--scanner", action="store_true", help="Serve for scanner")
    serve.add_argument("--ml", action="store_true", help="Serve for ML")
    serve.add_argument("--context", action="store_true", help="Serve for context")
    serve.add_argument("--symbol", type=str, help="Symbol for context")
    serve.add_argument("--symbols", type=str, nargs="+", help="Symbols for scanner/ml")
    serve.add_argument("--set", type=str, help="Feature set name")
    serve.add_argument("--json", action="store_true")

    quality = sub.add_parser("quality", help="Assess feature quality")
    quality.add_argument("--frame-id", type=str, help="Assess existing frame")
    quality.add_argument("--set", type=str, help="Assess new frame for set")
    quality.add_argument("--symbols", type=str, nargs="+", help="Symbols for new frame")
    quality.add_argument("--json", action="store_true")

    drift = sub.add_parser("drift", help="Detect feature drift")
    drift.add_argument("--feature", type=str, help="Feature name")
    drift.add_argument("--set", type=str, help="Feature set name")
    drift.add_argument("--json", action="store_true")

    leakage = sub.add_parser("leakage", help="Guard against feature leakage")
    leakage.add_argument("--frame-id", type=str, help="Check existing frame")
    leakage.add_argument("--set", type=str, help="Check new frame for set")
    leakage.add_argument("--symbols", type=str, nargs="+", help="Symbols for new frame")
    leakage.add_argument("--json", action="store_true")

    lineage = sub.add_parser("lineage", help="Track feature lineage")
    lineage.add_argument("feature", nargs="?", type=str, help="Feature name")
    lineage.add_argument("--set", type=str, help="Feature set name")
    lineage.add_argument("--json", action="store_true")

    versions = sub.add_parser("versions", help="Manage feature versions")
    versions.add_argument("feature", nargs="?", type=str, help="Feature name")
    versions.add_argument("--json", action="store_true")

    report = sub.add_parser("report", help="Generate feature store report")
    report.add_argument("--latest", action="store_true")
    report.add_argument("--json", action="store_true")

    recent = sub.add_parser("recent", help="Show recent feature store activity")
    recent.add_argument("--limit", type=int, default=10)
    recent.add_argument("--json", action="store_true")

    config = sub.add_parser("config", help="Show feature store config")
    config.add_argument("--json", action="store_true")

def add_final_handoff_parser(subparsers):
    parser = subparsers.add_parser("final-handoff", help="Final MVP Handoff and Release")
    sub = parser.add_subparsers(dest="handoff_command", required=True)

    build = sub.add_parser("build", help="Build final handoff manifest")
    build.add_argument("--save", action="store_true", help="Save the manifest")
    build.add_argument("--json", action="store_true", help="JSON output")

    show = sub.add_parser("show", help="Show final handoff manifest")
    show.add_argument("--latest", action="store_true", help="Load the latest manifest")
    show.add_argument("--json", action="store_true", help="JSON output")

    rp = sub.add_parser("release-pack", help="Build and show final release pack")
    rp.add_argument("--save", action="store_true", help="Save the release pack")
    rp.add_argument("--json", action="store_true", help="JSON output")

    op = sub.add_parser("operator-playbook", help="Generate operator playbook")
    op.add_argument("--json", action="store_true", help="JSON output")

    dp = sub.add_parser("developer-playbook", help="Generate developer playbook")
    dp.add_argument("--json", action="store_true", help="JSON output")

    cm = sub.add_parser("command-map", help="Generate final command map")
    cm.add_argument("--audience", type=str, help="Filter by audience (USER, OPERATOR, DEVELOPER, ALL)")
    cm.add_argument("--json", action="store_true", help="JSON output")

    mm = sub.add_parser("module-map", help="Generate final module map")
    mm.add_argument("--json", action="store_true", help="JSON output")

    rm = sub.add_parser("roadmap", help="Generate post-release roadmap")
    rm.add_argument("--json", action="store_true", help="JSON output")

    maint = sub.add_parser("maintenance", help="Generate maintenance tasks")
    maint.add_argument("--cadence", type=str, help="Filter by cadence (DAILY, WEEKLY, MONTHLY, ON_DEMAND)")
    maint.add_argument("--json", action="store_true", help="JSON output")

    rep = sub.add_parser("report", help="Generate final handoff report")
    rep.add_argument("--latest", action="store_true", help="Load latest report data")
    rep.add_argument("--json", action="store_true", help="JSON output")

    rec = sub.add_parser("recent", help="Show recent handoff actions")
    rec.add_argument("--limit", type=int, default=10, help="Max rows")
    rec.add_argument("--json", action="store_true", help="JSON output")

    cfg = sub.add_parser("config", help="Show final handoff configuration")
    cfg.add_argument("--json", action="store_true", help="JSON output")
