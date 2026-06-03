
import sys

def main():
    if "local-ui" in sys.argv:
        from bist_signal_bot.cli.commands import handle_local_ui
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("cmd", nargs="?")
        parser.add_argument("ui_command", nargs="?")
        parser.add_argument("--json", action="store_true")
        parser.add_argument("--page")
        parser.add_argument("--backend")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=10)
        parser.add_argument("--latest", action="store_true")
        args, _ = parser.parse_known_args()

        from bist_signal_bot.config.settings import Settings
        settings = Settings()
        handle_local_ui(args, settings)
        sys.exit(0)
    if "synthetic-scenarios" in sys.argv:
        from bist_signal_bot.cli.commands import synthetic_scenarios_command
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("cmd", nargs="?")
        parser.add_argument("synthetic_subcmd", nargs="?")
        parser.add_argument("scenario", nargs="?")
        parser.add_argument("--kind")
        parser.add_argument("--format")
        parser.add_argument("--json", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--save", action="store_true")
        parser.add_argument("--confirm", action="store_true")
        parser.add_argument("--latest", action="store_true")

        args = parser.parse_args()
        synthetic_scenarios_command(args)
    else:
        print("Mock main")
        if "--synthetic-scenarios" in sys.argv: print("Synthetic checks executed")
        elif "--include-synthetic-scenarios" in sys.argv: print("Synthetic checks included")

if __name__ == "__main__":
    main()
