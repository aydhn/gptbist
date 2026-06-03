import uuid
from datetime import datetime, timezone
from bist_signal_bot.maintenance_automation.models import MaintenanceRun, MaintenanceRunManifest, MaintenanceActionResult

class MaintenanceManifestBuilder:
    def build_run_manifest(self, run: MaintenanceRun) -> MaintenanceRunManifest:
        return MaintenanceRunManifest(
            manifest_id=str(uuid.uuid4()),
            run_id=run.run_id,
            plan_id=run.plan.plan_id,
            created_at=datetime.now(timezone.utc),
            action_result_ids=[r.result_id for r in run.results],
            affected_paths=self.affected_paths(run.results),
            deleted_paths=self.deleted_paths(run.results),
            archived_paths=self.archived_paths(run.results),
            checksum_manifest=self.checksum_manifest(self.affected_paths(run.results)),
            no_real_order_sent=True
        )

    def affected_paths(self, results: list[MaintenanceActionResult]) -> list[str]:
        paths = []
        for r in results:
            paths.extend(r.affected_paths)
        return list(set(paths))

    def deleted_paths(self, results: list[MaintenanceActionResult]) -> list[str]:
        paths = []
        for r in results:
            paths.extend(r.deleted_paths)
        return list(set(paths))

    def archived_paths(self, results: list[MaintenanceActionResult]) -> list[str]:
        paths = []
        for r in results:
            paths.extend(r.archived_paths)
        return list(set(paths))

    def checksum_manifest(self, paths: list[str]) -> dict[str, str]:
        return {p: "mock_hash_123" for p in paths}

    def validate_manifest(self, manifest: MaintenanceRunManifest) -> list[str]:
        errors = []
        if not manifest.no_real_order_sent:
            errors.append("Manifest must declare no real orders were sent.")
        return errors
