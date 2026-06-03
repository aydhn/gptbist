from typing import Any
from bist_signal_bot.plugins.models import (
    PluginManifest, PluginCapabilityAssessment, PluginContract,
    PluginHookRegistration, PluginValidationResult, PluginTestResult,
    PluginLoadResult, PluginGovernanceAssessment, PluginRegistryReport
)

def manifest_to_dict(manifest: PluginManifest) -> dict[str, Any]:
    return manifest.model_dump(mode='json')

def capability_assessment_to_dict(assessment: PluginCapabilityAssessment) -> dict[str, Any]:
    return assessment.model_dump(mode='json')

def contract_to_dict(contract: PluginContract) -> dict[str, Any]:
    return contract.model_dump(mode='json')

def hook_registration_to_dict(registration: PluginHookRegistration) -> dict[str, Any]:
    return registration.model_dump(mode='json')

def validation_to_dict(result: PluginValidationResult) -> dict[str, Any]:
    return result.model_dump(mode='json')

def test_result_to_dict(result: PluginTestResult) -> dict[str, Any]:
    return result.model_dump(mode='json')

def load_result_to_dict(result: PluginLoadResult) -> dict[str, Any]:
    return result.model_dump(mode='json')

def governance_to_dict(assessment: PluginGovernanceAssessment) -> dict[str, Any]:
    return assessment.model_dump(mode='json')

def report_to_dict(report: PluginRegistryReport) -> dict[str, Any]:
    return report.model_dump(mode='json')

def format_manifest_text(manifest: PluginManifest) -> str:
    lines = [
        f"Plugin ID: {manifest.plugin_id}",
        f"Name: {manifest.name}",
        f"Version: {manifest.version}",
        f"Kind: {manifest.kind.value}",
        f"Enabled: {manifest.enabled}",
        f"Description: {manifest.description}",
        f"Disclaimer: {manifest.disclaimer}"
    ]
    return "\n".join(lines)

def format_validation_text(result: PluginValidationResult) -> str:
    lines = [
        f"Validation ID: {result.validation_id}",
        f"Plugin ID: {result.plugin_id}",
        f"Status: {result.status.value}",
        f"Manifest Valid: {result.manifest_valid}",
        f"Contract Valid: {result.contract_valid}",
        f"Capabilities Valid: {result.capabilities_valid}",
        f"Findings: {len(result.findings)}",
        f"Disclaimer: {result.disclaimer}"
    ]
    return "\n".join(lines)

def format_test_result_text(result: PluginTestResult) -> str:
    lines = [
        f"Test ID: {result.test_id}",
        f"Plugin ID: {result.plugin_id}",
        f"Status: {result.status.value}",
        f"Tests Run: {result.tests_run}",
        f"Passed: {result.tests_passed}",
        f"Failed: {result.tests_failed}",
        f"Dry Run: {result.dry_run}",
        f"Disclaimer: {result.disclaimer}"
    ]
    return "\n".join(lines)

def format_load_result_text(result: PluginLoadResult) -> str:
    lines = [
        f"Load ID: {result.load_id}",
        f"Plugin ID: {result.plugin_id}",
        f"Status: {result.status.value}",
        f"Execution Mode: {result.execution_mode.value}",
        f"Loaded: {result.loaded}",
        f"Disclaimer: {result.disclaimer}"
    ]
    return "\n".join(lines)

def format_governance_text(assessment: PluginGovernanceAssessment) -> str:
    lines = [
        f"Governance ID: {assessment.governance_id}",
        f"Plugin ID: {assessment.plugin_id}",
        f"Status: {assessment.status.value}",
        f"Blocked Reasons: {len(assessment.blocked_reasons)}",
        f"Unsafe Language Findings: {len(assessment.unsafe_language_findings)}",
        f"Disclaimer: {assessment.disclaimer}"
    ]
    return "\n".join(lines)

def format_plugin_registry_report_markdown(report: PluginRegistryReport) -> str:
    md = [
        "# Plugin Registry Report",
        f"Generated at: {report.generated_at.isoformat()}",
        "",
        "## Summary",
        f"- Total Manifests: {len(report.manifests)}",
        f"- Validations: {len(report.validations)}",
        f"- Test Results: {len(report.test_results)}",
        "",
        "## Disclaimer",
        f"*{report.disclaimer}*",
        ""
    ]
    return "\n".join(md)
