with open("bist_signal_bot/runtime/orchestrator.py", "r") as f:
    lines = f.readlines()

with open("bist_signal_bot/runtime/orchestrator.py", "w") as f:
    for line in lines:
        if "with profiler.profile_context(" in line:
            continue
        if "perf_ctx.record(" in line:
            continue
        f.write(line)
