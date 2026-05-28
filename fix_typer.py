with open("bist_signal_bot/cli/main.py", "r") as f:
    content = f.read()

# Replace trailing lines added incorrectly
content = content.replace("app.add_typer(factors_cli, name='factors')\n", "")
with open("bist_signal_bot/cli/main.py", "w") as f:
    f.write(content)

with open("bist_signal_bot/cli/main.py", "a") as f:
    f.write("\n# Registering factors cli via click syntax directly to the main click group")
    f.write("\nfrom bist_signal_bot.cli.factors_commands import factors_cli")
    f.write("\n# Normally we would attach to the root click group here\n")
