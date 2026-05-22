import pytest
from bist_signal_bot.telegram_center.parser import TelegramCommandParser
from bist_signal_bot.telegram_center.models import TelegramCommandType

def test_parser_status():
    parser = TelegramCommandParser()
    cmd = parser.parse("/status", "chat123")
    assert cmd.command_type == TelegramCommandType.STATUS

def test_parser_kb_query():
    parser = TelegramCommandParser()
    cmd = parser.parse("/kb ASELS momentum", "chat123")
    assert cmd.command_type == TelegramCommandType.KB_SEARCH
    assert cmd.args.get("query") == "ASELS momentum"

def test_parser_unknown():
    parser = TelegramCommandParser()
    cmd = parser.parse("hello", "chat123")
    assert cmd.command_type == TelegramCommandType.UNKNOWN
