from bist_signal_bot.cli.main import run_cli
import sys

sys.argv = ["bist_signal_bot", "monitor", "heartbeat"]
run_cli()
sys.argv = ["bist_signal_bot", "monitor", "diagnostics"]
run_cli()
