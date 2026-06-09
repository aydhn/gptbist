import pytest
from bist_signal_bot.stress.reporting import format_shock_result_text
from bist_signal_bot.stress.models import ShockScenarioResult, StressScenario, StressScenarioType, StressSeverity, StressStatus

def test_format_shock_result_text_with_impact():
    scenario = StressScenario(
        scenario_id="scen1",
        name="Market Crash 20%",
        scenario_type=StressScenarioType.MARKET_SHOCK,
        severity=StressSeverity.HIGH
    )
    result = ShockScenarioResult(
        result_id="res1",
        scenario=scenario,
        status=StressStatus.PASS,
        estimated_portfolio_impact_pct=-15.5
    )

    text = format_shock_result_text(result)

    expected_lines = [
        "=== SHOCK: Market Crash 20% ===",
        "Severity: HIGH",
        "Status: PASS",
        "Est. Impact: -15.50%",
        "",
        "Note: " + result.disclaimer
    ]
    expected_text = "\n".join(expected_lines)

    assert text == expected_text

def test_format_shock_result_text_without_impact():
    scenario = StressScenario(
        scenario_id="scen2",
        name="Liquidity Crisis",
        scenario_type=StressScenarioType.LIQUIDITY_STRESS,
        severity=StressSeverity.EXTREME
    )
    result = ShockScenarioResult(
        result_id="res2",
        scenario=scenario,
        status=StressStatus.ERROR,
        estimated_portfolio_impact_pct=None
    )

    text = format_shock_result_text(result)

    expected_lines = [
        "=== SHOCK: Liquidity Crisis ===",
        "Severity: EXTREME",
        "Status: ERROR",
        "Est. Impact: N/A",
        "",
        "Note: " + result.disclaimer
    ]
    expected_text = "\n".join(expected_lines)

    assert text == expected_text

from bist_signal_bot.stress.reporting import shock_results_to_dataframe

def test_shock_results_to_dataframe():
    scenario1 = StressScenario(
        scenario_id="scen1",
        name="Market Crash 20%",
        scenario_type=StressScenarioType.MARKET_SHOCK,
        severity=StressSeverity.HIGH
    )
    result1 = ShockScenarioResult(
        result_id="res1",
        scenario=scenario1,
        status=StressStatus.PASS,
        estimated_portfolio_impact_pct=-15.556
    )

    scenario2 = StressScenario(
        scenario_id="scen2",
        name="Liquidity Crisis",
        scenario_type=StressScenarioType.LIQUIDITY_STRESS,
        severity=StressSeverity.EXTREME
    )
    result2 = ShockScenarioResult(
        result_id="res2",
        scenario=scenario2,
        status=StressStatus.ERROR,
        estimated_portfolio_impact_pct=None
    )

    df = shock_results_to_dataframe([result1, result2])

    assert list(df.columns) == ["Scenario", "Severity", "Portfolio Impact %", "Status"]
    assert len(df) == 2

    assert df.iloc[0]["Scenario"] == "Market Crash 20%"
    assert df.iloc[0]["Severity"] == "HIGH"
    assert df.iloc[0]["Portfolio Impact %"] == -15.56
    assert df.iloc[0]["Status"] == "PASS"

    assert df.iloc[1]["Scenario"] == "Liquidity Crisis"
    assert df.iloc[1]["Severity"] == "EXTREME"
    import pandas as pd; assert pd.isna(df.iloc[1]["Portfolio Impact %"])
    assert df.iloc[1]["Status"] == "ERROR"

def test_shock_results_to_dataframe_empty():
    df = shock_results_to_dataframe([])
    assert list(df.columns) == []
    assert len(df) == 0
