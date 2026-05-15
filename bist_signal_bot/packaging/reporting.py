import pandas as pd
from typing import Any

from bist_signal_bot.packaging.models import (
    EnvironmentDoctorReport, DependencyCheckResult, ReleaseManifest, ReleaseBundleResult
)

def environment_doctor_report_to_dict(report: EnvironmentDoctorReport) -> dict[str, Any]:
    return {
        "platform": report.platform.name,
        "python_version": report.python_version,
        "python_executable": report.python_executable,
        "environment_type": report.environment_type.name,
        "project_root": report.project_root,
        "overall_status": report.overall_status.name,
        "warnings": report.warnings,
        "generated_at": report.generated_at.isoformat(),
        "disclaimer": report.disclaimer,
        "checks": [c.summary() for c in report.checks],
        "dependencies": [
            {
                "package_name": d.package_name,
                "status": d.status.name,
                "message": d.message
            } for d in report.dependency_results
        ]
    }

def dependency_results_to_dataframe(results: list[DependencyCheckResult]) -> pd.DataFrame:
    data = []
    for r in results:
        data.append({
            "Package": r.package_name,
            "Required": r.required_version,
            "Installed": r.installed_version,
            "Status": r.status.name,
            "Optional": r.optional,
            "Message": r.message
        })
    return pd.DataFrame(data)

def release_manifest_to_dict(manifest: ReleaseManifest) -> dict[str, Any]:
    return {
        "release_id": manifest.release_id,
        "version": manifest.version,
        "created_at": manifest.created_at.isoformat(),
        "project_name": manifest.project_name,
        "python_requires": manifest.python_requires,
        "included_files": manifest.included_files,
        "excluded_patterns": manifest.excluded_patterns,
        "dependency_files": manifest.dependency_files,
        "cli_entrypoints": manifest.cli_entrypoints,
        "smoke_commands": manifest.smoke_commands,
        "quality_summary": manifest.quality_summary,
        "security_summary": manifest.security_summary,
        "environment_summary": manifest.environment_summary,
        "no_real_order_sent": manifest.no_real_order_sent,
        "disclaimer": manifest.disclaimer
    }

def release_bundle_result_to_dict(result: ReleaseBundleResult) -> dict[str, Any]:
    return {
        "release_id": result.release_id,
        "status": result.status.name,
        "format": result.format.name,
        "issues": result.issues,
        "started_at": result.started_at.isoformat(),
        "finished_at": result.finished_at.isoformat(),
        "elapsed_seconds": result.elapsed_seconds,
        "output_files": {k: str(v) for k, v in result.output_files.items()},
        "checks": [c.summary() for c in result.checks],
        "manifest": release_manifest_to_dict(result.manifest),
        "disclaimer": result.disclaimer
    }

def format_environment_doctor_text(report: EnvironmentDoctorReport) -> str:
    lines = [
        f"--- ENVIRONMENT DOCTOR REPORT ---",
        f"Platform: {report.platform.name}",
        f"Python: {report.python_version} ({report.python_executable})",
        f"Environment: {report.environment_type.name}",
        f"Overall Status: {report.overall_status.name}",
        f"",
        f"Checks:"
    ]

    for c in report.checks:
        lines.append(f"  [{c.status.name}] {c.check_name}: {c.message}")
        for rec in c.recommendations:
            lines.append(f"    -> {rec}")

    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in report.warnings:
            lines.append(f"  - {w}")

    lines.append("")
    lines.append(report.disclaimer)
    return "\n".join(lines)

def format_release_manifest_markdown(manifest: ReleaseManifest) -> str:
    lines = [
        f"# Release Manifest: {manifest.release_id}",
        f"**Version**: {manifest.version} | **Created**: {manifest.created_at.isoformat()}",
        f"**Project**: {manifest.project_name} | **Python**: {manifest.python_requires}",
        f"",
        f"## Smoke Commands",
        f"```bash"
    ]

    for cmd in manifest.smoke_commands:
        lines.append(" ".join(cmd))

    lines.extend([
        f"```",
        f"",
        f"## Summaries",
        f"- Quality: {'Present' if manifest.quality_summary else 'N/A'}",
        f"- Security: {'Present' if manifest.security_summary else 'N/A'}",
        f"- Environment: {'Present' if manifest.environment_summary else 'N/A'}",
        f"",
        f"*{manifest.disclaimer}*"
    ])

    return "\n".join(lines)

def format_release_bundle_text(result: ReleaseBundleResult) -> str:
    lines = [
        f"--- RELEASE BUNDLE RESULT ---",
        f"Release ID: {result.release_id}",
        f"Status: {result.status.name}",
        f"Format: {result.format.name}",
        f"Elapsed: {result.elapsed_seconds:.2f}s",
        f"",
        f"Outputs:"
    ]

    for k, v in result.output_files.items():
        lines.append(f"  {k}: {v}")

    if result.issues:
        lines.append("")
        lines.append("Issues:")
        for issue in result.issues:
            lines.append(f"  - {issue}")

    lines.append("")
    lines.append(result.disclaimer)
    return "\n".join(lines)

def format_release_report_markdown(result: ReleaseBundleResult) -> str:
    lines = [
        f"# BIST Signal Bot Release Report",
        f"",
        f"**Release ID**: {result.release_id}",
        f"**Version**: {result.manifest.version}",
        f"**Status**: {result.status.name}",
        f"**Format**: {result.format.name}",
        f"**Elapsed Time**: {result.elapsed_seconds:.2f} seconds",
        f"",
        f"## Files Generated",
    ]

    for key, path in result.output_files.items():
        lines.append(f"- **{key}**: `{path}`")

    if result.issues:
        lines.append(f"")
        lines.append(f"## Issues encountered")
        for issue in result.issues:
            lines.append(f"- {issue}")

    lines.extend([
        f"",
        f"## Environment Checks"
    ])

    for check in result.checks:
        lines.append(f"- [{check.status.name}] {check.check_name}: {check.message}")

    lines.extend([
        f"",
        f"## Disclaimer",
        f"*{result.disclaimer}*"
    ])

    return "\n".join(lines)
