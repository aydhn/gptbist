import os
from pathlib import Path

cli_path = Path("bist_signal_bot/cli/__main__.py")
if not cli_path.exists():
    cli_path.parent.mkdir(parents=True, exist_ok=True)
    cli_path.write_text("""import argparse
from bist_signal_bot.config.settings import Settings

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    try:
        from bist_signal_bot.cli.data_import_cli import add_data_import_parser, handle_data_import_cmd
        add_data_import_parser(subparsers)
    except ImportError:
        pass

    args = parser.parse_args()
    settings = Settings()

    if args.command == "data-import":
        handle_data_import_cmd(args, settings)

if __name__ == "__main__":
    main()
""")
