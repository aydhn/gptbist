import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.promotion import StrategyPromotionManager
from bist_signal_bot.strategy_registry.registry import StrategyRegistryManager
from bist_signal_bot.strategy_registry.scorecard import StrategyScorecardBuilder
from bist_signal_bot.strategy_registry.models import (
    StrategyDefinition, StrategyFamily, StrategyRegistryStatus, StrategyPromotionRequest, StrategyScorecard, StrategyGateDecision
)
from bist_signal_bot.core.exceptions import StrategyPromotionError

@pytest.fixture
def env(tmp_path):
    settings = Settings(STRATEGY_SCORE_MIN_VALIDATED=70.0)
    registry = StrategyRegistryManager(settings, tmp_path)
    defn = StrategyDefinition(strategy_id="1", strategy_name="test", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE)
    registry.store.append_definition(defn)
    return settings, tmp_path, registry

def test_promotion_requires_confirm(env):
    settings, tmp_path, registry = env
    promoter = StrategyPromotionManager(settings, tmp_path)

    req = StrategyPromotionRequest(strategy_id="1", target_status=StrategyRegistryStatus.VALIDATED_RESEARCH, reason="Test", confirm=False)
    with pytest.raises(StrategyPromotionError, match="explicit confirmation"):
        promoter.promote(req)

def test_promotion_blocks_on_low_score(env):
    settings, tmp_path, registry = env
    promoter = StrategyPromotionManager(settings, tmp_path)

    # Save a low scorecard
    scorecard = StrategyScorecard(
        scorecard_id="sc1", strategy_id="1", strategy_name="test", version="1",
        aggregate_score=50.0, status=StrategyRegistryStatus.CANDIDATE, gate_decision=StrategyGateDecision.ALLOW
    )
    registry.store.append_scorecard(scorecard)

    req = StrategyPromotionRequest(strategy_id="1", target_status=StrategyRegistryStatus.VALIDATED_RESEARCH, reason="Test", confirm=True)
    result = promoter.promote(req)

    assert result.decision == StrategyGateDecision.BLOCK
    assert any("below minimum" in r for r in result.blocked_reasons)
