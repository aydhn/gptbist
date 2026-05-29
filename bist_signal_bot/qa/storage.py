from pathlib import Path
from bist_signal_bot.qa.models import QAFixtureManifest, QAScenario, QACheckResult, SmokeTestResult, RegressionMatrixResult, ReleaseGateResult, ReproducibilityPack, QAReport

class QAStore:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def save_fixture_manifest(self, manifest: QAFixtureManifest) -> Path:
        return Path("manifest.json")

    def load_fixture_manifest(self) -> QAFixtureManifest | None:
        return None

    def save_scenarios(self, scenarios: list[QAScenario]) -> Path:
        return Path("scenarios.json")

    def load_scenarios(self) -> list[QAScenario]:
        return []

    def append_check_results(self, results: list[QACheckResult]) -> Path:
        return Path("checks.jsonl")

    def load_check_results(self, limit: int = 10000) -> list[QACheckResult]:
        return []

    def append_smoke_results(self, results: list[SmokeTestResult]) -> Path:
        return Path("smoke.jsonl")

    def append_regression_result(self, result: RegressionMatrixResult) -> Path:
        return Path("regression.jsonl")

    def load_latest_regression(self) -> RegressionMatrixResult | None:
        return None

    def append_release_gate(self, result: ReleaseGateResult) -> Path:
         return Path("release.jsonl")

    def load_latest_release_gate(self) -> ReleaseGateResult | None:
        return None

    def save_reproducibility_pack(self, pack: ReproducibilityPack) -> Path:
         return Path("pack.json")

    def save_report(self, report: QAReport, markdown_text: str) -> dict:
        return {}

    def load_latest_report(self) -> QAReport | None:
        return None
