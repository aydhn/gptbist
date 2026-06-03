import pytest
from pathlib import Path
from bist_signal_bot.plugins.models import (
    PluginManifest, PluginKind, PluginCapabilityKind, PluginStatus, PluginExecutionMode, PluginHookKind
)
from bist_signal_bot.plugins.contracts import PluginContractRegistry
from bist_signal_bot.plugins.manifest import PluginManifestParser
from bist_signal_bot.plugins.discovery import PluginDiscoveryEngine
from bist_signal_bot.plugins.loader import SafePluginLoader
from bist_signal_bot.plugins.hooks import PluginHookRegistry, PluginHookRegistration
from bist_signal_bot.plugins.capabilities import PluginCapabilityEvaluator
from bist_signal_bot.plugins.validation import PluginValidator
from bist_signal_bot.plugins.test_harness import PluginTestHarness
from bist_signal_bot.plugins.sandbox import PluginSandboxPolicy
from bist_signal_bot.plugins.governance import PluginGovernanceEngine
from bist_signal_bot.plugins.storage import PluginStore

def test_manifest_validation():
    manifest = PluginManifest(
        plugin_id="test_plugin",
        name="Test",
        version="1.0",
        kind=PluginKind.STRATEGY,
        description="A test"
    )
    assert manifest.plugin_id == "test_plugin"

def test_contract_registry():
    reg = PluginContractRegistry()
    contracts = reg.default_contracts()
    assert len(contracts) > 0
    strat_contract = reg.contract_for_kind(PluginKind.STRATEGY)
    assert strat_contract is not None
    assert "entrypoint" in strat_contract.required_fields

def test_manifest_parser(tmp_path):
    p = tmp_path / "plugin.json"
    p.write_text('{"plugin_id": "test_id", "name": "test", "version": "1", "kind": "STRATEGY", "description": "desc"}')
    parser = PluginManifestParser()
    m = parser.parse_manifest(p)
    assert m.plugin_id == "test_id"
    assert parser.validate_manifest_schema(m) == []

def test_discovery_engine(tmp_path):
    parser = PluginManifestParser()
    engine = PluginDiscoveryEngine(parser, tmp_path)
    # mock a dir
    d = tmp_path / "plugins" / "my_plugin"
    d.mkdir(parents=True)
    f = d / "plugin.json"
    f.write_text('{"plugin_id": "test_id", "name": "test", "version": "1", "kind": "STRATEGY", "description": "desc", "enabled": true}')
    manifests = engine.discover([tmp_path / "plugins"])
    assert len(manifests) == 1
    assert engine.discovery_summary(manifests)["enabled"] == 1

def test_safe_loader():
    loader = SafePluginLoader()
    manifest = PluginManifest(plugin_id="p1", name="p", version="1", kind=PluginKind.STRATEGY, description="d")
    res = loader.load_plugin(manifest, PluginExecutionMode.SAFE_METADATA_ONLY)
    assert res.loaded is True
    assert res.execution_mode == PluginExecutionMode.SAFE_METADATA_ONLY
    res_blocked = loader.load_plugin(manifest, PluginExecutionMode.LOCAL_EXECUTE)
    assert res_blocked.status == PluginStatus.BLOCKED

def test_hook_registry():
    reg = PluginHookRegistry()
    h = PluginHookRegistration(registration_id="h1", plugin_id="p1", hook_kind=PluginHookKind.STRATEGY_DISCOVERY, enabled=True, status=PluginStatus.UNKNOWN)
    reg.register_hook(h)
    assert len(reg.hooks_for_kind(PluginHookKind.STRATEGY_DISCOVERY)) == 1
    disp = reg.dispatch_hook(PluginHookKind.STRATEGY_DISCOVERY)
    assert len(disp) == 1
    assert disp[0]["dry_run"] is True

def test_capabilities_evaluator():
    evaluator = PluginCapabilityEvaluator()
    m = PluginManifest(plugin_id="p1", name="p", version="1", kind=PluginKind.STRATEGY, description="d", requested_capabilities=[PluginCapabilityKind.EXTERNAL_NETWORK, PluginCapabilityKind.REGISTER_STRATEGY])
    ass = evaluator.assess_capabilities(m)
    assert PluginCapabilityKind.EXTERNAL_NETWORK in ass.blocked_capabilities
    assert PluginCapabilityKind.REGISTER_STRATEGY in ass.allowed_capabilities
    assert ass.status == PluginStatus.BLOCKED

def test_plugin_validator():
    parser = PluginManifestParser()
    contracts = PluginContractRegistry()
    capabilities = PluginCapabilityEvaluator()
    sandbox = PluginSandboxPolicy()
    validator = PluginValidator(parser, contracts, capabilities, sandbox)

    m = PluginManifest(plugin_id="p1", name="p", version="1", kind=PluginKind.STRATEGY, description="d", requested_capabilities=[PluginCapabilityKind.EXTERNAL_NETWORK])
    # Contract validation fails because entrypoint missing, hook missing
    # Capabilities fails because EXTERNAL_NETWORK is blocked
    res = validator.validate_plugin(m)
    assert res.status == PluginStatus.BLOCKED # Because of capabilities
    assert res.contract_valid is False

def test_test_harness():
    harness = PluginTestHarness()
    m = PluginManifest(plugin_id="p1", name="p", version="1", kind=PluginKind.STRATEGY, description="A sure thing to win")
    res = harness.run_plugin_tests(m)
    assert res.tests_failed > 0
    # unsafe language found
    assert res.status == PluginStatus.FAIL

def test_sandbox_policy():
    s = PluginSandboxPolicy()
    m = PluginManifest(plugin_id="p1", name="p", version="1", kind=PluginKind.STRATEGY, description="d", metadata={"unsafe_language": True})
    assert len(s.validate_manifest_sandbox(m)) > 0

def test_governance_engine():
    gov = PluginGovernanceEngine()
    m = PluginManifest(plugin_id="p1", name="p", version="1", kind=PluginKind.STRATEGY, description="A sure thing to win", requested_capabilities=[PluginCapabilityKind.EXTERNAL_NETWORK])
    res = gov.assess_plugin(m)
    assert res.status == PluginStatus.BLOCKED
    assert len(res.unsafe_language_findings) > 0

def test_plugin_store(tmp_path):
    store = PluginStore(tmp_path)
    m = PluginManifest(plugin_id="p1", name="p", version="1", kind=PluginKind.STRATEGY, description="d")
    store.append_manifest(m)
    manifests = store.load_manifests()
    assert len(manifests) == 1
    assert manifests[0].plugin_id == "p1"
