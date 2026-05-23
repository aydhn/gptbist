from pathlib import Path
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import PROJECT_ROOT

from bist_signal_bot.deployment.profiles import DeploymentProfileManager
from bist_signal_bot.deployment.env_template import EnvTemplateBuilder
from bist_signal_bot.deployment.doctor import EnvironmentDoctor
from bist_signal_bot.deployment.directories import DeploymentDirectoryManager
from bist_signal_bot.deployment.first_run import FirstRunWizard
from bist_signal_bot.deployment.smoke import DeploymentSmokeTester
from bist_signal_bot.deployment.runbook import OperatorRunbookBuilder
from bist_signal_bot.deployment.storage import DeploymentStore


def get_default_settings() -> Settings:
    return Settings()

def get_default_base_dir() -> Path:
    return PROJECT_ROOT

def create_deployment_profile_manager(settings: Optional[Settings] = None) -> DeploymentProfileManager:
    return DeploymentProfileManager()

def create_env_template_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> EnvTemplateBuilder:
    base_dir = base_dir or get_default_base_dir()
    return EnvTemplateBuilder(base_dir=base_dir)

def create_environment_doctor(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> EnvironmentDoctor:
    settings = settings or get_default_settings()
    base_dir = base_dir or get_default_base_dir()
    return EnvironmentDoctor(settings=settings, base_dir=base_dir)

def create_first_run_wizard(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> FirstRunWizard:
    settings = settings or get_default_settings()
    base_dir = base_dir or get_default_base_dir()
    return FirstRunWizard(settings=settings, base_dir=base_dir)

def create_deployment_directory_manager(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DeploymentDirectoryManager:
    settings = settings or get_default_settings()
    base_dir = base_dir or get_default_base_dir()
    return DeploymentDirectoryManager(settings=settings, base_dir=base_dir)

def create_deployment_smoke_tester(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DeploymentSmokeTester:
    settings = settings or get_default_settings()
    base_dir = base_dir or get_default_base_dir()
    return DeploymentSmokeTester(settings=settings, base_dir=str(base_dir))

def create_operator_runbook_builder(settings: Optional[Settings] = None) -> OperatorRunbookBuilder:
    settings = settings or get_default_settings()
    return OperatorRunbookBuilder(settings=settings)

def create_deployment_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DeploymentStore:
    settings = settings or get_default_settings()
    # If base_dir provided, override deployment base dir explicitly if needed, but standard uses settings
    from bist_signal_bot.storage.paths import get_deployment_dir
    deploy_dir = base_dir or get_deployment_dir(settings)
    return DeploymentStore(settings=settings, base_dir=deploy_dir)
