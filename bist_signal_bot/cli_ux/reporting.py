import json
from typing import Any, Dict, List
from bist_signal_bot.cli_ux.models import (
    CLIOutputEnvelope, CLICommandContract, CLIOutputSchema,
    CLIErrorMessage, CLIAlias, WorkflowStepResult, WorkflowRun,
    CLICompatibilityResult, CLIUXReport
)

def envelope_to_dict(envelope: CLIOutputEnvelope) -> Dict[str, Any]:
    d = envelope.dict()
    d['created_at'] = d['created_at'].isoformat() if d['created_at'] else None
    d['status'] = d['status'].value
    d['output_mode'] = d['output_mode'].value
    return d

def contract_to_dict(contract: CLICommandContract) -> Dict[str, Any]:
    d = contract.dict()
    d['contract_type'] = d['contract_type'].value
    d['risk_level'] = d['risk_level'].value
    return d

def schema_to_dict(schema: CLIOutputSchema) -> Dict[str, Any]:
    return schema.dict(by_alias=True)

def error_message_to_dict(error: CLIErrorMessage) -> Dict[str, Any]:
    return error.dict()

def alias_to_dict(alias: CLIAlias) -> Dict[str, Any]:
    return alias.dict()

def workflow_step_to_dict(step: WorkflowStepResult) -> Dict[str, Any]:
    d = step.dict()
    d['started_at'] = d['started_at'].isoformat() if d['started_at'] else None
    d['finished_at'] = d['finished_at'].isoformat() if d['finished_at'] else None
    d['status'] = d['status'].value
    return d

def workflow_run_to_dict(run: WorkflowRun) -> Dict[str, Any]:
    d = run.dict()
    d['created_at'] = d['created_at'].isoformat() if d['created_at'] else None
    d['status'] = d['status'].value
    d['steps'] = [workflow_step_to_dict(s) for s in run.steps]
    return d

def compatibility_to_dict(result: CLICompatibilityResult) -> Dict[str, Any]:
    d = result.dict()
    d['created_at'] = d['created_at'].isoformat() if d['created_at'] else None
    d['status'] = d['status'].value
    return d

def cli_ux_report_to_dict(report: CLIUXReport) -> Dict[str, Any]:
    d = report.dict()
    d['generated_at'] = d['generated_at'].isoformat() if d['generated_at'] else None
    d['contracts'] = [contract_to_dict(c) for c in report.contracts]
    d['schemas'] = [schema_to_dict(s) for s in report.schemas]
    d['aliases'] = [alias_to_dict(a) for a in report.aliases]
    d['workflow_runs'] = [workflow_run_to_dict(w) for w in report.workflow_runs]
    if report.compatibility:
        d['compatibility'] = compatibility_to_dict(report.compatibility)
    return d

def format_contracts_text(contracts: List[CLICommandContract]) -> str:
    lines = ["Available Contracts:"]
    for c in contracts:
        lines.append(f"  {c.command_path} ({c.contract_type.value}) - {c.description}")
        lines.append(f"    Schema: {c.output_schema_name}")
        lines.append(f"    Stable Fields: {', '.join(c.stable_fields)}")
    return "\n".join(lines)

def format_aliases_text(aliases: List[CLIAlias]) -> str:
    lines = ["Available Aliases:"]
    for a in aliases:
        lines.append(f"  {a.alias} -> {a.target_command} ({a.description})")
    return "\n".join(lines)

def format_workflow_run_text(run: WorkflowRun) -> str:
    lines = [
        f"Workflow Run: {run.workflow_name}",
        f"Status: {run.status.value}",
        f"Exit Code: {run.exit_code}",
        "Steps:"
    ]
    for s in run.steps:
        lines.append(f"  [{s.status.value}] {s.command} ({s.elapsed_seconds:.2f}s if float available)")
    return "\n".join(lines)

def format_compatibility_text(result: CLICompatibilityResult) -> str:
    lines = [
        f"CLI Compatibility Status: {result.status.value}",
        f"Contracts Checked: {result.contracts_checked}",
        f"Compatible: {result.compatible_count}",
        f"Drift: {result.drift_count}",
        f"Missing: {result.missing_count}"
    ]
    return "\n".join(lines)

def format_cli_ux_report_markdown(report: CLIUXReport) -> str:
    lines = [
        "# CLI UX Report",
        f"Generated at: {report.generated_at.isoformat()}",
        "",
        "## Overview",
        f"Contracts: {len(report.contracts)}",
        f"Schemas: {len(report.schemas)}",
        f"Aliases: {len(report.aliases)}",
    ]

    if report.compatibility:
        lines.extend([
            "",
            "## Compatibility",
            f"Status: {report.compatibility.status.value}",
            f"Drift Count: {report.compatibility.drift_count}"
        ])

    lines.extend([
        "",
        "## Key Findings",
        *(f"- {f}" for f in report.key_findings),
        "",
        "---",
        f"*{report.disclaimer}*"
    ])

    return "\n".join(lines)
