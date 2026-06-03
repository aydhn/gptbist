import pytest
from pathlib import Path
from bist_signal_bot.explainability.storage import ExplainabilityStore
from bist_signal_bot.explainability.models import LocalExplanation, ExplanationObjectType, ExplanationScope, ExplanationMethod, ExplanationStatus

def test_storage_append_load_local(tmp_path):
    store = ExplainabilityStore(base_dir=tmp_path)
    exp = LocalExplanation(
        explanation_id="test1",
        object_type=ExplanationObjectType.MODEL,
        object_id="m1",
        scope=ExplanationScope.LOCAL_ROW,
        method=ExplanationMethod.FEATURE_ATTRIBUTION,
        status=ExplanationStatus.PASS
    )
    store.append_local_explanation(exp)

    loaded = store.load_local_explanations(object_id="m1")
    assert len(loaded) == 1
    assert loaded[0].explanation_id == "test1"

    # wrong object id
    loaded2 = store.load_local_explanations(object_id="m2")
    assert len(loaded2) == 0
