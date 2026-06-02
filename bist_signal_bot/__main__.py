
import sys

def main():
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
