import re

with open("bist_signal_bot/core/exceptions.py", "r") as f:
    content = f.read()

if "PerformanceError" not in content:
    performance_exceptions = """
class PerformanceError(BistSignalBotError):
    pass
class PerformanceTimerError(PerformanceError):
    pass
class PerformanceProfilerError(PerformanceError):
    pass
class ResourceBudgetError(PerformanceError):
    pass
class LocalCacheError(PerformanceError):
    pass
class PerformanceBenchmarkError(PerformanceError):
    pass
class BottleneckAnalysisError(PerformanceError):
    pass
class PerformanceRegressionError(PerformanceError):
    pass
class PerformanceStorageError(PerformanceError):
    pass
"""
    content += performance_exceptions
    with open("bist_signal_bot/core/exceptions.py", "w") as f:
        f.write(content)

with open("bist_signal_bot/core/audit.py", "r") as f:
    audit_content = f.read()

if "PERFORMANCE_PROFILE_CREATED" not in audit_content:
    performance_audit_events = """
    PERFORMANCE_PROFILE_CREATED = 'PERFORMANCE_PROFILE_CREATED'
    RESOURCE_BUDGET_EVALUATED = 'RESOURCE_BUDGET_EVALUATED'
    CACHE_ENTRY_CREATED = 'CACHE_ENTRY_CREATED'
    CACHE_ENTRY_INVALIDATED = 'CACHE_ENTRY_INVALIDATED'
    PERFORMANCE_BENCHMARK_RUN = 'PERFORMANCE_BENCHMARK_RUN'
    BOTTLENECKS_ANALYZED = 'BOTTLENECKS_ANALYZED'
    PERFORMANCE_REGRESSION_DETECTED = 'PERFORMANCE_REGRESSION_DETECTED'
    PERFORMANCE_REPORT_CREATED = 'PERFORMANCE_REPORT_CREATED'
"""
    # Find enum block and append to it
    audit_content = re.sub(r'(class AuditEventType\(str, Enum\):)', r'\1' + performance_audit_events, audit_content)
    with open("bist_signal_bot/core/audit.py", "w") as f:
        f.write(audit_content)
