import pytest
import pandas as pd
from bist_signal_bot.scenarios.reporting import (
    scenario_result_to_dict,
    scenario_step_results_to_dataframe,
    format_scenario_result_text,
    format_scenario_markdown
)
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
    res = ScenarioResult(
        run_id="run-123",
        scenario=config,
        status=ScenarioStatus.SUCCESS,
        elapsed_seconds=10.5
    )
    step = ScenarioStepResult(
        step_id="step1",
        name="Step 1",
        step_type=ScenarioStepType.COMMAND,
        status=ScenarioStatus.SUCCESS,
        elapsed_seconds=2.0
    )
    res.step_results.append(step)
    return res

def test_scenario_result_to_dict(dummy_result):
    data = scenario_result_to_dict(dummy_result)
    assert isinstance(data, dict)
    assert data["run_id"] == "run-123"
    assert data["status"] == "SUCCESS"

def test_scenario_step_results_to_dataframe(dummy_result):
    df = scenario_step_results_to_dataframe(dummy_result.step_results)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["step_id"] == "step1"

def test_format_scenario_result_text(dummy_result):
    text = format_scenario_result_text(dummy_result)
    assert "test-scenario" in text
    assert "SUCCESS" in text
    assert "kabul testi raporudur" in text

def test_format_scenario_markdown(dummy_result):
    md = format_scenario_markdown(dummy_result)
    assert "# Scenario Report: test-scenario" in md
    assert "**Status:** SUCCESS" in md
    assert "- **Step 1**: SUCCESS" in md
    assert "No real order was sent" in md
