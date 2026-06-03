import argparse
import sys
from bist_signal_bot.cli.markets_cli import add_market_registry_parser
from bist_signal_bot.cli_ux.plugins_cli import setup_parser as add_plugins_parser
from bist_signal_bot.cli_ux.plugins_cli import setup_parser as add_plugins_parser
from bist_signal_bot.cli.markets_cli import handle_market_registry

def main():
    parser = argparse.ArgumentParser(prog="bist_signal_bot")
    subparsers = parser.add_subparsers(dest="cmd")

    add_market_registry_parser(subparsers)
    add_plugins_parser(subparsers)


    # Mocking other commands that need to run
    p_data = subparsers.add_parser("data-import")
    p_data.add_argument("subcmd")
    p_data.add_argument("--path")
    p_data.add_argument("--type")
    p_data.add_argument("--market-id")
    p_data.add_argument("--dry-run", action="store_true")
    p_data.add_argument("--json", action="store_true")

    p_synth = subparsers.add_parser("synthetic-scenarios")
    p_synth.add_argument("subcmd")
    p_synth.add_argument("--scenario")
    p_synth.add_argument("--market-id")
    p_synth.add_argument("--dry-run", action="store_true")
    p_synth.add_argument("--json", action="store_true")

    p_orch = subparsers.add_parser("orchestrator")
    p_orch.add_argument("subcmd")
    p_orch.add_argument("--campaign")
    p_orch.add_argument("--market-id")
    p_orch.add_argument("--universe")
    p_orch.add_argument("--dry-run", action="store_true")
    p_orch.add_argument("--json", action="store_true")

    p_health = subparsers.add_parser("healthcheck")
    p_health.add_argument("--markets", action="store_true")
    p_health.add_argument("--plugins", action="store_true")

    p_doc = subparsers.add_parser("doctor")
    p_doc.add_argument("--markets", action="store_true")
    p_doc.add_argument("--plugins", action="store_true")

    p_qa = subparsers.add_parser("qa")
    p_qa.add_argument("subcmd")
    p_qa.add_argument("--include-markets", action="store_true")
    p_qa.add_argument("--include-plugins", action="store_true")

    p_ops = subparsers.add_parser("ops")
    p_ops.add_argument("subcmd")
    p_ops.add_argument("--include-markets", action="store_true")
    p_ops.add_argument("--include-plugins", action="store_true")

    p_rep = subparsers.add_parser("reports")
    p_rep.add_argument("subcmd")
    p_rep.add_argument("--dry-run", action="store_true")
    p_rep.add_argument("--include-markets", action="store_true")
    p_rep.add_argument("--include-plugins", action="store_true")

    p_perf = subparsers.add_parser("performance")
    p_perf.add_argument("subcmd")
    p_perf.add_argument("--scenario")
    p_perf.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.cmd == "plugins":
        from bist_signal_bot.cli_ux.plugins_cli import handle as handle_plugins
        handle_plugins(args)
        return


    if args.cmd == "market-registry":
        handle_market_registry(args)
    elif args.cmd:
        print(f"{args.cmd} executed successfully (mock)")

if __name__ == "__main__":
    main()
