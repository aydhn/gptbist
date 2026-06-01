from typing import Any, List
from bist_signal_bot.final_handoff.models import (
    FinalModuleSummary, FinalCommandMapEntry, OperatorPlaybook,
    DeveloperPlaybook, PostReleaseRoadmapItem, MaintenanceTask,
    FinalReleasePack, FinalHandoffManifest, FinalHandoffReport
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

def format_module_map_text(modules: List[FinalModuleSummary]) -> str:
    lines = ["# Final Module Map\n"]
    for module in modules:
        lines.append(f"## {module.title} ({module.module_name})")
        lines.append(f"- **Purpose**: {module.purpose}")
        lines.append(f"- **Owner**: {module.owner_area}")
        lines.append(f"- **Status**: {module.status.value}")
        lines.append(f"- **Commands**: {', '.join(module.main_commands)}")
        lines.append("")
    return "\n".join(lines)

def format_command_map_text(entries: List[FinalCommandMapEntry]) -> str:
    lines = ["# Final Command Map\n"]
    for entry in entries:
        lines.append(f"## {entry.command}")
        lines.append(f"- **Category**: {entry.category}")
        lines.append(f"- **Audience**: {entry.audience.value}")
        lines.append(f"- **Purpose**: {entry.purpose}")
        lines.append(f"- **Safe Mode**: {entry.safe_mode}")
        lines.append(f"- **Dry-Run Supported**: {entry.dry_run_supported}")
        lines.append(f"- **JSON Supported**: {entry.json_supported}")
        lines.append(f"\n> *Disclaimer*: {entry.disclaimer}\n")
    return "\n".join(lines)

def format_operator_playbook_markdown(playbook: OperatorPlaybook) -> str:
    lines = [f"# {playbook.title}\n"]

    lines.append("## Daily Routine")
    for cmd in playbook.daily_routine:
        lines.append(f"- `{cmd}`")
    lines.append("")

    lines.append("## Weekly Routine")
    for cmd in playbook.weekly_routine:
        lines.append(f"- `{cmd}`")
    lines.append("")

    lines.append("## Monthly Routine")
    for cmd in playbook.monthly_routine:
        lines.append(f"- `{cmd}`")
    lines.append("")

    lines.append("## Emergency Checks")
    for cmd in playbook.emergency_checks:
        lines.append(f"- `{cmd}`")
    lines.append("")

    lines.append("## Troubleshooting")
    for section in playbook.sections:
        lines.append(f"### {section.get('topic')}")
        lines.append(f"**Check**: `{section.get('check')}`")
        lines.append(f"**Resolution**: {section.get('resolution')}")
        lines.append("")

    lines.append(f"\n> *Disclaimer*: {playbook.disclaimer}\n")
    return "\n".join(lines)

def format_developer_playbook_markdown(playbook: DeveloperPlaybook) -> str:
    lines = [f"# {playbook.title}\n"]

    lines.append("## Coding Standards")
    for std in playbook.coding_standards:
        lines.append(f"- {std}")
    lines.append("")

    lines.append("## Test Standards")
    for std in playbook.test_standards:
        lines.append(f"- {std}")
    lines.append("")

    lines.append("## Release Standards")
    for std in playbook.release_standards:
        lines.append(f"- {std}")
    lines.append("")

    lines.append("## Extension Points")
    for ep in playbook.extension_points:
        lines.append(f"- {ep}")
    lines.append("")

    lines.append("## Developer Flows")
    for section in playbook.sections:
         lines.append(f"### {section.get('topic')}")
         for step in section.get('steps', []):
             lines.append(f"1. {step}")
         lines.append("")

    lines.append(f"\n> *Disclaimer*: {playbook.disclaimer}\n")
    return "\n".join(lines)

def format_roadmap_markdown(items: List[PostReleaseRoadmapItem]) -> str:
    lines = ["# Post-Release Roadmap\n"]
    for item in items:
        lines.append(f"## Phase {item.suggested_phase}: {item.title}")
        lines.append(f"- **Priority**: {item.priority.value}")
        lines.append(f"- **Target Area**: {item.target_area}")
        lines.append(f"- **Description**: {item.description}")
        if item.risks:
            lines.append(f"- **Risks**: {', '.join(item.risks)}")
        lines.append("")
    return "\n".join(lines)

def format_maintenance_markdown(tasks: List[MaintenanceTask]) -> str:
    lines = ["# Maintenance Cadence\n"]
    for task in tasks:
        lines.append(f"## {task.title}")
        lines.append(f"- **Cadence**: {task.cadence.value}")
        lines.append(f"- **Owner**: {task.owner_area}")
        lines.append(f"- **Command**: `{task.command_hint}`")
        lines.append(f"- **Expected Output**: {task.expected_output}")
        lines.append(f"- **Requires Confirm**: {task.requires_confirm}")
        lines.append(f"\n> *Disclaimer*: {task.disclaimer}\n")
    return "\n".join(lines)

def format_release_pack_text(pack: FinalReleasePack) -> str:
    lines = ["# Final Release Pack\n"]
    lines.append(f"- **Pack ID**: {pack.pack_id}")
    lines.append(f"- **Stage**: {pack.stage.value}")
    lines.append(f"- **Release Candidate**: {pack.release_candidate_id}")
    lines.append(f"- **Go/No-Go Decision**: {pack.go_no_go_decision}")

    lines.append("\n## Included Items")
    lines.append(f"- Docs: {len(pack.included_docs)}")
    lines.append(f"- Examples: {len(pack.included_examples)}")
    lines.append(f"- Reports: {len(pack.included_reports)}")
    lines.append(f"- Manifests: {len(pack.included_manifests)}")

    if pack.checksum_manifest:
         lines.append("\n## Checksums")
         for path, checksum in list(pack.checksum_manifest.items())[:5]: # Show first 5
             lines.append(f"- `{path}`: {checksum[:8]}...")
         if len(pack.checksum_manifest) > 5:
             lines.append(f"- ... and {len(pack.checksum_manifest) - 5} more files")

    lines.append(f"\n> *Disclaimer*: {pack.disclaimer}\n")
    return "\n".join(lines)

def format_handoff_manifest_text(manifest: FinalHandoffManifest) -> str:
    lines = ["# Final Handoff Manifest\n"]
    lines.append(f"- **Project**: {manifest.project_name}")
    lines.append(f"- **Final Status**: {manifest.final_status.value}")

    lines.append("\n## Summary")
    lines.append(manifest.project_summary)

    lines.append("\n## Metrics")
    lines.append(f"- Modules: {len(manifest.module_summaries)}")
    lines.append(f"- Commands: {len(manifest.command_entries)}")
    lines.append(f"- Roadmap Items: {len(manifest.roadmap_items)}")
    lines.append(f"- Maintenance Tasks: {len(manifest.maintenance_tasks)}")

    lines.append("\n## Next Steps")
    for step in manifest.next_steps:
        lines.append(f"- {step}")

    lines.append(f"\n> *Disclaimer*: {manifest.disclaimer}\n")
    return "\n".join(lines)

def format_final_handoff_report_markdown(report: FinalHandoffReport) -> str:
    lines = ["# Final Handoff Report\n"]
    lines.append(f"- **Report ID**: {report.report_id}")
    lines.append(f"- **Date**: {report.generated_at.isoformat()}")

    if report.manifest:
        lines.append(f"\n## Manifest Status: {report.manifest.final_status.value}")
        lines.append(f"Release Pack ID: {report.manifest.release_pack_id}")

    if report.key_findings:
        lines.append("\n## Key Findings")
        for finding in report.key_findings:
             lines.append(f"- {finding}")

    lines.append(f"\n> *Disclaimer*: {report.disclaimer}\n")
    return "\n".join(lines)
