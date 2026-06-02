from typing import Any
from bist_signal_bot.local_ui.models import (
    LocalUICapability, LocalUIWidget, LocalUIPage,
    LocalUILayout, LocalUIShortcut, LocalUIRunResult, LocalUIReport
)

def capability_to_dict(capability: LocalUICapability) -> dict[str, Any]:
    return capability.model_dump(mode='json')

def widget_to_dict(widget: LocalUIWidget) -> dict[str, Any]:
    return widget.model_dump(mode='json')

def page_to_dict(page: LocalUIPage) -> dict[str, Any]:
    return page.model_dump(mode='json')

def layout_to_dict(layout: LocalUILayout) -> dict[str, Any]:
    return layout.model_dump(mode='json')

def shortcut_to_dict(shortcut: LocalUIShortcut) -> dict[str, Any]:
    return shortcut.model_dump(mode='json')

def run_result_to_dict(result: LocalUIRunResult) -> dict[str, Any]:
    return result.model_dump(mode='json')

def local_ui_report_to_dict(report: LocalUIReport) -> dict[str, Any]:
    return report.model_dump(mode='json')

def format_capabilities_text(capabilities: list[LocalUICapability]) -> str:
    lines = ["## Capabilities"]
    for cap in capabilities:
        lines.append(f"- {cap.backend.value}: {cap.status.value} (Available: {cap.available})")
        if cap.warnings:
            lines.append(f"  Warnings: {', '.join(cap.warnings)}")
    return "\n".join(lines)

def format_page_text(page: LocalUIPage) -> str:
    lines = [f"### Page: {page.title} ({page.page_id})", f"Status: {page.status.value}"]
    for w in page.widgets:
        lines.append(f"  - Widget: {w.title} [{w.kind.value}] - Status: {w.status.value}")
    if page.disclaimer:
        lines.append(f"\nDisclaimer: {page.disclaimer}")
    return "\n".join(lines)

def format_layout_text(layout: LocalUILayout) -> str:
    lines = [f"## Layout: {layout.name}", f"Backend: {layout.backend.value}"]
    lines.append(f"Pages ({len(layout.pages)}):")
    for p in layout.pages:
        lines.append(f"- {p.title} ({p.status.value})")
    if layout.disclaimer:
        lines.append(f"\nDisclaimer: {layout.disclaimer}")
    return "\n".join(lines)

def format_shortcuts_text(shortcuts: list[LocalUIShortcut]) -> str:
    lines = ["## Shortcuts"]
    for s in shortcuts:
        dry_str = "(DRY RUN)" if s.dry_run else "(WRITE)"
        lines.append(f"- {s.label} {dry_str}: `{s.command}`")
    return "\n".join(lines)

def format_run_result_text(result: LocalUIRunResult) -> str:
    lines = [
        "## Run Result",
        f"Run ID: {result.run_id}",
        f"Backend: {result.backend.value}",
        f"Status: {result.status.value}",
        f"Started: {result.started_at}",
        f"Rendered Pages: {len(result.rendered_pages)}"
    ]
    if result.errors:
        lines.append(f"Errors: {', '.join(result.errors)}")
    if result.disclaimer:
        lines.append(f"\nDisclaimer: {result.disclaimer}")
    return "\n".join(lines)

def format_local_ui_report_markdown(report: LocalUIReport) -> str:
    parts = [
        f"# Local UI Report - {report.generated_at.isoformat()}",
        f"Report ID: {report.report_id}",
        "\n" + format_capabilities_text(report.capabilities)
    ]
    if report.layout:
        parts.append("\n" + format_layout_text(report.layout))
    if report.shortcuts:
        parts.append("\n" + format_shortcuts_text(report.shortcuts))
    if report.latest_run:
        parts.append("\n" + format_run_result_text(report.latest_run))

    if report.key_findings:
        parts.append("\n## Key Findings")
        for f in report.key_findings:
            parts.append(f"- {f}")

    if report.warnings:
        parts.append("\n## Warnings")
        for w in report.warnings:
            parts.append(f"- {w}")

    parts.append(f"\n---\n*Disclaimer: {report.disclaimer}*")
    return "\n".join(parts)
