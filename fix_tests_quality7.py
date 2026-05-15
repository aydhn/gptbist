with open("bist_signal_bot/tests/test_cli_quality.py", "r") as f:
    content = f.read()

content = content.replace("mock_result = QualityRunResult(run_id=\"123\", config=config, status=QualityCheckStatus.PASS)",
"""
    class MockQualityRunResult:
        def __init__(self, passed_val=True):
            self.status = MagicMock()
            self.status.value = "PASS" if passed_val else "FAIL"
            self.config = MagicMock()
            self.config.suite.value = "FAST"
            self.config.gate_level.value = "STD"
            self.test_summary = None
            self.coverage_summary = None
            self.static_summary = None
            self.disclaimer = ""
            self.run_id = "123"
            self.elapsed_seconds = 0.0
            self.checks = []
            self.passed_val = passed_val
        def summary(self):
            return {"run_id": "123", "status": "PASS", "gate_level": "STD", "suite": "FAST", "checks_total": 0, "checks_passed": 0, "checks_warn": 0, "checks_failed": 0, "checks_skipped": 0, "elapsed_seconds": 0.0}
        def failed_checks(self):
            return []
        def passed(self):
            return self.passed_val

    mock_result = MockQualityRunResult(passed_val=True)
""")

content = content.replace("mock_result = QualityRunResult(run_id=\"123\", config=config, status=QualityCheckStatus.FAIL)",
"""mock_result = MockQualityRunResult(passed_val=False)""")

with open("bist_signal_bot/tests/test_cli_quality.py", "w") as f:
    f.write(content)
