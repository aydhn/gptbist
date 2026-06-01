import pytest
from bist_signal_bot.final_handoff.release_pack import FinalReleasePackBuilder
from bist_signal_bot.final_handoff.models import ReleasePackStage

def test_release_pack_builder_docs_manifests():
    builder = FinalReleasePackBuilder()
    pack = builder.build_release_pack(stage=ReleasePackStage.DRAFT)
    assert len(pack.included_docs) > 0
    assert pack.stage == ReleasePackStage.DRAFT

def test_release_pack_builder_checksum():
    builder = FinalReleasePackBuilder()
    sums = builder.checksum_manifest(["test"])
    assert len(sums) > 0
