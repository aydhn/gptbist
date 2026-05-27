import os

cli_path = "bist_signal_bot/cli/commands.py"
with open(cli_path, "r") as f:
    content = f.read()

content = content.replace("def run_financials_command", "from pathlib import Path\ndef run_financials_command")

with open(cli_path, "w") as f:
    f.write(content)
