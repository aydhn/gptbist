import pytest
from bist_signal_bot.scenarios.validator import ScenarioValidator
from bist_signal_bot.scenarios.models import ScenarioResult, ScenarioConfig, ScenarioType, ScenarioStatus, ScenarioStepResult, ScenarioStepType

@pytest.fixture
def dummy_result():
    config = ScenarioConfig(
        scenario_id="test-scenario",
        name="Test",
        scenario_type=ScenarioType.CUSTOM,
        description="test",
        symbols=["ASELS"]
    )
    return ScenarioResult(
        run_id="run-123",
        scenario=config,
        status=ScenarioStatus.SUCCESS
    )

def test_validate_result_disclaimer(dummy_result):
    validator = ScenarioValidator()

    # Default should have the disclaimer and pass
    issues = validator.validate_result(dummy_result)
    assert len(issues) == 0

    # Remove disclaimer
    dummy_result.disclaimer = ""
    issues = validator.validate_result(dummy_result)
    assert len(issues) == 1
    assert "No real order was sent" in issues[0]

def test_validate_step_result_unsafe_claims():
    class DummyClaimGuard:
        def has_unsafe_claims(self, text):
            return "guaranteed" in text.lower()

    validator = ScenarioValidator(claim_guard=DummyClaimGuard())

    step = ScenarioStepResult(
        step_id="step1",
        name="Step 1",
        step_type=ScenarioStepType.COMMAND,
        status=ScenarioStatus.SUCCESS,
        stdout_tail="This strategy provides guaranteed returns."
    )

    issues = validator.validate_step_result(step)
    assert len(issues) > 0
    assert "unsafe financial claims" in issues[0]

def test_validate_real_order_language():
    validator = ScenarioValidator()

    step = ScenarioStepResult(
        step_id="step1",
        name="Step 1",
        step_type=ScenarioStepType.COMMAND,
        status=ScenarioStatus.SUCCESS,
        stdout_tail="Real trade sent to broker."
    )

    issues = validator.validate_step_result(step)
    assert len(issues) > 0
    assert "real orders were sent" in issues[0]

def test_validate_step_failure_status(dummy_result):
    validator = ScenarioValidator()

    step = ScenarioStepResult(
        step_id="step1",
        name="Step 1",
        step_type=ScenarioStepType.COMMAND,
        status=ScenarioStatus.FAILED
    )
    dummy_result.step_results.append(step)

    issues = validator.validate_result(dummy_result)
    assert len(issues) > 0
    assert "Result status is SUCCESS but some steps failed" in issues[0]
