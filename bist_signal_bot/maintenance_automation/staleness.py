import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
from bist_signal_bot.maintenance_automation.models import CleanupCandidate, MaintenanceArtifactKind

class MaintenanceStalenessDetector:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def detect_stale_artifacts(self) -> List[CleanupCandidate]:
        candidates = []
        candidates.extend(self.detect_stale_reports())
        candidates.extend(self.detect_stale_cache())
        return candidates

    def detect_stale_reports(self, max_age_days: Optional[int] = None) -> List[CleanupCandidate]:
        # Mock logic
        reports_dir = self.base_dir / "data" / "reports"
        candidates = []
        if reports_dir.exists():
            candidates.append(
                CleanupCandidate(
                    candidate_id=str(uuid.uuid4()),
                    artifact_kind=MaintenanceArtifactKind.REPORT,
                    path=str(reports_dir / "mock_stale_report.md"),
                    reason="Exceeded retention policy",
                    safe_to_delete=True,
                    requires_confirm=True
                )
            )
        return candidates

    def detect_stale_cache(self, max_age_days: Optional[int] = None) -> List[CleanupCandidate]:
        # Mock logic
        cache_dir = self.base_dir / "data" / "cache"
        candidates = []
        if cache_dir.exists():
             candidates.append(
                CleanupCandidate(
                    candidate_id=str(uuid.uuid4()),
                    artifact_kind=MaintenanceArtifactKind.CACHE,
                    path=str(cache_dir / "mock_stale_cache.bin"),
                    reason="Exceeded retention policy",
                    safe_to_delete=True,
                    requires_confirm=True
                )
            )
        return candidates

    def detect_failed_recent_jobs(self) -> List[str]:
        # Mock logic
        return ["job_mock_1"]

    def detect_missing_required_reports(self) -> List[str]:
         # Mock logic
        return ["daily_report_mock"]

    def staleness_summary(self) -> Dict[str, Any]:
        return {
            "stale_report_count": len(self.detect_stale_reports()),
            "stale_cache_count": len(self.detect_stale_cache()),
            "failed_recent_job_count": len(self.detect_failed_recent_jobs()),
            "missing_report_count": len(self.detect_missing_required_reports())
        }
