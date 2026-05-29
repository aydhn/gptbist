from bist_signal_bot.qa.models import *
import pandas as pd

def fixture_manifest_to_dict(manifest: QAFixtureManifest) -> dict: return manifest.model_dump()
def scenario_to_dict(scenario: QAScenario) -> dict: return scenario.model_dump()
def check_result_to_dict(result: QACheckResult) -> dict: return result.model_dump()
def smoke_result_to_dict(result: SmokeTestResult) -> dict: return result.model_dump()
def regression_item_to_dict(item: RegressionMatrixItem) -> dict: return item.model_dump()
def regression_matrix_to_dict(result: RegressionMatrixResult) -> dict: return result.model_dump()
def release_gate_to_dict(result: ReleaseGateResult) -> dict: return result.model_dump()
def reproducibility_pack_to_dict(pack: ReproducibilityPack) -> dict: return pack.model_dump()
def qa_report_to_dict(report: QAReport) -> dict: return report.model_dump()

def check_results_to_dataframe(results: list[QACheckResult]) -> pd.DataFrame:
    return pd.DataFrame([r.model_dump() for r in results])

def smoke_results_to_dataframe(results: list[SmokeTestResult]) -> pd.DataFrame:
     return pd.DataFrame([r.model_dump() for r in results])

def format_check_results_text(results: list[QACheckResult]) -> str: return "checks"
def format_smoke_results_text(results: list[SmokeTestResult]) -> str: return "smoke"
def format_regression_matrix_text(result: RegressionMatrixResult) -> str: return "matrix"
def format_release_gate_text(result: ReleaseGateResult) -> str: return "gate"
def format_qa_report_markdown(report: QAReport) -> str: return "report"
