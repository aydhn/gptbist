import uuid
from datetime import datetime, UTC
from typing import Any

from bist_signal_bot.calibration.models import OutcomeRecord, OutcomeHorizon, OutcomeLabel
from bist_signal_bot.calibration.storage import CalibrationStore
from bist_signal_bot.config.settings import Settings

class OutcomeDatasetBuilder:
    def __init__(self, settings: Settings | None = None, store: CalibrationStore | None = None):
        self.settings = settings or Settings()
        self.store = store

    def build_dataset(self, strategy_name: str | None = None, symbol: str | None = None,
                      horizon: OutcomeHorizon = OutcomeHorizon.FIVE_DAYS, limit: int = 10000) -> list[OutcomeRecord]:
        if not self.store:
            return []

        records = self.store.load_outcomes(strategy_name=strategy_name, symbol=symbol, limit=limit)
        records = [r for r in records if r.horizon == horizon]
        return records

    def record_from_signal_outcome(self, payload: dict[str, Any]) -> OutcomeRecord:
        gross = payload.get("gross_return_pct")
        net = payload.get("net_return_pct")
        label = self.assign_outcome_label(gross, net)

        return OutcomeRecord(
            outcome_id=str(uuid.uuid4()),
            signal_id=payload.get("signal_id"),
            symbol=payload.get("symbol", "UNKNOWN"),
            strategy_name=payload.get("strategy_name"),
            generated_at=payload.get("generated_at", datetime.now(UTC)),
            evaluated_at=payload.get("evaluated_at"),
            horizon=payload.get("horizon", OutcomeHorizon.FIVE_DAYS),
            raw_score=payload.get("raw_score"),
            confidence_score=payload.get("confidence_score"),
            consensus_score=payload.get("consensus_score"),
            ml_score=payload.get("ml_score"),
            strategy_score=payload.get("strategy_score"),
            risk_adjusted_score=payload.get("risk_adjusted_score"),
            review_confidence=payload.get("review_confidence"),
            gross_return_pct=gross,
            net_return_pct=net,
            max_favorable_excursion_pct=payload.get("max_favorable_excursion_pct"),
            max_adverse_excursion_pct=payload.get("max_adverse_excursion_pct"),
            cost_drag_pct=payload.get("cost_drag_pct"),
            slippage_bps=payload.get("slippage_bps"),
            fill_rate_pct=payload.get("fill_rate_pct"),
            outcome_label=label,
            regime_label=payload.get("regime_label"),
            sector=payload.get("sector"),
            liquidity_status=payload.get("liquidity_status"),
            metadata=payload.get("metadata", {})
        )

    def record_from_backtest_trade(self, payload: dict[str, Any]) -> OutcomeRecord:
        gross = payload.get("gross_return_pct")
        net = payload.get("net_return_pct")
        label = self.assign_outcome_label(gross, net)

        return OutcomeRecord(
            outcome_id=str(uuid.uuid4()),
            signal_id=None,
            symbol=payload.get("symbol", "UNKNOWN"),
            strategy_name=payload.get("strategy_name"),
            generated_at=payload.get("entry_time", datetime.now(UTC)),
            evaluated_at=payload.get("exit_time"),
            horizon=OutcomeHorizon.CUSTOM,
            raw_score=payload.get("score"),
            gross_return_pct=gross,
            net_return_pct=net,
            outcome_label=label,
            metadata={"source": "backtest_trade", **payload.get("metadata", {})}
        )

    def assign_outcome_label(self, gross_return_pct: float | None, net_return_pct: float | None,
                             threshold_success_pct: float | None = None, threshold_failure_pct: float | None = None) -> OutcomeLabel:
        use_net = getattr(self.settings, "CALIBRATION_USE_NET_RETURN_FOR_LABEL", True)
        val = net_return_pct if use_net and net_return_pct is not None else gross_return_pct

        if val is None:
            return OutcomeLabel.NOT_EVALUATED

        success_thresh = threshold_success_pct if threshold_success_pct is not None else getattr(self.settings, "CALIBRATION_SUCCESS_RETURN_PCT", 1.0)
        failure_thresh = threshold_failure_pct if threshold_failure_pct is not None else getattr(self.settings, "CALIBRATION_FAILURE_RETURN_PCT", -1.0)

        if val >= success_thresh:
            return OutcomeLabel.SUCCESS
        elif val <= failure_thresh:
            return OutcomeLabel.FAILURE
        elif val > 0:
            return OutcomeLabel.PARTIAL_SUCCESS
        else:
            return OutcomeLabel.NEUTRAL

    def filter_evaluable(self, records: list[OutcomeRecord]) -> list[OutcomeRecord]:
        return [r for r in records if r.outcome_label != OutcomeLabel.NOT_EVALUATED]

    def validate_records(self, records: list[OutcomeRecord]) -> list[str]:
        warnings = []
        min_records = getattr(self.settings, "CALIBRATION_MIN_RECORDS", 50)

        evaluable = self.filter_evaluable(records)

        if len(evaluable) < min_records:
            warnings.append(f"Insufficient evaluable records ({len(evaluable)} < {min_records})")

        return warnings
