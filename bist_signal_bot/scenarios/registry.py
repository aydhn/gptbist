from typing import Dict, List, Optional
from bist_signal_bot.scenarios.models import ScenarioConfig, ScenarioType, ScenarioStepConfig, ScenarioStepType, ScenarioStatus, ScenarioRiskLevel

class ScenarioRegistry:
    def __init__(self):
        self._scenarios: Dict[str, ScenarioConfig] = {}
        self._register_defaults()

    def _register_defaults(self):
        self._scenarios["smoke"] = self.build_smoke_scenario()
        self._scenarios["acceptance"] = self.build_acceptance_scenario()
        self._scenarios["e2e-research"] = self.build_e2e_research_scenario()
        self._scenarios["e2e-ml"] = self.build_e2e_ml_scenario()
        self._scenarios["security-failsafe"] = self.build_security_failsafe_scenario()
        self._scenarios["monitoring-recovery"] = self.build_monitoring_recovery_scenario()
        self._scenarios["performance-smoke"] = self.build_performance_smoke_scenario()

    def list_scenarios(self) -> List[ScenarioConfig]:
        return list(self._scenarios.values())

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioConfig]:
        return self._scenarios.get(scenario_id)

    def build_smoke_scenario(self) -> ScenarioConfig:
        return ScenarioConfig(
            scenario_id="smoke",
            name="Smoke Test",
            scenario_type=ScenarioType.SMOKE,
            description="Basic smoke test verifying package, healthcheck, security, monitoring, and quality.",
            symbols=["ASELS"],
            steps=[
                ScenarioStepConfig(
                    step_id="step1", name="Package Doctor", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "package", "doctor", "--json"], timeout_seconds=60,
                    assertions=["status_is:SUCCESS"]
                ),
                ScenarioStepConfig(
                    step_id="step2", name="Healthcheck", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "healthcheck"], timeout_seconds=60,
                    assertions=["status_is:SUCCESS"]
                ),
                ScenarioStepConfig(
                    step_id="step3", name="Security Audit", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "security", "audit", "--json"], timeout_seconds=60,
                    assertions=["status_is:SUCCESS"]
                ),
                ScenarioStepConfig(
                    step_id="step4", name="Monitor Status", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "monitor", "status", "--json"], timeout_seconds=60,
                    assertions=["status_is:SUCCESS"]
                ),
                ScenarioStepConfig(
                    step_id="step5", name="Quality Smoke", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "quality", "smoke", "--json"], timeout_seconds=120,
                    assertions=["status_is:SUCCESS"]
                )
            ]
        )

    def build_acceptance_scenario(self) -> ScenarioConfig:
        return ScenarioConfig(
            scenario_id="acceptance",
            name="Acceptance Test",
            scenario_type=ScenarioType.ACCEPTANCE,
            description="Core acceptance workflow covering scan, backtest, risk, regime, paper, research, and reports.",
            symbols=["ASELS", "THYAO", "GARAN"],
            steps=[
                ScenarioStepConfig(
                    step_id="scan", name="Scan", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "scan", "symbols", "ASELS", "THYAO", "GARAN", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=120
                ),
                ScenarioStepConfig(
                    step_id="backtest", name="Backtest", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "backtest", "run", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=120
                ),
                ScenarioStepConfig(
                    step_id="risk", name="Risk Evaluate", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "risk", "evaluate", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=60
                ),
                ScenarioStepConfig(
                    step_id="regime", name="Regime Classify", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "regime", "classify", "ASELS", "--source", "mock", "--json"], timeout_seconds=60
                ),
                ScenarioStepConfig(
                    step_id="paper", name="Paper Run-Once", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "paper", "run-once", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=60
                ),
                ScenarioStepConfig(
                    step_id="research", name="Research List", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "research", "list", "--json"], timeout_seconds=60
                ),
                ScenarioStepConfig(
                    step_id="report", name="Report Daily", step_type=ScenarioStepType.COMMAND,
                    command=["python", "-m", "bist_signal_bot", "report", "daily", "--symbols", "ASELS", "THYAO", "GARAN", "--json"], timeout_seconds=60
                )
            ]
        )

    def build_e2e_research_scenario(self) -> ScenarioConfig:
        return ScenarioConfig(
            scenario_id="e2e-research",
            name="E2E Research Flow",
            scenario_type=ScenarioType.E2E_RESEARCH,
            description="End-to-end research flow: scan, backtest, optimize, adaptive, journal, attribution, report.",
            symbols=["ASELS"],
            steps=[
                ScenarioStepConfig(step_id="scan", name="Scan", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "scan", "symbols", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=120),
                ScenarioStepConfig(step_id="backtest", name="Backtest", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "backtest", "run", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=120),
                ScenarioStepConfig(step_id="optimize", name="Optimize", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "optimize", "small", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=300),
                ScenarioStepConfig(step_id="adaptive", name="Adaptive", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "adaptive", "recommend", "--symbols", "ASELS", "--source", "mock", "--json"], timeout_seconds=120),
                ScenarioStepConfig(step_id="journal", name="Research Journal", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "research", "journal", "--json"], timeout_seconds=60),
                ScenarioStepConfig(step_id="attribution", name="Research Attribution", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "research", "attribution", "--json"], timeout_seconds=60),
                ScenarioStepConfig(step_id="report", name="Report Daily", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "report", "daily", "--symbols", "ASELS", "--json"], timeout_seconds=60)
            ]
        )

    def build_e2e_ml_scenario(self) -> ScenarioConfig:
        return ScenarioConfig(
            scenario_id="e2e-ml",
            name="E2E ML Flow",
            scenario_type=ScenarioType.E2E_ML,
            description="End-to-end ML flow: dataset, train, filter, scan, report.",
            symbols=["ASELS"],
            steps=[
                ScenarioStepConfig(step_id="ml-dataset", name="ML Dataset Build", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "ml-dataset", "build", "ASELS", "--source", "mock"], timeout_seconds=120),
                ScenarioStepConfig(step_id="ml-train", name="ML Train", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "ml-train", "train", "ASELS", "--source", "mock", "--json"], timeout_seconds=300),
                ScenarioStepConfig(step_id="ml-filter", name="ML Filter Predict", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "ml-filter", "predict", "ASELS", "--source", "mock", "--json"], timeout_seconds=120),
                ScenarioStepConfig(step_id="scan-ml", name="Scan with ML", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "scan", "symbols", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=120),
                ScenarioStepConfig(step_id="report", name="Report Daily", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "report", "daily", "--symbols", "ASELS", "--json"], timeout_seconds=60)
            ]
        )

    def build_security_failsafe_scenario(self) -> ScenarioConfig:
        return ScenarioConfig(
            scenario_id="security-failsafe",
            name="Security Failsafe Test",
            scenario_type=ScenarioType.SECURITY_FAILSAFE,
            description="Tests the security kill-switch blocking mechanisms.",
            steps=[
                ScenarioStepConfig(step_id="ks-activate", name="Kill-switch Activate", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "security", "kill-switch", "activate", "--scope", "RUNTIME"], timeout_seconds=60),
                ScenarioStepConfig(step_id="dry-run-blocked", name="Runtime Dry-Run Blocked", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "runtime", "dry-run"], timeout_seconds=60, expected_exit_code=1),
                ScenarioStepConfig(step_id="ks-deactivate", name="Kill-switch Deactivate", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "security", "kill-switch", "deactivate", "--confirm"], timeout_seconds=60),
                ScenarioStepConfig(step_id="dry-run-ok", name="Runtime Dry-Run OK", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "runtime", "dry-run"], timeout_seconds=60, expected_exit_code=0)
            ]
        )

    def build_monitoring_recovery_scenario(self) -> ScenarioConfig:
         return ScenarioConfig(
            scenario_id="monitoring-recovery",
            name="Monitoring Recovery",
            scenario_type=ScenarioType.MONITORING_RECOVERY,
            description="Tests monitoring diagnostics, repair, and stale lock clearing.",
            steps=[
                ScenarioStepConfig(step_id="status1", name="Runtime Status", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "runtime", "status"], timeout_seconds=60),
                ScenarioStepConfig(step_id="diagnostics", name="Diagnostics", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "monitor", "diagnostics"], timeout_seconds=60),
                ScenarioStepConfig(step_id="repair", name="Repair", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "monitor", "repair", "--dry-run"], timeout_seconds=60),
                ScenarioStepConfig(step_id="unlock", name="Unlock", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "runtime", "unlock", "--stale-only"], timeout_seconds=60),
                ScenarioStepConfig(step_id="status2", name="Runtime Status Post", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "runtime", "status"], timeout_seconds=60)
            ]
        )

    def build_performance_smoke_scenario(self) -> ScenarioConfig:
        return ScenarioConfig(
            scenario_id="performance-smoke",
            name="Performance Smoke",
            scenario_type=ScenarioType.PERFORMANCE_SMOKE,
            description="Smoke tests for performance tools.",
            steps=[
                ScenarioStepConfig(step_id="resource", name="Resource", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "performance", "resource", "--json"], timeout_seconds=60),
                ScenarioStepConfig(step_id="cache", name="Cache", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "performance", "cache", "--dry-run", "--json"], timeout_seconds=60),
                ScenarioStepConfig(step_id="batch", name="Batch Recommend", step_type=ScenarioStepType.COMMAND, command=["python", "-m", "bist_signal_bot", "performance", "batch-recommend", "--workload", "scanner", "--symbols", "30", "--json"], timeout_seconds=60)
            ]
        )

    def validate_scenario(self, config: ScenarioConfig) -> None:
        pass # The pydantic model validator does most of the job.
