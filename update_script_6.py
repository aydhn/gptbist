import os
import re

path = "bist_signal_bot/portfolio/risk_engine.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    hybrid_repl = """
        for s in candidates:
            base_score = max(s.score, 0)
            conf = max(s.confidence, 0)

            ml_score = 0.0
            if "ml_adjusted_score" in s.metadata:
                ml_score = s.metadata["ml_adjusted_score"]
            elif "ml_prediction_score" in s.metadata:
                ml_score = s.metadata["ml_prediction_score"]

            volatility_factor = 1.0
            if "features" in s.metadata and "volatility_risk_score" in s.metadata["features"]:
                v_score = s.metadata["features"]["volatility_risk_score"]
                if v_score and v_score > 0:
                    volatility_factor = max(0.1, 100.0 / v_score)

            if ml_score > 0:
                hybrid_score = (base_score * 0.4 + conf * 0.2 + ml_score * 0.4) * volatility_factor
            else:
                hybrid_score = (base_score * 0.6 + conf * 0.4) * volatility_factor

            scores[s.symbol] = hybrid_score"""

    content = re.sub(
        r"for s in candidates:\n\s*base_score = max\(s\.score, 0\)\n\s*conf = max\(s\.confidence, 0\)\n\s*volatility_factor = 1\.0\n\s*if \"features\" in s\.metadata and \"volatility_risk_score\" in s\.metadata\[\"features\"\]:\n\s*v_score = s\.metadata\[\"features\"\]\[\"volatility_risk_score\"\]\n\s*if v_score and v_score > 0:\n\s*volatility_factor = max\(0\.1, 100\.0 / v_score\)\n\s*scores\[s\.symbol\] = \(base_score \* 0\.6 \+ conf \* 0\.4\) \* volatility_factor",
        hybrid_repl,
        content
    )
    with open(path, "w") as f:
        f.write(content)

print("Updated portfolio engine")
