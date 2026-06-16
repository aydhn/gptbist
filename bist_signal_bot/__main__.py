"""Package entry point.

``python -m bist_signal_bot ...`` and the ``bist-signal-bot`` console script both
delegate to the single real CLI dispatcher in :mod:`bist_signal_bot.cli.main`.

Previously this module contained a *mock* argparse CLI that printed
``"<cmd> executed successfully (mock)"`` for almost every command, completely
shadowing the real 550-command CLI. That mock has been removed.
"""
import sys

from bist_signal_bot.cli.main import run_cli


def main() -> int:
    return run_cli(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
