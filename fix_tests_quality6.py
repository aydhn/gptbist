with open("bist_signal_bot/tests/test_cli_quality.py", "r") as f:
    content = f.read()

content = content.replace('''
    from bist_signal_bot.quality.models import QualityRunResult, QualityRunConfig, QualityCheckStatus
    config = QualityRunConfig()
    mock_result = QualityRunResult(run_id="123", config=config, status=QualityCheckStatus.PASS)
''', '''
    from bist_signal_bot.quality.models import QualityRunResult, QualityRunConfig, QualityCheckStatus
    config = QualityRunConfig()
    mock_result = QualityRunResult(run_id="123", config=config, status=QualityCheckStatus.PASS)
''')

content = content.replace('''mock_result.passed.return_value = True''', '')
content = content.replace('''mock_result.passed.return_value = False''', '')

with open("bist_signal_bot/tests/test_cli_quality.py", "w") as f:
    f.write(content)
