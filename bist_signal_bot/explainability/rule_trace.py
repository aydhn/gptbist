import uuid
from datetime import datetime
from typing import Any
from bist_signal_bot.explainability.models import (
    RuleTrace,
    DecisionTraceStep,
    ExplanationStatus
)

class RuleTraceBuilder:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def build_rule_trace(self, strategy_name: str, rule_results: list[dict[str, Any]], symbol: str | None = None, as_of: datetime | None = None) -> RuleTrace:
        steps = []
        passed_rules = 0
        failed_rules = 0
        evidence_refs = []
        warnings = []

        for i, rule in enumerate(rule_results):
            step = self.rule_step(rule, i)
            steps.append(step)
            if step.passed is True:
                passed_rules += 1
            elif step.passed is False:
                failed_rules += 1

            if "missing" in step.message.lower() or not step.input_refs:
                warnings.append(f"Missing feature in rule {step.step_name}")

            evidence_refs.extend(rule.get("evidence_refs", []))

        status = self.status_from_rules(passed_rules, failed_rules)
        if warnings:
            status = ExplanationStatus.WATCH

        return RuleTrace(
            rule_trace_id=str(uuid.uuid4()),
            strategy_name=strategy_name,
            symbol=symbol,
            as_of=as_of,
            rules_evaluated=steps,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            evidence_refs=list(set(evidence_refs)),
            status=status,
            warnings=warnings
        )

    def rule_step(self, rule: dict[str, Any], index: int) -> DecisionTraceStep:
        return DecisionTraceStep(
            step_id=str(uuid.uuid4()),
            step_name=rule.get("rule_name", f"rule_{index}"),
            condition=rule.get("condition"),
            input_refs=rule.get("input_refs", {}),
            output_value=rule.get("output_value"),
            passed=rule.get("passed"),
            message=rule.get("message", "Rule passed." if rule.get("passed") else "Rule failed.")
        )

    def trace_moving_average_strategy(self, feature_row: dict[str, Any], strategy_name: str = "moving_average_trend") -> RuleTrace:
        rules = []
        ma50 = feature_row.get("ma_50")
        ma200 = feature_row.get("ma_200")
        close = feature_row.get("close")

        passed = False
        message = "Missing features for rule"
        if ma50 is not None and ma200 is not None:
            passed = float(ma50) > float(ma200)
            message = "MA50 > MA200" if passed else "MA50 <= MA200"

        rules.append({
            "rule_name": "Trend Alignment",
            "condition": "ma_50 > ma_200",
            "input_refs": {"ma_50": ma50, "ma_200": ma200},
            "passed": passed,
            "message": message
        })

        return self.build_rule_trace(strategy_name, rules)

    def trace_breakout_strategy(self, feature_row: dict[str, Any], strategy_name: str = "breakout_trend") -> RuleTrace:
        rules = []
        close = feature_row.get("close")
        high20 = feature_row.get("high_20d")

        passed = False
        message = "Missing features for rule"
        if close is not None and high20 is not None:
            passed = float(close) > float(high20)
            message = "Close > High20D" if passed else "Close <= High20D"

        rules.append({
            "rule_name": "20D Breakout",
            "condition": "close > high_20d",
            "input_refs": {"close": close, "high_20d": high20},
            "passed": passed,
            "message": message
        })

        return self.build_rule_trace(strategy_name, rules)

    def status_from_rules(self, passed_rules: int, failed_rules: int) -> ExplanationStatus:
        if failed_rules > 0:
            return ExplanationStatus.FAIL
        if passed_rules == 0:
            return ExplanationStatus.WATCH
        return ExplanationStatus.PASS
