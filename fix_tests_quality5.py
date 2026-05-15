with open("bist_signal_bot/tests/test_cli_quality.py", "r") as f:
    content = f.read()

# Fix mock results so format_quality_result_text works properly
content = content.replace('''
    mock_result = MagicMock()
    mock_result.summary.return_value = {"run_id": "123", "status": "PASS", "gate_level": "STD", "suite": "FAST", "checks_total": 0, "checks_passed": 0, "checks_warn": 0, "checks_failed": 0, "checks_skipped": 0, "elapsed_seconds": 0.0}
    mock_result.test_summary = None
    mock_result.coverage_summary = None
    mock_result.static_summary = None
    mock_result.disclaimer = ""
    mock_result.passed.return_value = True''', '''
    from bist_signal_bot.quality.models import QualityRunResult, QualityRunConfig, QualityCheckStatus
    config = QualityRunConfig()
    mock_result = QualityRunResult(run_id="123", config=config, status=QualityCheckStatus.PASS)
''')

content = content.replace('''
    mock_result = MagicMock()
    mock_result.passed.return_value = False''', '''
    from bist_signal_bot.quality.models import QualityRunResult, QualityRunConfig, QualityCheckStatus
    config = QualityRunConfig()
    mock_result = QualityRunResult(run_id="123", config=config, status=QualityCheckStatus.FAIL)
''')

with open("bist_signal_bot/tests/test_cli_quality.py", "w") as f:
    f.write(content)
