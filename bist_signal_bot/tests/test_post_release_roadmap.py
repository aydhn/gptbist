import pytest
from bist_signal_bot.final_handoff.roadmap import PostReleaseRoadmapBuilder

def test_roadmap_builder_items():
    builder = PostReleaseRoadmapBuilder()
    items = builder.build_roadmap()
    assert len(items) > 0
    assert any("Performance Optimization" in i.title for i in items)

def test_roadmap_builder_validation():
    builder = PostReleaseRoadmapBuilder()
    items = builder.build_roadmap()
    # mock a bad item
    items[0].description = "This will guarantee profit."
    warnings = builder.validate_roadmap(items)
    assert len(warnings) > 0
