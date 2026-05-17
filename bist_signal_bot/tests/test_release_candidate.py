import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.release.candidate import ReleaseCandidateBuilder
from bist_signal_bot.core.exceptions import ReleaseCandidateError

def test_candidate_builder_fails_if_readiness_bad(monkeypatch):
    from bist_signal_bot.release.models import ReleaseReadinessReport, ReleaseReadinessConfig, ReleaseStage, ReleaseProfile, ReleaseStatus

    class MockEvaluator:
        def evaluate(self, cfg=None):
            return ReleaseReadinessReport(
                readiness_id="1",
                config=ReleaseReadinessConfig(stage=ReleaseStage.RELEASE_CANDIDATE, profile=ReleaseProfile.FULL_SAFE_LOCAL, version="1"),
                status=ReleaseStatus.FAILED,
                readiness_score=0.0
            )

    builder = ReleaseCandidateBuilder(settings=Settings(), readiness_evaluator=MockEvaluator())
    with pytest.raises(ReleaseCandidateError, match="Cannot build candidate"):
        builder.build_candidate()

def test_candidate_builder_manifest_created(monkeypatch):
    from bist_signal_bot.release.models import ReleaseReadinessReport, ReleaseReadinessConfig, ReleaseStage, ReleaseProfile, ReleaseStatus

    class MockEvaluator:
        def evaluate(self, cfg=None):
            return ReleaseReadinessReport(
                readiness_id="1",
                config=ReleaseReadinessConfig(stage=ReleaseStage.RELEASE_CANDIDATE, profile=ReleaseProfile.FULL_SAFE_LOCAL, version="1"),
                status=ReleaseStatus.READY,
                readiness_score=100.0
            )

    builder = ReleaseCandidateBuilder(settings=Settings(), readiness_evaluator=MockEvaluator())
    m = builder.build_candidate()
    assert m.no_real_order_sent is True
