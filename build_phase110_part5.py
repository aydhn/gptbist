import os

def create_reporting():
    content = """from typing import Any, Dict
from bist_signal_bot.release_policy.models import (
    BranchPolicy, VersionSnapshot, ChangeRequest, CompatibilityCheckResult,
    ChangelogEntry, MigrationNote, DeprecationNotice, ReleaseBranchFreezeManifest,
    FinalClosureManifest, ReleasePolicyGovernanceAssessment, ReleasePolicyReport
)

def branch_policy_to_dict(policy: BranchPolicy) -> Dict[str, Any]:
    return policy.model_dump()

def version_snapshot_to_dict(snapshot: VersionSnapshot) -> Dict[str, Any]:
    return snapshot.model_dump()

def change_request_to_dict(change: ChangeRequest) -> Dict[str, Any]:
    return change.model_dump()

def compatibility_result_to_dict(result: CompatibilityCheckResult) -> Dict[str, Any]:
    return result.model_dump()

def changelog_entry_to_dict(entry: ChangelogEntry) -> Dict[str, Any]:
    return entry.model_dump()

def migration_note_to_dict(note: MigrationNote) -> Dict[str, Any]:
    return note.model_dump()

def deprecation_notice_to_dict(notice: DeprecationNotice) -> Dict[str, Any]:
    return notice.model_dump()

def freeze_manifest_to_dict(manifest: ReleaseBranchFreezeManifest) -> Dict[str, Any]:
    return manifest.model_dump()

def closure_manifest_to_dict(manifest: FinalClosureManifest) -> Dict[str, Any]:
    return manifest.model_dump()

def governance_to_dict(assessment: ReleasePolicyGovernanceAssessment) -> Dict[str, Any]:
    return assessment.model_dump()

def report_to_dict(report: ReleasePolicyReport) -> Dict[str, Any]:
    return report.model_dump()

def format_branch_policy_text(policy: BranchPolicy) -> str:
    return f"Branch Policy ({policy.branch_kind.value}): {policy.policy_id}"

def format_version_snapshot_text(snapshot: VersionSnapshot) -> str:
    return f"Version Snapshot: {snapshot.project_version}"

def format_compatibility_text(result: CompatibilityCheckResult) -> str:
    return f"Compatibility Check: {result.status.value}"

def format_freeze_text(manifest: ReleaseBranchFreezeManifest) -> str:
    return f"Freeze Manifest for {manifest.branch_name}: Frozen={manifest.frozen}"

def format_closure_text(manifest: FinalClosureManifest) -> str:
    return f"Final Closure Manifest: Phase {manifest.phase_range} - Status={manifest.final_status.value}"

def format_release_policy_report_markdown(report: ReleasePolicyReport) -> str:
    lines = ["# Release Policy Report"]
    if report.closures:
        lines.append(f"Closure Status: {report.closures[-1].final_status.value}")
    if report.governance_assessments:
        lines.append(f"Governance Status: {report.governance_assessments[-1].status.value}")
    lines.append(f"\\n> *{report.disclaimer}*\\n")
    return "\\n".join(lines)
"""
    with open("bist_signal_bot/release_policy/reporting.py", "w") as f:
        f.write(content)

