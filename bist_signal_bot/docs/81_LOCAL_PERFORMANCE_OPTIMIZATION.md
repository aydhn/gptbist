# LOCAL PERFORMANCE PROFILING, RESOURCE BUDGETING & BENCHMARK HARNESS

This document outlines the architecture for Local Performance Optimization V1.

## Architecture
- Performance Models (`models.py`)
- Timers & Profilers (`timers.py`, `profiler.py`)
- Resource Budget (`resource_budget.py`)
- Local Cache (`cache.py`)
- Benchmark Harness (`benchmark.py`)
- Bottlenecks & Regressions (`bottlenecks.py`, `regression.py`)
- Reporting & Storage (`reporting.py`, `storage.py`)

## Guidelines
- Performance output is NOT investment advice.
- No HTML scraping, paid APIs, broker APIs.
- Cache writes must be confirmed.
- Defaults to dry-run for tests and benchmarks.
