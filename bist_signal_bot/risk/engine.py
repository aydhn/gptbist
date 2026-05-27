import logging
from datetime import datetime, timezone
import pandas as pd
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.signals.models import SignalCandidate
from .models import (
    RiskContext, RiskDecision, RiskBatchResult, RiskSide,
    RiskDecisionStatus, RiskFilterResult
)
from .base_risk_engine import BaseRiskEngine
from .position_sizing import PositionSizer
from .stops import StopModel
from .targets import TargetModel
from .filters import RiskFilterEngine
from bist_signal_bot.core.exceptions import RiskEngineError

class RiskEngine(BaseRiskEngine):
    def __init__(self,
                 position_sizer: PositionSizer | None = None,
                 stop_model: StopModel | None = None,
                 target_model: TargetModel | None = None,
                 filter_engine: RiskFilterEngine | None = None,
                 settings: Settings | None = None,
                 logger: logging.Logger | None = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger("bist_signal_bot.risk")
        self.position_sizer = position_sizer or PositionSizer(self.settings)
        self.stop_model = stop_model or StopModel(self.settings)
        self.target_model = target_model or TargetModel(self.settings)
        self.filter_engine = filter_engine or RiskFilterEngine(self.settings)

    @classmethod
    def from_settings(cls, settings: Settings) -> 'RiskEngine':
        return cls(settings=settings)

    def risk_side_from_signal(self, signal: SignalCandidate) -> RiskSide:
        val = signal.direction.value
        if val == "LONG": return RiskSide.LONG
        elif val == "SHORT": return RiskSide.SHORT
        return RiskSide.FLAT

    def build_default_context(self, equity: float | None = None, available_cash: float | None = None) -> RiskContext:
        return RiskContext(
            equity=equity if equity is not None else self.settings.RISK_DEFAULT_EQUITY,
            available_cash=available_cash if available_cash is not None else self.settings.RISK_DEFAULT_AVAILABLE_CASH
        )

    def evaluate_signal(self, signal: SignalCandidate, context: RiskContext, data: pd.DataFrame | None = None) -> RiskDecision:
        side = self.risk_side_from_signal(signal)

        if side == RiskSide.FLAT:
            fr = RiskFilterResult(passed=False, status=RiskDecisionStatus.WATCH_ONLY)
            return RiskDecision(
                signal=signal, status=RiskDecisionStatus.WATCH_ONLY, side=side, approved=False,
                filter_result=fr, final_score=signal.score, final_confidence=signal.confidence
            )

        try:
            stop_price = self.stop_model.calculate_stop(signal, data)
            target_price = self.target_model.calculate_target(signal, stop_price, data)

            stop_method = getattr(self.stop_model.settings, "RISK_STOP_METHOD", "NONE")
            target_method = getattr(self.target_model.settings, "RISK_TARGET_METHOD", "NONE")

            from .models import StopMethod, TargetMethod
            try: sm = StopMethod(stop_method)
            except: sm = StopMethod.NONE
            try: tm = TargetMethod(target_method)
            except: tm = TargetMethod.NONE

            stop_target = self.target_model.build_stop_target_reference(
                signal, stop_price, target_price, sm, tm
            )

            pos_size = self.position_sizer.calculate_position_size(signal, context, stop_target)

            filter_res = self.filter_engine.evaluate(signal, context, stop_target, pos_size, data)

            final_score = max(0.0, min(100.0, signal.score + filter_res.score_adjustment))
            approved = filter_res.passed
            status = filter_res.status

            max_loss = pos_size.risk_amount
            max_loss_pct = pos_size.risk_pct

            disclaimer = "Risk decision research output only. Not investment advice. No order was sent."

            return RiskDecision(
                signal=signal,
                status=status,
                side=side,
                approved=approved,
                position_size=pos_size,
                stop_target=stop_target,
                filter_result=filter_res,
                final_score=final_score,
                final_confidence=signal.confidence,
                max_loss_amount=max_loss,
                max_loss_pct=max_loss_pct,
                estimated_total_cost=pos_size.estimated_cost,
                estimated_cost_bps=(pos_size.estimated_cost / pos_size.final_notional * 10000) if pos_size.final_notional > 0 else None,
                generated_at=datetime.now(timezone.utc),
                disclaimer=disclaimer
            )

        except Exception as e:
            self.logger.error(f"Error evaluating risk for {signal.symbol}: {str(e)}", exc_info=True)
            fr = RiskFilterResult(passed=False, status=RiskDecisionStatus.ERROR, warnings=[str(e)])
            return RiskDecision(
                signal=signal, status=RiskDecisionStatus.ERROR, side=side, approved=False,
                filter_result=fr, final_score=signal.score, final_confidence=signal.confidence
            )

    def evaluate_batch(self, signals: list[SignalCandidate], context: RiskContext, data_by_symbol: dict[str, pd.DataFrame] | None = None) -> RiskBatchResult:
        start_time = datetime.now(timezone.utc)
        decisions = []
        app = 0
        rej = 0
        red = 0
        wat = 0

        data_by_symbol = data_by_symbol or {}

        for sig in signals:
            d = data_by_symbol.get(sig.symbol)
            dec = self.evaluate_signal(sig, context, d)
            decisions.append(dec)
            if dec.status == RiskDecisionStatus.APPROVED: app += 1
            elif dec.status == RiskDecisionStatus.REJECTED: rej += 1
            elif dec.status == RiskDecisionStatus.REDUCED:
                red += 1
                app += 1
            elif dec.status == RiskDecisionStatus.WATCH_ONLY: wat += 1

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

        return RiskBatchResult(
            decisions=decisions,
            requested_count=len(signals),
            approved_count=app,
            rejected_count=rej,
            reduced_count=red,
            watch_only_count=wat,
            elapsed_seconds=elapsed,
            generated_at=datetime.now(timezone.utc)
        )

# Added for Disclosure Integration
# DisclosureImpactAssessment risk engine narrative risk input.
# Legal/regulatory, dilution, liquidity pressure tags produce risk warning.
