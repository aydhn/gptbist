import pytest
from bist_signal_bot.final_audit.storage import FinalAuditStore
from bist_signal_bot.final_audit.release_candidate import ReleaseCandidateBuilder
from bist_signal_bot.final_audit.go_no_go import GoNoGoEvaluator

def test_final_audit_store_append_load_candidate(tmp_path):
    store = FinalAuditStore(base_dir=tmp_path)
    store.audit_dir = tmp_path
    store.candidate_path = tmp_path / "cand.jsonl"

    cand = ReleaseCandidateBuilder(base_dir=tmp_path).build_candidate()
    store.append_release_candidate(cand)

    loaded = store.load_latest_release_candidate()
    assert loaded is not None
    assert loaded.candidate_id == cand.candidate_id

def test_final_audit_store_append_load_go_no_go(tmp_path):
    store = FinalAuditStore(base_dir=tmp_path)
    store.audit_dir = tmp_path
    store.go_no_go_path = tmp_path / "gng.jsonl"

    cand = ReleaseCandidateBuilder(base_dir=tmp_path).build_candidate()
    gng = GoNoGoEvaluator().evaluate(cand)

    store.append_go_no_go(gng)
    loaded = store.load_latest_go_no_go()
    assert loaded is not None
    assert loaded.decision_id == gng.decision_id
