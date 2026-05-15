with open("bist_signal_bot/tests/test_cli_quality.py", "r") as f:
    content = f.read()

# Fix mock results by making the MagicMock return what format_quality_result_text expects
content = content.replace('''mock_result = MagicMock()
    mock_result.summary.return_value = {"run_id": "123", "status": "PASS", "gate_level": "STD", "suite": "FAST", "checks_total": 0, "checks_passed": 0, "checks_warn": 0, "checks_failed": 0, "checks_skipped": 0, "elapsed_seconds": 0.0}
    mock_result.test_summary = None
    mock_result.coverage_summary = None
    mock_result.static_summary = None
    mock_result.disclaimer = ""''', '''
    mock_result = MagicMock()
    mock_result.summary.return_value = {"run_id": "123", "status": "PASS", "gate_level": "STD", "suite": "FAST", "checks_total": 0, "checks_passed": 0, "checks_warn": 0, "checks_failed": 0, "checks_skipped": 0, "elapsed_seconds": 0.0}
    mock_result.test_summary = None
    mock_result.coverage_summary = None
    mock_result.static_summary = None
    mock_result.disclaimer = ""
    mock_result.passed.return_value = True''')

with open("bist_signal_bot/tests/test_cli_quality.py", "w") as f:
    f.write(content)
