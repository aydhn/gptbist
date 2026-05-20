import pytest
from datetime import datetime
import pandas as pd
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.ensemble.models import (
    SignalVote, SignalSourceType, SignalVoteDirection, EnsembleWeights,
    EnsembleRequest, EnsembleMode, EnsembleDecision, ConsensusSignal
)
from bist_signal_bot.ensemble.weights import EnsembleWeightManager
from bist_signal_bot.ensemble.scoring import EnsembleScorer
from bist_signal_bot.ensemble.conflicts import ConflictResolver
from bist_signal_bot.ensemble.explainability import EnsembleExplainer
from bist_signal_bot.ensemble.engine import EnsembleEngine
from bist_signal_bot.ensemble.storage import EnsembleStore
from bist_signal_bot.ensemble.collectors import SignalVoteCollector



class MockSettings(Settings):
    ENSEMBLE_DIR_NAME: str = "test_ensemble"
    ENSEMBLE_WEIGHT_STRATEGY: float = 0.25
    ENSEMBLE_WEIGHT_INDICATOR: float = 0.10
    ENSEMBLE_WEIGHT_PATTERN: float = 0.05
    ENSEMBLE_WEIGHT_DIVERGENCE: float = 0.05
    ENSEMBLE_WEIGHT_ML: float = 0.15
    ENSEMBLE_WEIGHT_REGIME: float = 0.10
    ENSEMBLE_WEIGHT_RISK: float = 0.15
    ENSEMBLE_WEIGHT_FUNDAMENTAL: float = 0.05
    ENSEMBLE_WEIGHT_BREADTH: float = 0.05
    ENSEMBLE_WEIGHT_RELATIVE_STRENGTH: float = 0.03
    ENSEMBLE_WEIGHT_SECTOR_ROTATION: float = 0.01
    ENSEMBLE_WEIGHT_ADAPTIVE: float = 0.01
    ENSEMBLE_SAVE_OUTPUTS: bool = True
    ENSEMBLE_DEFAULT_STRATEGIES: str = ""

@pytest.fixture
def mock_settings(tmp_path):
    s = MockSettings(_env_file=None)
    return s

def test_signal_vote_validation():
    v = SignalVote(vote_id="1", source_type=SignalSourceType.STRATEGY, source_name="Test", symbol="asels", direction=SignalVoteDirection.LONG_BIAS, score=150.0)
    assert v.symbol == "ASELS"
    assert v.score == 100.0

    with pytest.raises(ValueError):
        SignalVote(vote_id="2", source_type=SignalSourceType.STRATEGY, source_name="", symbol="THYAO", direction=SignalVoteDirection.LONG_BIAS)

    with pytest.raises(ValueError):
        SignalVote(vote_id="3", source_type=SignalSourceType.STRATEGY, source_name="T", symbol="THYAO", direction=SignalVoteDirection.LONG_BIAS, weight=-1.0)

def test_ensemble_weights_normalize():
    w = EnsembleWeights(strategy_weight=1.0, indicator_weight=1.0, pattern_weight=0, divergence_weight=0,
                        ml_weight=0, regime_weight=0, risk_weight=0, fundamental_weight=0, breadth_weight=0,
                        relative_strength_weight=0, sector_rotation_weight=0, adaptive_weight=0)
    norm = w.normalized()
    assert norm.strategy_weight == 0.5
    assert norm.indicator_weight == 0.5
    assert norm.ml_weight == 0.0

def test_weight_manager_regime(mock_settings):
    wm = EnsembleWeightManager(mock_settings)
    base = wm.default_weights()

    trend = wm.weights_for_regime("TRENDING", base)
    assert trend.strategy_weight > base.normalized().strategy_weight

    stress = wm.weights_for_regime("STRESSED", base)
    assert stress.risk_weight > base.normalized().risk_weight

    with pytest.raises(Exception):
        wm.save_weights(base, confirm=False)

def test_conflict_resolver():
    cr = ConflictResolver()
    v1 = SignalVote(vote_id="1", source_type=SignalSourceType.STRATEGY, source_name="T", symbol="ASELS", direction=SignalVoteDirection.LONG_BIAS)
    v2 = SignalVote(vote_id="2", source_type=SignalSourceType.STRATEGY, source_name="T2", symbol="ASELS", direction=SignalVoteDirection.SHORT_BIAS)

    conflicts = cr.detect_conflicts("ASELS", [v1, v2])
    assert len(conflicts) > 0
    assert conflicts[0].conflict_type == "DIRECTIONAL_CONFLICT"

    v3 = SignalVote(vote_id="3", source_type=SignalSourceType.RISK, source_name="R", symbol="ASELS", direction=SignalVoteDirection.REJECT)
    c2 = cr.detect_conflicts("ASELS", [v1, v3])
    assert any(c.conflict_type == "RISK_CONFLICT" for c in c2)

def test_ensemble_scorer():
    s = Settings(_env_file=None)
    s.model_config["extra"] = "allow"
    sc = EnsembleScorer(s)

    v1 = SignalVote(vote_id="1", source_type=SignalSourceType.STRATEGY, source_name="T", symbol="ASELS", direction=SignalVoteDirection.LONG_BIAS, score=80, confidence=70)
    v2 = SignalVote(vote_id="2", source_type=SignalSourceType.STRATEGY, source_name="T2", symbol="ASELS", direction=SignalVoteDirection.LONG_BIAS, score=90, confidence=80)

    w = EnsembleWeights().normalized()
    w.strategy_weight = 1.0

    sig = sc.score_consensus("ASELS", [v1, v2], w, EnsembleMode.METADATA_ONLY, datetime.now())
    assert sig.decision == EnsembleDecision.APPROVED_RESEARCH
    assert sig.consensus_score == 85.0
    assert sig.agreement_ratio == 1.0

def test_ensemble_engine(mock_settings, tmp_path):
    store = EnsembleStore(mock_settings, base_dir=tmp_path)
    engine = EnsembleEngine(
        collector=SignalVoteCollector(settings=mock_settings),
        scorer=EnsembleScorer(mock_settings),
        conflict_resolver=ConflictResolver(),
        explainer=EnsembleExplainer(),
        weight_manager=EnsembleWeightManager(mock_settings),
        store=store,
        settings=mock_settings
    )

    req = EnsembleRequest(symbols=["ASELS"], timeframe="1d", save_output=True)
    res = engine.run(req)

    assert res.elapsed_seconds >= 0
    assert len(res.consensus_signals) == 1

    paths = res.output_files
    assert "json" in paths
    assert "report_md" in paths

    loaded = store.list_recent_results()
    assert len(loaded) == 1
