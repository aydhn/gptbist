import pytest
from bist_signal_bot.runtime.pipelines import RuntimePipelineConfig

def test_runtime_pipeline_config_fields():
    config = RuntimePipelineConfig()
    assert hasattr(config, 'telegram_digest_after_run')
    assert hasattr(config, 'telegram_send_runtime_summary')
    assert hasattr(config, 'telegram_dry_run')
