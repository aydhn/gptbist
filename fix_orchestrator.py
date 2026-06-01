with open("bist_signal_bot/runtime/orchestrator.py", "r") as f:
    content = f.read()

# Remove old/invalid imports from the previous attempt that relied on different models
content = content.replace("from bist_signal_bot.performance.models import BenchmarkType\n", "")
content = content.replace("profiler = create_local_profiler(self.settings)\n", "")
content = content.replace("profiler.start_benchmark(BenchmarkType.RUNTIME)\n", "")
content = content.replace("profiler.end_benchmark()\n", "")

with open("bist_signal_bot/runtime/orchestrator.py", "w") as f:
    f.write(content)
