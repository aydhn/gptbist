import pytest
from bist_signal_bot.release_policy.change_control import ChangeControlManager
from bist_signal_bot.release_policy.models import ChangeType, ChangeRiskLevel, VersionBumpType
from bist_signal_bot.release_policy.changelog import ChangelogBuilder
from bist_signal_bot.release_policy.migrations import MigrationNoteBuilder
from bist_signal_bot.release_policy.versioning import VersionGovernanceEngine

def test_change_control():
    manager = ChangeControlManager()
    req = manager.create_change_request("Title", "Break everything", ChangeType.BREAKING, ["core"])
    assert req.requires_migration is True
    assert req.proposed_version_bump == VersionBumpType.MAJOR

    req2 = manager.create_change_request("Sec update", "vuln fix", ChangeType.SECURITY, ["core"], ChangeRiskLevel.CRITICAL)
    assert req2.risk_level == ChangeRiskLevel.CRITICAL

def test_version_engine():
    engine = VersionGovernanceEngine()
    assert engine.parse_semver("1.0.0") == {"major": 1, "minor": 0, "patch": 0}
    assert engine.is_valid_semver("not_a_version") is False
    assert engine.compare_versions("1.0.0", "1.1.0") == -1

def test_changelog():
    manager = ChangeControlManager()
    builder = ChangelogBuilder()

    req = manager.create_change_request("Title", "Desc", ChangeType.FEATURE, ["core"])
    entries = builder.build_changelog_entries([req], "1.0.0")
    assert len(entries) == 1

    req_bad = manager.create_change_request("Title", "investment advice", ChangeType.FEATURE, ["core"])
    entries_bad = builder.build_changelog_entries([req_bad], "1.0.0")
    errors = builder.validate_changelog(entries_bad)
    assert len(errors) == 1

def test_migration_notes():
    manager = ChangeControlManager()
    builder = MigrationNoteBuilder()

    req = manager.create_change_request("Title", "Desc", ChangeType.SCHEMA, ["core"])
    notes = builder.build_migration_notes([req], "0.9.0", "1.0.0")
    assert len(notes) == 1
    assert notes[0].steps != []
