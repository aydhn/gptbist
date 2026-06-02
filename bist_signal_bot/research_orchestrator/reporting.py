import pandas as pd
from typing import Any

from bist_signal_bot.research_orchestrator.models import (
    ResearchTask, ResearchDependency, ResearchRunPlan, ResearchTaskResult,
    ResearchRunManifest, ResearchRun, ResearchCampaign, ResearchGuardrailCheck,
    ResearchOrchestratorReport
)

def task_to_dict(task: ResearchTask) -> dict[str, Any]:
    return task.model_dump(mode="json")

def dependency_to_dict(dep: ResearchDependency) -> dict[str, Any]:
    return dep.model_dump(mode="json")

def plan_to_dict(plan: ResearchRunPlan) -> dict[str, Any]:
    return plan.model_dump(mode="json")

def task_result_to_dict(result: ResearchTaskResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def manifest_to_dict(manifest: ResearchRunManifest) -> dict[str, Any]:
    return manifest.model_dump(mode="json")

def run_to_dict(run: ResearchRun) -> dict[str, Any]:
    return run.model_dump(mode="json")

def campaign_to_dict(campaign: ResearchCampaign) -> dict[str, Any]:
    return campaign.model_dump(mode="json")

def guardrail_check_to_dict(check: ResearchGuardrailCheck) -> dict[str, Any]:
    return check.model_dump(mode="json")

def orchestrator_report_to_dict(report: ResearchOrchestratorReport) -> dict[str, Any]:
    return report.model_dump(mode="json")

def plans_to_dataframe(plans: list[ResearchRunPlan]) -> pd.DataFrame:
    if not plans:
        return pd.DataFrame()
    data = [plan_to_dict(p) for p in plans]
    return pd.DataFrame(data)

def runs_to_dataframe(runs: list[ResearchRun]) -> pd.DataFrame:
    if not runs:
        return pd.DataFrame()
    data = [run_to_dict(r) for r in runs]
    return pd.DataFrame(data)

def format_plan_text(plan: ResearchRunPlan) -> str:
    lines = [
        f"Plan ID: {plan.plan_id}",
        f"Campaign: {plan.campaign_type.value}",
        f"Status: {plan.status.value}",
        f"Mode: {plan.execution_mode.value}",
        f"Tasks: {len(plan.tasks)}",
        f"Disclaimer: {plan.disclaimer}"
    ]
    return "\n".join(lines)

def format_run_text(run: ResearchRun) -> str:
    lines = [
        f"Run ID: {run.run_id}",
        f"Plan ID: {run.plan.plan_id}",
        f"Status: {run.status.value}",
        f"Tasks Run: {len(run.task_results)}",
        f"Disclaimer: {run.disclaimer}"
    ]
    return "\n".join(lines)

def format_campaign_text(campaign: ResearchCampaign) -> str:
    lines = [
        f"Campaign ID: {campaign.campaign_id}",
        f"Name: {campaign.name}",
        f"Type: {campaign.campaign_type.value}",
        f"Description: {campaign.description}",
        f"Disclaimer: {campaign.disclaimer}"
    ]
    return "\n".join(lines)

def format_guardrails_text(checks: list[ResearchGuardrailCheck]) -> str:
    lines = ["Guardrail Checks:"]
    for c in checks:
        lines.append(f"- {c.name}: {c.status.value} (Blocked: {c.blocked})")
    return "\n".join(lines)

def format_manifest_text(manifest: ResearchRunManifest) -> str:
    lines = [
        f"Manifest ID: {manifest.manifest_id}",
        f"Run ID: {manifest.run_id}",
        f"Mode: {manifest.execution_mode.value}",
        f"Checksums: {len(manifest.checksum_manifest)}",
        f"Disclaimer: {manifest.disclaimer}"
    ]
    return "\n".join(lines)

def format_orchestrator_report_markdown(report: ResearchOrchestratorReport) -> str:
    lines = [
        "# Research Orchestrator Report",
        f"Generated At: {report.generated_at}",
        "",
        f"Plans: {len(report.plans)}",
        f"Runs: {len(report.runs)}",
        f"Campaigns: {len(report.campaigns)}",
        "",
        "## Key Findings",
    ]
    for f in report.key_findings:
        lines.append(f"- {f}")

    lines.extend([
        "",
        "## Disclaimer",
        f"_{report.disclaimer}_"
    ])
    return "\n".join(lines)

def render_orchestrator_template(context: dict) -> dict:
    from bist_signal_bot.report_templates.models import RenderedReportSection, ReportValidationStatus
    return {
        "rendered_section_id": "sec_orch",
        "section_key": "orchestrator",
        "title": "Orchestrator Report",
        "content_markdown": "*Orchestrator summary.*",
        "content_json": {"status": "PASS"},
        "status": ReportValidationStatus.PASS,
        "warnings": []
    }
