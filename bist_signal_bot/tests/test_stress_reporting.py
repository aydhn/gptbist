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
