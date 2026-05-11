import os
import re

path = "bist_signal_bot/config/settings.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "ENABLE_ML_INFERENCE: bool =" not in content:
        ml_inference_settings = """
    # ML INFERENCE
    ENABLE_ML_INFERENCE: bool = Field(default=True)
    ML_INFERENCE_DEFAULT_MODEL_ID: str = Field(default="")
    ML_INFERENCE_MODE: str = Field(default="SCORE_AND_FILTER")
    ML_SCORE_BLEND_MODE: str = Field(default="WEIGHTED_AVERAGE")
    ML_SCORE_WEIGHT: float = Field(default=0.35)
    ML_STRATEGY_SCORE_WEIGHT: float = Field(default=0.65)
    ML_MIN_PROBABILITY_POSITIVE: float = Field(default=0.55)
    ML_MAX_PROBABILITY_NEGATIVE: float = Field(default=0.60)
    ML_MIN_PREDICTION_SCORE: float = Field(default=50.0)
    ML_REJECT_ON_MISSING_FEATURES: bool = Field(default=True)
    ML_ALLOW_EXTRA_FEATURES: bool = Field(default=True)
    ML_LATEST_ONLY: bool = Field(default=True)

    STRATEGY_USE_ML_FILTER: bool = Field(default=False)
    STRATEGY_ML_MODEL_ID: str = Field(default="")

    SCANNER_USE_ML_FILTER: bool = Field(default=False)
    SCANNER_ML_MODEL_ID: str = Field(default="")
    SCANNER_MIN_ML_SCORE: float = Field(default=50.0)
    SCANNER_MIN_ML_PROBABILITY: float = Field(default=0.55)

    RISK_USE_ML_FILTER: bool = Field(default=False)
    RISK_MIN_ML_SCORE: float = Field(default=50.0)
    RISK_MIN_ML_PROBABILITY_POSITIVE: float = Field(default=0.55)
    RISK_REJECT_IF_ML_MISSING: bool = Field(default=False)

    BACKTEST_USE_ML_FILTER: bool = Field(default=False)
    BACKTEST_ML_MODEL_ID: str = Field(default="")

    PAPER_USE_ML_FILTER: bool = Field(default=False)
    PAPER_ML_MODEL_ID: str = Field(default="")
"""
        content = content.replace("model_config = SettingsConfigDict(env_file=\".env\", env_file_encoding=\"utf-8\", extra=\"ignore\")", ml_inference_settings + "\n    model_config = SettingsConfigDict(env_file=\".env\", env_file_encoding=\"utf-8\", extra=\"ignore\")")

        with open(path, "w") as f:
            f.write(content)

print("Updated config/settings.py")

path = "bist_signal_bot/core/exceptions.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "class MLInferenceError" not in content:
        exc_str = """
class MLInferenceError(BistSignalBotError):
    pass

class MLFeatureAlignmentError(MLInferenceError):
    pass

class MLFilterError(MLInferenceError):
    pass

class MLScoreError(MLInferenceError):
    pass

class MLSignalIntegrationError(MLInferenceError):
    pass

class MLModelMismatchError(MLInferenceError):
    pass
"""
        content = content + exc_str
        with open(path, "w") as f:
            f.write(content)

print("Updated core/exceptions.py")

path = ".env.example"
if os.path.exists(path):
    with open(path, "a") as f:
        f.write("""
# ML INFERENCE
ENABLE_ML_INFERENCE=true
ML_INFERENCE_DEFAULT_MODEL_ID=""
ML_INFERENCE_MODE="SCORE_AND_FILTER"
ML_SCORE_BLEND_MODE="WEIGHTED_AVERAGE"
ML_SCORE_WEIGHT=0.35
ML_STRATEGY_SCORE_WEIGHT=0.65
ML_MIN_PROBABILITY_POSITIVE=0.55
ML_MAX_PROBABILITY_NEGATIVE=0.60
ML_MIN_PREDICTION_SCORE=50.0
ML_REJECT_ON_MISSING_FEATURES=true
ML_ALLOW_EXTRA_FEATURES=true
ML_LATEST_ONLY=true

STRATEGY_USE_ML_FILTER=false
STRATEGY_ML_MODEL_ID=""

SCANNER_USE_ML_FILTER=false
SCANNER_ML_MODEL_ID=""
SCANNER_MIN_ML_SCORE=50.0
SCANNER_MIN_ML_PROBABILITY=0.55

RISK_USE_ML_FILTER=false
RISK_MIN_ML_SCORE=50.0
RISK_MIN_ML_PROBABILITY_POSITIVE=0.55
RISK_REJECT_IF_ML_MISSING=false

BACKTEST_USE_ML_FILTER=false
BACKTEST_ML_MODEL_ID=""

PAPER_USE_ML_FILTER=false
PAPER_ML_MODEL_ID=""
""")
print("Updated .env.example")
