from typing import Any, List
from bist_signal_bot.final_handoff.models import (
    FinalModuleSummary,
    FinalCommandMapEntry,
    OperatorPlaybook,
    DeveloperPlaybook,
    PostReleaseRoadmapItem,
    MaintenanceTask,
    FinalReleasePack,
    FinalHandoffManifest,
    FinalHandoffReport
)

def module_summary_to_dict(summary: FinalModuleSummary) -> dict[str, Any]:
    return summary.model_dump()

def command_entry_to_dict(entry: FinalCommandMapEntry) -> dict[str, Any]:
    return entry.model_dump()

def operator_playbook_to_dict(playbook: OperatorPlaybook) -> dict[str, Any]:
    return playbook.model_dump()

def developer_playbook_to_dict(playbook: DeveloperPlaybook) -> dict[str, Any]:
    return playbook.model_dump()

def roadmap_item_to_dict(item: PostReleaseRoadmapItem) -> dict[str, Any]:
    return item.model_dump()

def maintenance_task_to_dict(task: MaintenanceTask) -> dict[str, Any]:
    return task.model_dump()

def release_pack_to_dict(pack: FinalReleasePack) -> dict[str, Any]:
    return pack.model_dump()

def handoff_manifest_to_dict(manifest: FinalHandoffManifest) -> dict[str, Any]:
    return manifest.model_dump()

def handoff_report_to_dict(report: FinalHandoffReport) -> dict[str, Any]:
    return report.model_dump()

def format_module_map_text(modules: list[FinalModuleSummary]) -> str:
    lines = ["# Final Module Map\n"]
    for m in modules:
        lines.append(f"## {m.title} ({m.module_name})")
        lines.append(f"- **Status**: {m.status.value}")
        lines.append(f"- **Purpose**: {m.purpose}")
        lines.append(f"- **Owner Area**: {m.owner_area}")
        if m.dependencies:
            lines.append(f"- **Dependencies**: {', '.join(m.dependencies)}")
        if m.warnings:
            lines.append(f"- **Warnings**: {', '.join(m.warnings)}")
        lines.append("")
    return "\n".join(lines)

def format_command_map_text(entries: list[FinalCommandMapEntry]) -> str:
    lines = ["# Final Command Map\n"]
    for e in entries:
        lines.append(f"## {e.command}")
        lines.append(f"- **Audience**: {e.audience.value}")
        lines.append(f"- **Purpose**: {e.purpose}")
        lines.append(f"- **Safe Mode**: {e.safe_mode}")
        lines.append(f"- *Disclaimer*: {e.disclaimer}")
        lines.append("")
    return "\n".join(lines)

def format_operator_playbook_markdown(playbook: OperatorPlaybook) -> str:
    lines = [f"# {playbook.title}\n"]
    lines.append(f"*Disclaimer: {playbook.disclaimer}*\n")

    if playbook.daily_routine:
        lines.append("## Daily Routine")
        for task in playbook.daily_routine:
            lines.append(f"- {task}")
        lines.append("")

    if playbook.weekly_routine:
        lines.append("## Weekly Routine")
        for task in playbook.weekly_routine:
            lines.append(f"- {task}")
        lines.append("")

    if playbook.monthly_routine:
        lines.append("## Monthly Routine")
        for task in playbook.monthly_routine:
            lines.append(f"- {task}")
        lines.append("")

    if playbook.emergency_checks:
        lines.append("## Emergency Checks")
        for task in playbook.emergency_checks:
            lines.append(f"- {task}")
        lines.append("")

    return "\n".join(lines)

def format_developer_playbook_markdown(playbook: DeveloperPlaybook) -> str:
    lines = [f"# {playbook.title}\n"]
    lines.append(f"*Disclaimer: {playbook.disclaimer}*\n")

    if playbook.coding_standards:
        lines.append("## Coding Standards")
        for std in playbook.coding_standards:
            lines.append(f"- {std}")
        lines.append("")

    if playbook.test_standards:
        lines.append("## Test Standards")
        for std in playbook.test_standards:
            lines.append(f"- {std}")
        lines.append("")

    if playbook.extension_points:
        lines.append("## Extension Points")
        for pt in playbook.extension_points:
            lines.append(f"- {pt}")
        lines.append("")

    return "\n".join(lines)

def format_roadmap_markdown(items: list[PostReleaseRoadmapItem]) -> str:
    lines = ["# Post-Release Roadmap\n"]
    for i in items:
        lines.append(f"## {i.title} [{i.priority.value}]")
        lines.append(f"- **Target**: {i.target_area}")
        lines.append(f"- **Phase**: {i.suggested_phase or 'N/A'}")
        lines.append(f"- **Status**: {i.status.value}")
        lines.append(f"- **Description**: {i.description}")
        lines.append("")
    return "\n".join(lines)

def format_maintenance_markdown(tasks: list[MaintenanceTask]) -> str:
    lines = ["# Maintenance Cadence\n"]
    for t in tasks:
        lines.append(f"## {t.title} ({t.cadence.value})")
        lines.append(f"- **Command**: `{t.command_hint}`")
        lines.append(f"- **Requires Confirm**: {t.requires_confirm}")
        lines.append(f"- *Disclaimer*: {t.disclaimer}")
        lines.append("")
    return "\n".join(lines)

def format_release_pack_text(pack: FinalReleasePack) -> str:
    lines = [f"# Final Release Pack ({pack.stage.value})\n"]
    lines.append(f"*Disclaimer: {pack.disclaimer}*\n")
    lines.append(f"- **Release Candidate**: {pack.release_candidate_id or 'N/A'}")
    lines.append(f"- **Go/No-Go**: {pack.go_no_go_decision or 'N/A'}")
    lines.append("")

    if pack.included_docs:
        lines.append("## Docs")
        for d in pack.included_docs:
            lines.append(f"- {d}")
        lines.append("")

    return "\n".join(lines)

def format_handoff_manifest_text(manifest: FinalHandoffManifest) -> str:
    lines = [f"# Final Handoff Manifest: {manifest.project_name}\n"]
    lines.append(f"*Disclaimer: {manifest.disclaimer}*\n")
    lines.append(f"- **Status**: {manifest.final_status.value}")
    lines.append(f"- **Release Pack**: {manifest.release_pack_id or 'N/A'}")
    lines.append(f"- **Release Candidate**: {manifest.release_candidate_id or 'N/A'}")
    lines.append(f"- **Go/No-Go**: {manifest.go_no_go_decision or 'N/A'}")
    lines.append("")
    lines.append(f"**Summary**: {manifest.project_summary}\n")
    return "\n".join(lines)

def format_final_handoff_report_markdown(report: FinalHandoffReport) -> str:
    lines = [f"# Final Handoff Report\n"]
    lines.append(f"Generated at: {report.generated_at.isoformat()}\n")
    lines.append(f"*Disclaimer: {report.disclaimer}*\n")

    if report.manifest:
        lines.append("## Manifest Summary")
        lines.append(f"Status: {report.manifest.final_status.value}")
        lines.append("")

    if report.key_findings:
        lines.append("## Key Findings")
        for k in report.key_findings:
            lines.append(f"- {k}")
        lines.append("")

    return "\n".join(lines)
