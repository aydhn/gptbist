from typing import Any, List, Optional
from bist_signal_bot.review_workflow.models import ReviewPlaybook, ReviewPlaybookType, ReviewCasePriority

class ReviewPlaybookRegistry:
    def __init__(self):
        self._playbooks = self.default_playbooks()
        self._playbook_map = {pb.playbook_id: pb for pb in self._playbooks}
        self._playbook_map.update({pb.playbook_type.name: pb for pb in self._playbooks})

    def default_playbooks(self) -> List[ReviewPlaybook]:
        return [
            ReviewPlaybook(
                playbook_id="pb-high-score-high-risk",
                playbook_type=ReviewPlaybookType.HIGH_SCORE_HIGH_RISK,
                name="High Score High Risk",
                description="Review case where signal has high score but risk or conflict is high.",
                triggers=["HIGH_SCORE", "HIGH_RISK"],
                required_signoff_priority=ReviewCasePriority.HIGH
            ),
            ReviewPlaybook(
                playbook_id="pb-macro-pressure",
                playbook_type=ReviewPlaybookType.MACRO_PRESSURE,
                name="Macro Pressure",
                description="Review macro pressure context conflicts.",
                triggers=["MACRO_PRESSURE"]
            ),
            ReviewPlaybook(
                playbook_id="pb-breadth-divergence",
                playbook_type=ReviewPlaybookType.BREADTH_DIVERGENCE,
                name="Breadth Divergence",
                description="Review market breadth divergence.",
                triggers=["BREADTH_DIVERGENCE"]
            ),
            ReviewPlaybook(
                playbook_id="pb-event-blackout",
                playbook_type=ReviewPlaybookType.EVENT_BLACKOUT,
                name="Event Blackout",
                description="Review event blackout risks.",
                triggers=["EVENT_BLACKOUT"],
                required_signoff_priority=ReviewCasePriority.HIGH
            ),
            ReviewPlaybook(
                playbook_id="pb-disclosure-high-severity",
                playbook_type=ReviewPlaybookType.DISCLOSURE_HIGH_SEVERITY,
                name="Disclosure High Severity",
                description="Review high severity disclosures.",
                triggers=["DISCLOSURE_HIGH_SEVERITY"],
                required_signoff_priority=ReviewCasePriority.CRITICAL
            ),
            ReviewPlaybook(
                playbook_id="pb-valuation-value-trap",
                playbook_type=ReviewPlaybookType.VALUATION_VALUE_TRAP,
                name="Valuation Value Trap",
                description="Review valuation value trap risks.",
                triggers=["VALUATION_VALUE_TRAP"]
            ),
            ReviewPlaybook(
                playbook_id="pb-factor-crowding",
                playbook_type=ReviewPlaybookType.FACTOR_CROWDING,
                name="Factor Crowding",
                description="Review factor crowding risks.",
                triggers=["FACTOR_CROWDING"]
            ),
            ReviewPlaybook(
                playbook_id="pb-liquidity-cost",
                playbook_type=ReviewPlaybookType.LIQUIDITY_COST,
                name="Liquidity Cost",
                description="Review liquidity and cost issues.",
                triggers=["LIQUIDITY_COST"]
            ),
            ReviewPlaybook(
                playbook_id="pb-calibration-low-reliability",
                playbook_type=ReviewPlaybookType.CALIBRATION_LOW_RELIABILITY,
                name="Calibration Low Reliability",
                description="Review calibration low reliability issues.",
                triggers=["CALIBRATION_LOW_RELIABILITY"]
            ),
            ReviewPlaybook(
                playbook_id="pb-validation-overfit",
                playbook_type=ReviewPlaybookType.VALIDATION_OVERFIT,
                name="Validation Overfit",
                description="Review validation overfit risks.",
                triggers=["VALIDATION_OVERFIT"]
            ),
            ReviewPlaybook(
                playbook_id="pb-portfolio-concentration",
                playbook_type=ReviewPlaybookType.PORTFOLIO_CONCENTRATION,
                name="Portfolio Concentration",
                description="Review portfolio concentration limits.",
                triggers=["PORTFOLIO_CONCENTRATION"]
            ),
            ReviewPlaybook(
                playbook_id="pb-missing-data",
                playbook_type=ReviewPlaybookType.MISSING_DATA,
                name="Missing Data",
                description="Review missing data gaps.",
                triggers=["MISSING_DATA"]
            ),
            ReviewPlaybook(
                playbook_id="pb-standard-signal-review",
                playbook_type=ReviewPlaybookType.STANDARD_SIGNAL_REVIEW,
                name="Standard Signal Review",
                description="Standard signal review workflow.",
                triggers=[]
            )
        ]

    def select_playbooks(self, snapshot: Any = None, conflicts: List[Any] = None, gaps: List[Any] = None) -> List[ReviewPlaybook]:
        selected = set()
        triggers = self.playbook_triggers_from_snapshot(snapshot)
        if conflicts:
            for conflict in conflicts:
                if hasattr(conflict, "conflict_type"):
                    triggers.append(str(conflict.conflict_type))
                elif isinstance(conflict, str):
                    triggers.append(conflict)
        if gaps:
            triggers.append("MISSING_DATA")

        for playbook in self._playbooks:
            for trigger in playbook.triggers:
                if trigger in triggers:
                    selected.add(playbook.playbook_id)

        if not selected:
            selected.add("pb-standard-signal-review")

        return [self._playbook_map[pid] for pid in selected]

    def get_playbook(self, playbook_id_or_type: str) -> Optional[ReviewPlaybook]:
        return self._playbook_map.get(playbook_id_or_type)

    def playbook_triggers_from_snapshot(self, snapshot: Any) -> List[str]:
        triggers = []
        if snapshot:
            if getattr(snapshot, "composite_score", 0) > 80 and getattr(snapshot, "risk_score", 0) > 80:
                triggers.append("HIGH_SCORE_HIGH_RISK")

            context_status = getattr(snapshot, "context_status", "")
            if context_status == "MACRO_PRESSURE":
                triggers.append("MACRO_PRESSURE")
            elif context_status == "EVENT_BLACKOUT":
                triggers.append("EVENT_BLACKOUT")
        return triggers

    def validate_playbook(self, playbook: ReviewPlaybook) -> List[str]:
        errors = []
        if not playbook.playbook_id:
            errors.append("playbook_id is required")
        if not playbook.name:
            errors.append("name is required")
        return errors
