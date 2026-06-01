import pytest
import json
from argparse import Namespace
from bist_signal_bot.cli.commands import handle_performance_command

def test_cli_performance_profile(capsys):
    args = Namespace(
        perf_command="profile",
        module="test",
        command=None,
        json=True
    )
    handle_performance_command(args, None)

    captured = capsys.readouterr()
    output = json.loads(captured.out)

    assert output["status"] == "ok"
    assert output["command"] == "profile"
    assert output["module"] == "test"

def test_cli_performance_benchmark(capsys):
    args = Namespace(
        perf_command="benchmark",
        scenario="ORCHESTRATOR_DRY_RUN",
        json=True
    )
    handle_performance_command(args, None)

    captured = capsys.readouterr()
    output = json.loads(captured.out)

    assert output["status"] == "ok"
    assert output["command"] == "benchmark"
    assert output["scenario"] == "ORCHESTRATOR_DRY_RUN"

def test_cli_performance_cache(capsys):
    args = Namespace(
        perf_command="cache",
        cache_command="list",
        json=True
    )
    handle_performance_command(args, None)

    captured = capsys.readouterr()
    output = json.loads(captured.out)

    assert output["status"] == "ok"
    assert output["command"] == "cache"
    assert output["cache_command"] == "list"
