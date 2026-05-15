with open("bist_signal_bot/tests/test_cli_quality.py", "r") as f:
    content = f.read()

# Make the magicmock just return standard float for elapsed seconds
# Actually, the issue is mock_result.summary() returns a magic mock dict where the values are magic mocks
# We need to make sure summary() returns a real dict

content = content.replace('''
        def summary(self):
            return {"run_id": "123", "status": "PASS", "gate_level": "STD", "suite": "FAST", "checks_total": 0, "checks_passed": 0, "checks_warn": 0, "checks_failed": 0, "checks_skipped": 0, "elapsed_seconds": 0.0}
''', '''
        def summary(self):
            return {"run_id": "123", "status": "PASS", "gate_level": "STD", "suite": "FAST", "checks_total": 0, "checks_passed": 0, "checks_warn": 0, "checks_failed": 0, "checks_skipped": 0, "elapsed_seconds": 0.0}
''')

# Well, let's just make the run mock return a proper QualityRunResult so it isn't a mock at all
# I'll rewrite test_cli_quality.py
