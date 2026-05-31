import pytest
from datetime import datetime, timezone
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.model_registry.models import *
from bist_signal_bot.model_registry.artifacts import ModelArtifactManager
from bist_signal_bot.model_registry.model_cards import ModelCardBuilder
from bist_signal_bot.model_registry.validation import ModelValidationGovernance
from bist_signal_bot.model_registry.calibration import ModelCalibrationGovernance
from bist_signal_bot.model_registry.promotion import ModelPromotionManager
from bist_signal_bot.model_registry.drift import ModelDriftDetector
from bist_signal_bot.model_registry.lineage import ModelLineageTracker
from bist_signal_bot.model_registry.governance import ModelGovernanceEngine
from bist_signal_bot.model_registry.experiments import ExperimentTracker
from bist_signal_bot.model_registry.registry import LocalModelRegistry

class DummyStore:
    def __init__(self):
        self.artifacts = []
        self.experiments = []
        self.models = []
        self.promotion_requests = []
        self.lineage_edges = []
        self.assessments = []

    def append_artifact(self, a): self.artifacts.append(a)
    def load_artifacts(self, model_id=None, limit=1000): return self.artifacts

    def append_experiment_run(self, r): self.experiments.append(r)
    def load_experiment_runs(self, experiment_name=None, limit=1000): return self.experiments

    def append_model(self, m): self.models.append(m)
    def load_models(self, status=None, limit=1000): return self.models
    def load_model_cards(self, model_id=None, limit=1000): return []
    def load_validation_summaries(self, model_id=None, limit=1000): return []
    def load_calibration_summaries(self, model_id=None, limit=1000): return []

    def get_model(self, m_id): return next((m for m in self.models if m.model_id == m_id), None)

    def append_promotion_request(self, r): self.promotion_requests.append(r)
    def load_promotion_requests(self, model_id=None, limit=1000): return self.promotion_requests

    def append_lineage_edges(self, edges): self.lineage_edges.extend(edges)
    def load_lineage_edges(self): return self.lineage_edges

    def append_governance_assessment(self, a): self.assessments.append(a)
    def load_latest_governance(self, model_id): return self.assessments[-1] if self.assessments else None

def test_experiment_tracker():
    store = DummyStore()
    tracker = ExperimentTracker(store=store)
    run = tracker.start_run("test_exp", "test_model", ModelKind.CLASSIFIER)
    assert run.status == ExperimentStatus.RUNNING

    run2 = tracker.complete_run(run.run_id, {"auc": 0.85})
    assert run2.status == ExperimentStatus.COMPLETED
    assert run2.metrics["auc"] == 0.85

    best = tracker.best_run("test_exp", "auc")
    assert best.run_id == run.run_id



def test_artifact_manager(tmp_path, monkeypatch):
    store = DummyStore()
    mgr = ModelArtifactManager(store=store)
    monkeypatch.setattr(mgr, "_is_safe", lambda x: True)

    model_path = tmp_path / "model.json"
    model_path.write_text('{"params": 1}')

    art = mgr.register_artifact(model_path, model_id="m1", confirm=True)
    assert art.artifact_format == ModelArtifactFormat.JSON
    assert art.checksum is not None


def test_model_card_builder():
    builder = ModelCardBuilder()
    m = ModelRecord(model_id="m1", model_name="m1", version="1.0", model_kind=ModelKind.CLASSIFIER, status=ModelRegistryStatus.STAGING, created_at=datetime.now(timezone.utc))
    card = builder.build_card(m, input_features=["f1", "f2"])

    assert "real order execution" in card.not_intended_use.lower()
    assert len(card.input_features) == 2
    md = builder.render_markdown(card)
    assert "Disclaimer:" in md

def test_validation_governance():
    settings = Settings()
    settings.MODEL_VALIDATION_MIN_SAMPLE = 100
    gov = ModelValidationGovernance(settings)

    issues = gov.check_min_sample(50)
    assert len(issues) == 1

    summary = gov.summarize_validation("m1", sample_count=150, metrics={"auc": 0.8}, feature_quality_score=85.0)
    assert summary.status == ModelGovernanceStatus.PASS

def test_calibration_governance():
    settings = Settings()
    settings.MODEL_CALIBRATION_MIN_RELIABILITY_SCORE = 60.0
    gov = ModelCalibrationGovernance(settings)

    issues = gov.check_reliability(50.0)
    assert len(issues) == 1

    summary = gov.summarize_calibration("m1", reliability_score=75.0, expected_calibration_error=0.05, sample_count=200)
    assert summary.status == ModelGovernanceStatus.PASS

def test_drift_detector():
    settings = Settings()
    det = ModelDriftDetector(settings)

    # Fake baseline and current
    finding = det.detect_performance_decay("m1", 0.90, 0.70, "auc")
    assert finding.status == ModelGovernanceStatus.FAIL
    assert finding.drift_score > 10.0

def test_lineage_tracker():
    store = DummyStore()
    tracker = ModelLineageTracker(store=store)

    edge = tracker.link_feature_set_to_model("fs1", "m1")
    assert edge.relation == "PROVIDES_FEATURES"
    assert len(store.lineage_edges) == 1

    graph = tracker.build_lineage_graph("m1")
    assert len(graph["nodes"]) == 2

def test_promotion_manager():
    store = DummyStore()
    registry = LocalModelRegistry(store=store)
    gov = ModelGovernanceEngine(registry=registry, store=store)
    mgr = ModelPromotionManager(registry=registry, governance_engine=gov, store=store)

    m = ModelRecord(model_id="m1", model_name="m1", version="1.0", model_kind=ModelKind.CLASSIFIER, status=ModelRegistryStatus.STAGING, created_at=datetime.now(timezone.utc))
    store.append_model(m)

    req = mgr.request_promotion("m1", ModelPromotionStage.ACTIVE_RESEARCH, "Testing")
    assert req.approved == False # because artifacts/cards are missing

def test_governance_engine():
    store = DummyStore()
    registry = LocalModelRegistry(store=store)
    gov = ModelGovernanceEngine(registry=registry, store=store)

    m = ModelRecord(model_id="m1", model_name="m1", version="1.0", model_kind=ModelKind.CLASSIFIER, status=ModelRegistryStatus.STAGING, created_at=datetime.now(timezone.utc))
    store.append_model(m)

    assessment = gov.assess_model("m1")
    assert assessment.artifact_status == ModelGovernanceStatus.FAIL # missing
    assert assessment.status == ModelGovernanceStatus.FAIL
