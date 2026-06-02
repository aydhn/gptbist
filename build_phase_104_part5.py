import os
from pathlib import Path

def ensure_file(path, content, append=False):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if append and os.path.exists(path):
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + content + "\n")
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + "\n")

# 20. VALIDATION
val_code = """
import uuid
from datetime import datetime
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticScenarioValidationResult, SyntheticScenarioStatus

class SyntheticScenarioValidator:
    def validate_ohlcv(self, dataset: SyntheticDataset) -> list[str]:
        findings = []
        for i, r in enumerate(dataset.rows):
             if r.get("high", 0) < max(r.get("open", 0), r.get("close", 0)):
                 findings.append(f"Row {i} OHLCV invariant failed")
                 break # only report once
        return findings

    def validate_required_outputs(self, spec: SyntheticScenarioSpec, datasets: list[SyntheticDataset]) -> list[str]:
        findings = []
        got = [d.output_kind for d in datasets]
        for req in spec.output_kinds:
             if req not in got:
                 findings.append(f"Missing required output: {req.value}")
        return findings

    def validate_determinism(self, spec: SyntheticScenarioSpec, generator=None) -> list[str]:
        return []

    def status_from_findings(self, findings: list[str]) -> SyntheticScenarioStatus:
        if findings: return SyntheticScenarioStatus.FAIL
        return SyntheticScenarioStatus.PASS

    def validate_spec(self, spec: SyntheticScenarioSpec) -> SyntheticScenarioValidationResult:
        return SyntheticScenarioValidationResult(
            validation_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            created_at=datetime.utcnow(),
            status=SyntheticScenarioStatus.PASS,
            findings=[],
            failed_outputs=[]
        )

    def validate_datasets(self, spec: SyntheticScenarioSpec, datasets: list[SyntheticDataset]) -> SyntheticScenarioValidationResult:
        findings = self.validate_required_outputs(spec, datasets)
        for ds in datasets:
             if "OHLCV" in ds.output_kind.value:
                  findings.extend(self.validate_ohlcv(ds))
        status = self.status_from_findings(findings)

        return SyntheticScenarioValidationResult(
            validation_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            created_at=datetime.utcnow(),
            status=status,
            findings=findings,
            failed_outputs=[]
        )
"""
ensure_file("bist_signal_bot/synthetic_scenarios/validation.py", val_code)

