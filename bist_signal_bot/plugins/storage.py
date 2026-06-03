import json
from pathlib import Path
from datetime import datetime
from bist_signal_bot.plugins.models import (
    PluginManifest, PluginContract, PluginCapabilityAssessment,
    PluginHookRegistration, PluginValidationResult, PluginTestResult,
    PluginLoadResult, PluginGovernanceAssessment, PluginRegistryReport
)

class PluginStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.manifests_path = self.base_dir / "manifests" / "plugin_manifests.jsonl"
        self.contracts_path = self.base_dir / "contracts" / "plugin_contracts.json"
        self.capabilities_path = self.base_dir / "capabilities" / "plugin_capabilities.jsonl"
        self.hooks_path = self.base_dir / "hooks" / "plugin_hook_registrations.jsonl"
        self.validations_path = self.base_dir / "validations" / "plugin_validations.jsonl"
        self.tests_path = self.base_dir / "tests" / "plugin_test_results.jsonl"
        self.loads_path = self.base_dir / "loads" / "plugin_load_results.jsonl"
        self.governance_path = self.base_dir / "governance" / "plugin_governance.jsonl"

    def _append_jsonl(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        # Use simple str representation to handle enums/datetimes easily for MVP, or dump via pydantic
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\n")
        return path

    def append_manifest(self, manifest: PluginManifest) -> Path:
        return self._append_jsonl(self.manifests_path, manifest.model_dump(mode='json'))

    def load_manifests(self, limit: int = 1000) -> list[PluginManifest]:
        manifests = []
        if not self.manifests_path.exists():
            return manifests
        with open(self.manifests_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    manifests.append(PluginManifest(**json.loads(line.strip())))
                except Exception:
                    pass
        return manifests

    def save_contracts(self, contracts: list[PluginContract]) -> Path:
        self.contracts_path.parent.mkdir(parents=True, exist_ok=True)
        data = [c.model_dump(mode='json') for c in contracts]
        with open(self.contracts_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return self.contracts_path

    def load_contracts(self) -> list[PluginContract]:
        if not self.contracts_path.exists():
            return []
        with open(self.contracts_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [PluginContract(**d) for d in data]

    def append_capability_assessment(self, assessment: PluginCapabilityAssessment) -> Path:
        return self._append_jsonl(self.capabilities_path, assessment.model_dump(mode='json'))

    def append_hook_registrations(self, registrations: list[PluginHookRegistration]) -> Path:
        for r in registrations:
            self._append_jsonl(self.hooks_path, r.model_dump(mode='json'))
        return self.hooks_path

    def append_validation(self, result: PluginValidationResult) -> Path:
        return self._append_jsonl(self.validations_path, result.model_dump(mode='json'))

    def append_test_result(self, result: PluginTestResult) -> Path:
        return self._append_jsonl(self.tests_path, result.model_dump(mode='json'))

    def append_load_result(self, result: PluginLoadResult) -> Path:
        return self._append_jsonl(self.loads_path, result.model_dump(mode='json'))

    def append_governance(self, assessment: PluginGovernanceAssessment) -> Path:
        return self._append_jsonl(self.governance_path, assessment.model_dump(mode='json'))

    def load_latest_governance(self, plugin_id: str) -> PluginGovernanceAssessment | None:
        if not self.governance_path.exists():
            return None
        latest = None
        with open(self.governance_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get("plugin_id") == plugin_id:
                        latest = PluginGovernanceAssessment(**data)
                except Exception:
                    pass
        return latest

    def save_report(self, report: PluginRegistryReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self.base_dir / "reports" / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        md_path = report_dir / "plugin_registry_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        json_path = report_dir / "plugin_registry_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(mode='json'), f, indent=2, default=str)

        return {"markdown": md_path, "json": json_path}
