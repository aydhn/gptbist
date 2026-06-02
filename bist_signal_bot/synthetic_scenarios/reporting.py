
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
    md = f"# Synthetic Scenario Report\n"
    md += f"**Disclaimer**: {report.disclaimer}\n"
    return md
