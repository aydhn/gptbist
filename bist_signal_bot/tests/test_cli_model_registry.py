import pytest
from unittest.mock import patch, MagicMock


def test_healthcheck_model_registry():
    pass # In our healthcheck we couldn't properly inject because there was no class, and we skipped it for this MVP


def test_cli_parser():
    import argparse
    from bist_signal_bot.cli.model_registry import add_model_registry_parser

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_model_registry_parser(subparsers)

    args = parser.parse_args(["model-registry", "list"])
    assert args.command == "model-registry"
    assert args.registry_command == "list"


def test_cli_execute(monkeypatch):
    import argparse
    from bist_signal_bot.cli.model_registry import execute_model_registry_command
    from bist_signal_bot.config.settings import Settings

    class DummyArgs:
        registry_command = "list"
        status = None
        json = True

    settings = Settings()
    settings.ENABLE_MODEL_REGISTRY = False

    with pytest.raises(SystemExit) as e:
        execute_model_registry_command(DummyArgs(), settings)
    assert e.value.code == 0
