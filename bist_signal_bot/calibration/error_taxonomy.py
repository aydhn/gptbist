import uuid
from bist_signal_bot.calibration.models import (
    OutcomeRecord, CalibrationScoreType, ErrorCase, ErrorCaseType, OutcomeLabel
)
from bist_signal_bot.config.settings import Settings

class ErrorTaxonomyBuilder:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def classify_errors(self, records: list[OutcomeRecord], score_type: CalibrationScoreType, high_conf_threshold: float = 75.0, low_conf_threshold: float = 35.0) -> list[ErrorCase]:
        errors = []
        for r in records:
            if r.outcome_label == OutcomeLabel.NOT_EVALUATED:
                continue
            cases = self.classify_record(r, score_type, high_conf_threshold, low_conf_threshold)
            errors.extend(cases)
        return errors

    def classify_record(self, record: OutcomeRecord, score_type: CalibrationScoreType, high_conf_threshold: float, low_conf_threshold: float) -> list[ErrorCase]:
        cases = []
        val = score_type.value.lower()
        if val == 'signal_confidence':
            val = 'confidence_score'
        score = getattr(record, val, None)

        if score is not None:
            if score >= high_conf_threshold and record.outcome_label == OutcomeLabel.FAILURE:
                cases.append(ErrorCase(
                    error_id=str(uuid.uuid4()),
                    outcome_id=record.outcome_id,
                    signal_id=record.signal_id,
                    symbol=record.symbol,
                    strategy_name=record.strategy_name,
                    error_type=ErrorCaseType.HIGH_CONFIDENCE_FAILURE,
                    severity=self.error_severity(record, ErrorCaseType.HIGH_CONFIDENCE_FAILURE),
                    message=f"High confidence ({score}) resulted in failure.",
                    score_at_signal=score,
                    net_return_pct=record.net_return_pct
                ))
            elif score <= low_conf_threshold and record.outcome_label == OutcomeLabel.SUCCESS:
                cases.append(ErrorCase(
                    error_id=str(uuid.uuid4()),
                    outcome_id=record.outcome_id,
                    signal_id=record.signal_id,
                    symbol=record.symbol,
                    strategy_name=record.strategy_name,
                    error_type=ErrorCaseType.LOW_CONFIDENCE_SUCCESS,
                    severity=self.error_severity(record, ErrorCaseType.LOW_CONFIDENCE_SUCCESS),
                    message=f"Low confidence ({score}) resulted in success.",
                    score_at_signal=score,
                    net_return_pct=record.net_return_pct
                ))

        if record.cost_drag_pct is not None and record.cost_drag_pct > 1.0:
            cases.append(ErrorCase(
                error_id=str(uuid.uuid4()),
                outcome_id=record.outcome_id,
                signal_id=record.signal_id,
                symbol=record.symbol,
                strategy_name=record.strategy_name,
                error_type=ErrorCaseType.EXECUTION_COST_DRAG,
                severity=self.error_severity(record, ErrorCaseType.EXECUTION_COST_DRAG),
                message=f"High execution cost drag: {record.cost_drag_pct}%.",
                score_at_signal=score,
                net_return_pct=record.net_return_pct
            ))

        if record.liquidity_status in ["ILLIQUID", "LOW"] and (record.fill_rate_pct is None or record.fill_rate_pct < 100.0):
            cases.append(ErrorCase(
                error_id=str(uuid.uuid4()),
                outcome_id=record.outcome_id,
                signal_id=record.signal_id,
                symbol=record.symbol,
                strategy_name=record.strategy_name,
                error_type=ErrorCaseType.LIQUIDITY_FAILURE,
                severity=self.error_severity(record, ErrorCaseType.LIQUIDITY_FAILURE),
                message=f"Liquidity failure for {record.liquidity_status} instrument.",
                score_at_signal=score,
                net_return_pct=record.net_return_pct
            ))

        return cases

    def error_severity(self, record: OutcomeRecord, error_type: ErrorCaseType) -> str:
        if error_type == ErrorCaseType.HIGH_CONFIDENCE_FAILURE:
            if record.net_return_pct is not None and record.net_return_pct < -5.0:
                return "CRITICAL"
            return "HIGH"
        elif error_type == ErrorCaseType.LOW_CONFIDENCE_SUCCESS:
            return "LOW"
        elif error_type == ErrorCaseType.EXECUTION_COST_DRAG:
            return "MEDIUM"
        elif error_type == ErrorCaseType.LIQUIDITY_FAILURE:
            return "HIGH"
        return "MEDIUM"

    def summarize_errors(self, errors: list[ErrorCase]) -> dict[str, int]:
        summary = {}
        for e in errors:
            summary[e.error_type.value] = summary.get(e.error_type.value, 0) + 1
        return summary
