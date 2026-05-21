import re

filepath = "bist_signal_bot/core/exceptions.py"
with open(filepath, "r") as f:
    content = f.read()

# Make sure BistBotError exists at the top before using it
if "class BistBotError" not in content:
    # Actually wait, BistBotError might be defined elsewhere in core.exceptions, but wait, this file is core.exceptions!
    print("Finding BistBotError definition...")
