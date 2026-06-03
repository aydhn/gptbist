from bist_signal_bot.maintenance_automation.models import CleanupCandidate

class MaintenanceStalenessDetector:
    def detect_stale_artifacts(self) -> list[CleanupCandidate]:
        return self.detect_stale_reports() + self.detect_stale_cache()

    def detect_stale_reports(self, max_age_days: int = 30) -> list[CleanupCandidate]:
        return []

    def detect_stale_cache(self, max_age_days: int = 30) -> list[CleanupCandidate]:
        return []

    def detect_failed_recent_jobs(self) -> list[str]:
        return ["job_mock_fail_1"] if False else []

    def detect_missing_required_reports(self) -> list[str]:
        return []

    def staleness_summary(self) -> dict:
        return {
            "stale_reports_count": len(self.detect_stale_reports()),
            "stale_cache_count": len(self.detect_stale_cache()),
            "failed_jobs_count": len(self.detect_failed_recent_jobs())
        }
