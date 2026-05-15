import os
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.packaging.environment import EnvironmentDoctor
from bist_signal_bot.packaging.release import ReleaseBundleBuilder
from bist_signal_bot.packaging.dependencies import DependencyChecker

def create_environment_doctor(settings: Settings | None = None, base_dir: Path | None = None) -> EnvironmentDoctor:
    return EnvironmentDoctor(settings, base_dir)

def create_release_bundle_builder(settings: Settings | None = None, base_dir: Path | None = None) -> ReleaseBundleBuilder:
    return ReleaseBundleBuilder(settings=settings)

def create_dependency_checker(settings: Settings | None = None) -> DependencyChecker:
    return DependencyChecker(settings)
