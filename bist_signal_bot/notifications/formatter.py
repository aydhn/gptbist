import json
from bist_signal_bot.plugins.models import (
    PluginManifest, PluginValidationResult, PluginTestResult, PluginLoadResult,
    PluginGovernanceAssessment, PluginRegistryReport
)

def format_plugin_manifest(manifest: PluginManifest) -> str:
    return "Plugin: " + str(manifest.plugin_id) + "\nName: " + str(manifest.name) + "\nDisclaimer: Yatırım tavsiyesi değildir."

def format_plugin_validation(result: PluginValidationResult) -> str:
    return "Plugin: " + str(result.plugin_id) + "\nStatus: " + str(result.status.value) + "\nDisclaimer: Yatırım tavsiyesi değildir."

def format_plugin_test_result(result: PluginTestResult) -> str:
    return "Plugin: " + str(result.plugin_id) + "\nStatus: " + str(result.status.value) + "\nDisclaimer: Yatırım tavsiyesi değildir."

def format_plugin_load_result(result: PluginLoadResult) -> str:
    return "Plugin: " + str(result.plugin_id) + "\nStatus: " + str(result.status.value) + "\nDisclaimer: Yatırım tavsiyesi değildir."

def format_plugin_governance(assessment: PluginGovernanceAssessment) -> str:
    return "Plugin: " + str(assessment.plugin_id) + "\nStatus: " + str(assessment.status.value) + "\nDisclaimer: Yatırım tavsiyesi değildir."

def format_plugin_registry_report(report: PluginRegistryReport) -> str:
    return "Total Manifests: " + str(len(report.manifests)) + "\nDisclaimer: Yatırım tavsiyesi değildir."