# 21. STORAGE
store_code = """
import json
import os
from pathlib import Path
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticScenarioManifest, SyntheticScenarioValidationResult, SyntheticStressCase, SyntheticEdgeCase, SyntheticScenarioReport, SyntheticOutputKind, SyntheticScenarioKind, SyntheticFrequency, SyntheticScenarioStatus

def _serialize(obj):
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj, '__dict__'): return {k: _serialize(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list): return [_serialize(v) for v in obj]
    if isinstance(obj, dict): return {k: _serialize(v) for k, v in obj.items()}
    from datetime import datetime
    if isinstance(obj, datetime): return obj.isoformat()
    return obj

class SyntheticScenarioStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.specs_file = self.base_dir / "specs" / "synthetic_specs.json"
        self.datasets_file = self.base_dir / "datasets" / "synthetic_datasets.jsonl"
        self.manifests_file = self.base_dir / "manifests" / "synthetic_manifests.jsonl"
        self.validations_file = self.base_dir / "validations" / "synthetic_validations.jsonl"
        self.stress_file = self.base_dir / "stress" / "synthetic_stress_cases.jsonl"
        self.edge_file = self.base_dir / "edge_cases" / "synthetic_edge_cases.jsonl"

    def _ensure_dirs(self):
        for f in [self.specs_file, self.datasets_file, self.manifests_file, self.validations_file, self.stress_file, self.edge_file]:
            f.parent.mkdir(parents=True, exist_ok=True)

    def save_specs(self, specs: list[SyntheticScenarioSpec]) -> Path:
        self._ensure_dirs()
        data = [_serialize(s) for s in specs]
        with open(self.specs_file, "w", encoding="utf-8") as f:
             json.dump(data, f, indent=2)
        return self.specs_file

    def load_specs(self) -> list[SyntheticScenarioSpec]:
        if not self.specs_file.exists(): return []
        with open(self.specs_file, "r", encoding="utf-8") as f:
             data = json.load(f)
             # simple stub load
             return []

    def append_dataset(self, dataset: SyntheticDataset) -> Path:
        self._ensure_dirs()
        with open(self.datasets_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(_serialize(dataset)) + "\\n")
        return self.datasets_file

    def load_datasets(self, scenario_id: str | None = None, limit: int = 10000) -> list[SyntheticDataset]:
        return []

    def append_manifest(self, manifest: SyntheticScenarioManifest) -> Path:
        self._ensure_dirs()
        with open(self.manifests_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(_serialize(manifest)) + "\\n")
        return self.manifests_file

    def load_latest_manifest(self, scenario_id: str | None = None) -> SyntheticScenarioManifest | None:
        return None

    def append_validation(self, result: SyntheticScenarioValidationResult) -> Path:
        self._ensure_dirs()
        with open(self.validations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(_serialize(result)) + "\\n")
        return self.validations_file

    def append_stress_cases(self, cases: list[SyntheticStressCase]) -> Path:
        self._ensure_dirs()
        with open(self.stress_file, "a", encoding="utf-8") as f:
             for c in cases:
                 f.write(json.dumps(_serialize(c)) + "\\n")
        return self.stress_file

    def append_edge_cases(self, cases: list[SyntheticEdgeCase]) -> Path:
        self._ensure_dirs()
        with open(self.edge_file, "a", encoding="utf-8") as f:
             for c in cases:
                 f.write(json.dumps(_serialize(c)) + "\\n")
        return self.edge_file

    def export_dataset(self, dataset: SyntheticDataset, output_dir: Path, format: str = "jsonl", confirm: bool = False) -> Path | None:
        if not confirm:
            print("Export requires confirmation")
            return None
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{dataset.dataset_id}.{format}"
        if format == "jsonl":
            with open(path, "w", encoding="utf-8") as f:
                 for row in dataset.rows:
                      f.write(json.dumps(row) + "\\n")
        return path

    def save_report(self, report: SyntheticScenarioReport, markdown_text: str) -> dict[str, Path]:
        from datetime import datetime
        dstr = datetime.now().strftime("%Y%m%d")
        rdir = self.base_dir / "reports" / dstr
        rdir.mkdir(parents=True, exist_ok=True)
        md_path = rdir / "synthetic_scenario_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
             f.write(markdown_text)
        return {"markdown": md_path}
"""
# Small fix for enum import in storage
store_code = "from enum import Enum\n" + store_code
ensure_file("bist_signal_bot/synthetic_scenarios/storage.py", store_code)

# 22. REPORTING
rep_code = """
from typing import Any
from .models import *

def spec_to_dict(spec: SyntheticScenarioSpec) -> dict[str, Any]:
    return {"scenario_id": spec.scenario_id, "kind": spec.kind.value}
def dataset_to_dict(dataset: SyntheticDataset) -> dict[str, Any]:
    return {"dataset_id": dataset.dataset_id, "rows": dataset.row_count}
def stress_case_to_dict(case: SyntheticStressCase) -> dict[str, Any]:
    return {"stress_name": case.stress_name}
def edge_case_to_dict(case: SyntheticEdgeCase) -> dict[str, Any]:
    return {"name": case.name}
def manifest_to_dict(manifest: SyntheticScenarioManifest) -> dict[str, Any]:
    return {"manifest_id": manifest.manifest_id}
def validation_to_dict(result: SyntheticScenarioValidationResult) -> dict[str, Any]:
    return {"status": result.status.value}
def report_to_dict(report: SyntheticScenarioReport) -> dict[str, Any]:
    return {"report_id": report.report_id}

def format_spec_text(spec: SyntheticScenarioSpec) -> str:
    return f"Spec {spec.scenario_id}"
def format_dataset_text(dataset: SyntheticDataset) -> str:
    return f"Dataset {dataset.dataset_id}"
def format_manifest_text(manifest: SyntheticScenarioManifest) -> str:
    return f"Manifest {manifest.manifest_id}"
def format_validation_text(result: SyntheticScenarioValidationResult) -> str:
    return f"Validation {result.status.value}"

def format_synthetic_scenario_report_markdown(report: SyntheticScenarioReport) -> str:
    md = f"# Synthetic Scenario Report\\n"
    md += f"**Disclaimer**: {report.disclaimer}\\n"
    return md
"""
ensure_file("bist_signal_bot/synthetic_scenarios/reporting.py", rep_code)
