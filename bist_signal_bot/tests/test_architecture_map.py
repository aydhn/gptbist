from bist_signal_bot.docs_hub.architecture import ArchitectureMapBuilder

def test_architecture_builder():
    builder = ArchitectureMapBuilder()
    amap = builder.build_map()
    assert amap.module_count > 0
