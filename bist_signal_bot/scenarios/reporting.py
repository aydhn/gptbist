from typing import Any, Dict, List
import pandas as pd

from bist_signal_bot.scenarios.models import ScenarioResult, ScenarioStepResult, GoldenComparisonResult

def scenario_result_to_dict(result: ScenarioResult) -> Dict[str, Any]:
    return result.model_dump(mode='json')

def scenario_step_results_to_dataframe(steps: List[ScenarioStepResult]) -> pd.DataFrame:
    data = [s.model_dump(mode='json') for s in steps]
    return pd.DataFrame(data)

def golden_comparison_to_dict(result: GoldenComparisonResult) -> Dict[str, Any]:
    return result.model_dump(mode='json')

def format_scenario_result_text(result: ScenarioResult) -> str:
    summary = result.summary()

    text = f"BIST Bot Scenario Summary\n\n"
    text += f"Scenario: {summary.get('scenario_id')}\n"
    text += f"Status: {summary.get('status')}\n"
    text += f"Steps: {summary.get('steps')}\n"
    text += f"Failed: {summary.get('steps') - summary.get('passed_steps', summary.get('steps'))}\n"

    golden_str = "matched" if result.golden_comparison and result.golden_comparison.get('matched') else "not_matched/N_A"
    text += f"Golden: {golden_str}\n"
    text += f"Elapsed: {summary.get('elapsed', 0.0):.1f} sec\n\n"

    text += "Bu çıktı kabul testi raporudur.\n"
    text += "Yatırım tavsiyesi değildir.\n"
    text += "Gerçek emir gönderilmedi.\n"

    return text

def format_scenario_markdown(result: ScenarioResult) -> str:
    summary = result.summary()

    md = f"# Scenario Report: {summary.get('scenario_id')}\n\n"
    md += f"**Status:** {summary.get('status')}\n"
    md += f"**Elapsed:** {summary.get('elapsed', 0.0):.1f}s\n\n"

    md += "## Steps\n"
    for step in result.step_results:
        md += f"- **{step.name}**: {step.status.value} ({step.elapsed_seconds:.1f}s)\n"
        if step.issues:
             for issue in step.issues:
                 md += f"  - Issue: {issue}\n"

    md += f"\n## Disclaimer\n{result.disclaimer}\n"
    return md

def format_golden_comparison_text(result: GoldenComparisonResult) -> str:
    status = "MATCHED" if result.matched else f"FAILED ({len(result.differences)} diffs)"
    return f"Golden Comparison for {result.scenario_id}: {status}"
