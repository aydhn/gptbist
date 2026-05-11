import os
import re

# Update scanner/ranking.py to support ML_SCORE and ML_PROBABILITY sort keys
path = "bist_signal_bot/scanner/ranking.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    ml_score_logic = """
        if sort_key.value == "ML_SCORE":
            if sig and "ml_prediction_score" in sig.metadata:
                return float(sig.metadata["ml_prediction_score"])
            return 0.0

        if sort_key.value == "ML_PROBABILITY":
            if sig and "ml_probability_positive" in sig.metadata:
                val = sig.metadata["ml_probability_positive"]
                return float(val) if val is not None else 0.0
            return 0.0

        if sort_key == ScanSortKey.FINAL_SCORE:"""

    content = content.replace("if sort_key == ScanSortKey.FINAL_SCORE:", ml_score_logic)

    with open(path, "w") as f:
        f.write(content)

# Update scanner/models.py to add ML sort keys
path = "bist_signal_bot/scanner/models.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "ML_SCORE" not in content:
        content = content.replace("LOW_VOLATILITY = \"LOW_VOLATILITY\"", "LOW_VOLATILITY = \"LOW_VOLATILITY\"\n    ML_SCORE = \"ML_SCORE\"\n    ML_PROBABILITY = \"ML_PROBABILITY\"")

        # update ScanRequest
        req_repl = """
    max_symbols: int | None = None
    use_ml_filter: bool = False
    ml_model_id: str | None = None
    ml_inference_mode: str | None = None
    min_ml_probability: float | None = None
    min_ml_score: float | None = None"""
        content = content.replace("max_symbols: int | None = None", req_repl)

        with open(path, "w") as f:
            f.write(content)

print("Updated scanner models and ranking")
