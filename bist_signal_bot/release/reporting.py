import json
from typing import Any
import pandas as pd

from bist_signal_bot.release.models import (
    ReleaseCheckResult, ReleaseReadinessReport, ReleaseBlocker,
    SafeLaunchRehearsalResult, ReleaseCandidateManifest, ReleaseNotes
)

def release_check_to_dict(check: ReleaseCheckResult) -> dict[str, Any]:
    return check.summary()

def readiness_report_to_dict(report: ReleaseReadinessReport) -> dict[str, Any]:
    return report.safe_public_dict()

def release_blockers_to_dataframe(blockers: list[ReleaseBlocker]) -> pd.DataFrame:
    data = []
    for b in blockers:
        data.append({
            "Blocker ID": b.blocker_id,
            "Category": b.category.value,
            "Severity": b.severity.value,
            "Title": b.title,
            "Blocking": b.blocking
        })
    return pd.DataFrame(data)

def release_checks_to_dataframe(checks: list[ReleaseCheckResult]) -> pd.DataFrame:
    data = []
    for c in checks:
        data.append({
            "Check ID": c.check_id,
            "Name": c.name,
            "Category": c.category.value,
            "Status": c.status.value,
            "Severity": c.severity.value
        })
    return pd.DataFrame(data)

def rehearsal_result_to_dict(result: SafeLaunchRehearsalResult) -> dict[str, Any]:
    return {
        "rehearsal_id": result.rehearsal_id,
        "status": result.status.value,
        "profile": result.profile.value,
        "steps": len(result.steps),
        "disclaimer": result.disclaimer
    }

def candidate_manifest_to_dict(manifest: ReleaseCandidateManifest) -> dict[str, Any]:
    return {
        "candidate_id": manifest.candidate_id,
        "version": manifest.version,
        "stage": manifest.stage.value,
        "no_real_order_sent": manifest.no_real_order_sent,
        "disclaimer": manifest.disclaimer
    }

def release_notes_to_dict(notes: ReleaseNotes) -> dict[str, Any]:
    return {
        "version": notes.version,
        "stage": notes.stage.value,
        "title": notes.title,
        "disclaimer": notes.disclaimer
    }

def format_readiness_text(report: ReleaseReadinessReport) -> str:
    lines = [
        f"Readiness ID: {report.readiness_id}",
        f"Version: {report.config.version} ({report.config.stage.value})",
        f"Status: {report.status.value} (Score: {report.readiness_score:.1f})",
        f"Blockers: {len(report.blockers)}",
        f"Checks: {report.passed_count} Pass, {report.warning_count} Warn, {report.failed_count} Fail, {report.skipped_count} Skip",
        "",
        "Disclaimer: " + report.disclaimer
    ]
    return "\n".join(lines)

def format_readiness_markdown(report: ReleaseReadinessReport) -> str:
    lines = [
        f"# Release Readiness Report (v{report.config.version})",
        "",
        f"**Status**: {report.status.value}",
        f"**Score**: {report.readiness_score:.1f}",
        f"**Blockers**: {len(report.blockers)}",
        "",
        "## Summary",
        f"- Pass: {report.passed_count}",
        f"- Warn: {report.warning_count}",
        f"- Fail: {report.failed_count}",
        f"- Skip: {report.skipped_count}",
        "",
        f"*{report.disclaimer}*"
    ]
    return "\n".join(lines)

def format_rehearsal_text(result: SafeLaunchRehearsalResult) -> str:
    return f"Rehearsal {result.rehearsal_id} [{result.status.value}] Profile: {result.profile.value}\n{result.disclaimer}"

def format_candidate_manifest_text(manifest: ReleaseCandidateManifest) -> str:
    return f"Candidate {manifest.version} ({manifest.stage.value})\nID: {manifest.candidate_id}\n{manifest.disclaimer}"

def format_release_notes_markdown(notes: ReleaseNotes) -> str:
    from bist_signal_bot.release.notes import ReleaseNotesBuilder
    return ReleaseNotesBuilder().render_markdown(notes)
