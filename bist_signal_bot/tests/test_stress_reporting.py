import pytest
import pandas as pd
from bist_signal_bot.stress.reporting import (
    format_shock_result_text,
    shock_results_to_dataframe,
    format_stress_result_text,
    format_stress_report_markdown
)
from bist_signal_bot.stress.models import (
    ShockScenarioResult,
    StressScenario,
    StressScenarioType,
    StressSeverity,
    StressStatus,
    StressTestResult,
    StressTestRequest,
    StressInputType,
    MonteCarloResult,
    MonteCarloConfig,
    MonteCarloMethod,
    RiskOfRuinResult,
    DrawdownSimulationResult
)

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



def test_format_stress_result_text_full():
    request = StressTestRequest(
        input_type=StressInputType.MOCK,
        symbols=["AAPL"],
        monte_carlo_config=MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=1000,
            horizon_days=252,
            seed=42,
            initial_value=10000.0
        ),
        ruin_threshold_pct=20.0
    )

    mc_result = MonteCarloResult(
        result_id="mc1",
        config=request.monte_carlo_config,
        status=StressStatus.PASS,
        final_return_pct_p05=5.25
    )

    ror_result = RiskOfRuinResult(
        result_id="ror1",
        status=StressStatus.PASS,
        ruin_threshold_pct=20.0,
        estimated_ruin_probability_pct=2.15
    )

    result = StressTestResult(
        stress_id="STRESS1",
        request=request,
        status=StressStatus.WARN,
        stress_score=85.5,
        stress_rating=StressSeverity.MEDIUM,
        warnings=["Test warning 1", "Test warning 2"],
        monte_carlo_result=mc_result,
        risk_of_ruin_result=ror_result,
        disclaimer="Disclaimer text here"
    )

    text = format_stress_result_text(result)

    expected = "\n".join([
        "=== STRESS TEST RESULT ===",
        "Rating: MEDIUM",
        "Score: 85.50",
        "Status: WARN",
        "Warnings: 2",
        "MC p05 Return: 5.25%",
        "Risk of Ruin: 2.15%",
        "",
        "Note: Disclaimer text here"
    ])

    assert text == expected

def test_format_stress_result_text_minimal():
    request = StressTestRequest(
        input_type=StressInputType.MOCK,
        symbols=["AAPL"],
        monte_carlo_config=MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=1000,
            horizon_days=252,
            seed=42,
            initial_value=10000.0
        ),
        ruin_threshold_pct=20.0
    )

    result = StressTestResult(
        stress_id="STRESS2",
        request=request,
        status=StressStatus.ERROR,
        stress_score=None,
        stress_rating=StressSeverity.EXTREME,
        warnings=[],
        monte_carlo_result=None,
        risk_of_ruin_result=None,
        disclaimer="Another disclaimer"
    )

    text = format_stress_result_text(result)

    expected = "\n".join([
        "=== STRESS TEST RESULT ===",
        "Rating: EXTREME",
        "Score: N/A",
        "Status: ERROR",
        "Warnings: 0",
        "",
        "Note: Another disclaimer"
    ])

    assert text == expected

def test_format_stress_result_text_partial():
    request = StressTestRequest(
        input_type=StressInputType.MOCK,
        symbols=["AAPL"],
        monte_carlo_config=MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=1000,
            horizon_days=252,
            seed=42,
            initial_value=10000.0
        ),
        ruin_threshold_pct=20.0
    )

    mc_result = MonteCarloResult(
        result_id="mc2",
        config=request.monte_carlo_config,
        status=StressStatus.PASS,
        final_return_pct_p05=None
    )

    ror_result = RiskOfRuinResult(
        result_id="ror2",
        status=StressStatus.PASS,
        ruin_threshold_pct=20.0,
        estimated_ruin_probability_pct=None
    )

    result = StressTestResult(
        stress_id="STRESS3",
        request=request,
        status=StressStatus.PASS,
        stress_score=None,
        stress_rating=StressSeverity.LOW,
        warnings=[],
        monte_carlo_result=mc_result,
        risk_of_ruin_result=ror_result,
        disclaimer="Disclaimer text here"
    )

    text = format_stress_result_text(result)

    expected = "\n".join([
        "=== STRESS TEST RESULT ===",
        "Rating: LOW",
        "Score: N/A",
        "Status: PASS",
        "Warnings: 0",
        "MC p05 Return: N/A",
        "Risk of Ruin: N/A",
        "",
        "Note: Disclaimer text here"
    ])

    assert text == expected


def test_format_stress_report_markdown_full():
    request = StressTestRequest(
        input_type=StressInputType.MOCK,
        symbols=["AAPL"],
        monte_carlo_config=MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=1000,
            horizon_days=252,
            seed=42,
            initial_value=10000.0
        ),
        ruin_threshold_pct=20.0
    )

    mc_result = MonteCarloResult(
        result_id="mc3",
        config=request.monte_carlo_config,
        status=StressStatus.PASS,
        final_return_pct_p05=5.25,
        final_return_pct_p50=10.5
    )

    ror_result = RiskOfRuinResult(
        result_id="ror3",
        status=StressStatus.PASS,
        ruin_threshold_pct=20.0,
        estimated_ruin_probability_pct=2.15,
        worst_loss_streak=5
    )

    dd_result = DrawdownSimulationResult(
        result_id="dd3",
        status=StressStatus.PASS,
        max_drawdown_pct=-15.0,
        longest_drawdown_days=45
    )

    scenario = StressScenario(
        scenario_id="scen3",
        name="Market Crash 20%",
        scenario_type=StressScenarioType.MARKET_SHOCK,
        severity=StressSeverity.HIGH
    )
    shock_result = ShockScenarioResult(
        result_id="shock3",
        scenario=scenario,
        status=StressStatus.PASS,
        estimated_portfolio_impact_pct=-15.5
    )

    result = StressTestResult(
        stress_id="STRESS4",
        request=request,
        status=StressStatus.PASS,
        stress_score=85.5,
        stress_rating=StressSeverity.LOW,
        warnings=["Test warning"],
        monte_carlo_result=mc_result,
        risk_of_ruin_result=ror_result,
        drawdown_result=dd_result,
        shock_results=[shock_result],
        disclaimer="Disclaimer text here"
    )

    md = format_stress_report_markdown(result)
    assert "# Stress Test Research Report" in md
    assert "## Monte Carlo Simulation" in md
    assert "## Shock Scenarios" in md
    assert "## Drawdown Simulation" in md
    assert "## Risk of Ruin Estimate" in md
