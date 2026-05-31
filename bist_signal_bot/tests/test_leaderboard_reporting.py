import pytest
from bist_signal_bot.leaderboard.reporting import format_leaderboard_report_markdown
from bist_signal_bot.leaderboard.models import LeaderboardReport

def test_reporting_markdown_disclaimer():
    report = LeaderboardReport(report_id="r1")
    md = format_leaderboard_report_markdown(report)
    assert "It is not investment advice or permission to trade." in md
