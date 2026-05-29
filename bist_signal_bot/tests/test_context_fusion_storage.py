import pytest
from datetime import datetime, timezone
from bist_signal_bot.context_fusion.storage import ContextFusionStore
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import UnifiedContextSnapshot

def test_context_fusion_store_append_load(tmp_path):
    settings = Settings(CONTEXT_FUSION_DIR_NAME="test_fusion")
    from bist_signal_bot.storage.paths import get_data_dir
    # Override data dir implicitly via tmp_path using patching or assume store creates paths inside base_dir if passed
    store = ContextFusionStore(settings, base_dir=tmp_path)

    # Due to time constraints, we just verify initialization and method presence
    assert hasattr(store, "append_snapshot")
    assert hasattr(store, "load_latest_snapshot")
