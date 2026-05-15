with open("bist_signal_bot/tests/test_cli_quality.py", "r") as f:
    content = f.read()

content = content.replace('patch("bist_signal_bot.cli.commands.create_quality_gate_runner")', 'patch("bist_signal_bot.cli.commands.create_quality_gate_runner")')
# Wait, looking at the error:
# AttributeError: <module 'bist_signal_bot.cli.commands' from '/app/bist_signal_bot/cli/commands.py'> does not have the attribute 'create_quality_gate_runner'
# It seems the `create_quality_gate_runner` is NOT imported at module level in cli/commands.py
# Ah, it's imported INSIDE handle_quality_command!
# from bist_signal_bot.app.quality_app import create_quality_gate_runner

content = content.replace(
    '@patch("bist_signal_bot.cli.commands.create_quality_gate_runner")',
    '@patch("bist_signal_bot.app.quality_app.QualityGateRunner")'
)

with open("bist_signal_bot/tests/test_cli_quality.py", "w") as f:
    f.write(content)
