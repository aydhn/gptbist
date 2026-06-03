import uuid
from typing import List, Dict
from datetime import datetime, timezone
import hashlib
from bist_signal_bot.maintenance_automation.models import (
    MaintenanceRun,
    MaintenanceRunManifest,
    MaintenanceActionResult
)

class MaintenanceManifestBuilder:
    def build_run_manifest(self, run: MaintenanceRun) -> MaintenanceRunManifest:
        action_result_ids = [r.result_id for r in run.results]
        affected_paths = self.affected_paths(run.results)
        deleted_paths = self.deleted_paths(run.results)
        archived_paths = self.archived_paths(run.results)

        checksums = self.checksum_manifest(affected_paths + archived_paths)

        return MaintenanceRunManifest(
            manifest_id=str(uuid.uuid4()),
            run_id=run.run_id,
            plan_id=run.plan.plan_id,
            created_at=datetime.now(timezone.utc),
            action_result_ids=action_result_ids,
            affected_paths=affected_paths,
            deleted_paths=deleted_paths,
            archived_paths=archived_paths,
            checksum_manifest=checksums,
            dry_run=run.plan.dry_run,
            no_real_order_sent=True
        )

    def affected_paths(self, results: List[MaintenanceActionResult]) -> List[str]:
        paths = set()
        for r in results:
            paths.update(r.affected_paths)
        return list(paths)

    def deleted_paths(self, results: List[MaintenanceActionResult]) -> List[str]:
        paths = set()
        for r in results:
            paths.update(r.deleted_paths)
        return list(paths)

    def archived_paths(self, results: List[MaintenanceActionResult]) -> List[str]:
        paths = set()
        for r in results:
            paths.update(r.archived_paths)
        return list(paths)

    def checksum_manifest(self, paths: List[str]) -> Dict[str, str]:
        manifest = {}
        for path_str in paths:
            try:
                # Mock checksumming
                manifest[path_str] = hashlib.sha256(path_str.encode()).hexdigest()
            except Exception:
                pass
        return manifest

    def validate_manifest(self, manifest: MaintenanceRunManifest) -> List[str]:
        errors = []
        if not manifest.no_real_order_sent:
            errors.append("Maintenance run manifest must confirm no real order was sent.")
        if not manifest.disclaimer or "not investment advice" not in manifest.disclaimer.lower():
            errors.append("Disclaimer must clearly state it is not investment advice.")
        return errors
