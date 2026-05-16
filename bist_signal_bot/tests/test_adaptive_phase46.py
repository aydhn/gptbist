import pytest
from datetime import datetime, timezone
import json
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.adaptive.models import (
    AdaptivePolicy,
    AdaptiveMode,
    AdaptiveEvidence,
    AdaptiveEvidenceType,
    AdaptiveStrategyCandidate,
    AdaptiveRefreshPlan,
    AdaptiveDecisionStatus,
    AdaptiveRecommendation
)
from bist_signal_bot.adaptive.policy import AdaptivePolicyManager
from bist_signal_bot.adaptive.evidence import AdaptiveEvidenceCollector
from bist_signal_bot.adaptive.scoring import AdaptiveScorer
from bist_signal_bot.adaptive.strategy_selector import AdaptiveStrategySelector
from bist_signal_bot.adaptive.parameter_store import AdaptiveParameterStore
from bist_signal_bot.adaptive.refresh_planner import AdaptiveRefreshPlanner
from bist_signal_bot.adaptive.model_refresh import ModelRefreshPlanner
from bist_signal_bot.adaptive.engine import AdaptiveEngine
from bist_signal_bot.adaptive.storage import AdaptiveStore

def test_adaptive_policy_validation():
    p = AdaptivePolicy()
    assert p.mode == AdaptiveMode.RECOMMEND_ONLY

    with pytest.raises(ValueError):
        AdaptivePolicy(min_oos_positive_split_pct=150.0)

def test_adaptive_evidence_clamp():
    e = AdaptiveEvidence(
        evidence_id="1",
        evidence_type=AdaptiveEvidenceType.BACKTEST,
        score=150.0,
        confidence=-10.0,
        generated_at=datetime.now(timezone.utc)
    )
    assert e.score == 100.0
    assert e.confidence == 0.0

def test_policy_manager(tmp_path):
    mgr = AdaptivePolicyManager()
    p = mgr.build_default_policy()
    assert p.min_evidence_count == 2

    path = tmp_path / "policy.json"
    mgr.save_policy(p, path)
    assert path.exists()

    loaded = mgr.load_policy(path)
    assert loaded.mode == AdaptiveMode.RECOMMEND_ONLY

def test_evidence_collector_empty(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    collector = AdaptiveEvidenceCollector(s)

    ev = collector.collect_from_optimization()
    assert len(ev) == 0

def test_evidence_collector_optimization(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    opt_dir = tmp_path / getattr(s, "OPTIMIZATION_RESULTS_DIR_NAME", "optimization")
    opt_dir.mkdir(parents=True, exist_ok=True)

    with open(opt_dir / "mock_opt.json", "w") as f:
        json.dump({
            "symbol": "ASELS",
            "strategy_name": "mock",
            "best_params": {"a": 1},
            "metrics": {"profit_factor": 2.0}
        }, f)

    collector = AdaptiveEvidenceCollector(s)
    ev = collector.collect_from_optimization()
    assert len(ev) == 1
    assert ev[0].symbol == "ASELS"

def test_adaptive_scorer():
    s = AdaptiveScorer()
    p = AdaptivePolicy()

    ev = AdaptiveEvidence(
        evidence_id="1",
        evidence_type=AdaptiveEvidenceType.BACKTEST,
        score=80.0,
        generated_at=datetime.now(timezone.utc),
        metrics={"max_drawdown_pct": 50.0} # policy defaults to max 35.0
    )

    cand = AdaptiveStrategyCandidate(
        symbol="ASELS",
        strategy_name="mock",
        params={},
        evidence_items=[ev]
    )

    scored = s.score_candidate(cand, p)
    # Min evidence is 2 by default
    assert scored.status == AdaptiveDecisionStatus.INSUFFICIENT_EVIDENCE

    # Change policy
    p.min_evidence_count = 1
    cand2 = AdaptiveStrategyCandidate(
        symbol="ASELS",
        strategy_name="mock",
        params={},
        evidence_items=[ev]
    )
    scored2 = s.score_candidate(cand2, p)
    # Exceeds drawdown
    assert scored2.status == AdaptiveDecisionStatus.REJECTED

def test_strategy_selector():
    scorer = AdaptiveScorer()
    sel = AdaptiveStrategySelector(scorer)

    ev = AdaptiveEvidence(
        evidence_id="1",
        evidence_type=AdaptiveEvidenceType.BACKTEST,
        symbol="ASELS",
        strategy_name="mock",
        score=90.0,
        confidence=80.0,
        generated_at=datetime.now(timezone.utc)
    )

    p = AdaptivePolicy(min_evidence_count=1)
    top = sel.select_top_candidates(sel.build_candidates(["ASELS"], ["mock"], [ev]), 5, p)

    assert len(top) == 1
    assert top[0].status == AdaptiveDecisionStatus.APPROVED_RESEARCH

def test_parameter_store(tmp_path):
    store = AdaptiveParameterStore(tmp_path)

    # Needs confirm
    from bist_signal_bot.adaptive.models import AdaptiveParameterSet
    now = datetime.now(timezone.utc)
    p = AdaptiveParameterSet(
        parameter_set_id="1",
        strategy_name="mock",
        params={},
        source="test",
        score=50.0,
        created_at=now,
        updated_at=now
    )

    with pytest.raises(Exception):
        store.upsert_parameter_set(p, confirm=False)

    store.upsert_parameter_set(p, confirm=True)
    loaded = store.load_active_parameters()
    assert len(loaded) == 1

def test_refresh_planner():
    planner = AdaptiveRefreshPlanner()
    p = AdaptivePolicy(min_evidence_count=2)

    cand = AdaptiveStrategyCandidate(
        symbol="ASELS",
        strategy_name="mock",
        params={},
        status=AdaptiveDecisionStatus.INSUFFICIENT_EVIDENCE
    )

    plan = planner.build_refresh_plan([cand], [], p)
    assert len(plan.items) == 1
    assert plan.items[0].action.value == "RUN_BACKTEST"

def test_model_refresh_planner():
    planner = ModelRefreshPlanner()
    p = AdaptivePolicy()

    # ML Filter active but no model
    ev = AdaptiveEvidence(
        evidence_id="1",
        evidence_type=AdaptiveEvidenceType.BACKTEST,
        strategy_name="ml_filter",
        generated_at=datetime.now(timezone.utc)
    )

    recs = planner.recommend_model_refresh([], [ev], p)
    assert len(recs) == 1
    assert recs[0].should_retrain == True

def test_adaptive_engine(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    engine = AdaptiveEngine(settings=s)

    rec = engine.recommend(["ASELS"], ["mock"])
    assert rec.status in (AdaptiveDecisionStatus.INSUFFICIENT_EVIDENCE, AdaptiveDecisionStatus.APPROVED_RESEARCH, AdaptiveDecisionStatus.SKIPPED)

def test_reporting():
    from bist_signal_bot.adaptive.reporting import format_adaptive_report_markdown

    now = datetime.now(timezone.utc)
    rec = AdaptiveRecommendation(
        recommendation_id="r1",
        mode=AdaptiveMode.RECOMMEND_ONLY,
        status=AdaptiveDecisionStatus.SKIPPED,
        generated_at=now,
        policy=AdaptivePolicy()
    )
    md = format_adaptive_report_markdown(rec)
    assert "Disclaimer" in md
    assert "Not investment advice" in md
