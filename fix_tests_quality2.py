import re

# Fix test_parse_pytest_summary properly
with open("bist_signal_bot/quality/test_runner.py", "r") as f:
    content = f.read()

# Make parser work with standard outputs like '=== 3 passed, 1 failed, 2 warnings in 0.12s ==='
content = content.replace(
    'passed = output.count(" PASSED ") + output.count(" passed ")',
    '''import re
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        m_pass = re.search(r"(\\d+) passed", output)
        if m_pass: passed = int(m_pass.group(1))
        m_fail = re.search(r"(\\d+) failed", output)
        if m_fail: failed = int(m_fail.group(1))
        m_skip = re.search(r"(\\d+) skipped", output)
        if m_skip: skipped = int(m_skip.group(1))
        m_err = re.search(r"(\\d+) error", output)
        if m_err: errors = int(m_err.group(1))
'''
)
content = content.replace('failed = output.count(" FAILED ") + output.count(" failed ")', '')
content = content.replace('skipped = output.count(" SKIPPED ") + output.count(" skipped ")', '')
content = content.replace('errors = output.count(" ERROR ") + output.count(" errors ")', '')

with open("bist_signal_bot/quality/test_runner.py", "w") as f:
    f.write(content)

# Fix test_gate_eval_release_missing_tools
with open("bist_signal_bot/quality/gate.py", "r") as f:
    content = f.read()

content = content.replace(
    "from bist_signal_bot.quality.models import (",
    "from bist_signal_bot.quality.models import (\n    QualityTool,"
)

with open("bist_signal_bot/quality/gate.py", "w") as f:
    f.write(content)

# Fix CLI mocks
with open("bist_signal_bot/tests/test_cli_quality.py", "r") as f:
    content = f.read()

content = content.replace(
    'mock_result = MagicMock()',
    '''mock_result = MagicMock()
    mock_result.summary.return_value = {"run_id": "123", "status": "PASS", "gate_level": "STD", "suite": "FAST", "checks_total": 0, "checks_passed": 0, "checks_warn": 0, "checks_failed": 0, "checks_skipped": 0, "elapsed_seconds": 0.0}
    mock_result.test_summary = None
    mock_result.coverage_summary = None
    mock_result.static_summary = None
    mock_result.disclaimer = ""'''
)

with open("bist_signal_bot/tests/test_cli_quality.py", "w") as f:
    f.write(content)

# Fix coverage test string type error
with open("bist_signal_bot/tests/test_quality_coverage.py", "r") as f:
    content = f.read()

content = content.replace('res.stdout = "Name  Stmts  Miss  Cover\\n-------------------------\\nTOTAL    100    50    50%"', "res.stdout = \"Name  Stmts  Miss  Cover\\n-------------------------\\nTOTAL    100    50    50%\"\n        res.stderr = \"\"")

with open("bist_signal_bot/tests/test_quality_coverage.py", "w") as f:
    f.write(content)
