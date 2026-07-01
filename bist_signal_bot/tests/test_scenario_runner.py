import pytest
from pathlib import Path
from bist_signal_bot.scenarios.runner import ScenarioRunner, ScenarioRunnerDependencies
from bist_signal_bot.scenarios.registry import ScenarioRegistry
from bist_signal_bot.scenarios.models import ScenarioStatus, ScenarioType
from bist_signal_bot.scenarios.storage import ScenarioStore

def test_runner_smoke_scenario(tmp_path):
    store = ScenarioStore(base_dir=tmp_path)
    # Using a subset or mock so we don't actually wait for heavy real commands
    runner = ScenarioRunner(deps=ScenarioRunnerDependencies(storage=store))

    # Let's run the smoke scenario but substitute its command for a simple one to not block
    # and fail due to environment differences.
    registry = ScenarioRegistry()
    smoke = registry.get_scenario("smoke")
    for step in smoke.steps:
        step.command = ["echo", "mock_success"]

    res = runner.run_config(smoke)

    assert res.status == ScenarioStatus.SUCCESS
    assert len(res.step_results) == 5
    assert all(s.status == ScenarioStatus.SUCCESS for s in res.step_results)

    # Check outputs were saved
    assert res.output_files.get("json") is not None
    assert Path(res.output_files["json"]).exists()

def test_runner_continue_on_error(tmp_path):
    store = ScenarioStore(base_dir=tmp_path)
    runner = ScenarioRunner(deps=ScenarioRunnerDependencies(storage=store))
    registry = ScenarioRegistry()
    acc = registry.get_scenario("acceptance")

    # Inject a failure
    acc.steps[0].command = ["exit", "1"]
    acc.continue_on_error = False

    res1 = runner.run_config(acc)
    assert res1.status == ScenarioStatus.FAILED
    assert len(res1.step_results) == 1 # stopped at first step

    # Re-run with continue_on_error
    acc.continue_on_error = True
    for step in acc.steps[1:]:
        step.command = ["echo", "ok"]

    res2 = runner.run_config(acc)
    assert res2.status == ScenarioStatus.PARTIAL_SUCCESS
    assert len(res2.step_results) == 7 # ran all steps despite failure

def test_runner_cleanup(tmp_path):
    store = ScenarioStore(base_dir=tmp_path)
    runner = ScenarioRunner(deps=ScenarioRunnerDependencies(storage=store))
    registry = ScenarioRegistry()
    smoke = registry.get_scenario("smoke")
    for step in smoke.steps:
        step.command = ["echo", "mock_success"]

    res = runner.run_config(smoke)

    # Sandbox should exist
    sandbox_dir = store.get_scenario_runs_dir() / "sandbox" / res.run_id

    with pytest.raises(ValueError):
         runner.cleanup_sandbox(res.run_id, confirm=False)

    cleanup_res = runner.cleanup_sandbox(res.run_id, confirm=True)
    assert cleanup_res["status"] in ["success", "not_found"]
    assert not sandbox_dir.exists()

def test_runner_golden_update_requires_confirm(tmp_path):
    store = ScenarioStore(base_dir=tmp_path)
    runner = ScenarioRunner(deps=ScenarioRunnerDependencies(storage=store))

    registry = ScenarioRegistry()
    smoke = registry.get_scenario("smoke")
    for step in smoke.steps:
        step.command = ["echo", "mock_success"]

    res = runner.run(scenario_id="smoke", update_golden=True, confirm_update_golden=False)
    # The runner catches the error and adds it to issues
    assert res.status == ScenarioStatus.FAILED # Fails because of validation (missing disclaimer etc)
    assert not res.golden_comparison or res.golden_comparison.get('matched') is False
