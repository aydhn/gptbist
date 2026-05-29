from pathlib import Path
from bist_signal_bot.bootstrap.storage import BootstrapStore
from bist_signal_bot.bootstrap.profiles import RunProfileRegistry
from bist_signal_bot.bootstrap.initializer import BootstrapInitializer
from bist_signal_bot.bootstrap.validator import BootstrapValidator
from bist_signal_bot.bootstrap.demo import OfflineDemoRunner
from bist_signal_bot.bootstrap.recipes import CommandRecipeRegistry
from bist_signal_bot.bootstrap.release_bundle import ReleaseBundleBuilder
from bist_signal_bot.bootstrap.onboarding import OnboardingGuideBuilder

def create_bootstrap_store(settings=None, base_dir: Path | None = None) -> BootstrapStore:
    return BootstrapStore(settings, base_dir)

def create_run_profile_registry(settings=None) -> RunProfileRegistry:
    return RunProfileRegistry(settings)

def create_bootstrap_initializer(settings=None, base_dir: Path | None = None) -> BootstrapInitializer:
    return BootstrapInitializer(settings, base_dir)

def create_bootstrap_validator(settings=None, base_dir: Path | None = None) -> BootstrapValidator:
    return BootstrapValidator(settings, base_dir)

def create_offline_demo_runner(settings=None, base_dir: Path | None = None) -> OfflineDemoRunner:
    return OfflineDemoRunner(settings, base_dir)

def create_command_recipe_registry(settings=None) -> CommandRecipeRegistry:
    return CommandRecipeRegistry(settings)

def create_release_bundle_builder(settings=None, base_dir: Path | None = None) -> ReleaseBundleBuilder:
    return ReleaseBundleBuilder(settings, base_dir)

def create_onboarding_guide_builder(settings=None) -> OnboardingGuideBuilder:
    return OnboardingGuideBuilder(settings)
