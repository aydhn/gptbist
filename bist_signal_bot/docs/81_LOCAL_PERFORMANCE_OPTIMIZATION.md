# Local Performance Optimization

This layer provides deterministic performance profiling, resource budgeting, local caching, and benchmark regression detection. It is explicitly designed to remain offline, safe, and research-only.

## Components
- **Timers**: `PerformanceTimer`
- **Profilers**: `LocalPerformanceProfiler`
- **Budgets**: `ResourceBudgetManager`
- **Cache**: `LocalCacheManager`
- **Benchmarks**: `PerformanceBenchmarkRunner`
- **Bottlenecks**: `BottleneckAnalyzer`
- **Regressions**: `PerformanceRegressionDetector`
- **Storage**: JSON/JSONL local file backend

## Integrations
- CLI output is augmented with performance metadata.
- QA Release gates, ops readiness, and health checks ensure resource consumption is tracked.

*No real orders, cloud LLMs, HTML scraping, or broker APIs are permitted.*
