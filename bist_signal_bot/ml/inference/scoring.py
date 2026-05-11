from typing import Any, Tuple, List
from bist_signal_bot.ml.inference.models import MLPredictionDirection, MLScoreBlendMode, MLInferenceConfig
from bist_signal_bot.ml.training.models import MLPredictionItem, MLPredictionType
from bist_signal_bot.signals.models import SignalCandidate

class MLPredictionScorer:

    def prediction_to_score(self, prediction_item: MLPredictionItem | dict[str, Any]) -> tuple[float, MLPredictionDirection, list[str]]:
        reasons = []
        score = 50.0
        direction = MLPredictionDirection.NEUTRAL

        is_dict = isinstance(prediction_item, dict)
        pred_type = prediction_item.get("prediction_type") if is_dict else prediction_item.prediction_type
        prob_pos = prediction_item.get("probability_positive") if is_dict else prediction_item.probability_positive
        prob_neg = prediction_item.get("probability_negative") if is_dict else prediction_item.probability_negative
        pred_val = prediction_item.get("predicted_value") if is_dict else prediction_item.predicted_value

        if pred_type in [MLPredictionType.CLASS_LABEL, "CLASS_LABEL"]:
            if prob_pos is not None:
                score = prob_pos * 100.0
                if prob_pos >= 0.55:
                    direction = MLPredictionDirection.POSITIVE
                    reasons.append(f"Positive probability {prob_pos:.2f} >= threshold")
                elif prob_neg is not None and prob_neg >= 0.55:
                    direction = MLPredictionDirection.NEGATIVE
                    reasons.append(f"Negative probability {prob_neg:.2f} is dominant")
                else:
                    reasons.append("Probabilities neutral")
            else:
                # Fallback to hard label
                if str(pred_val) == "1" or str(pred_val) == "1.0":
                    score = 60.0
                    direction = MLPredictionDirection.POSITIVE
                    reasons.append("Hard label positive mapping to score 60")
                elif str(pred_val) == "0" or str(pred_val) == "0.0":
                    score = 40.0
                    direction = MLPredictionDirection.NEGATIVE
                    reasons.append("Hard label negative mapping to score 40")

        elif pred_type in [MLPredictionType.REGRESSION_VALUE, "REGRESSION_VALUE"]:
            try:
                val = float(pred_val)
                score = self.normalize_regression_prediction(val)
                if val > 0:
                    direction = MLPredictionDirection.POSITIVE
                    reasons.append(f"Regression val {val} > 0")
                elif val < 0:
                    direction = MLPredictionDirection.NEGATIVE
                    reasons.append(f"Regression val {val} < 0")
            except (ValueError, TypeError):
                reasons.append("Could not parse regression value")

        score = max(0.0, min(100.0, score))
        return score, direction, reasons

    def blend_signal_score(self, signal: SignalCandidate, ml_score: float, config: MLInferenceConfig) -> tuple[float, float, list[str]]:
        reasons = []
        original_score = signal.score
        adjusted_score = original_score

        if config.blend_mode == MLScoreBlendMode.REPLACE:
            adjusted_score = ml_score
            reasons.append(f"Replaced score {original_score} with {ml_score}")
        elif config.blend_mode == MLScoreBlendMode.WEIGHTED_AVERAGE:
            w_ml = config.ml_score_weight
            w_st = config.strategy_score_weight
            tot = w_ml + w_st
            if tot > 0:
                adjusted_score = (original_score * w_st + ml_score * w_ml) / tot
                reasons.append(f"Weighted average {w_st}:{w_ml} applied")
        elif config.blend_mode == MLScoreBlendMode.ADDITIVE_BONUS:
            if ml_score > 60:
                adjusted_score += 10
                reasons.append("Bonus +10 applied due to high ML score")
            elif ml_score < 40:
                adjusted_score -= 10
                reasons.append("Penalty -10 applied due to low ML score")
        elif config.blend_mode == MLScoreBlendMode.PENALTY_ONLY:
            if ml_score < 50:
                diff = 50 - ml_score
                adjusted_score -= (diff * 0.5)
                reasons.append(f"Penalty applied for low score, lowered by {diff * 0.5}")
        elif config.blend_mode == MLScoreBlendMode.METADATA_ONLY:
            reasons.append("Score not adjusted (metadata only mode)")

        adjusted_score = max(0.0, min(100.0, adjusted_score))

        # Confidence logic
        original_conf = signal.confidence
        adjusted_conf = original_conf
        if ml_score > 80 or ml_score < 20:
            adjusted_conf += 5
            reasons.append("Confidence +5 due to strong ML conviction")
        adjusted_conf = max(0.0, min(100.0, adjusted_conf))

        return adjusted_score, adjusted_conf, reasons

    def probability_confidence(self, probability_positive: float | None, probability_negative: float | None, probability_neutral: float | None = None) -> float | None:
        if probability_positive is None or probability_negative is None:
            return None
        return max(probability_positive, probability_negative) * 100.0

    def normalize_regression_prediction(self, value: float, scale: float = 0.05) -> float:
        # Simple clamping logic
        val_scaled = (value / scale) * 50
        score = 50 + val_scaled
        return max(0.0, min(100.0, score))
