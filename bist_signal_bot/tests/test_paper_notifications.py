import pytest
from bist_signal_bot.notifications.formatter import format_paper_execution_report as TelegramFormatter
from bist_signal_bot.paper.models import PaperRunResult, PaperAccount, PaperAccountStatus

def test_paper_notification_formatter():
    # 44. Notification formatter paper summary üretir.
    formatter = TelegramFormatter()

    acc = PaperAccount(account_id="test", initial_cash=1000, cash=1000, equity=1000)
    result = PaperRunResult(account=acc, status="SUCCESS")

    out = formatter.format_paper_run_result(result)
    assert "BIST Bot Paper Trading" in out
    assert "Gerçek emir gönderilmedi" in out
