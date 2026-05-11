from bist_signal_bot.ml.inference.scoring import MLPredictionScorer
from bist_signal_bot.ml.inference.models import MLPredictionDirection, MLInferenceConfig, MLScoreBlendMode
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection

def test_scorer_prediction_to_score_probability():
    scorer = MLPredictionScorer()
    item = {
        "prediction_type": "CLASS_LABEL",
        "probability_positive": 0.8,
        "probability_negative": 0.2,
        "predicted_value": "1"
    }

    score, d, r = scorer.prediction_to_score(item)
    assert score == 80.0
    assert d == MLPredictionDirection.POSITIVE

def test_scorer_blend_mode_weighted():
    scorer = MLPredictionScorer()
    sig = SignalCandidate(
        symbol="ABC", strategy_name="test", direction=SignalDirection.LONG, score=60, confidence=50
    )

    cfg = MLInferenceConfig(model_id="test_model", blend_mode=MLScoreBlendMode.WEIGHTED_AVERAGE, ml_score_weight=0.5, strategy_score_weight=0.5)
    adj_score, conf, reasons = scorer.blend_signal_score(sig, 80, cfg)

    assert adj_score == 70.0 # (60 * 0.5 + 80 * 0.5)
