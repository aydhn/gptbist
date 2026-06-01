with open("bist_signal_bot/config/settings.py", "r") as f:
    content = f.read()

# Make sure ENABLE_PERFORMANCE (not just ENABLE_PERFORMANCE_PROFILING) is added.
performance_settings = """
    # --- PERFORMANCE OPTIMIZATION SETTINGS ---
    ENABLE_PERFORMANCE: bool = Field(default=True)
    PERFORMANCE_DIR_NAME: str = Field(default="performance")
    PERFORMANCE_RESEARCH_ONLY: bool = Field(default=True)
    PERFORMANCE_SAVE_RESULTS: bool = Field(default=True)

    PERFORMANCE_PROFILE_COMMANDS: bool = Field(default=True)
    PERFORMANCE_COLLECT_RESOURCE_USAGE: bool = Field(default=True)
    PERFORMANCE_PSUTIL_OPTIONAL: bool = Field(default=True)
    PERFORMANCE_DEFAULT_DRY_RUN: bool = Field(default=True)

    PERFORMANCE_DEFAULT_MAX_RUNTIME_SECONDS: float = Field(default=60.0)
    PERFORMANCE_DEFAULT_MAX_MEMORY_MB: float = Field(default=2048.0)
    PERFORMANCE_DEFAULT_MAX_DISK_MB: float = Field(default=1024.0)
    PERFORMANCE_WARN_RUNTIME_SECONDS: float = Field(default=30.0)
    PERFORMANCE_FAIL_RUNTIME_SECONDS: float = Field(default=120.0)

    PERFORMANCE_CACHE_ENABLED: bool = Field(default=True)
    PERFORMANCE_CACHE_DIR_NAME: str = Field(default="cache")
    PERFORMANCE_CACHE_DEFAULT_TTL_SECONDS: int = Field(default=86400)
    PERFORMANCE_CACHE_REQUIRES_CONFIRM: bool = Field(default=True)
    PERFORMANCE_CACHE_MAX_SIZE_MB: float = Field(default=1024.0)
    PERFORMANCE_CACHE_SECRET_SCAN_ENABLED: bool = Field(default=True)

    PERFORMANCE_BENCHMARK_ENABLED: bool = Field(default=True)
    PERFORMANCE_BENCHMARK_SAVE_RESULTS: bool = Field(default=True)
    PERFORMANCE_BENCHMARK_REGRESSION_THRESHOLD_PCT: float = Field(default=25.0)
    PERFORMANCE_BENCHMARK_BASELINE_REQUIRED: bool = Field(default=False)

    PERFORMANCE_REGRESSION_ENABLED: bool = Field(default=True)
    PERFORMANCE_REGRESSION_WARN_PCT: float = Field(default=20.0)
    PERFORMANCE_REGRESSION_FAIL_PCT: float = Field(default=50.0)

    RUNTIME_PERFORMANCE_ENABLED: bool = Field(default=True)
    RUNTIME_PROFILE_ORCHESTRATOR_TASKS: bool = Field(default=True)

    QA_INCLUDE_PERFORMANCE: bool = Field(default=True)
    QA_PERFORMANCE_FAIL_ON_REGRESSION: bool = Field(default=False)

    OPS_INCLUDE_PERFORMANCE: bool = Field(default=True)
    REPORT_INCLUDE_PERFORMANCE: bool = Field(default=True)
    RESEARCH_AUTO_LOG_PERFORMANCE: bool = Field(default=False)

    @field_validator("PERFORMANCE_DEFAULT_MAX_RUNTIME_SECONDS", "PERFORMANCE_DEFAULT_MAX_MEMORY_MB", "PERFORMANCE_DEFAULT_MAX_DISK_MB", "PERFORMANCE_WARN_RUNTIME_SECONDS", "PERFORMANCE_FAIL_RUNTIME_SECONDS", "PERFORMANCE_CACHE_DEFAULT_TTL_SECONDS", "PERFORMANCE_CACHE_MAX_SIZE_MB")
    @classmethod
    def validate_positive_performance_thresholds(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Performance thresholds and TTLs must be positive")
        return v

    @field_validator("PERFORMANCE_BENCHMARK_REGRESSION_THRESHOLD_PCT", "PERFORMANCE_REGRESSION_WARN_PCT", "PERFORMANCE_REGRESSION_FAIL_PCT")
    @classmethod
    def validate_performance_regression_pcts(cls, v):
        if v is not None and v < 0:
            raise ValueError("Performance regression percentages must be >= 0")
        return v

"""
if "ENABLE_PERFORMANCE: bool" not in content:
    content = content.replace("    ENABLE_RESEARCH_ORCHESTRATOR: bool", performance_settings + "\n    ENABLE_RESEARCH_ORCHESTRATOR: bool")
    with open("bist_signal_bot/config/settings.py", "w") as f:
        f.write(content)
