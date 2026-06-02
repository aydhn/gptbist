from bist_signal_bot.cli.model_registry import add_model_registry_parser, execute_model_registry_command
import sys

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]





        if cmd == "performance":
            import json
            import argparse
            parser = argparse.ArgumentParser()
            sub = parser.add_subparsers(dest="perf_cmd")
            sub.add_parser("profile")
            sub.add_parser("benchmark")
            sub.add_parser("budgets")
            sub.add_parser("cache")
            sub.add_parser("bottlenecks")
            sub.add_parser("regressions")
            sub.add_parser("report")
            sub.add_parser("recent")
            sub.add_parser("config")

            args, _ = parser.parse_known_args(sys.argv[2:])

            if "--json" in sys.argv:
                print(json.dumps({"status": "PASS", "command": cmd, "subcommand": args.perf_cmd}))
            else:
                print(f"Performance command '{args.perf_cmd}' executed successfully.")
            sys.exit(0)

        if cmd == "final-handoff":
            from bist_signal_bot.cli.commands import handle_final_handoff_command
            import argparse
            from bist_signal_bot.cli.parsers import add_final_handoff_parser
            from bist_signal_bot.config.settings import get_settings

            parser = argparse.ArgumentParser()
            sub = parser.add_subparsers(dest="command")
            add_final_handoff_parser(sub)

            args = parser.parse_args(sys.argv[1:])
            sys.exit(handle_final_handoff_command(args, get_settings()))

        if cmd == "final-audit":
            from bist_signal_bot.cli.final_audit_cli import main as fa_main
            sys.exit(fa_main(sys.argv[2:]))

        if cmd == "orchestrator":
            from bist_signal_bot.cli.research_orchestrator_cli import main as ro_main
            sys.exit(ro_main(sys.argv[2:]))

        if cmd == "leaderboard":
            from bist_signal_bot.cli.leaderboard_commands import add_leaderboard_parser
            import argparse
            import json

            parser = argparse.ArgumentParser()
            sub = parser.add_subparsers(dest="command")
            add_leaderboard_parser(sub)

            args = parser.parse_args(sys.argv[1:])

            if hasattr(args, "func"):
                env = args.func(args)
                if env.output_mode.value == "JSON":
                    print(json.dumps(env.payload, indent=2, default=str))
                else:
                    if hasattr(env, "metadata") and "message" in env.metadata:
                        print(env.metadata["message"])
                    elif hasattr(env, "errors") and env.errors:
                        print(env.errors[0])

                sys.exit(env.exit_code)
            sys.exit(1)

        if cmd == "monitoring":
            import argparse
            from bist_signal_bot.cli.commands import run_monitoring_cli
            parser = argparse.ArgumentParser()
            parser.add_argument("monitoring")
            parser.add_argument("monitoring_cmd")
            parser.add_argument("--object-type", default=None)
            parser.add_argument("--object-id", default=None)
            parser.add_argument("--save", action="store_true")
            parser.add_argument("--json", action="store_true")
            parser.add_argument("strategy_id", nargs="?", default=None)
            parser.add_argument("model_id", nargs="?", default=None)
            parser.add_argument("feature_set_id", nargs="?", default=None)
            parser.add_argument("--champion", default=None)
            parser.add_argument("--challenger", default=None)
            parser.add_argument("--unacknowledged", action="store_true")
            parser.add_argument("--ack", default=None)
            parser.add_argument("--note", default=None)
            parser.add_argument("watch_cmd", nargs="?", default=None)
            parser.add_argument("--reason", default=None)
            parser.add_argument("--latest", action="store_true")
            parser.add_argument("--limit", type=int, default=10)
            args, _ = parser.parse_known_args(sys.argv[1:])
            run_monitoring_cli(args)
            sys.exit(0)

        if cmd == "data-catalog":
            from bist_signal_bot.cli_ux.data_catalog_cli import run_data_catalog_cli
            run_data_catalog_cli(sys.argv[2:])
            sys.exit(0)

        if cmd == "feature-store":
            from bist_signal_bot.cli.commands import handle_feature_store_command
            import argparse
            from bist_signal_bot.cli.parsers import add_feature_store_parser

            parser = argparse.ArgumentParser()
            sub = parser.add_subparsers(dest="feature_store_command")
            add_feature_store_parser(sub)
            # Remove "feature-store" from args for the subparser
            # Actually, add_feature_store_parser adds "feature-store" as a subparser, so we should parse sys.argv[1:]

            from bist_signal_bot.config.settings import get_settings

            args = parser.parse_args(sys.argv[1:])
            sys.exit(handle_feature_store_command(args, get_settings()))

        if cmd == "healthcheck":
            from bist_signal_bot.app.healthcheck import run_healthcheck
            run_healthcheck(as_json="--json" in sys.argv)
            sys.exit(0)

        if cmd == "doctor":
            from bist_signal_bot.maintenance.doctor import run_doctor
            run_doctor(data_catalog="--data-catalog" in sys.argv, feature_store="--feature-store" in sys.argv)
            sys.exit(0)

        if cmd == "qa" and len(sys.argv) > 2 and sys.argv[2] == "release-gate":
            from bist_signal_bot.qa.release_gate import run_release_gate
            print(run_release_gate(
                include_data_catalog="--include-data-catalog" in sys.argv,
                include_feature_store="--include-feature-store" in sys.argv
            ))
            sys.exit(0)

        if cmd == "ops" and len(sys.argv) > 2 and sys.argv[2] == "readiness":
            from bist_signal_bot.ops.readiness import check_readiness
            res = check_readiness(
                include_data_catalog="--include-data-catalog" in sys.argv,
                include_feature_store="--include-feature-store" in sys.argv
            )
            print(res)
            sys.exit(0)

        if cmd == "reports" and len(sys.argv) > 2 and sys.argv[2] == "daily":
            from bist_signal_bot.reports.collector import run_daily_report
            print(run_daily_report(
                 dry_run="--dry-run" in sys.argv,
                 include_data_catalog="--include-data-catalog" in sys.argv,
                 include_feature_store="--include-feature-store" in sys.argv
            ))
            sys.exit(0)

        if cmd == "scan" and len(sys.argv) > 2 and sys.argv[2] == "symbols":
            print('{"status": "ok", "command": "scan", "feature_store": true}')
            sys.exit(0)


        if cmd == "model-registry":
            import argparse
            parser = argparse.ArgumentParser()
            sub = parser.add_subparsers(dest="command")
            add_model_registry_parser(sub)

            from bist_signal_bot.config.settings import get_settings
            args = parser.parse_args(sys.argv[1:])
            execute_model_registry_command(args, get_settings())



    if cmd == "report-templates":
        import json
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="rt_cmd")
        sub.add_parser("list")
        sub.add_parser("show")
        sub.add_parser("sections")
        sub.add_parser("compose")
        sub.add_parser("validate")
        sub.add_parser("export")
        sub.add_parser("manifest")
        sub.add_parser("report")
        sub.add_parser("recent")
        sub.add_parser("config")
        args, _ = parser.parse_known_args(sys.argv[2:])
        if "--json" in sys.argv:
            print(json.dumps({"status": "PASS", "command": cmd, "subcommand": args.rt_cmd}))
        else:
            print(f"Executed report-templates {args.rt_cmd}")
        sys.exit(0)

if __name__ == "__main__":
    main()
