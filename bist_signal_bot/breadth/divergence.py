import uuid
from datetime import datetime
from bist_signal_bot.breadth.models import (
    BreadthDivergence, BreadthDivergenceType, BreadthMetric, BreadthRegimeSnapshot,
    BreadthReport, BreadthScope, BreadthStatus, HighLowBreadthSummary, ParticipationSummary, VolumeBreadthSummary
)
from bist_signal_bot.config.settings import Settings

class BreadthDivergenceDetector:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def detect(self, index_returns: list[float] | None, breadth_history: list[BreadthRegimeSnapshot] | list[BreadthMetric], current_report: BreadthReport | None = None) -> list[BreadthDivergence]:
        divergences = []
        if not index_returns or len(index_returns) < 2 or not current_report:
            # Cannot detect divergence without index returns and current context
            return divergences

        as_of = current_report.generated_at
        scope = current_report.scope
        scope_name = current_report.scope_name

        index_return = index_returns[-1]
        prev_regime = breadth_history[-1] if breadth_history else None

        breadth_change = None
        if isinstance(prev_regime, BreadthRegimeSnapshot) and prev_regime.breadth_score is not None and current_report.regime and current_report.regime.breadth_score is not None:
             breadth_change = current_report.regime.breadth_score - prev_regime.breadth_score

        div1 = self.detect_index_up_breadth_down(index_return, breadth_change)
        if div1:
            div1.as_of = as_of
            div1.scope = scope
            div1.scope_name = scope_name
            divergences.append(div1)

        div2 = self.detect_new_high_non_confirmation(index_return > 0, current_report.high_low, current_report.participation)
        if div2:
             div2.as_of = as_of
             div2.scope = scope
             div2.scope_name = scope_name
             divergences.append(div2)

        div3 = self.detect_volume_divergence(index_return, current_report.volume_breadth)
        if div3:
             div3.as_of = as_of
             div3.scope = scope
             div3.scope_name = scope_name
             divergences.append(div3)

        for d in divergences:
             d.divergence_score = self.divergence_score(d)

        return divergences

    def detect_index_up_breadth_down(self, index_return_pct: float | None, breadth_change_pct: float | None) -> BreadthDivergence | None:
        if index_return_pct is None or breadth_change_pct is None:
            return None

        if index_return_pct > 0.5 and breadth_change_pct < -2.0:
            return BreadthDivergence(
                divergence_id=str(uuid.uuid4()),
                as_of=datetime.now(),
                scope=BreadthScope.UNKNOWN,
                scope_name="UNKNOWN",
                divergence_type=BreadthDivergenceType.INDEX_UP_BREADTH_DOWN,
                index_return_pct=index_return_pct,
                breadth_change_pct=breadth_change_pct,
                status=BreadthStatus.DIVERGENT,
                message="Index is up but overall breadth is declining."
            )
        elif index_return_pct < -0.5 and breadth_change_pct > 2.0:
            return BreadthDivergence(
                divergence_id=str(uuid.uuid4()),
                as_of=datetime.now(),
                scope=BreadthScope.UNKNOWN,
                scope_name="UNKNOWN",
                divergence_type=BreadthDivergenceType.INDEX_DOWN_BREADTH_UP,
                index_return_pct=index_return_pct,
                breadth_change_pct=breadth_change_pct,
                status=BreadthStatus.DIVERGENT,
                message="Index is down but overall breadth is improving."
            )
        return None

    def detect_new_high_non_confirmation(self, index_near_high: bool, high_low: HighLowBreadthSummary | None, participation: ParticipationSummary | None) -> BreadthDivergence | None:
        if not index_near_high or not high_low or not participation:
            return None

        # Example logic: Index is up, but 52w highs are very low or participation is weak
        if high_low.high_low_score is not None and high_low.high_low_score < 30.0 and participation.participation_score is not None and participation.participation_score < 40.0:
            return BreadthDivergence(
                divergence_id=str(uuid.uuid4()),
                as_of=datetime.now(),
                scope=BreadthScope.UNKNOWN,
                scope_name="UNKNOWN",
                divergence_type=BreadthDivergenceType.PRICE_NEW_HIGH_BREADTH_NOT_CONFIRMING,
                status=BreadthStatus.DIVERGENT,
                message="Index making new highs but breadth metrics are not confirming."
            )
        return None

    def detect_volume_divergence(self, index_return_pct: float | None, volume_breadth: VolumeBreadthSummary | None) -> BreadthDivergence | None:
        if index_return_pct is None or not volume_breadth or volume_breadth.volume_breadth_score is None:
            return None

        if index_return_pct > 0.5 and volume_breadth.volume_breadth_score < 40.0:
            return BreadthDivergence(
                divergence_id=str(uuid.uuid4()),
                as_of=datetime.now(),
                scope=BreadthScope.UNKNOWN,
                scope_name="UNKNOWN",
                divergence_type=BreadthDivergenceType.VOLUME_DIVERGENCE,
                index_return_pct=index_return_pct,
                status=BreadthStatus.DIVERGENT,
                message="Index is up but volume is predominantly negative."
            )
        return None

    def divergence_score(self, divergence: BreadthDivergence) -> float | None:
        # Simplistic scoring
        if divergence.divergence_type in [BreadthDivergenceType.INDEX_UP_BREADTH_DOWN, BreadthDivergenceType.INDEX_DOWN_BREADTH_UP]:
            return 80.0
        elif divergence.divergence_type == BreadthDivergenceType.PRICE_NEW_HIGH_BREADTH_NOT_CONFIRMING:
            return 70.0
        elif divergence.divergence_type == BreadthDivergenceType.VOLUME_DIVERGENCE:
            return 60.0
        return 50.0
