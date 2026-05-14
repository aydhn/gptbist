from bist_signal_bot.cli.main import run_cli
import sys

cmds = [
    ["bist_signal_bot", "monitor", "heartbeat"],
    ["bist_signal_bot", "monitor", "heartbeat", "--component", "RUNTIME", "--status", "HEALTHY", "--message", "manual heartbeat"],
    ["bist_signal_bot", "monitor", "diagnostics"],
    ["bist_signal_bot", "monitor", "alerts", "--limit", "20"],
    ["bist_signal_bot", "monitor", "test-alert"],
    ["bist_signal_bot", "monitor", "metrics", "--limit", "100"],
    ["bist_signal_bot", "monitor", "repair", "--dry-run"],
    ["bist_signal_bot", "monitor", "repair", "--clear-stale-lock"],
    ["bist_signal_bot", "monitor", "cleanup", "--retention-days", "30", "--dry-run"],
    ["bist_signal_bot", "monitor", "config"],
]

for cmd in cmds:
    print(f"\n--- Running: {' '.join(cmd)} ---")
    sys.argv = cmd
    run_cli()
