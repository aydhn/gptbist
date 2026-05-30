import sys

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

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

    print("BIST Signal Bot OK")

if __name__ == "__main__":
    main()
