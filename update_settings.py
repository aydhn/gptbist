import sys

settings_path = "bist_signal_bot/config/settings.py"
with open(settings_path, "r") as f:
    content = f.read()

# Add Model Registry settings
registry_settings = """
    # Model Registry
    ENABLE_MODEL_REGISTRY: bool = True
    MODEL_REGISTRY_DIR_NAME: str = "model_registry"
    MODEL_REGISTRY_RESEARCH_ONLY: bool = True
    MODEL_REGISTRY_SAVE_RESULTS: bool = True

    MODEL_REGISTRY_REQUIRE_MODEL_CARD: bool = True
    MODEL_REGISTRY_REQUIRE_VALIDATION: bool = True
    MODEL_REGISTRY_REQUIRE_CALIBRATION: bool = True
    MODEL_REGISTRY_REQUIRE_ARTIFACT: bool = True
    MODEL_REGISTRY_REQUIRE_FEATURE_SET_VERSION: bool = True

    MODEL_ARTIFACT_LOAD_CHECK_ENABLED: bool = False
    MODEL_ARTIFACT_CHECKSUM_REQUIRED: bool = True
    MODEL_ARTIFACT_ALLOWED_FORMATS: str = "JSON,JOBLIB,PICKLE,SKLEARN,TEXT,DIRECTORY"
    MODEL_ARTIFACT_PICKLE_LOAD_BLOCKED: bool = True

    MODEL_VALIDATION_MIN_SAMPLE: int = 100
    MODEL_VALIDATION_MIN_WALK_FORWARD_FOLDS: int = 3
    MODEL_VALIDATION_OVERFIT_WARN_ENABLED: bool = True
    MODEL_VALIDATION_FEATURE_QUALITY_MIN_SCORE: float = 70.0

    MODEL_CALIBRATION_MIN_SAMPLE: int = 100
    MODEL_CALIBRATION_MIN_RELIABILITY_SCORE: float = 60.0
    MODEL_CALIBRATION_MAX_ECE_WARN: float = 0.15

    MODEL_PROMOTION_REQUIRES_CONFIRM: bool = True
    MODEL_PROMOTION_ACTIVE_RESEARCH_REQUIRES_PASS: bool = True
    MODEL_PROMOTION_BLOCK_ON_LEAKAGE: bool = True
    MODEL_PROMOTION_BLOCK_ON_MISSING_CARD: bool = True
    MODEL_PROMOTION_BLOCK_ON_MISSING_ARTIFACT: bool = True

    MODEL_DRIFT_ENABLED: bool = True
    MODEL_DRIFT_MIN_SAMPLE: int = 30
    MODEL_DRIFT_SCORE_WARN: float = 60.0
    MODEL_PERFORMANCE_DECAY_WARN: float = 0.10
    MODEL_CALIBRATION_DECAY_WARN: float = 0.05

    RUNTIME_MODEL_REGISTRY_ENABLED: bool = True
    RUNTIME_INFERENCE_REQUIRE_REGISTERED_MODEL: bool = True
    RUNTIME_INFERENCE_BLOCK_GOVERNANCE_FAIL: bool = False
    RUNTIME_INFERENCE_WARN_ON_MODEL_DRIFT: bool = True

    QA_INCLUDE_MODEL_REGISTRY: bool = True
    QA_MODEL_REGISTRY_FAIL_ON_BLOCKED_GOVERNANCE: bool = True
    QA_MODEL_REGISTRY_FAIL_ON_MISSING_CARD: bool = False

    OPS_INCLUDE_MODEL_REGISTRY: bool = True
    REPORT_INCLUDE_MODEL_REGISTRY: bool = True
    RESEARCH_AUTO_LOG_MODEL_REGISTRY: bool = False
"""

# Insert before 'def check_drift_settings' or just before 'def get_settings'
if "def get_settings()" in content:
    content = content.replace("def get_settings()", registry_settings + "\n\n" + "def get_settings()")
    with open(settings_path, "w") as f:
        f.write(content)
    print("Updated settings")
else:
    print("Could not find get_settings in settings.py")
