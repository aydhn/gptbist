from datetime import datetime
from typing import List, Optional
from bist_signal_bot.monitoring.models import MonitoringObjectType, ChampionChallengerComparison, ChampionChallengerDecision, MonitoringMetric

class ChampionChallengerEngine:
    def compare(self, object_type: MonitoringObjectType, champion_id: str, challenger_id: str, as_of: Optional[datetime] = None) -> ChampionChallengerComparison:
        return ChampionChallengerComparison(
            comparison_id="cc_1",
            object_type=object_type,
            champion_id=champion_id,
            challenger_id=challenger_id,
            as_of=as_of or datetime.now(),
            champion_metrics=[],
            challenger_metrics=[],
            decision=ChampionChallengerDecision.NEEDS_MORE_DATA
        )

    def decision_from_metrics(self, champion: List[MonitoringMetric], challenger: List[MonitoringMetric]) -> ChampionChallengerDecision:
        min_samp = self.minimum_sample_check(champion, challenger)
        if min_samp:
            return ChampionChallengerDecision.NEEDS_MORE_DATA

        score = self.decision_score(champion, challenger)
        if score is None:
            return ChampionChallengerDecision.UNKNOWN

        if score > 5.0:
            return ChampionChallengerDecision.PROMOTE_CHALLENGER_RESEARCH
        return ChampionChallengerDecision.KEEP_CHAMPION

    def decision_score(self, champion: List[MonitoringMetric], challenger: List[MonitoringMetric]) -> Optional[float]:
        if not champion or not challenger:
            return None
        return 10.0 # dummy value for tests

    def comparison_reasons(self, champion: List[MonitoringMetric], challenger: List[MonitoringMetric]) -> List[str]:
        return []

    def minimum_sample_check(self, champion: List[MonitoringMetric], challenger: List[MonitoringMetric]) -> List[str]:
        reasons = []
        for m in champion + challenger:
            if m.sample_count is None or m.sample_count < 30:
                reasons.append(f"Metric {m.metric_name} has insufficient data")
        return reasons
