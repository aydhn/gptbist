import uuid
from typing import List, Optional
from pathlib import Path
from datetime import datetime, timezone
from bist_signal_bot.maintenance_automation.models import (
    CleanupCandidate,
    RetentionPolicy,
    MaintenanceArtifactKind,
    MaintenanceActionResult,
    MaintenanceActionType,
    MaintenanceStatus
)

class MaintenanceCleanupEngine:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def find_cleanup_candidates(self, policies: Optional[List[RetentionPolicy]] = None) -> List[CleanupCandidate]:
        if not policies:
            return []

        candidates = []
        for policy in policies:
            candidates.extend(self.cleanup_candidates_for_policy(policy))
        return candidates

    def cleanup_candidates_for_policy(self, policy: RetentionPolicy) -> List[CleanupCandidate]:
        # Mock logic to find files
        # It would walk policy.path_pattern, check age against policy.retention_days
        return []

    def safe_to_delete(self, path: Path, artifact_kind: MaintenanceArtifactKind) -> bool:
        # Protect source code, docs, config
        abs_path = path.resolve()

        # Ensure it is inside base_dir (simulating PathGuard)
        try:
            abs_path.relative_to(self.base_dir.resolve())
        except ValueError:
            return False

        path_str = str(abs_path)
        if path.suffix == '.py' or 'config' in path_str or 'docs' in path_str:
            return False

        return True

    def cleanup(self, candidate: CleanupCandidate, dry_run: bool = True, confirm: bool = False) -> MaintenanceActionResult:
        return self.cleanup_many([candidate], dry_run, confirm)

    def cleanup_many(self, candidates: List[CleanupCandidate], dry_run: bool = True, confirm: bool = False) -> MaintenanceActionResult:
        affected_paths = []
        deleted_paths = []
        status = MaintenanceStatus.PASS
        skipped = False
        message = ""

        if not confirm:
            skipped = True
            status = MaintenanceStatus.SKIPPED
            message = "Cleanup skipped because confirm is False."

            # even if skipped, we list affected paths for dry-run
            for c in candidates:
                affected_paths.append(c.path)

            return MaintenanceActionResult(
                result_id=str(uuid.uuid4()),
                action_id="cleanup_many",
                action_type=MaintenanceActionType.CACHE_CLEANUP,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                status=status,
                skipped=skipped,
                dry_run=dry_run,
                affected_paths=affected_paths,
                message=message
            )

        # Execution logic (mocked)
        for c in candidates:
            affected_paths.append(c.path)
            if not dry_run:
                # Actual deletion would happen here if safe_to_delete
                if self.safe_to_delete(Path(c.path), c.artifact_kind):
                    deleted_paths.append(c.path)

        message = f"Cleanup processed {len(candidates)} candidates. Dry-run: {dry_run}"

        return MaintenanceActionResult(
            result_id=str(uuid.uuid4()),
            action_id="cleanup_many",
            action_type=MaintenanceActionType.CACHE_CLEANUP,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            status=status,
            skipped=skipped,
            dry_run=dry_run,
            affected_paths=affected_paths,
            deleted_paths=deleted_paths,
            message=message
        )
