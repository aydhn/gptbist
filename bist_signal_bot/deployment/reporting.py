from typing import Any, Dict, List, Union
import pandas as pd
from bist_signal_bot.deployment.models import (
    DeploymentProfile,
    EnvironmentCheckResult,
    EnvTemplateResult,
    FirstRunResult,
    SmokeTestResult,
    OperatorRunbook
)

def deployment_profile_to_dict(profile: DeploymentProfile) -> Dict[str, Any]:
    return profile.model_dump(mode="json")

def environment_check_to_dict(check: EnvironmentCheckResult) -> Dict[str, Any]:
    return check.model_dump(mode="json")

def env_template_result_to_dict(result: EnvTemplateResult) -> Dict[str, Any]:
    return result.model_dump(mode="json")

def first_run_result_to_dict(result: FirstRunResult) -> Dict[str, Any]:
    return result.safe_public_dict()

def smoke_test_result_to_dict(result: SmokeTestResult) -> Dict[str, Any]:
    return result.model_dump(mode="json")

def operator_runbook_to_dict(runbook: OperatorRunbook) -> Dict[str, Any]:
    return runbook.model_dump(mode="json")

def checks_to_dataframe(checks: List[EnvironmentCheckResult]) -> pd.DataFrame:
    data = []
    for c in checks:
        data.append({
            "check_type": c.check_type.name,
            "status": c.status.name,
            "decision": c.decision.name,
            "title": c.title,
            "message": c.message
        })
    return pd.DataFrame(data)

def format_environment_doctor_text(checks: List[EnvironmentCheckResult]) -> str:
    lines = ["Environment Doctor Report", "=" * 25]
    passed = sum(1 for c in checks if c.status.name == "PASS")
    lines.append(f"Passed: {passed}/{len(checks)}\n")

    for c in checks:
        lines.append(f"[{c.status.name}] {c.title}: {c.message}")
        if c.remediation:
            lines.append("  Remediation:")
            for r in c.remediation:
                lines.append(f"  - {r}")
    return "\n".join(lines)

def format_first_run_text(result: FirstRunResult) -> str:
    lines = ["First Run Wizard Report", "=" * 25]
    lines.append(f"Profile: {result.profile.name}")
    lines.append(f"Status: {result.status.name}")
    lines.append(f"Started at: {result.started_at}")
    lines.append(f"Finished at: {result.finished_at}\n")

    lines.append("Steps:")
    for step in result.steps:
        lines.append(f"- [{step.status.name}] {step.step_type.name}: {step.message}")

    lines.append(f"\n_{result.disclaimer}_")
    return "\n".join(lines)

def format_smoke_test_text(result: SmokeTestResult) -> str:
    lines = ["Smoke Test Report", "=" * 17]
    lines.append(f"Status: {result.status.name}")
    lines.append(f"Started at: {result.started_at}\n")

    lines.append("Commands Executed:")
    for c in result.checks:
        lines.append(f"- [{c.status.name}] {c.title}: {c.message}")

    lines.append(f"\n_{result.disclaimer}_")
    return "\n".join(lines)

def format_profile_text(profile: DeploymentProfile) -> str:
    lines = [f"Profile: {profile.name}", "-" * len(profile.name)]
    lines.append(f"Type: {profile.profile_type.name}")
    lines.append(f"Description: {profile.description}")
    lines.append(f"Broker Enabled: {profile.broker_enabled}")
    lines.append(f"Real Order Enabled: {profile.real_order_enabled}")
    lines.append(f"Telegram Send: {profile.telegram_send_enabled}")
    lines.append(f"Scheduler Dry Run: {profile.scheduler_dry_run}\n")

    lines.append("Settings Overrides:")
    for k, v in profile.settings_overrides.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)

def format_operator_runbook_markdown(runbook: OperatorRunbook) -> str:
    from bist_signal_bot.deployment.runbook import OperatorRunbookBuilder
    # Avoid cyclic imports by recreating or using a minimal function
    lines = [f"# {runbook.title}", f"**Oluşturulma:** {runbook.created_at}", "", f"_{runbook.disclaimer}_", ""]
    for section in runbook.sections:
        lines.append(f"## {section['title']}")
        lines.append(section['content'])
        lines.append("")
    return "\n".join(lines)

def format_deployment_report_markdown(result: Union[FirstRunResult, SmokeTestResult, List[EnvironmentCheckResult]]) -> str:
    lines = ["# Deployment Report\n"]
    if isinstance(result, FirstRunResult):
        lines.append(format_first_run_text(result))
    elif isinstance(result, SmokeTestResult):
        lines.append(format_smoke_test_text(result))
    elif isinstance(result, list) and all(isinstance(x, EnvironmentCheckResult) for x in result):
        lines.append(format_environment_doctor_text(result))
    else:
        lines.append("Unknown result type.")

    lines.append("\n_This output is operational only. No real order was sent._")
    return "\n".join(lines)
