import sys

# 1. test_monitoring_alerts.py
with open("bist_signal_bot/tests/test_monitoring_alerts.py", "r") as f:
    content = f.read()

content = content.replace('def send_message(self, message):', 'def send_message(self, message, **kwargs):')

with open("bist_signal_bot/tests/test_monitoring_alerts.py", "w") as f:
    f.write(content)

# 2. test_monitoring_diagnostics.py
with open("bist_signal_bot/tests/test_monitoring_diagnostics.py", "r") as f:
    content = f.read()

content = content.replace('def load(self):', 'def load(self):\n        class MockState:\n            def __init__(self, running):\n                self.is_running = running\n                self.current_run_id = "test"\n        return MockState(self.running)')
content = content.replace('from bist_signal_bot.runtime.models import RuntimeState', '')

with open("bist_signal_bot/tests/test_monitoring_diagnostics.py", "w") as f:
    f.write(content)

# 3. test_monitoring_metrics.py
with open("bist_signal_bot/tests/test_monitoring_metrics.py", "r") as f:
    content = f.read()

content = content.replace('RuntimePipelineConfig(strategy_name="test", source="mock", symbols=[])', 'RuntimePipelineConfig(strategy_name="test", source="mock", symbols=["ASELS"], universe_mode="SYMBOLS")')

with open("bist_signal_bot/tests/test_monitoring_metrics.py", "w") as f:
    f.write(content)

# 4. test_runtime_monitoring_integration.py
with open("bist_signal_bot/tests/test_runtime_monitoring_integration.py", "r") as f:
    content = f.read()

content = content.replace('def scan(self, req):', 'def scan(self, *args, **kwargs):')

with open("bist_signal_bot/tests/test_runtime_monitoring_integration.py", "w") as f:
    f.write(content)

# 5. test_cli_monitor.py
with open("bist_signal_bot/tests/test_cli_monitor.py", "r") as f:
    content = f.read()

content = content.replace('def parse_arguments(args):\n    original_argv = sys.argv\n    sys.argv = ["bist_signal_bot"] + args\n    try:\n        parsed = parse_args()\n        return parsed\n    finally:\n        sys.argv = original_argv', 'def parse_arguments(args):\n    return parse_args(args)')
content = content.replace('from bist_signal_bot.cli.parsers import parse_args', 'from bist_signal_bot.cli.parsers import parse_args')

with open("bist_signal_bot/tests/test_cli_monitor.py", "w") as f:
    f.write(content)

# 6. test_healthcheck_monitoring.py
with open("bist_signal_bot/tests/test_healthcheck_monitoring.py", "r") as f:
    content = f.read()

content = content.replace('run_healthcheck(s)', 'run_healthcheck(settings=s)')

with open("bist_signal_bot/tests/test_healthcheck_monitoring.py", "w") as f:
    f.write(content)
