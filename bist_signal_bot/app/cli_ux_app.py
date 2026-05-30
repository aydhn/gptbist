from pathlib import Path
from typing import Optional

from bist_signal_bot.cli_ux.storage import CLIUXStore
from bist_signal_bot.cli_ux.output_contracts import CLIOutputContractRegistry
from bist_signal_bot.cli_ux.schemas import CLIOutputSchemaRegistry
from bist_signal_bot.cli_ux.exit_codes import CLIExitCodeMapper
from bist_signal_bot.cli_ux.errors import CLIErrorNormalizer
from bist_signal_bot.cli_ux.formatters import CLIUXFormatter
from bist_signal_bot.cli_ux.aliases import CLIAliasRegistry
from bist_signal_bot.cli_ux.workflow_runner import CLIWorkflowRunner
from bist_signal_bot.cli_ux.recipe_executor import CommandRecipeExecutor
from bist_signal_bot.cli_ux.command_registry import CLICommandRegistry
from bist_signal_bot.cli_ux.compatibility import CLICompatibilityChecker

def create_cli_ux_store(settings=None, base_dir: Optional[Path] = None) -> CLIUXStore:
    return CLIUXStore(settings=settings, base_dir=base_dir)

def create_cli_output_contract_registry(settings=None) -> CLIOutputContractRegistry:
    return CLIOutputContractRegistry(settings=settings)

def create_cli_output_schema_registry(settings=None) -> CLIOutputSchemaRegistry:
    return CLIOutputSchemaRegistry(settings=settings)

def create_cli_exit_code_mapper(settings=None) -> CLIExitCodeMapper:
    return CLIExitCodeMapper(settings=settings)

def create_cli_error_normalizer(settings=None) -> CLIErrorNormalizer:
    return CLIErrorNormalizer(settings=settings)

def create_cli_ux_formatter(settings=None) -> CLIUXFormatter:
    return CLIUXFormatter(settings=settings)

def create_cli_alias_registry(settings=None) -> CLIAliasRegistry:
    return CLIAliasRegistry(settings=settings)

def create_cli_workflow_runner(settings=None, base_dir: Optional[Path] = None) -> CLIWorkflowRunner:
    return CLIWorkflowRunner(settings=settings, base_dir=base_dir)

def create_command_recipe_executor(settings=None, base_dir: Optional[Path] = None) -> CommandRecipeExecutor:
    return CommandRecipeExecutor(settings=settings, base_dir=base_dir)

def create_cli_command_registry(settings=None) -> CLICommandRegistry:
    return CLICommandRegistry(settings=settings)

def create_cli_compatibility_checker(settings=None, base_dir: Optional[Path] = None) -> CLICompatibilityChecker:
    return CLICompatibilityChecker(settings=settings, base_dir=base_dir)