def create_storage():
    content = """import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from bist_signal_bot.release_policy.models import (
    BranchPolicy, VersionSnapshot, ChangeRequest, CompatibilityCheckResult,
    ChangelogEntry, MigrationNote, DeprecationNotice, ReleaseBranchFreezeManifest,
    FinalClosureManifest, ReleasePolicyGovernanceAssessment, ReleasePolicyReport
)
from bist_signal_bot.storage.paths import get_release_policy_dir
from bist_signal_bot.release_policy.reporting import report_to_dict

class ReleasePolicyStore:
    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = base_dir or get_release_policy_dir()
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Subdirectories
        (self.base_dir / "branch_policies").mkdir(exist_ok=True)
        (self.base_dir / "versions").mkdir(exist_ok=True)
        (self.base_dir / "changes").mkdir(exist_ok=True)
        (self.base_dir / "compatibility").mkdir(exist_ok=True)
        (self.base_dir / "changelog").mkdir(exist_ok=True)
        (self.base_dir / "migrations").mkdir(exist_ok=True)
        (self.base_dir / "deprecations").mkdir(exist_ok=True)
        (self.base_dir / "freezes").mkdir(exist_ok=True)
        (self.base_dir / "closures").mkdir(exist_ok=True)
        (self.base_dir / "governance").mkdir(exist_ok=True)
        (self.base_dir / "reports").mkdir(exist_ok=True)

    def save_branch_policies(self, policies: List[BranchPolicy]) -> Path:
        path = self.base_dir / "branch_policies" / "branch_policies.json"
        with open(path, "w") as f:
            json.dump([p.model_dump(mode='json') for p in policies], f, indent=2)
        return path

    def load_branch_policies(self) -> List[BranchPolicy]:
        path = self.base_dir / "branch_policies" / "branch_policies.json"
        if not path.exists():
            return []
        with open(path, "r") as f:
            data = json.load(f)
        return [BranchPolicy.model_validate(d) for d in data]

    def _append_jsonl(self, path: Path, model: Any):
        with open(path, "a") as f:
            f.write(json.dumps(model.model_dump(mode='json')) + "\\n")
        return path

    def append_version_snapshot(self, snapshot: VersionSnapshot) -> Path:
        return self._append_jsonl(self.base_dir / "versions" / "version_snapshots.jsonl", snapshot)

    def load_latest_version_snapshot(self) -> Optional[VersionSnapshot]:
        path = self.base_dir / "versions" / "version_snapshots.jsonl"
        if not path.exists(): return None
        with open(path, "r") as f:
            lines = f.readlines()
        if not lines: return None
        return VersionSnapshot.model_validate_json(lines[-1])

    def append_change_request(self, change: ChangeRequest) -> Path:
        return self._append_jsonl(self.base_dir / "changes" / "change_requests.jsonl", change)

    def load_change_requests(self, limit: int = 1000) -> List[ChangeRequest]:
        path = self.base_dir / "changes" / "change_requests.jsonl"
        if not path.exists(): return []
        with open(path, "r") as f:
            lines = f.readlines()
        return [ChangeRequest.model_validate_json(l) for l in lines[-limit:]]

    def append_compatibility_result(self, result: CompatibilityCheckResult) -> Path:
        return self._append_jsonl(self.base_dir / "compatibility" / "compatibility_checks.jsonl", result)

    def load_latest_compatibility_result(self) -> Optional[CompatibilityCheckResult]:
        path = self.base_dir / "compatibility" / "compatibility_checks.jsonl"
        if not path.exists(): return None
        with open(path, "r") as f:
            lines = f.readlines()
        if not lines: return None
        return CompatibilityCheckResult.model_validate_json(lines[-1])

    def append_changelog_entries(self, entries: List[ChangelogEntry]) -> Path:
        path = self.base_dir / "changelog" / "changelog_entries.jsonl"
        for entry in entries:
            self._append_jsonl(path, entry)
        return path

    def append_migration_notes(self, notes: List[MigrationNote]) -> Path:
        path = self.base_dir / "migrations" / "migration_notes.jsonl"
        for note in notes:
            self._append_jsonl(path, note)
        return path

    def append_deprecation_notices(self, notices: List[DeprecationNotice]) -> Path:
        path = self.base_dir / "deprecations" / "deprecation_notices.jsonl"
        for notice in notices:
            self._append_jsonl(path, notice)
        return path

    def append_freeze_manifest(self, manifest: ReleaseBranchFreezeManifest) -> Path:
        return self._append_jsonl(self.base_dir / "freezes" / "release_branch_freezes.jsonl", manifest)

    def load_latest_freeze_manifest(self) -> Optional[ReleaseBranchFreezeManifest]:
        path = self.base_dir / "freezes" / "release_branch_freezes.jsonl"
        if not path.exists(): return None
        with open(path, "r") as f:
            lines = f.readlines()
        if not lines: return None
        return ReleaseBranchFreezeManifest.model_validate_json(lines[-1])

    def append_closure_manifest(self, manifest: FinalClosureManifest) -> Path:
        return self._append_jsonl(self.base_dir / "closures" / "final_closure_manifests.jsonl", manifest)

    def load_latest_closure_manifest(self) -> Optional[FinalClosureManifest]:
        path = self.base_dir / "closures" / "final_closure_manifests.jsonl"
        if not path.exists(): return None
        with open(path, "r") as f:
            lines = f.readlines()
        if not lines: return None
        return FinalClosureManifest.model_validate_json(lines[-1])

    def append_governance_assessment(self, assessment: ReleasePolicyGovernanceAssessment) -> Path:
        return self._append_jsonl(self.base_dir / "governance" / "release_policy_governance.jsonl", assessment)

    def save_report(self, report: ReleasePolicyReport, markdown_text: str) -> Dict[str, Path]:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        report_dir = self.base_dir / "reports" / date_str
        report_dir.mkdir(exist_ok=True)

        md_path = report_dir / "release_policy_report.md"
        with open(md_path, "w") as f:
            f.write(markdown_text)

        json_path = report_dir / "release_policy_report.json"
        with open(json_path, "w") as f:
            json.dump(report_to_dict(report), f, indent=2)

        return {"markdown": md_path, "json": json_path}
"""
    with open("bist_signal_bot/release_policy/storage.py", "w") as f:
        f.write(content)

def update_paths():
    content = """
def get_release_policy_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import get_settings
    s = settings or get_settings()
    data_dir = getattr(s, 'DATA_DIR', Path('data'))
    if isinstance(data_dir, str):
        data_dir = Path(data_dir)
    return data_dir / getattr(s, 'RELEASE_POLICY_DIR_NAME', 'release_policy')
"""
    with open("bist_signal_bot/storage/paths.py", "a") as f:
        f.write(content)


if __name__ == "__main__":
    create_reporting()
    create_storage()
    update_paths()
    print("Part 5 complete.")
