with open("bist_signal_bot/core/exceptions.py", "r") as f:
    content = f.read()

# Already exists, but let's make sure our specific ones exist
if "PerformanceTimerError" not in content:
    performance_exceptions = """
class PerformanceTimerError(PerformanceError):
    pass
class PerformanceProfilerError(PerformanceError):
    pass
class ResourceBudgetError(PerformanceError):
    pass
class LocalCacheError(PerformanceError):
    pass
"""
    content += performance_exceptions
    with open("bist_signal_bot/core/exceptions.py", "w") as f:
        f.write(content)
