import pytest
from pathlib import Path
from bist_signal_bot.final_audit.release_candidate import ReleaseCandidateBuilder

def test_release_candidate_builder_modules():
    builder = ReleaseCandidateBuilder()
    cand = builder.build_candidate()
    assert "core" in cand.included_modules
    assert cand.module_statuses["core"] == "PASS"

def test_release_candidate_checksums(tmp_path):
    builder = ReleaseCandidateBuilder(base_dir=tmp_path)
    # mock files
    d = tmp_path / "bist_signal_bot"
    d.mkdir()
    (d / "a.py").write_text("x=1")

    cand = builder.build_candidate()
    assert len(cand.checksum_manifest) > 0
    assert "bist_signal_bot/a.py" in cand.checksum_manifest
