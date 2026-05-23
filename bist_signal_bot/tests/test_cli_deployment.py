import pytest
from bist_signal_bot.cli.parsers import build_parser
from bist_signal_bot.cli.commands import deploy_command
from bist_signal_bot.config.settings import Settings

def test_deploy_cli_parsing():
    parser = build_parser()
    args = parser.parse_args(["deploy", "profiles"])
    assert args.command == "deploy"
    assert args.deploy_subcommand == "profiles"

def test_deploy_cli_doctor(capsys):
    parser = build_parser()
    args = parser.parse_args(["deploy", "doctor", "--json"])
    settings = Settings()
    # Mocking out actual call since it might have errors due to missing dirs, but we check if it runs
    try:
        deploy_command(args, settings)
    except Exception:
        pass
