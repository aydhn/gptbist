from bist_signal_bot.qa.models import QAScenario, QAScenarioKind, QAStatus, QAModuleName
import uuid

class QAScenarioFactory:
    def __init__(self, settings=None):
        self.settings = settings

    def default_scenarios(self) -> list[QAScenario]:
        return [
            self.build_scenario(QAScenarioKind.BASELINE),
            self.build_scenario(QAScenarioKind.HIGH_SCORE_HIGH_RISK),
            self.build_scenario(QAScenarioKind.MACRO_STRESS),
            self.build_scenario(QAScenarioKind.EVENT_BLACKOUT),
            self.build_scenario(QAScenarioKind.MISSING_DATA)
        ]

    def scenario_by_name(self, name: str) -> QAScenario | None:
        for s in self.default_scenarios():
            if s.name == name or s.scenario_kind.value == name:
                return s
        return None

    def build_scenario(self, kind: QAScenarioKind) -> QAScenario:
        return QAScenario(
            scenario_id=str(uuid.uuid4()),
            scenario_kind=kind,
            name=f"Scenario: {kind.value}",
            description=f"Synthetic scenario for {kind.value}",
            expected_status=QAStatus.PASS if kind == QAScenarioKind.BASELINE else QAStatus.WATCH,
            expected_warnings=self.expected_warnings_for_kind(kind)
        )

    def expected_warnings_for_kind(self, kind: QAScenarioKind) -> list[str]:
        if kind == QAScenarioKind.MACRO_STRESS: return ["Macro stress detected"]
        if kind == QAScenarioKind.EVENT_BLACKOUT: return ["Event blackout detected"]
        if kind == QAScenarioKind.MISSING_DATA: return ["Missing data"]
        return []
