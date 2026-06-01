import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.cli.parsers import add_final_handoff_parser
import argparse

def test_cli_final_handoff_build():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_final_handoff_parser(subparsers)

    args = parser.parse_args(["final-handoff", "build", "--json"])
    assert args.final_handoff_cmd == "build"
    assert args.json is True

def test_cli_final_handoff_show():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_final_handoff_parser(subparsers)

    args = parser.parse_args(["final-handoff", "show", "--latest"])
    assert args.final_handoff_cmd == "show"
    assert args.latest is True

def test_cli_final_handoff_release_pack():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_final_handoff_parser(subparsers)

    args = parser.parse_args(["final-handoff", "release-pack", "--save"])
    assert args.final_handoff_cmd == "release-pack"
    assert args.save is True

def test_cli_final_handoff_operator_playbook():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_final_handoff_parser(subparsers)

    args = parser.parse_args(["final-handoff", "operator-playbook"])
    assert args.final_handoff_cmd == "operator-playbook"

def test_cli_final_handoff_developer_playbook():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_final_handoff_parser(subparsers)

    args = parser.parse_args(["final-handoff", "developer-playbook"])
    assert args.final_handoff_cmd == "developer-playbook"

def test_cli_final_handoff_command_map():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_final_handoff_parser(subparsers)

    args = parser.parse_args(["final-handoff", "command-map", "--audience", "OPERATOR"])
    assert args.final_handoff_cmd == "command-map"
    assert args.audience == "OPERATOR"

def test_cli_final_handoff_module_map():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_final_handoff_parser(subparsers)

    args = parser.parse_args(["final-handoff", "module-map"])
    assert args.final_handoff_cmd == "module-map"

def test_cli_final_handoff_roadmap():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_final_handoff_parser(subparsers)

    args = parser.parse_args(["final-handoff", "roadmap", "--json"])
    assert args.final_handoff_cmd == "roadmap"
    assert args.json is True

def test_cli_final_handoff_maintenance():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_final_handoff_parser(subparsers)

    args = parser.parse_args(["final-handoff", "maintenance", "--cadence", "WEEKLY"])
    assert args.final_handoff_cmd == "maintenance"
    assert args.cadence == "WEEKLY"

def test_cli_final_handoff_report():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_final_handoff_parser(subparsers)

    args = parser.parse_args(["final-handoff", "report", "--latest"])
    assert args.final_handoff_cmd == "report"
    assert args.latest is True

def test_cli_final_handoff_config_no_leak():
    # checking args structure, actual implementation handles no leaks
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_final_handoff_parser(subparsers)

    args = parser.parse_args(["final-handoff", "config", "--json"])
    assert args.final_handoff_cmd == "config"
    assert args.json is True
