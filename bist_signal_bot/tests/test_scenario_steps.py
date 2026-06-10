import pytest
from bist_signal_bot.scenarios.steps import ScenarioStepExecutor
from bist_signal_bot.scenarios.models import ScenarioStepConfig, ScenarioStepType, ScenarioStatus

def test_execute_command_success(tmp_path):
    executor = ScenarioStepExecutor()
    step = ScenarioStepConfig(
        step_id="cmd-1",
        name="Test Echo",
        step_type=ScenarioStepType.COMMAND,
        command=["echo", "Hello World"],
        timeout_seconds=5
    )
    res = executor.execute_step(step, tmp_path)
    assert res.status == ScenarioStatus.SUCCESS
    assert res.exit_code == 0
    assert "Hello World" in res.stdout_tail

def test_execute_command_failure(tmp_path):
    executor = ScenarioStepExecutor()
    step = ScenarioStepConfig(
        step_id="cmd-2",
        name="Test Fail",
        step_type=ScenarioStepType.COMMAND,
        command=["ls", "/non/existent/path"],
        timeout_seconds=5,
        expected_exit_code=0
    )
    res = executor.execute_step(step, tmp_path)
    assert res.status == ScenarioStatus.FAILED
    assert res.exit_code != 0

def test_execute_command_timeout(tmp_path):
    executor = ScenarioStepExecutor()
    step = ScenarioStepConfig(
        step_id="cmd-3",
        name="Test Timeout",
        step_type=ScenarioStepType.COMMAND,
        command=["sleep", "2"],
        timeout_seconds=1
    )
    res = executor.execute_step(step, tmp_path)
    assert res.status == ScenarioStatus.TIMEOUT

def test_execute_assertions(tmp_path):
    executor = ScenarioStepExecutor()
    step = ScenarioStepConfig(
        step_id="assert-1",
        name="Test Assertions",
        step_type=ScenarioStepType.COMMAND,
        command=["echo", "Guaranteed profit is 100% win"],
        timeout_seconds=5,
        assertions=["status_is:SUCCESS", "contains_text:profit", "no_unsafe_claim"]
    )
    res = executor.execute_step(step, tmp_path)
    # exit code 0 is SUCCESS, but assertion fails
    assert res.status == ScenarioStatus.FAILED
    assert res.assertions_passed == 2 # status + contains_text
    assert res.assertions_failed == 1 # no_unsafe_claim
    assert any("unsafe" in i for i in res.issues)

def test_execute_command_validation_failure():
    with pytest.raises(ValueError, match="Command 'rm' is not allowed."):
        ScenarioStepConfig(
            step_id="cmd-invalid",
            name="Test Invalid",
            step_type=ScenarioStepType.COMMAND,
            command=["rm", "-rf", "/"],
            timeout_seconds=5
        )
