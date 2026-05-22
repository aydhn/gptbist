import pytest
from bist_signal_bot.telegram_center.reporting import format_telegram_command_result_text
from bist_signal_bot.telegram_center.models import TelegramCommandResult, TelegramCommandStatus, TelegramCommandDecision
import uuid

def test_reporting_disclaimer():
    res = TelegramCommandResult(
        result_id=str(uuid.uuid4()),
        command_id=str(uuid.uuid4()),
        status=TelegramCommandStatus.EXECUTED,
        decision=TelegramCommandDecision.ALLOW,
        response_text="Test response",
        disclaimer="Not investment advice"
    )
    text = format_telegram_command_result_text(res)
    assert "Not investment advice" in text
