from bist_signal_bot.config.settings import Settings
from bist_signal_bot.governance.models import EvidencePackRequest
from bist_signal_bot.governance.evidence import EvidencePackBuilder

def test_evidence_pack_dry_run(tmp_path):
    settings = Settings()
    builder = EvidencePackBuilder(settings, base_dir=tmp_path)

    request = EvidencePackRequest(pack_name="test_pack", dry_run=True)
    manifest = builder.build_pack(request)

    assert manifest.archive_path is None
    assert "Dry run mode enabled" in manifest.warnings[0]

def test_evidence_pack_creates_archive(tmp_path):
    settings = Settings()
    builder = EvidencePackBuilder(settings, base_dir=tmp_path)

    request = EvidencePackRequest(pack_name="test_pack", dry_run=False, output_dir=str(tmp_path))
    manifest = builder.build_pack(request)

    assert manifest.archive_path is not None
    assert manifest.checksum_sha256 is not None
