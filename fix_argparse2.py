with open("bist_signal_bot/cli/main.py", "a") as f:
    f.write("""
def run_cli():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'factors':
        from bist_signal_bot.cli.factors_commands import factors_cli
        sys.argv.pop(1)
        factors_cli()
        sys.exit(0)
""")
