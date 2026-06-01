import re

with open(".env.example", "a") as f:
    f.write("\n")
    f.write("# --- PERFORMANCE OPTIMIZATION SETTINGS ---\n")
    f.write("ENABLE_PERFORMANCE=true\n")
    f.write("PERFORMANCE_DEFAULT_MAX_RUNTIME_SECONDS=60.0\n")
    f.write("PERFORMANCE_CACHE_ENABLED=true\n")
    f.write("PERFORMANCE_BENCHMARK_ENABLED=true\n")
    f.write("PERFORMANCE_REGRESSION_ENABLED=true\n")

with open("README.md", "r") as f:
    content = f.read()

if "## Local Performance Profiling & Optimization" not in content:
    perf_section = """
## Local Performance Profiling & Optimization
The `bist_signal_bot/performance` layer provides resource budgeting, bottleneck analysis, performance regression testing and caching. It enables deterministic local performance tracking ensuring that execution remains fast without trading off safety or deterministic behavior. See `docs/81_LOCAL_PERFORMANCE_OPTIMIZATION.md` for details.
"""
    content += perf_section
    with open("README.md", "w") as f:
        f.write(content)
