import pytest
from datetime import datetime, timezone
import uuid
from bist_signal_bot.cli_ux.models import (
    CLIStatus, CLIOutputMode, CLIExitCode, CommandRiskLevel,
    CommandContractType, CLIOutputEnvelope, CLICommandContract,
    CLIOutputSchema, CLIErrorMessage, CLIAlias, WorkflowStepResult, WorkflowRun
)
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
from bist_signal_bot.cli_ux.storage import CLIUXStore

def test_cli_output_envelope():
    env = CLIOutputEnvelope(
        envelope_id="test",
        created_at=datetime.now(timezone.utc),
        command="test",
        status=CLIStatus.SUCCESS,
        exit_code=0,
        output_mode=CLIOutputMode.JSON,
        payload={"data": "test"}
    )
    assert env.disclaimer != ""
    assert env.exit_code == 0

def test_output_contract_registry():
    registry = CLIOutputContractRegistry()
    contracts = registry.default_contracts()
    assert len(contracts) > 0
    c = registry.get_contract("healthcheck")
    assert c is not None
    assert c.command_path == "healthcheck"

def test_schema_registry():
    registry = CLIOutputSchemaRegistry()
    schemas = registry.default_schemas()
    assert len(schemas) > 0
    s = registry.safe_json_schema("HealthcheckOutput")
    assert s is not None

def test_exit_code_mapper():
    mapper = CLIExitCodeMapper()
    assert mapper.code_for_status(CLIStatus.SUCCESS) == CLIExitCode.SUCCESS
    assert mapper.code_for_status(CLIStatus.FAILED) == CLIExitCode.INTERNAL_ERROR

    class FakeBlockedError(Exception): pass
    class FakeSafetyBlockedError(Exception): pass
    assert mapper.code_for_exception(FakeSafetyBlockedError()) == CLIExitCode.SAFETY_BLOCKED

def test_error_normalizer():
    normalizer = CLIErrorNormalizer()
    err = normalizer.normalize_exception(FileNotFoundError("test file"))
    assert err.error_type == "FileNotFoundError"
    assert "missing" in err.user_message.lower()

def test_formatter():
    formatter = CLIUXFormatter()
    env = CLIOutputEnvelope(
        envelope_id="test",
        created_at=datetime.now(timezone.utc),
        command="test",
        status=CLIStatus.SUCCESS,
        exit_code=0,
        output_mode=CLIOutputMode.JSON,
        payload={"secret": "mytoken123", "public": "ok"}
    )
    formatted = formatter.format_json(env)
    assert "mytoken123" not in formatted
    assert "REDACTED" in formatted

def test_alias_registry():
    registry = CLIAliasRegistry()
    aliases = registry.default_aliases()
    assert len(aliases) > 0
    assert registry.resolve_alias("bt scan") == "scan symbols"

def test_workflow_runner():
    runner = CLIWorkflowRunner()
    run = runner.run_workflow("test", ["echo '1'"], dry_run=True)
    assert run.status == CLIStatus.SUCCESS

    # test blocked
    run2 = runner.run_workflow("test2", ["delete something"], dry_run=False)
    assert run2.status == CLIStatus.BLOCKED

def test_recipe_executor():
    executor = CommandRecipeExecutor()
    cmds = executor.preview_recipe("QUICKSTART")
    assert len(cmds) > 0

def test_command_registry():
    registry = CLICommandRegistry()
    cmds = registry.registered_commands()
    assert len(cmds) > 0

def test_compatibility_checker():
    checker = CLICompatibilityChecker()
    res = checker.check_compatibility()
    assert res.contracts_checked > 0

def test_cli_ux_store(tmp_path):
    store = CLIUXStore(base_dir=tmp_path)
    run = WorkflowRun(
        run_id="test",
        created_at=datetime.now(timezone.utc),
        workflow_name="test",
        status=CLIStatus.SUCCESS,
        exit_code=0
    )
    store.append_workflow_run(run)
    runs = store.load_workflow_runs()
    assert len(runs) == 1
    assert runs[0].run_id == "test"
