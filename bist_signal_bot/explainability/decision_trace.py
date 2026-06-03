import uuid
from datetime import datetime
from typing import Any
from bist_signal_bot.explainability.models import (
    DecisionTrace,
    DecisionTraceStep,
    ExplanationObjectType,
    ExplanationStatus
)
from bist_signal_bot.security.redaction import redact_secrets

class DecisionTraceBuilder:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def build_trace(self, object_type: ExplanationObjectType, object_id: str, steps: list[dict[str, Any]], symbol: str | None = None, as_of: datetime | None = None) -> DecisionTrace:
        trace_steps = []
        for i, s in enumerate(steps):
            trace_steps.append(self.step_from_mapping(s, i))

        status = self.classify_trace(trace_steps)
        final_output = redact_secrets(steps[-1].get("final_output", {})) if steps else {}

        return DecisionTrace(
            trace_id=str(uuid.uuid4()),
            object_type=object_type,
            object_id=object_id,
            symbol=symbol,
            as_of=as_of,
            steps=trace_steps,
            final_output=final_output,
            status=status
        )

    def step_from_mapping(self, mapping: dict[str, Any], index: int) -> DecisionTraceStep:
        return DecisionTraceStep(
            step_id=str(uuid.uuid4()),
            step_name=mapping.get("step_name", f"step_{index}"),
            condition=mapping.get("condition"),
            input_refs=mapping.get("input_refs", {}),
            output_value=mapping.get("output_value"),
            passed=mapping.get("passed"),
            message=mapping.get("message", ""),
            warnings=mapping.get("warnings", [])
        )

    def trace_from_scanner_result(self, result: Any) -> DecisionTrace:
        return self.build_trace(
            object_type=ExplanationObjectType.SCANNER_RESULT,
            object_id=getattr(result, "id", "unknown"),
            steps=getattr(result, "trace_steps", []),
            symbol=getattr(result, "symbol", None)
        )

    def trace_from_inference_result(self, result: Any) -> DecisionTrace:
        return self.build_trace(
            object_type=ExplanationObjectType.MODEL,
            object_id=getattr(result, "model_id", "unknown"),
            steps=getattr(result, "trace_steps", []),
            symbol=getattr(result, "symbol", None)
        )

    def trace_from_validation_result(self, result: Any) -> DecisionTrace:
        return self.build_trace(
            object_type=ExplanationObjectType.VALIDATION_RESULT,
            object_id=getattr(result, "id", "unknown"),
            steps=getattr(result, "trace_steps", [])
        )

    def classify_trace(self, steps: list[DecisionTraceStep]) -> ExplanationStatus:
        if not steps:
            return ExplanationStatus.WATCH
        if any("missing evidence" in s.message.lower() for s in steps):
            return ExplanationStatus.WATCH
        if any(not s.passed for s in steps if s.passed is not None):
            return ExplanationStatus.FAIL
        return ExplanationStatus.PASS
