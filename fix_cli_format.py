filepath = "bist_signal_bot/cli/commands.py"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace("from .formatting import format_json", "")

with open(filepath, "w") as f:
    f.write(content)
