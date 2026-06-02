import os

with open("README.md", "a") as f:
    f.write("""
## Performance Optimization
* Profiling
* Benchmark
* Resource budget
* Local cache
* Bottleneck analysis
* Regression checks
* QA/Ops integration
* CLI performance commands
""")

os.makedirs("bist_signal_bot/docs", exist_ok=True)
with open("bist_signal_bot/docs/81_LOCAL_PERFORMANCE_OPTIMIZATION.md", "w") as f:
    f.write("""
# Local Performance Optimization v1
- Architecture
- Timing measurement
- Resource budget
- Local cache design
- Benchmark scenarios
- Bottleneck analysis
- Regression detection
- Orchestrator integration
- QA/Ops integration
- Safe language rules
- Troubleshooting
""")

os.makedirs("bist_signal_bot/examples", exist_ok=True)
with open("bist_signal_bot/examples/performance_workflow.md", "w") as f:
    f.write("""
# Performance Workflow
- profile module
- benchmark scenario
- cache list/invalidate
- bottlenecks
- regressions
- report
""")
