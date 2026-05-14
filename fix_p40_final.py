with open("bist_signal_bot/tests/test_monitoring_alerts.py", "r") as f:
    c = f.read()
c = c.replace('def send_message(self, message, **kwargs):', 'def send_message(self, message, *args, **kwargs):')
with open("bist_signal_bot/tests/test_monitoring_alerts.py", "w") as f:
    f.write(c)

with open("bist_signal_bot/tests/test_monitoring_metrics.py", "r") as f:
    c = f.read()
c = c.replace('RuntimePipelineConfig(strategy_name="test", source="mock", symbols=["ASELS"], universe_mode="SYMBOLS")', 'RuntimePipelineConfig(strategy_name="test", source="mock", symbols=["ASELS"])')
with open("bist_signal_bot/tests/test_monitoring_metrics.py", "w") as f:
    f.write(c)

with open("bist_signal_bot/tests/test_runtime_monitoring_integration.py", "r") as f:
    c = f.read()
c = c.replace('RuntimePipelineConfig(strategy_name="test", source="mock", symbols=["ASELS"], universe_mode="SYMBOLS")', 'RuntimePipelineConfig(strategy_name="test", source="mock", symbols=["ASELS"])')
with open("bist_signal_bot/tests/test_runtime_monitoring_integration.py", "w") as f:
    f.write(c)

with open("bist_signal_bot/tests/test_healthcheck_monitoring.py", "r") as f:
    c = f.read()
c = c.replace('run_healthcheck(settings=s)', 'run_healthcheck(s)')
with open("bist_signal_bot/tests/test_healthcheck_monitoring.py", "w") as f:
    f.write(c)
