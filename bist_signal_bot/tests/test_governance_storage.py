from bist_signal_bot.config.settings import Settings
from bist_signal_bot.governance.models import AuditReviewResult, AuditReviewRequest, GovernanceStatus
from bist_signal_bot.governance.storage import GovernanceStore
from bist_signal_bot.governance.policy import GovernancePolicyManager
from datetime import datetime
import uuid

def test_governance_storage_policy(tmp_path):
    store = GovernanceStore(Settings(), base_dir=tmp_path)
    mgr = GovernancePolicyManager(Settings())
    policy = mgr.default_policy()

    store.save_policy(policy)
    loaded = store.load_policy()
    assert loaded is not None
    assert loaded.policy_id == policy.policy_id

def test_governance_storage_review(tmp_path):
    store = GovernanceStore(Settings(), base_dir=tmp_path)
    review = AuditReviewResult(
        review_id=f"rev_{uuid.uuid4().hex[:8]}",
        request=AuditReviewRequest(),
        status=GovernanceStatus.PASS,
        generated_at=datetime.utcnow()
    )

    paths = store.save_review(review)
    assert "json" in paths
    assert "latest" in paths

    loaded = store.load_latest_review()
    assert loaded is not None
    assert loaded.review_id == review.review_id
