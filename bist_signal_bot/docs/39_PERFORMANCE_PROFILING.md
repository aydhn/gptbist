# Performance Profiling (Phase 67)

BIST Signal Bot includes a fully local, operational performance profiling and benchmarking layer designed to track the bot's runtime latency and memory footprint. It does not use any cloud profilers, broker APIs, or paid services, and it generates no investment advice.

## Features

- **Timer & Spans**: Nested timing spans with monotonic clocks.
- **Resource Sampler**: Lightweight background sampling of CPU and Memory (and GPU if available via NVML/nvidia-smi).
- **Benchmarks**: Controlled, synthetic test runs for isolated modules (e.g., Scanner, Backtesting, ML Inference, Knowledge Index).
- **Baselines & Regressions**: Compare new commits or configs against an operational baseline.
- **Bottlenecks & Recommendations**: Automated findings (e.g., "High memory growth") and mitigation tips.

## Usage

### Resource Snapshot
Quickly check what the bot can see.
`python -m bist_signal_bot perf resources`

### Benchmarking
Run an isolated test to determine max throughput. By default, relies on synthetic data.
`python -m bist_signal_bot perf benchmark scanner --sample-size 50 --iterations 3`
`python -m bist_signal_bot perf benchmark backtest --symbols ASELS --strategy moving_average_trend`

### Profiling Runtime
See how long each stage of the standard pipeline takes.
`python -m bist_signal_bot perf profile runtime --synthetic`

### Baselines and Compare
Save your current system's speed as a baseline.
`python -m bist_signal_bot perf baseline create --benchmark BENCHMARK_ID --confirm`
`python -m bist_signal_bot perf compare --latest`

## Disclaimers

- These profiles do NOT send real market orders.
- This is NOT financial advice.
- GPU profiling is best-effort and will fallback gracefully if `pynvml` or `nvidia-smi` is not installed.
