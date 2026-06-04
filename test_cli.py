import sys
from bist_signal_bot.cli.release_policy_cli import setup_release_policy_parser, handle_release_policy_command
import argparse

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="rp_command")
setup_release_policy_parser(subparsers)

args = parser.parse_args(["release-policy", "status"])
handle_release_policy_command(args)
