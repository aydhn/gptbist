import pytest
from bist_signal_bot.runtime.pipelines import RuntimePipelineBuilder
from bist_signal_bot.runtime.models import RuntimePipelineConfig, RuntimeJobType
from bist_signal_bot.core.exceptions import RuntimeValidationError

def test_pipeline_builder_steps():
    config = RuntimePipelineConfig(
        strategy_name="test",
        use_ml_filter=True,
        ml_model_id="model-1",
        use_regime_filter=True,
        use_paper=True,
        send_telegram=True
    )

    steps = RuntimePipelineBuilder.build_runtime_pipeline_steps(config)

    assert RuntimeJobType.HEALTHCHECK in steps
    assert RuntimeJobType.SIGNAL_SCAN in steps
    assert RuntimeJobType.REGIME_ANALYSIS in steps
    assert RuntimeJobType.ML_INFERENCE in steps
    assert RuntimeJobType.PAPER_RUN in steps
    assert RuntimeJobType.TELEGRAM_SUMMARY in steps

def test_pipeline_builder_validation():
    config = RuntimePipelineConfig(strategy_name="")
    with pytest.raises(RuntimeValidationError):
        RuntimePipelineBuilder.validate_pipeline_config(config)

    config = RuntimePipelineConfig(strategy_name="test", use_ml_filter=True, ml_model_id="")
    with pytest.raises(RuntimeValidationError):
        RuntimePipelineBuilder.validate_pipeline_config(config)
