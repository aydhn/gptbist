from pathlib import Path
from typing import Any
from bist_signal_bot.plugins import (
    PluginStore, PluginContractRegistry, PluginManifestParser,
    PluginDiscoveryEngine, SafePluginLoader, PluginHookRegistry,
    PluginCapabilityEvaluator, PluginValidator, PluginTestHarness,
    PluginSandboxPolicy, PluginGovernanceEngine
)

def create_plugin_store(settings: Any = None, base_dir: Path | None = None) -> PluginStore:
    from bist_signal_bot.storage.paths import get_plugins_dir
    dir_path = base_dir or get_plugins_dir(settings)
    return PluginStore(base_dir=dir_path)

def create_plugin_contract_registry(settings: Any = None, base_dir: Path | None = None) -> PluginContractRegistry:
    return PluginContractRegistry()

def create_plugin_manifest_parser(settings: Any = None, base_dir: Path | None = None) -> PluginManifestParser:
    return PluginManifestParser()

def create_plugin_discovery_engine(settings: Any = None, base_dir: Path | None = None) -> PluginDiscoveryEngine:
    from bist_signal_bot.config.settings import get_settings
    s = settings or get_settings()
    root = Path(getattr(s, 'BASE_DIR', '.'))
    return PluginDiscoveryEngine(parser=create_plugin_manifest_parser(s), root_dir=root)

def create_safe_plugin_loader(settings: Any = None, base_dir: Path | None = None) -> SafePluginLoader:
    return SafePluginLoader()

def create_plugin_hook_registry(settings: Any = None, base_dir: Path | None = None) -> PluginHookRegistry:
    return PluginHookRegistry()

def create_plugin_capability_evaluator(settings: Any = None, base_dir: Path | None = None) -> PluginCapabilityEvaluator:
    return PluginCapabilityEvaluator()

def create_plugin_sandbox_policy(settings: Any = None, base_dir: Path | None = None) -> PluginSandboxPolicy:
    return PluginSandboxPolicy()

def create_plugin_validator(settings: Any = None, base_dir: Path | None = None) -> PluginValidator:
    return PluginValidator(
        parser=create_plugin_manifest_parser(settings),
        contracts=create_plugin_contract_registry(settings),
        capabilities=create_plugin_capability_evaluator(settings),
        sandbox=create_plugin_sandbox_policy(settings)
    )

def create_plugin_test_harness(settings: Any = None, base_dir: Path | None = None) -> PluginTestHarness:
    return PluginTestHarness()

def create_plugin_governance_engine(settings: Any = None, base_dir: Path | None = None) -> PluginGovernanceEngine:
    return PluginGovernanceEngine()
