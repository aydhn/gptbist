import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
from bist_signal_bot.cli.parsers import build_parser, parse_args

def test_build_parser():
    parser = build_parser()
    assert parser is not None

def test_parse_args_default():
    args = parse_args([])
    assert args.command == "healthcheck"
    assert args.json is False
    assert args.verbose is False

def test_parse_args_healthcheck_json():
    args = parse_args(["healthcheck", "--json"])
    assert args.command == "healthcheck"
    assert args.json is True

def test_parse_args_config_json():
    args = parse_args(["config", "--json"])
    assert args.command == "config"
    assert args.json is True

def test_parse_args_symbols_yfinance():
    args = parse_args(["symbols", "--yfinance"])
    assert args.command == "symbols"
    assert args.yfinance is True

def test_parse_args_validate_symbol():
    args = parse_args(["validate-symbol", "ASELS"])
    assert args.command == "validate-symbol"
    assert args.symbol == "ASELS"

def test_parse_args_provider_status():
    args = parse_args(["provider-status"])
    assert args.command == "provider-status"

def test_parse_args_storage_status():
    args = parse_args(["storage-status"])
    assert args.command == "storage-status"

def test_parse_args_calendar_status():
    args = parse_args(["calendar-status", "--at", "2026-04-24T18:20:00+03:00"])
    assert args.command == "calendar-status"
    assert args.at == "2026-04-24T18:20:00+03:00"

def test_parse_args_telegram_test():
    args = parse_args(["telegram-test", "--message", "Test message"])
    assert args.command == "telegram-test"
    assert args.message == "Test message"

def test_parse_args_mock_data():
    args = parse_args(["mock-data", "ASELS", "--rows", "10", "--save"])
    assert args.command == "mock-data"
    assert args.symbol == "ASELS"
    assert args.rows == 10
    assert args.save is True

def test_parse_args_quality_demo():
    args = parse_args(["quality-demo", "ASELS", "--rows", "20"])
    assert args.command == "quality-demo"
    assert args.symbol == "ASELS"
    assert args.rows == 20

def test_parse_args_version():
    args = parse_args(["version"])
    assert args.command == "version"

def test_parse_args_diagnose():
    args = parse_args(["diagnose", "--json"])
    assert args.command == "diagnose"
    assert args.json is True
