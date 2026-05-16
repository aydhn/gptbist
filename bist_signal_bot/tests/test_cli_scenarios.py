import pytest
from click.testing import CliRunner
from bist_signal_bot.cli.commands import cli

def test_cli_scenario_list():
    runner = CliRunner()
    result = runner.invoke(cli, ["scenario", "list"])
    assert result.exit_code == 0
    assert "smoke" in result.output
    assert "acceptance" in result.output

def test_cli_scenario_show():
    runner = CliRunner()
    result = runner.invoke(cli, ["scenario", "show", "smoke"])
    assert result.exit_code == 0
    assert "Smoke Test" in result.output

    # JSON output
    result_json = runner.invoke(cli, ["scenario", "show", "smoke", "--json"])
    assert result_json.exit_code == 0
    assert "step_type" in result_json.output

def test_cli_scenario_config():
    runner = CliRunner()
    result = runner.invoke(cli, ["scenario", "config"])
    assert result.exit_code == 0
    assert "enabled" in result.output

def test_cli_scenario_cleanup_requires_confirm():
    runner = CliRunner()
    result = runner.invoke(cli, ["scenario", "cleanup", "some-id"])
    assert result.exit_code == 0
    assert "Error: Cleanup requires explicit confirmation" in result.output

def test_cli_scenario_golden_update_requires_confirm():
    runner = CliRunner()
    result = runner.invoke(cli, ["scenario", "golden", "update", "smoke"])
    assert result.exit_code == 0
    assert "Update requires --confirm flag" in result.output
