from bist_signal_bot.reports.sections import add_drift_section
from unittest.mock import patch

@patch("bist_signal_bot.drift.reporting.format_drift_result_text")
def test_add_drift_section(mock_format):
    mock_format.return_value = "Mocked Drift Result"
    mock_result = {"some": "result"}

    output = add_drift_section(mock_result)

    mock_format.assert_called_once_with(mock_result)
    assert "\n--- Drift & Decay Monitoring ---\n" in output
    assert "Mocked Drift Result" in output

test_add_drift_section()
print("Success")
