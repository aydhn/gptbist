

def route_calibration(args_to_parse: list[str]) -> int:
    import argparse
    from bist_signal_bot.cli.calibration_cli import setup_calibration_parser, handle_calibration_command
    from bist_signal_bot.cli_ux.cli_parser import add_cli_ux_subparser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_cli_ux_subparser(subparsers)
    setup_calibration_parser(subparsers)

    args, _ = parser.parse_known_args(args_to_parse)

    from bist_signal_bot.config.settings import Settings

    class MockCtx:
        def __init__(self, settings):
            self.settings = settings
    ctx = MockCtx(settings=Settings())
    return handle_calibration_command(args, ctx)

def route_portfolio_construct(args_to_parse: list[str]) -> int:
    import argparse
    root_parser = argparse.ArgumentParser()
    root_subs = root_parser.add_subparsers(dest="command")
    from bist_signal_bot.cli.parsers import add_portfolio_construct_parser
    add_portfolio_construct_parser(root_subs)
    args, unknown = root_parser.parse_known_args(args_to_parse)

    from bist_signal_bot.cli.portfolio_construct_commands import handle_portfolio_construct_command
    from bist_signal_bot.config.settings import get_settings
    handle_portfolio_construct_command(args, get_settings())
    return 0

def route_strategy_registry(args_to_parse: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="registry_command")
    from bist_signal_bot.cli.parsers import add_strategy_registry_parser
    add_strategy_registry_parser(subparsers)

    args, _ = parser.parse_known_args(['strategy-registry'] + args_to_parse[1:])
    from bist_signal_bot.cli.commands import handle_strategy_registry
    try:
         from bist_signal_bot.config.settings import Settings
         s = Settings()
         return handle_strategy_registry(args, s)
    except Exception as e:
         print(f"Strategy Registry Error: {e}")
    return 1

