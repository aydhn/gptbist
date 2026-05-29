import pytest
from pathlib import Path
from bist_signal_bot.bootstrap.models import RunProfileName, BootstrapStatus
from bist_signal_bot.bootstrap.profiles import RunProfileRegistry
from bist_signal_bot.bootstrap.initializer import BootstrapInitializer
from bist_signal_bot.bootstrap.validator import BootstrapValidator
from bist_signal_bot.bootstrap.demo import OfflineDemoRunner
from bist_signal_bot.bootstrap.recipes import CommandRecipeRegistry
from bist_signal_bot.bootstrap.release_bundle import ReleaseBundleBuilder
from bist_signal_bot.bootstrap.onboarding import OnboardingGuideBuilder
from bist_signal_bot.bootstrap.storage import BootstrapStore

def test_registry_unsafe_override():
    reg = RunProfileRegistry()
    prof = reg.get_profile(RunProfileName.STANDARD)
    prof.env_overrides["ENABLE_BROKER"] = "true"
    warnings = reg.validate_profile(prof)
    assert any("BLOCK" in w for w in warnings)

def test_registry_defaults():
    reg = RunProfileRegistry()
    profs = reg.default_profiles()
    assert len(profs) == 6
    names = [p.name for p in profs]
    assert RunProfileName.STANDARD in names

def test_initializer_dry_run(tmp_path):
    init = BootstrapInitializer(base_dir=tmp_path)
    res = init.init_project(confirm=False)
    assert res.status == BootstrapStatus.SKIPPED
    assert not list(tmp_path.iterdir())

def test_initializer_confirm(tmp_path):
    init = BootstrapInitializer(base_dir=tmp_path)
    res = init.init_project(confirm=True)
    assert res.status == BootstrapStatus.PASS
    assert (tmp_path / "data").exists()

def test_validator_paths(tmp_path):
    val = BootstrapValidator(base_dir=tmp_path)
    res = val.check_paths()
    assert res.status == BootstrapStatus.PASS

def test_demo_runner(tmp_path):
    runner = OfflineDemoRunner(base_dir=tmp_path)
    res = runner.run_demo()
    assert res.status == BootstrapStatus.PASS
    assert len(res.commands_run) > 0

def test_recipes():
    reg = CommandRecipeRegistry()
    res = reg.default_recipes()
    assert len(res) > 0
    md = reg.render_recipe_markdown(res[0])
    assert "# Quickstart" in md

def test_release_bundle(tmp_path):
    builder = ReleaseBundleBuilder(base_dir=tmp_path)
    man = builder.build_manifest()
    assert man.status == BootstrapStatus.PASS

def test_onboarding():
    builder = OnboardingGuideBuilder()
    guide = builder.build_guide()
    assert guide.title == "Local MVP Onboarding"

def test_storage(tmp_path):
    store = BootstrapStore(base_dir=tmp_path)
    builder = ReleaseBundleBuilder(base_dir=tmp_path)
    man = builder.build_manifest()
    store.append_release_bundle(man)
    assert (tmp_path / "bootstrap/release/release_bundle_manifests.jsonl").exists()
