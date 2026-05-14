with open("bist_signal_bot/cli/main.py", "r") as f:
    content = f.read()
if "monitor" not in content:
    content = content.replace(
        "        \"runtime\": lambda a, c: __import__(\"bist_signal_bot.cli.commands\", fromlist=[\"cmd_runtime\"]).cmd_runtime(a, c.settings),\n\n        \"ml-dataset\"",
        "        \"runtime\": lambda a, c: __import__(\"bist_signal_bot.cli.commands\", fromlist=[\"cmd_runtime\"]).cmd_runtime(a, c.settings),\n        \"monitor\": lambda a, c: __import__(\"bist_signal_bot.cli.commands\", fromlist=[\"cmd_monitor\"]).cmd_monitor(a, c.settings),\n\n        \"ml-dataset\""
    )
    # also add it to the choices list if needed but usually it is done in parser
with open("bist_signal_bot/cli/main.py", "w") as f:
    f.write(content)
