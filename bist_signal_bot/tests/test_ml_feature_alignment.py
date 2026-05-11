import pytest
import pandas as pd
from bist_signal_bot.ml.inference.feature_alignment import MLFeatureAligner
from bist_signal_bot.ml.inference.models import MLFeatureAlignmentStatus
from bist_signal_bot.core.exceptions import MLFeatureAlignmentError

def test_feature_aligner_success():
    aligner = MLFeatureAligner()
    df = pd.DataFrame({
        "feat_1": [1, 2],
        "feat_2": [3, 4],
        "symbol": ["A", "B"]
    })

    res = aligner.align_features(df, ["feat_1", "feat_2"], allow_extra_features=True)
    assert res.status == MLFeatureAlignmentStatus.ALIGNED
    assert list(res.aligned_data.columns) == ["feat_1", "feat_2"]

def test_feature_aligner_missing_reject():
    aligner = MLFeatureAligner()
    df = pd.DataFrame({"feat_1": [1, 2]})

    res = aligner.align_features(df, ["feat_1", "feat_2"], reject_on_missing=True)
    assert res.status == MLFeatureAlignmentStatus.MISSING_FEATURES
    assert "feat_2" in res.missing_features
    assert res.aligned_data is None

def test_feature_aligner_missing_allow():
    aligner = MLFeatureAligner()
    df = pd.DataFrame({"feat_1": [1, 2]})

    res = aligner.align_features(df, ["feat_1", "feat_2"], reject_on_missing=False)
    assert res.status == MLFeatureAlignmentStatus.ALIGNED
    assert "feat_2" in res.aligned_data.columns
    assert pd.isna(res.aligned_data["feat_2"].iloc[0])

def test_feature_aligner_forbidden():
    aligner = MLFeatureAligner()
    df = pd.DataFrame({"feat_1": [1], "label_fwd": [2]})

    with pytest.raises(MLFeatureAlignmentError):
        aligner.align_features(df, ["feat_1", "label_fwd"])
