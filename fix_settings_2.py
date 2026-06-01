import os
with open("bist_signal_bot/config/settings.py", "r") as f:
    lines = f.readlines()

fields = """
    # --- RESEARCH ORCHESTRATOR / CAMPAIGN RUNNER SETTINGS ---
    ENABLE_RESEARCH_ORCHESTRATOR: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_DIR_NAME: str = Field(default="research_orchestrator")
    RESEARCH_ORCHESTRATOR_RESEARCH_ONLY: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_SAVE_RESULTS: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_DEFAULT_MODE: str = Field(default="DRY_RUN")
    RESEARCH_ORCHESTRATOR_DEFAULT_STOP_ON_FAIL: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_ALLOW_LOCAL_EXECUTE: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_REQUIRE_CONFIRM_FOR_LOCAL_EXECUTE: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_TIMEOUT_SECONDS: int = Field(default=300)
    RESEARCH_ORCHESTRATOR_MAX_RETRIES: int = Field(default=0)
    RESEARCH_ORCHESTRATOR_ENABLE_DAG: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_BLOCK_ON_DAG_CYCLE: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_SKIP_DOWNSTREAM_ON_REQUIRED_FAIL: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_GUARDRAILS_ENABLED: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_BLOCK_UNSAFE_COMMANDS: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_BLOCK_BROKER_COMMANDS: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_BLOCK_EXTERNAL_CALLS: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_REQUIRE_SAFE_LANGUAGE: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_LOAD_DEFAULT_CAMPAIGNS: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_DEFAULT_CAMPAIGN: str = Field(default="QUICK_RESEARCH_SCAN")
    RESEARCH_ORCHESTRATOR_DEFAULT_PROFILE: str = Field(default="STANDARD")
    RESEARCH_ORCHESTRATOR_BUILD_MANIFEST: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_INCLUDE_CONFIG_SNAPSHOT: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_INCLUDE_ENV_SUMMARY: bool = Field(default=True)
    RESEARCH_ORCHESTRATOR_INCLUDE_CHECKSUMS: bool = Field(default=True)
    RUNTIME_RESEARCH_ORCHESTRATOR_ENABLED: bool = Field(default=True)
    RUNTIME_RESEARCH_ORCHESTRATOR_WARN_ONLY: bool = Field(default=True)
    QA_INCLUDE_RESEARCH_ORCHESTRATOR: bool = Field(default=True)
    QA_ORCHESTRATOR_FAIL_ON_BLOCKED_GUARDRAIL: bool = Field(default=True)
    QA_ORCHESTRATOR_FAIL_ON_DAG_CYCLE: bool = Field(default=True)
    OPS_INCLUDE_RESEARCH_ORCHESTRATOR: bool = Field(default=True)
    REPORT_INCLUDE_RESEARCH_ORCHESTRATOR: bool = Field(default=True)
    RESEARCH_AUTO_LOG_ORCHESTRATOR: bool = Field(default=False)
"""

new_lines = []
for line in lines:
    new_lines.append(line)
    if line.startswith("class Settings(BaseSettings):"):
        new_lines.append(fields)

with open("bist_signal_bot/config/settings.py", "w") as f:
    f.writelines(new_lines)
