import sys

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "data-catalog":
        from bist_signal_bot.cli_ux.data_catalog_cli import run_data_catalog_cli
        run_data_catalog_cli(sys.argv[2:])
        sys.exit(0)
    # the rest of the cli dispatch would normally go here
