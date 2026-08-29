from bist_signal_bot.reports.sections import ReportSectionBuilder, append_final_handoff_section, add_drift_section
from bist_signal_bot.reports.models import ReportConfig, ReportDataBundle, ReportType
from unittest.mock import patch, MagicMock

def test_build_disclaimer():
    builder = ReportSectionBuilder()
    config = ReportConfig()
    section = builder.build_disclaimer_section(config)
    assert section.title == "Disclaimer"
    assert "Not investment advice" in section.body_markdown

def test_build_executive_summary():
    builder = ReportSectionBuilder()
    bundle = ReportDataBundle(report_type=ReportType.DAILY)
    config = ReportConfig()
    section = builder.build_executive_summary(bundle, config)
    assert section.title == "Executive Summary"

def test_append_final_handoff_section_disabled():
    class MockSettings:
        ENABLE_FINAL_HANDOFF = False

    section = append_final_handoff_section(MockSettings())
    assert section.title == "Final Handoff"
    assert "disabled" in section.body_markdown

@patch("bist_signal_bot.app.final_handoff_app.create_final_handoff_store")
def test_append_final_handoff_section_exception(mock_create_store):
    mock_create_store.side_effect = Exception("Test Exception")
    class MockSettings:
        ENABLE_FINAL_HANDOFF = True

    section = append_final_handoff_section(MockSettings())
    assert section.title == "Final MVP Handoff"
    assert "Failed to load" in section.body_markdown
    assert "Test Exception" in section.body_markdown

@patch("bist_signal_bot.app.final_handoff_app.create_final_handoff_store")
def test_append_final_handoff_section_success(mock_create_store):
    mock_store = MagicMock()
    mock_manifest = MagicMock()
    mock_manifest.final_status.value = "APPROVED"
    mock_manifest.go_no_go_decision = "GO"
    mock_store.load_latest_manifest.return_value = mock_manifest

    mock_pack = MagicMock()
    mock_pack.stage.value = "READY"
    mock_store.load_latest_release_pack.return_value = mock_pack

    mock_create_store.return_value = mock_store

    class MockSettings:
        ENABLE_FINAL_HANDOFF = True

    section = append_final_handoff_section(MockSettings())
    assert section.title == "Final MVP Handoff"
    assert "APPROVED" in section.body_markdown
    assert "GO" in section.body_markdown
    assert "READY" in section.body_markdown

@patch("bist_signal_bot.app.final_handoff_app.create_final_handoff_store")
def test_append_final_handoff_section_success_no_data(mock_create_store):
    mock_store = MagicMock()
    mock_store.load_latest_manifest.return_value = None
    mock_store.load_latest_release_pack.return_value = None

    mock_create_store.return_value = mock_store

    class MockSettings:
        ENABLE_FINAL_HANDOFF = True

    section = append_final_handoff_section(MockSettings())
    assert section.title == "Final MVP Handoff"
    assert "No final handoff data found" in section.body_markdown

@patch("bist_signal_bot.drift.reporting.format_drift_result_text")
def test_add_drift_section(mock_format):
    mock_format.return_value = "Mocked Drift Result"
    mock_result = {"some": "result"}

    output = add_drift_section(mock_result)

    mock_format.assert_called_once_with(mock_result)
    assert "\n--- Drift & Decay Monitoring ---\n" in output
    assert "Mocked Drift Result" in output
