import uuid
from typing import List, Optional

from bist_signal_bot.performance.models import (
    BottleneckFinding, BenchmarkRunResult, PerformanceRecommendation,
    PerformanceSeverity, BenchmarkType, PerformanceRegressionResult
)

class PerformanceRecommendationEngine:
    def recommend(self, findings: List[BottleneckFinding], result: Optional[BenchmarkRunResult] = None) -> List[PerformanceRecommendation]:
        recs = []
        for finding in findings:
            if "memory growth" in finding.name.lower():
                recs.append(PerformanceRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    title="Reduce memory footprint in data processing",
                    severity=finding.severity,
                    action="Consider processing data in smaller batches or avoiding deep copies of large Pandas DataFrames.",
                    expected_impact="Lower peak memory usage and fewer OOM risks.",
                    risk="May require code refactoring around data pipelines.",
                    requires_code_change=True
                ))
            if "Slow execution" in finding.name:
                recs.append(PerformanceRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    title="Optimize slow logic loop",
                    severity=finding.severity,
                    action="Review the slow span for heavy I/O or unvectorized operations. Try to vectorize pandas calculations or cache results.",
                    expected_impact="Faster execution times.",
                    risk="Logic bugs if vectorized incorrectly.",
                    requires_code_change=True
                ))
            if "throughput" in finding.name.lower():
                recs.append(PerformanceRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    title="Increase batch sizes or concurrency",
                    severity=finding.severity,
                    action="If CPU/Memory is underutilized, consider increasing batch sizes or parallelizing this workload.",
                    expected_impact="Higher throughput items/second.",
                    risk="Could exhaust memory if batch size is too large.",
                    requires_code_change=False
                ))

        # Benchmark specific safe rules
        if result and result.request.benchmark_type == BenchmarkType.KNOWLEDGE_INDEX:
            if any("slow" in f.name.lower() for f in findings):
                recs.append(PerformanceRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    title="Use incremental knowledge indexing",
                    severity=PerformanceSeverity.LOW,
                    action="Ensure KNOWLEDGE_INCREMENTAL_INDEX=True to avoid full rebuilds.",
                    expected_impact="Significantly faster index updates.",
                    requires_code_change=False
                ))

        if result and result.request.heavy:
            recs.append(PerformanceRecommendation(
                recommendation_id=str(uuid.uuid4()),
                title="Schedule heavy workloads after-hours",
                severity=PerformanceSeverity.INFO,
                action="For heavy benchmarks or jobs, schedule them outside of active trading hours via Scheduler.",
                expected_impact="No impact on live execution latency.",
                requires_code_change=False
            ))

        # Deduplicate
        unique = {}
        for r in recs:
            if r.title not in unique:
                unique[r.title] = r

        return list(unique.values())

    def recommend_for_regression(self, regression: PerformanceRegressionResult) -> List[PerformanceRecommendation]:
        recs = []
        for reg_msg in regression.regressions:
            if "memory_peak_mb" in reg_msg:
                recs.append(PerformanceRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    title="Investigate recent memory leaks",
                    severity=PerformanceSeverity.HIGH,
                    action="Review recent commits for unclosed file handles, large dataframe copies, or caching logic changes.",
                    requires_code_change=True
                ))
            if "elapsed_seconds" in reg_msg:
                recs.append(PerformanceRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    title="Investigate recent latency regression",
                    severity=PerformanceSeverity.HIGH,
                    action="Review recent commits for new network calls, unoptimized loops, or disabled caches.",
                    requires_code_change=True
                ))
        return recs

