import logging
from typing import Any

from bist_signal_bot.performance.models import (
    WorkloadProfileResult, CacheReport, ResourceSnapshot, ResourceLevel, WorkloadType
)

class PerformanceRecommendationEngine:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("bist_signal_bot.performance.recommendations")

    def recommend_from_profile(self, result: WorkloadProfileResult) -> list[str]:
        recommendations = []
        if result.resource_after and result.resource_after.memory_percent:
            if result.resource_after.memory_percent > 85.0:
                recommendations.append("Memory usage is critically high during this workload. Reduce batch sizes or rows.")

        if result.request.workload_type == WorkloadType.SCANNER:
            if result.elapsed_seconds > len(result.request.symbols) * 2.0:
                recommendations.append("Scanner average per symbol is high. Consider using THREADS concurrency mode.")

        if result.request.workload_type == WorkloadType.OPTIMIZATION:
            recommendations.append("Ensure OPTIMIZATION_MAX_COMBINATIONS is kept low to avoid excessive CPU usage.")

        return recommendations

    def recommend_from_cache(self, report: CacheReport) -> list[str]:
        recommendations = []
        if report.safe_delete_size_mb > 500:
            recommendations.append(f"Cache holds {report.safe_delete_size_mb:.1f} MB of safe-to-delete files. Run cleanup.")
        if report.dry_run:
            recommendations.append("Cache scan was dry-run. Re-run with --confirm to execute deletion.")
        if report.policy.name == "KEEP_ALL":
            recommendations.append("Policy is KEEP_ALL. Storage may grow indefinitely.")
        return recommendations

    def recommend_from_resources(self, snapshot: ResourceSnapshot) -> list[str]:
        recommendations = []
        if snapshot.memory_percent is not None and snapshot.memory_percent > 80.0:
            recommendations.append("Memory is above 80%. Avoid starting ML or Optimization workloads.")
        if snapshot.disk_percent is not None and snapshot.disk_percent > 85.0:
            recommendations.append("Disk space is running low. Consider cleaning up old reports or cache.")
        if snapshot.cpu_count is not None and snapshot.cpu_count < 4:
            recommendations.append("System has limited CPU cores. Keep concurrency mode to SERIAL.")
        return recommendations

    def recommend_runtime_settings(self, snapshot: ResourceSnapshot) -> dict[str, Any]:
        settings = {}
        if snapshot.memory_percent is not None and snapshot.memory_percent > 85.0:
            settings["PERFORMANCE_MAX_WORKERS"] = 1
            settings["PERFORMANCE_DEFAULT_BATCH_SIZE"] = 5
        elif snapshot.cpu_count is not None and snapshot.cpu_count >= 8:
            settings["PERFORMANCE_MAX_WORKERS"] = 4
            settings["PERFORMANCE_DEFAULT_BATCH_SIZE"] = 25
        else:
            settings["PERFORMANCE_MAX_WORKERS"] = 2
            settings["PERFORMANCE_DEFAULT_BATCH_SIZE"] = 10

        return settings
