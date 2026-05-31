import pytest
from bist_signal_bot.cli.leaderboard_commands import (
    handle_leaderboard_cohorts, handle_leaderboard_policies, handle_leaderboard_config
)
from argparse import Namespace
from bist_signal_bot.cli_ux.models import CLIStatus

def test_handle_leaderboard_cohorts():
    args = Namespace(json=False)
    env = handle_leaderboard_cohorts(args)
    assert env.status == CLIStatus.SUCCESS
    assert "Strategy Research Cohort" in env.metadata["message"]

def test_handle_leaderboard_policies():
    args = Namespace(json=False, show="")
    env = handle_leaderboard_policies(args)
    assert env.status == CLIStatus.SUCCESS
    assert "strategy_research_selection_v1" in env.metadata["message"]

def test_handle_leaderboard_config():
    args = Namespace(json=False)
    env = handle_leaderboard_config(args)
    assert env.status == CLIStatus.SUCCESS
    assert "LEADERBOARD_RESEARCH_ONLY" in env.metadata["message"]