def route_config_registry(args_to_parse: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    from bist_signal_bot.cli_ux.cli_parser import add_cli_ux_subparser
    add_cli_ux_subparser(subparsers)
    from bist_signal_bot.cli.parsers import add_config_registry_parser
    add_config_registry_parser(subparsers)

    args, _ = parser.parse_known_args(['config-registry'] + args_to_parse[1:])
    from bist_signal_bot.cli.commands_registry import run_config_registry_command
    try:
         from bist_signal_bot.config.settings import Settings
         s = Settings()
         run_config_registry_command(args, s)
    except Exception as e:
         print(f"Config Registry Error: {e}")
    return 0

def route_governance(args_to_parse: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    from bist_signal_bot.cli_ux.cli_parser import add_cli_ux_subparser
    add_cli_ux_subparser(subparsers)
    from bist_signal_bot.cli.parsers import add_governance_parser
    from bist_signal_bot.cli.event_calendar_group import register_event_calendar_commands
    register_event_calendar_commands(subparsers)
    add_governance_parser(subparsers)

    args, _ = parser.parse_known_args(['governance'] + args_to_parse[1:])
    from bist_signal_bot.cli.commands import handle_governance_command
    handle_governance_command(args)
    return 0

def route_event_calendar(args_to_parse: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    from bist_signal_bot.cli_ux.cli_parser import add_cli_ux_subparser
    add_cli_ux_subparser(subparsers)
    from bist_signal_bot.cli.event_calendar_group import register_event_calendar_commands
    register_event_calendar_commands(subparsers)
    args, _ = parser.parse_known_args(["event-calendar"] + args_to_parse[1:])
    from bist_signal_bot.cli.event_calendar_group import handle_event_calendar_command
    handle_event_calendar_command(args)
    return 0

def route_valuation(args_to_parse: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    from bist_signal_bot.cli_ux.cli_parser import add_cli_ux_subparser
    add_cli_ux_subparser(subparsers)
    from bist_signal_bot.cli.parsers import add_valuation_parser
    add_valuation_parser(subparsers)
    args, _ = parser.parse_known_args(['valuation'] + args_to_parse[1:])

    from bist_signal_bot.cli.valuation_commands import (
        cmd_valuation_compute, cmd_valuation_show, cmd_valuation_multiples,
        cmd_valuation_bands, cmd_valuation_compare_peers, cmd_valuation_risk,
        cmd_valuation_report, cmd_valuation_recent, cmd_valuation_config
    )
    from bist_signal_bot.app.bootstrap import bootstrap_app
    ctx = bootstrap_app()
    val_cmd = args.val_command
    if val_cmd == "compute":
        return cmd_valuation_compute(args, ctx)
    elif val_cmd == "show":
        return cmd_valuation_show(args, ctx)
    elif val_cmd == "multiples":
        return cmd_valuation_multiples(args, ctx)
    elif val_cmd == "bands":
        return cmd_valuation_bands(args, ctx)
    elif val_cmd == "compare-peers":
        return cmd_valuation_compare_peers(args, ctx)
    elif val_cmd == "risk":
        return cmd_valuation_risk(args, ctx)
    elif val_cmd == "report":
        return cmd_valuation_report(args, ctx)
    elif val_cmd == "recent":
        return cmd_valuation_recent(args, ctx)
    elif val_cmd == "config":
        return cmd_valuation_config(args, ctx)
    return 0

def route_what_if(args_to_parse: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    from bist_signal_bot.cli_ux.cli_parser import add_cli_ux_subparser
    add_cli_ux_subparser(subparsers)
    from bist_signal_bot.cli.parsers import setup_whatif_parser
    setup_whatif_parser(subparsers)
    args, _ = parser.parse_known_args(['what-if'] + args_to_parse[1:])
    from bist_signal_bot.cli.commands import handle_whatif_commands
    return handle_whatif_commands(args)

def route_explain(args_to_parse: list[str]) -> int:
    from bist_signal_bot.cli.explain import handle_explain
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    from bist_signal_bot.cli_ux.cli_parser import add_cli_ux_subparser
    add_cli_ux_subparser(subparsers)
    from bist_signal_bot.cli.explain import setup_parser
    setup_parser(subparsers)
    args, _ = parser.parse_known_args(args_to_parse)
    handle_explain(args)
    return 0

def route_qa(args_to_parse: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="qa_command")

    fix_p = subparsers.add_parser("fixtures")
    fix_subs = fix_p.add_subparsers(dest="action")
    fix_subs.add_parser("validate")
    fix_build = fix_subs.add_parser("build-synthetic")
    fix_build.add_argument("--output", default=".qa_tmp/fixtures")
    fix_man = fix_subs.add_parser("manifest")
    fix_man.add_argument("--json", action="store_true")

    scen_p = subparsers.add_parser("scenarios")
    scen_subs = scen_p.add_subparsers(dest="action")
    scen_subs.add_parser("list")
    scen_show = scen_subs.add_parser("show")
    scen_show.add_argument("name")
    scen_show.add_argument("--json", action="store_true")

    rep_p = subparsers.add_parser("replay")
    rep_p.add_argument("--scenario")
    rep_p.add_argument("--all", action="store_true")
    rep_p.add_argument("--json", action="store_true")

    smoke_p = subparsers.add_parser("smoke")
    smoke_p.add_argument("--critical-only", action="store_true")
    smoke_p.add_argument("--json", action="store_true")

    reg_p = subparsers.add_parser("regression")
    reg_p.add_argument("--json", action="store_true")

    rel_p = subparsers.add_parser("release-gate")
    rel_p.add_argument("--skip-pytest", action="store_true")
    rel_p.add_argument("--json", action="store_true")

    saf_p = subparsers.add_parser("safety")
    saf_p.add_argument("--json", action="store_true")

    noe_p = subparsers.add_parser("no-external-calls")
    noe_p.add_argument("--json", action="store_true")

    repr_p = subparsers.add_parser("reproducibility")
    repr_subs = repr_p.add_subparsers(dest="action")
    repr_build = repr_subs.add_parser("build")
    repr_build.add_argument("--json", action="store_true")

    cov_p = subparsers.add_parser("coverage")
    cov_p.add_argument("--json", action="store_true")

    repo_p = subparsers.add_parser("report")
    repo_p.add_argument("--latest", action="store_true")
    repo_p.add_argument("--json", action="store_true")

    rec_p = subparsers.add_parser("recent")
    rec_p.add_argument("--limit", type=int, default=10)
    rec_p.add_argument("--json", action="store_true")

    cfg_p = subparsers.add_parser("config")
    cfg_p.add_argument("--json", action="store_true")

    args, _ = parser.parse_known_args(args_to_parse[1:])
    from bist_signal_bot.cli.commands import handle_qa_command
    try:
        from bist_signal_bot.config.settings import Settings
        s = Settings()
        return handle_qa_command(args, s)
    except Exception as e:
        print(f"QA Error: {e}")
    return 1
